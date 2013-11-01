#!/usr/bin/env python

# Copyright 2005, 2006 Free Software Foundation, Inc.
 
# This file is part of GNU Radio
 
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
 
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
 
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.


# Projectname: uwicore@umh_80211_MAC

# Filename: uwicore_mac_utils.py

# This python file includes all the methods involving MAC tasks, such as carrier sensing, 
# fragmentation and re-assembly tasks, generation of 802.11 compliant frames and send-to and 
# receive-from PHY layer mechanisms. The original PHY code was developed by FTW (Forschungszentrum 
# Telekommunikation Wien / Telecommunications Research Center Vienna, http://www.ftw.at). The code 
# was first presented and described in the following publication:

# P.Fuxjaeger, A. Costantini, D. Valerio, P. Castiglione, G. Zacheo, T. Zemen and F. Ricciato, "IEEE 802.11p Transmission Using GNURadio", in Proceedings of the IEEE Karlsruhe Workshop on Software Radios (WSR10), pp. 1-4, 2010.

# The Uwicore Laboratory at the University Miguel Hernandez of Elche has added additional 
# functionalities to the FTW PHY code, in particular: Carrier Sensing functions, and 
# reconfigurability of the transmission GNU radio graph to allow for the possibility to 
# transmit different MAC frames (also of varying size). In addition, the Uwicore PHY 
# contribution communicates with the MAC layer, and is capable to process requests from 
# the MAC to sense or to transmit a packet to the wireless medium. 

# The FTW OFMD code triggers the encoding procedures and sends the complex baseband 
# signal to the USRP2 sink. The Uwicore carrier sensing function, based on the example 
# 'USRP_spectrum_sense' provided by GNU Radio, estimates the power of the signal using
# the signal's Power Spectrum Density (PSD).

# Ubiquitous Wireless Communications Research Laboratory 
# Uwicore, http://www.uwicore.umh.es
# Communications Engineering Department
# University Miguel Hernandez of Elche
# Avda de la Universidad, s/n
# 03202 Elche, Spain

# Release: April 2011

# Original FTW PHY code authors:
#	Andrea Costantini 
#	Paul Fuxjaeger (fuxjaeger@ftw.at)
#	Danilo Valerio (valerio@ftw.at)
#	Paolo Castiglione (castiglione@ftw.at)
#	Giammarco Zacheo (zacheo@ftw.at)

# Authors of the PHY added functionalities:
#	Juan R. Gutierrez-Agullo (jgutierrez@umh.es)
#	Baldomero Coll-Perales (bcoll@umh.es)
#	Dr. Javier Gozalvez (j.gozalvez@umh.es)


from gnuradio import gru, gr#, ftw
import gnuradio.ieee802_11 as gr_ieee802_11
import struct, numpy, math, sys, time
import socket, pickle, random

""" Generate an 802.11 compliant Beacon frame """
def get_BEACON_info(payload, regime, symboltime):

        # MAC header for a BEACON FRAME 
    mac_framectrl = chr(0b10000000) + chr(0x00)                                                  
    mac_duration = chr(0x00) + chr(0x00)                                                  
    mac_address1  = chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff)  
    mac_address2 = payload["address2"]
    mac_address3 = chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff) 
    time_stamp,tiempo = timestamp()
    BI = beacon_int(payload["BI"])
    capability_info = chr(0x00) + chr(0x00)
    mac_seqctrl = calculate_seq_control(payload["N_SEQ"],payload["N_FRAG"])
    
        # pre-assemble the MPDU (duration is filled with dummy and CRC32 is missing at this point)
    packet = mac_framectrl + mac_duration + mac_address1 + mac_address2 + mac_address3 + mac_seqctrl + time_stamp + BI + capability_info 
        # switch coding rate and constellation according to regime profile
    if (regime == "1"):
        modulation = "bpsk"
        rate = 1 / float(2)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "2"):
        modulation = "bpsk"
        rate = 3 / float(4)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "3"):
        modulation = "qpsk"
        rate = 1 / float(2)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "4"):
        modulation = "qpsk"
        rate = 3 / float(4)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "5"):
        modulation = "qam16"
        rate = 1 / float(2)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "6"):
        modulation = "qam16"
        rate = 3 / float(4)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "7"):
        modulation = "qam64"
        rate = 2 / float(3)
        N_cbps = 288
        N_bpsc = 6
    elif(regime == "8"):
        modulation = "qam64"
        rate = 3 / float(4)
        N_cbps = 288
        N_bpsc = 6
    
    # uncoded bits per OFDM symbol
    N_dbps = int(N_cbps * rate)    

    # number of DATA symbols the frame needs to have
    # 16 service bits, 32 crc bits and 6 tail bits need to be included
    N_sym = int(math.ceil((16 + 32 + 6 + 8 * len(packet)) / float(N_dbps)))

    # airtime of frame in microseconds
    # the additional 2 at the end of this formula is not in the 
    # standard encoding rules but in the annex G reference frame it is there!
    txtime = int(5 * symboltime + symboltime * N_sym) + 2 
    mac_duration = chr((txtime >> 8) & 0xff) + chr(txtime & 0xff)
    
    # number of uncoded bits that could be sent using N_sym DATA OFDM symbols 
    N_data = int(N_sym * N_dbps)

    # number of (uncoded) padding bits that need to be added at the end
    N_pad = N_data - (16 + 32 + 6 + 8 * len(packet))

        # assemble the MPDU (now duration is correct)
    packet = mac_framectrl + mac_duration + mac_address1 + mac_address2 + mac_address3 + mac_seqctrl + time_stamp + BI + capability_info

    dic = {"packet":packet, "packet_len":(len(packet) + 4), "txtime":txtime, "mac_duration":mac_duration, "modulation":modulation, \
           "rate":rate, "N_sym":N_sym, "N_data":N_data, "N_pad":N_pad, "N_cbps":N_cbps, "N_bpsc":N_bpsc, "N_dbps":N_dbps, \
           "mac_add1":mac_address1, "mac_add2":mac_address2,"N_SEQ":payload["N_SEQ"],"N_FRAG":payload["N_FRAG"], "MF":0, \
           "timestamp":tiempo, "BI":payload["BI"]}        
        
    return dic

""" Generate an 802.11 compliant CTS frame """
def get_CTS_info(payload, regime, symboltime):

        # MAC header for a CTS CONTROL FRAME 
    mac_framectrl = chr(0xc4) + chr(0x00)                                                  
    mac_duration = chr(0x00) + chr(0x00)
    mac_ra = payload["mac_ra"]                                                  
      
    
        # pre-assemble the MPDU (duration is filled with dummy and CRC32 is missing at this point)
    packet = mac_framectrl + mac_duration + mac_ra

        # switch coding rate and constellation according to regime profile
    if (regime == "1"):
        modulation = "bpsk"
        rate = 1 / float(2)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "2"):
        modulation = "bpsk"
        rate = 3 / float(4)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "3"):
        modulation = "qpsk"
        rate = 1 / float(2)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "4"):
        modulation = "qpsk"
        rate = 3 / float(4)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "5"):
        modulation = "qam16"
        rate = 1 / float(2)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "6"):
        modulation = "qam16"
        rate = 3 / float(4)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "7"):
        modulation = "qam64"
        rate = 2 / float(3)
        N_cbps = 288
        N_bpsc = 6
    elif(regime == "8"):
        modulation = "qam64"
        rate = 3 / float(4)
        N_cbps = 288
        N_bpsc = 6
    
    # uncoded bits per OFDM symbol
    N_dbps = int(N_cbps * rate)    

    # number of DATA symbols the frame needs to have
    # 16 service bits, 32 crc bits and 6 tail bits need to be included
    N_sym = int(math.ceil((16 + 32 + 6 + 8 * len(packet)) / float(N_dbps)))

    # airtime of frame in microseconds
    # the additional 2 at the end of this formula is not in the 
    # standard encoding rules but in the annex G reference frame it is there!
    txtime = int(5 * symboltime + symboltime * N_sym) + 2
    txtime = txtime + payload["duration"]
    txtime = int(txtime) + 1  
    mac_duration = chr((txtime >> 8) & 0xff) + chr(txtime & 0xff)
    
    # number of uncoded bits that could be sent using N_sym DATA OFDM symbols 
    N_data = int(N_sym * N_dbps)

    # number of (uncoded) padding bits that need to be added at the end
    N_pad = N_data - (16 + 32 + 6 + 8 * len(packet))

        # assemble the MPDU (now duration is correct)
    packet = mac_framectrl + mac_duration + mac_ra

    dic = {"packet":packet, "packet_len":(len(packet) + 4), "txtime":txtime, "mac_duration":mac_duration, "modulation":modulation, \
           "rate":rate, "N_sym":N_sym, "N_data":N_data, "N_pad":N_pad, "N_cbps":N_cbps, "N_bpsc":N_bpsc, "N_dbps":N_dbps, "RX_add":mac_ra, "timestamp":payload["timestamp"]}    

    return dic

""" Generate an 802.11 compliant RTS frame """
def get_RTS_info(payload, regime, symboltime):

        # MAC header for a RTS CONTROL FRAME 
    mac_framectrl = chr(0xb4) + chr(0x00)                                                  
    mac_duration = chr(0x00) + chr(0x00)
    mac_ra = payload["mac_ra"]
    mac_ta = payload["mac_ta"]                                                  
                                      
    
        # pre-assemble the MPDU (duration is filled with dummy and CRC32 is missing at this point)
    packet = mac_framectrl + mac_duration + mac_ra + mac_ta

        # switch coding rate and constellation according to regime profile
    if (regime == "1"):
        modulation = "bpsk"
        rate = 1 / float(2)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "2"):
        modulation = "bpsk"
        rate = 3 / float(4)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "3"):
        modulation = "qpsk"
        rate = 1 / float(2)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "4"):
        modulation = "qpsk"
        rate = 3 / float(4)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "5"):
        modulation = "qam16"
        rate = 1 / float(2)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "6"):
        modulation = "qam16"
        rate = 3 / float(4)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "7"):
        modulation = "qam64"
        rate = 2 / float(3)
        N_cbps = 288
        N_bpsc = 6
    elif(regime == "8"):
        modulation = "qam64"
        rate = 3 / float(4)
        N_cbps = 288
        N_bpsc = 6
    
    # uncoded bits per OFDM symbol
    N_dbps = int(N_cbps * rate)    

    # number of DATA symbols the frame needs to have
    # 16 service bits, 32 crc bits and 6 tail bits need to be included
    N_sym = int(math.ceil((16 + 32 + 6 + 8 * len(packet)) / float(N_dbps)))

    # airtime of frame in microseconds
    # the additional 2 at the end of this formula is not in the 
    # standard encoding rules but in the annex G reference frame it is there!
    txtime = int(5 * symboltime + symboltime * N_sym) + 2
    txtime = txtime + payload["duration"]  
    txtime = int(txtime) + 1  
    mac_duration = chr((txtime >> 8) & 0xff) + chr(txtime & 0xff)
    
    # number of uncoded bits that could be sent using N_sym DATA OFDM symbols 
    N_data = int(N_sym * N_dbps)

    # number of (uncoded) padding bits that need to be added at the end
    N_pad = N_data - (16 + 32 + 6 + 8 * len(packet))

        # assemble the MPDU (now duration is correct)
    packet = mac_framectrl + mac_duration + mac_ra + mac_ta

    dic = {"packet":packet, "packet_len":(len(packet) + 4), "txtime":txtime, "mac_duration":mac_duration, "modulation":modulation, \
           "rate":rate, "N_sym":N_sym, "N_data":N_data, "N_pad":N_pad, "N_cbps":N_cbps, "N_bpsc":N_bpsc, "N_dbps":N_dbps, "RX_add":mac_ra, "TX_add":mac_ta, "timestamp":payload["timestamp"]}    

    return dic

""" Generate an 802.11 compliant ACK frame """
def get_ACK_info(payload, regime, symboltime):

        # MAC header for a ACK CONTROL FRAME 
    mac_framectrl = chr(0xd4) + chr(0x00)                                                  
    mac_duration = chr(0x00) + chr(0x00)
    mac_ra = payload["mac_ra"]                                                  
    mac_seqctrl = chr(0x00) + chr(0x00)                                                  
    
        # pre-assemble the MPDU (duration is filled with dummy and CRC32 is missing at this point)
    packet = mac_framectrl + mac_duration + mac_ra

        # switch coding rate and constellation according to regime profile
    if (regime == "1"):
        modulation = "bpsk"
        rate = 1 / float(2)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "2"):
        modulation = "bpsk"
        rate = 3 / float(4)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "3"):
        modulation = "qpsk"
        rate = 1 / float(2)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "4"):
        modulation = "qpsk"
        rate = 3 / float(4)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "5"):
        modulation = "qam16"
        rate = 1 / float(2)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "6"):
        modulation = "qam16"
        rate = 3 / float(4)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "7"):
        modulation = "qam64"
        rate = 2 / float(3)
        N_cbps = 288
        N_bpsc = 6
    elif(regime == "8"):
        modulation = "qam64"
        rate = 3 / float(4)
        N_cbps = 288
        N_bpsc = 6
    
    # uncoded bits per OFDM symbol
    N_dbps = int(N_cbps * rate)    

    # number of DATA symbols the frame needs to have
    # 16 service bits, 32 crc bits and 6 tail bits need to be included
    N_sym = int(math.ceil((16 + 32 + 6 + 8 * len(packet)) / float(N_dbps)))

    # airtime of frame in microseconds
    # the additional 2 at the end of this formula is not in the 
    # standard encoding rules but in the annex G reference frame it is there!
    txtime = int(5 * symboltime + symboltime * N_sym) + 2   
    
    # number of uncoded bits that could be sent using N_sym DATA OFDM symbols 
    N_data = int(N_sym * N_dbps)

    # number of (uncoded) padding bits that need to be added at the end
    N_pad = N_data - (16 + 32 + 6 + 8 * len(packet))

        # assemble the MPDU
    packet = mac_framectrl + mac_duration + mac_ra

    dic = {"packet":packet, "packet_len":(len(packet) + 4), "txtime":txtime, "mac_duration":mac_duration, "modulation":modulation, \
           "rate":rate, "N_sym":N_sym, "N_data":N_data, "N_pad":N_pad, "N_cbps":N_cbps, "N_bpsc":N_bpsc, "N_dbps":N_dbps, "RX_add":mac_ra, "timestamp":time.time()}    

    return dic

""" Generate an 802.11 compliant Data frame for Test purposes """
def get_TEST(payload, regime, symboltime):

        # MAC header for a UNICAST DATA FRAME
    mac_framectrl = chr(0x08) + chr(0b00000000)                                               # this is a data frame
    mac_duration = chr(0x00) + chr(0x00)                                                  # dummy, value will be set by script
    mac_address1 = chr(0x00)+chr(0x18)+chr(0xde)+chr(0x12)+chr(0x0f)+chr(0x37)
    mac_address2 = chr(0x00)+chr(0x22)+chr(0x5f)+chr(0x3a)+chr(0x1f)+chr(0x51)
    mac_address3 = chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff)  # some BSSID mac-address
    mac_seqctrl = calculate_seq_control(payload["N_SEQ"],payload["N_FRAG"])
    
        # pre-assemble the MPDU (duration is filled with dummy and CRC32 is missing at this point)
    packet = mac_framectrl + mac_duration + mac_address1 + mac_address2 + mac_address3 + mac_seqctrl + payload["payload"]
        # switch coding rate and constellation according to regime profile (Igual que el estandar IEEE 802.11a)
    if (regime == "1"):
        modulation = "bpsk"
        rate = 1 / float(2)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "2"):
        modulation = "bpsk"
        rate = 3 / float(4)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "3"):
        modulation = "qpsk"
        rate = 1 / float(2)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "4"):
        modulation = "qpsk"
        rate = 3 / float(4)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "5"):
        modulation = "qam16"
        rate = 1 / float(2)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "6"):
        modulation = "qam16"
        rate = 3 / float(4)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "7"):
        modulation = "qam64"
        rate = 2 / float(3)
        N_cbps = 288
        N_bpsc = 6
    elif(regime == "8"):
        modulation = "qam64"
        rate = 3 / float(4)
        N_cbps = 288
        N_bpsc = 6
    
    # uncoded bits per OFDM symbol
    N_dbps = int(N_cbps * rate)    

    # number of DATA symbols the frame needs to have
    # 16 service bits, 32 crc bits and 6 tail bits need to be included
    N_sym = int(math.ceil((16 + 32 + 6 + 8 * len(packet)) / float(N_dbps)))

    # airtime of frame in microseconds
    # the additional 2 at the end of this formula is not in the 
    # standard encoding rules but in the annex G reference frame it is there!
    txtime = int(5 * symboltime + symboltime * N_sym) + 2 
    mac_duration = chr((txtime >> 8) & 0xff) + chr(txtime & 0xff)
    
    # number of uncoded bits that could be sent using N_sym DATA OFDM symbols 
    N_data = int(N_sym * N_dbps)

    # number of (uncoded) padding bits that need to be added at the end
    N_pad = N_data - (16 + 32 + 6 + 8 * len(packet))

        # assemble the MPDU (now duration is correct)
    packet = mac_framectrl + mac_duration + mac_address1 + mac_address2 + mac_address3 + mac_seqctrl + payload["payload"]

    dic = {"packet":packet, "packet_len":(len(packet) + 4), "txtime":txtime, "mac_duration":mac_duration, "modulation":modulation, \
           "rate":rate, "N_sym":N_sym, "N_data":N_data, "N_pad":N_pad, "N_cbps":N_cbps, "N_bpsc":N_bpsc, "N_dbps":N_dbps, \
           "mac_add1":mac_address1, "mac_add2":mac_address2,"N_SEQ":payload["N_SEQ"],"N_FRAG":payload["N_FRAG"], "MF":0, "PAYLOAD":payload["payload"], "timestamp":payload["timestamp"]}        
        
    return dic

""" Generate an 802.11 compliant retransmitted Data frame """
def get_retx_info(payload, regime, symboltime):

        # MAC header for a UNICAST RETRANSMITTED DATA FRAME 
    mac_framectrl = chr(0x08) + chr(0b00001000)                                               
    mac_duration = chr(0x00) + chr(0x00)                                     
    mac_address1 = payload["address1"]
    mac_address2 = payload["address2"]
    mac_address3 = chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff)  
    mac_seqctrl = calculate_seq_control(payload["N_SEQ"],payload["N_FRAG"])
    
        # pre-assemble the MPDU (duration is filled with dummy and CRC32 is missing at this point)
    packet = mac_framectrl + mac_duration + mac_address1 + mac_address2 + mac_address3 + mac_seqctrl + payload["payload"]
        # switch coding rate and constellation according to regime profile (Igual que el estandar IEEE 802.11a)
    if (regime == "1"):
        modulation = "bpsk"
        rate = 1 / float(2)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "2"):
        modulation = "bpsk"
        rate = 3 / float(4)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "3"):
        modulation = "qpsk"
        rate = 1 / float(2)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "4"):
        modulation = "qpsk"
        rate = 3 / float(4)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "5"):
        modulation = "qam16"
        rate = 1 / float(2)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "6"):
        modulation = "qam16"
        rate = 3 / float(4)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "7"):
        modulation = "qam64"
        rate = 2 / float(3)
        N_cbps = 288
        N_bpsc = 6
    elif(regime == "8"):
        modulation = "qam64"
        rate = 3 / float(4)
        N_cbps = 288
        N_bpsc = 6
    
    # uncoded bits per OFDM symbol
    N_dbps = int(N_cbps * rate)    

    # number of DATA symbols the frame needs to have
    # 16 service bits, 32 crc bits and 6 tail bits need to be included
    N_sym = int(math.ceil((16 + 32 + 6 + 8 * len(packet)) / float(N_dbps)))

    # airtime of frame in microseconds
    # the additional 2 at the end of this formula is not in the 
    # standard encoding rules but in the annex G reference frame it is there!
    txtime = int(5 * symboltime + symboltime * N_sym) + 2 
    mac_duration = chr((txtime >> 8) & 0xff) + chr(txtime & 0xff)
    
    # number of uncoded bits that could be sent using N_sym DATA OFDM symbols 
    N_data = int(N_sym * N_dbps)

    # number of (uncoded) padding bits that need to be added at the end
    N_pad = N_data - (16 + 32 + 6 + 8 * len(packet))

        # assemble the MPDU (now duration is correct)
    packet = mac_framectrl + mac_duration + mac_address1 + mac_address2 + mac_address3 + mac_seqctrl + payload["payload"]

    dic = {"packet":packet, "packet_len":(len(packet) + 4), "txtime":txtime, "mac_duration":mac_duration, "modulation":modulation, \
           "rate":rate, "N_sym":N_sym, "N_data":N_data, "N_pad":N_pad, "N_cbps":N_cbps, "N_bpsc":N_bpsc, "N_dbps":N_dbps, \
           "mac_add1":mac_address1, "mac_add2":mac_address2,"N_SEQ":payload["N_SEQ"],"N_FRAG":payload["N_FRAG"], "MF":0, "PAYLOAD":payload["payload"], "timestamp":payload["timestamp"]}        
        
        #DEBUG
    return dic

""" Generate an 802.11 compliant DATA frame """
def get_info(payload, regime, symboltime):

        # MAC header for a UNICAST DATA FRAME 
    mac_framectrl = chr(0x08) + chr(0b00000000)                                               # this is a data frame
    mac_duration = chr(0x00) + chr(0x00)                                                  # dummy, value will be set by script
    mac_address1 = payload["address1"]
    mac_address2 = payload["address2"]
    mac_address3 = chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff)  # some BSSID mac-address
    mac_seqctrl = calculate_seq_control(payload["N_SEQ"],payload["N_FRAG"])
    
        # pre-assemble the MPDU (duration is filled with dummy and CRC32 is missing at this point)
    packet = mac_framectrl + mac_duration + mac_address1 + mac_address2 + mac_address3 + mac_seqctrl + payload["payload"]
        # switch coding rate and constellation according to regime profile (Igual que el estandar IEEE 802.11a)
    if (regime == "1"):
        modulation = "bpsk"
        rate = 1 / float(2)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "2"):
        modulation = "bpsk"
        rate = 3 / float(4)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "3"):
        modulation = "qpsk"
        rate = 1 / float(2)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "4"):
        modulation = "qpsk"
        rate = 3 / float(4)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "5"):
        modulation = "qam16"
        rate = 1 / float(2)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "6"):
        modulation = "qam16"
        rate = 3 / float(4)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "7"):
        modulation = "qam64"
        rate = 2 / float(3)
        N_cbps = 288
        N_bpsc = 6
    elif(regime == "8"):
        modulation = "qam64"
        rate = 3 / float(4)
        N_cbps = 288
        N_bpsc = 6
    
    # uncoded bits per OFDM symbol
    N_dbps = int(N_cbps * rate)    

    # number of DATA symbols the frame needs to have
    # 16 service bits, 32 crc bits and 6 tail bits need to be included
    N_sym = int(math.ceil((16 + 32 + 6 + 8 * len(packet)) / float(N_dbps)))

    # airtime of frame in microseconds
    # the additional 2 at the end of this formula is not in the 
    # standard encoding rules but in the annex G reference frame it is there!
    txtime = int(5 * symboltime + symboltime * N_sym) + 2 
    mac_duration = chr((txtime >> 8) & 0xff) + chr(txtime & 0xff)
    
    # number of uncoded bits that could be sent using N_sym DATA OFDM symbols 
    N_data = int(N_sym * N_dbps)

    # number of (uncoded) padding bits that need to be added at the end
    N_pad = N_data - (16 + 32 + 6 + 8 * len(packet))

        # assemble the MPDU (now duration is correct)
    packet = mac_framectrl + mac_duration + mac_address1 + mac_address2 + mac_address3 + mac_seqctrl + payload["payload"]

    dic = {"packet":packet, "packet_len":(len(packet) + 4), "txtime":txtime, "mac_duration":mac_duration, "modulation":modulation, \
           "rate":rate, "N_sym":N_sym, "N_data":N_data, "N_pad":N_pad, "N_cbps":N_cbps, "N_bpsc":N_bpsc, "N_dbps":N_dbps, \
           "mac_add1":mac_address1, "mac_add2":mac_address2,"N_SEQ":payload["N_SEQ"],"N_FRAG":payload["N_FRAG"], "MF":0, "PAYLOAD":payload["payload"],"timestamp":payload["timestamp"]}        
        
        #DEBUG
    return dic

'''
# OLD Method 
def get_retx_info(payload, regime, symboltime):

        # MAC header for a UNICAST RETXED DATA FRAME 
    mac_framectrl = chr(0x08) + chr(0b00001000)                                             
    mac_duration = chr(0x00) + chr(0x00)                                                 
    mac_address1 = payload["address1"]
    mac_address2 = payload["address2"]
    mac_address3 = chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff)  
    mac_seqctrl = calculate_seq_control(payload["N_SEQ"],payload["N_FRAG"])
    
        # pre-assemble the MPDU (duration is filled with dummy and CRC32 is missing at this point)
    packet = mac_framectrl + mac_duration + mac_address1 + mac_address2 + mac_address3 + mac_seqctrl + payload["payload"]
        # switch coding rate and constellation according to regime profile (Igual que el estandar IEEE 802.11a)
    if (regime == "1"):
        modulation = "bpsk"
        rate = 1 / float(2)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "2"):
        modulation = "bpsk"
        rate = 3 / float(4)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "3"):
        modulation = "qpsk"
        rate = 1 / float(2)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "4"):
        modulation = "qpsk"
        rate = 3 / float(4)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "5"):
        modulation = "qam16"
        rate = 1 / float(2)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "6"):
        modulation = "qam16"
        rate = 3 / float(4)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "7"):
        modulation = "qam64"
        rate = 2 / float(3)
        N_cbps = 288
        N_bpsc = 6
    elif(regime == "8"):
        modulation = "qam64"
        rate = 3 / float(4)
        N_cbps = 288
        N_bpsc = 6
    
    # uncoded bits per OFDM symbol
    N_dbps = int(N_cbps * rate)    

    # number of DATA symbols the frame needs to have
    # 16 service bits, 32 crc bits and 6 tail bits need to be included
    N_sym = int(math.ceil((16 + 32 + 6 + 8 * len(packet)) / float(N_dbps)))

    # airtime of frame in microseconds
    # the additional 2 at the end of this formula is not in the 
    # standard encoding rules but in the annex G reference frame it is there!
    txtime = int(5 * symboltime + symboltime * N_sym) + 2 
    mac_duration = chr((txtime >> 8) & 0xff) + chr(txtime & 0xff)
    
    # number of uncoded bits that could be sent using N_sym DATA OFDM symbols 
    N_data = int(N_sym * N_dbps)

    # number of (uncoded) padding bits that need to be added at the end
    N_pad = N_data - (16 + 32 + 6 + 8 * len(packet))

        # assemble the MPDU (now duration is correct)
    packet = mac_framectrl + mac_duration + mac_address1 + mac_address2 + mac_address3 + mac_seqctrl + payload["payload"]

    dic = {"packet":packet, "packet_len":(len(packet) + 4), "txtime":txtime, "mac_duration":mac_duration, "modulation":modulation, \
           "rate":rate, "N_sym":N_sym, "N_data":N_data, "N_pad":N_pad, "N_cbps":N_cbps, "N_bpsc":N_bpsc, "N_dbps":N_dbps, \
           "mac_add1":mac_address1, "mac_add2":mac_address2,"N_SEQ":payload["N_SEQ"],"N_FRAG":payload["N_FRAG"], "MF":0, "PAYLOAD":payload["payload"]}        
        
    return dic

'''

""" Generate an 802.11 compliant fragmented Data frame """
def get_info_frag(payload, regime, symboltime):

        # MAC header for a FRAGMENTED UNICAST DATA FRAME  
    mac_framectrl = chr(0x08) + chr(0b00000100)            
    mac_duration = chr(0x00) + chr(0x00)
    mac_address1 = payload["address1"]
    mac_address2 = payload["address2"]
    mac_address3 = chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff)  # Broadcast
    mac_seqctrl = calculate_seq_control(payload["N_SEQ"],payload["N_FRAG"])

    
        # pre-assemble the MPDU (duration is filled with dummy and CRC32 is missing at this point)
    packet = mac_framectrl + mac_duration + mac_address1 + mac_address2 + mac_address3 + mac_seqctrl + payload["payload"]
        # switch coding rate and constellation according to regime profile (Igual que el estandar IEEE 802.11a)
    if (regime == "1"):
        modulation = "bpsk"
        rate = 1 / float(2)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "2"):
        modulation = "bpsk"
        rate = 3 / float(4)
        N_cbps = 48
        N_bpsc = 1
    elif(regime == "3"):
        modulation = "qpsk"
        rate = 1 / float(2)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "4"):
        modulation = "qpsk"
        rate = 3 / float(4)
        N_cbps = 96
        N_bpsc = 2
    elif(regime == "5"):
        modulation = "qam16"
        rate = 1 / float(2)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "6"):
        modulation = "qam16"
        rate = 3 / float(4)
        N_cbps = 192
        N_bpsc = 4
    elif(regime == "7"):
        modulation = "qam64"
        rate = 2 / float(3)
        N_cbps = 288
        N_bpsc = 6
    elif(regime == "8"):
        modulation = "qam64"
        rate = 3 / float(4)
        N_cbps = 288
        N_bpsc = 6
    
    # uncoded bits per OFDM symbol
    N_dbps = int(N_cbps * rate)    

    # number of DATA symbols the frame needs to have
    # 16 service bits, 32 crc bits and 6 tail bits need to be included
    N_sym = int(math.ceil((16 + 32 + 6 + 8 * len(packet)) / float(N_dbps)))

    # airtime of frame in microseconds
    # the additional 2 at the end of this formula is not in the 
    # standard encoding rules but in the annex G reference frame it is there!
    txtime = int(5 * symboltime + symboltime * N_sym) + 2 
    mac_duration = chr((txtime >> 8) & 0xff) + chr(txtime & 0xff)
    
    # number of uncoded bits that could be sent using N_sym DATA OFDM symbols 
    N_data = int(N_sym * N_dbps)

    # number of (uncoded) padding bits that need to be added at the end
    N_pad = N_data - (16 + 32 + 6 + 8 * len(packet))

        # assemble the MPDU (now duration is correct)
    packet = mac_framectrl + mac_duration + mac_address1 + mac_address2 + mac_address3 + mac_seqctrl + payload["payload"]

    dic = {"packet":packet, "packet_len":(len(packet) + 4), "txtime":txtime, "mac_duration":mac_duration, "modulation":modulation, \
           "rate":rate, "N_sym":N_sym, "N_data":N_data, "N_pad":N_pad, "N_cbps":N_cbps, "N_bpsc":N_bpsc, "N_dbps":N_dbps, \
           "mac_add1":mac_address1, "mac_add2":mac_address2,"N_SEQ":payload["N_SEQ"],"N_FRAG":payload["N_FRAG"], "MF":1, "PAYLOAD":payload["payload"], "timestamp":payload["timestamp"]}        
        
    return dic



def ftw_make(header, payload, regime, symboltime):
    
    if header == "DATA":
        info = get_info(payload, regime, symboltime)
    elif header == "DATA_FRAG":  
        info = get_info_frag(payload, regime, symboltime)
    elif header == "DATA_RETX":  
        info = get_retx_info(payload, regime, symboltime)
    elif header == "RTS":  
        info = get_RTS_info(payload, regime, symboltime)
    elif header == "CTS":  
        info = get_CTS_info(payload, regime, symboltime)
    elif header == "ACK":  
        info = get_ACK_info(payload, regime, symboltime)
    elif header == "BEACON":  
        info = get_BEACON_info(payload, regime, symboltime)
    
    packet = info["packet"]
    packet_len = info["packet_len"]
    N_sym = info["N_sym"]
    N_data = info["N_data"]
    N_pad = info["N_pad"]
    txtime = info["txtime"]

    # check length of MPDU
    MAXLEN = 3168
    if packet_len > MAXLEN:
        raise ValueError, "MPDU-length must be in [0, %d]" % (MAXLEN,)
    
    #print"Txtime in microseconds:",txtime
    #print"Length of MPDU in bytes = ", packet_len
    #print"Number of DATA OFDM symbols = ", N_sym    
    #print"Number of padding bits = ", N_pad

    # generate rate bits in SIGNAL OFDM symbol
    if (regime == "1"):
        rate_bits = 0x0d
    elif (regime == "2"):
        rate_bits = 0x0f
    elif (regime == "3"):
        rate_bits = 0x05
    elif (regime == "4"):
        rate_bits = 0x07
    elif (regime == "5"):
        rate_bits = 0x09
    elif (regime == "6"):
        rate_bits = 0x0b
    elif (regime == "7"):
        rate_bits = 0x01
    elif (regime == "8"):
        rate_bits = 0x03

    # generate length bits in SIGNAL OFDM symbol
    app = 0
    for i in range (0, 12):
        app = app | (((packet_len >> i) & 1) << (11 - i))
    Length = app

    # generate parity check bit in SIGNAL OFDM symbol
    parA = parB = 0    
    for k in range (0, 12):
        parA += ((Length >> k) & (0x01))
        parB += ((rate_bits >> k) & (0x01))
    parity_bit = (parA + parB) % 2
    
    # generate tail and padding bits
    if ((N_pad + 6) % 8 == 0):
        app = ''
        for i in range (0, (N_pad + 6) / 8):
            app += chr(0x00)
        TAIL_and_PAD = app
    else:
        app = ''
        for i in range (0, (N_pad + 6) / 8):
            app += chr(0x00)
        # add one more byte if N_pad + 6 is not a multiple of 8
        # we remove those bits again after the convolutional encoder
        TAIL_and_PAD = app + chr(0x00)      
        
    # generate all bits for SIGNAL OFDM symbol
    Signal_tail = 0x0
    Signal_field = 0x000
    Signal_field = (rate_bits << 20) | (Length << 7) | Signal_tail | (parity_bit << 6)
    chr1 = chr((Signal_field >> 16) & 0xff)    
    chr2 = chr((Signal_field >> 8) & 0xff)
    chr3 = chr(Signal_field & 0xff)
    SIGNAL_FIELD = chr1 + chr2 + chr3

    # generate 16 all-zero SERVICE bits
    SERVICE = chr(0x00) + chr(0x00)

    PLCP_HEADER = SIGNAL_FIELD + SERVICE
    
    MPDU = make_MPDU (packet)    
    
    MPDU_with_crc32 = gen_and_append_crc32(MPDU , packet) 

    Length = len(MPDU_with_crc32)

    
    #return PLCP_HEADER + MPDU_with_crc32 + TAIL_and_PAD , Length
    MPDU_creado = {"MPDU":PLCP_HEADER + MPDU_with_crc32 + TAIL_and_PAD , "LENGTH":Length, "INFO":info, "HEADER":header}
    return MPDU_creado

def parse_mac(pkt):
    packet={"HEADER":"","DATA":""}
    app=list(pkt)
    if app[0]==chr(0x80):
        header="BEACON"
        mac_duration=ord(app[2])*256 + ord(app[3])
        mac_address1=app[4]+app[5]+app[6]+app[7]+app[8]+app[9]
        mac_address2=app[10]+app[11]+app[12]+app[13]+app[14]+app[15]
        mac_address3=app[16]+app[17]+app[18]+app[19]+app[20]+app[21]
        mac_seqctrl = app[22]+app[23]
        mac_seq = (ord(app[22]) >> 4) + ord(app[23]) * 16
        mac_frag =  (ord(app[22]) & 0xf)
        timestamp=ord(app[24]) << 56 + ord(app[25]) << 48 + ord(app[26]) << 40 + ord(app[27]) << 32 + \
                  ord(app[28]) << 24 + ord(app[29]) << 16 + ord(app[30]) << 8 + ord(app[31])
        BI= ord(app[32]) << 8 + ord(app[33])
        capability_info = ord(app[34]) << 8 + ord(app[35])              
        info = {"packet":pkt, "mac_duration":mac_duration, "mac_add1":mac_address1, "mac_add2":mac_address2, \
                "N_SEQ":mac_seq,"N_FRAG":mac_frag, "MF":mac_frag, "timestamp":timestamp, "BI":BI}        
        beacon = {"INFO":info}
        
        packet=create_packet(header,beacon)
        
    elif app[0]==chr(0xc4):
        header="CTS"
        #mac_duration=app[2]+app[3]
        txtime=ord(app[2])*256 + ord(app[3])
        mac_ra=app[4]+app[5]+app[6]+app[7]+app[8]+app[9]
        info = {"packet":pkt, "txtime":txtime, "RX_add":mac_ra}
        cts = {"INFO":info}  
        packet=create_packet(header,cts)
        
        
    elif app[0]==chr(0xb4):
        header="RTS"
        txtime=ord(app[2])*256 + ord(app[3])
        mac_ra=app[4]+app[5]+app[6]+app[7]+app[8]+app[9]
        mac_ta=app[4]+app[5]+app[6]+app[7]+app[8]+app[9]
        info = {"packet":pkt, "txtime":txtime, "RX_add":mac_ra, "TX_add":mac_ta}    
        rts = {"INFO":info}
        packet=create_packet(header,rts)
        
        
    elif app[0]==chr(0xd4):
        header="ACK"
        txtime=ord(app[2])*256 + ord(app[3])
        mac_ra=app[4]+app[5]+app[6]+app[7]+app[8]+app[9]
        info = {"packet":pkt, "RX_add":mac_ra}   
        ack = {"INFO":info} 
        packet=create_packet(header,ack)
    elif app[0]==chr(0x08) and app[1]==chr(0x00):
        header="DATA"
        txtime=ord(app[2])*256 + ord(app[3])
        mac_address1=app[4]+app[5]+app[6]+app[7]+app[8]+app[9]
        mac_address2=app[10]+app[11]+app[12]+app[13]+app[14]+app[15]
        mac_address3=app[16]+app[17]+app[18]+app[19]+app[20]+app[21]
        mac_seqctrl = app[22]+app[23]
        mac_seq = (ord(app[22]) >> 4) + ord(app[23]) * 16
        mac_frag =  (ord(app[22]) & 0xf)
        
        payload=app[24:len(app)-4]
        
        info = {"packet":pkt, "txtime":txtime, "mac_add1":mac_address1, "mac_add2":mac_address2,"N_SEQ":mac_seq,"N_FRAG":mac_frag, "MF":mac_frag, "PAYLOAD":payload}
        data = {"INFO":info}       
        packet=create_packet(header,data)
    elif app[0]==chr(0x08) and app[1]==chr(0x04):
        header="DATA_FRAG"
        txtime=ord(app[2])*256 + ord(app[3])
        mac_address1=app[4]+app[5]+app[6]+app[7]+app[8]+app[9]
        mac_address2=app[10]+app[11]+app[12]+app[13]+app[14]+app[15]
        mac_address3=app[16]+app[17]+app[18]+app[19]+app[20]+app[21]
        mac_seqctrl = app[22]+app[23]
        mac_seq = (ord(app[22]) >> 4) + ord(app[23]) * 16
        mac_frag =  (ord(app[22]) & 0xf)
        payload=app[24:len(app)-4]
                
        info = {"packet":pkt, "txtime":txtime, "mac_add1":mac_address1, "mac_add2":mac_address2,"N_SEQ":mac_seq, "N_FRAG":mac_frag, "MF":mac_frag, "PAYLOAD":payload}        
        data = {"INFO":info}             
        
        packet=create_packet(header,data)
    elif app[0]==chr(0x08) and app[1]==chr(0x08):
        header="DATA_RETX"
        txtime=ord(app[2])*256 + ord(app[3])
        mac_address1=app[4]+app[5]+app[6]+app[7]+app[8]+app[9]
        mac_address2=app[10]+app[11]+app[12]+app[13]+app[14]+app[15]
        mac_address3=app[16]+app[17]+app[18]+app[19]+app[20]+app[21]
        mac_seqctrl = app[22]+app[23]
        mac_seq = (ord(app[22]) >> 4) + ord(app[23]) * 16
        mac_frag =  (ord(app[22]) & 0xf)
        payload=app[24:len(app)-4]
                
        info = {"packet":pkt, "txtime":txtime, "mac_add1":mac_address1, "mac_add2":mac_address2,"N_SEQ":mac_seq, "N_FRAG":mac_frag, "MF":mac_frag, "PAYLOAD":payload}        
        data = {"INFO":info}             
        packet=create_packet(header,data)
        
    return packet
    
def make_MPDU(payload):
    app = conv_packed_binary_string_to_1_0_string(payload)
    app = list(app)
    mpdu = ['0'] * len(app)
    j = 0
    while (j < len(app)):
        for i in range (0, 8):
            mpdu[i + j] = app[7 - i + j]     # Change into transmit order
        j += 8
    mpdu = "".join(mpdu)
    return conv_1_0_string_to_packed_binary_string(mpdu)

def gen_and_append_crc32(MPDU, packet_for_crc):
    crc = gr_ieee802_11.crc32(packet_for_crc)
    return MPDU + struct.pack(">I", hexint(crc) & 0xFFFFFFFF)

def conv_packed_binary_string_to_1_0_string(s):
    """
    '\xAF' --> '10101111'
    """
    r = []
    for ch in s:
        x = ord(ch)
        for i in range(7, -1, -1):
            t = (x >> i) & 0x1
            r.append(t)

    return ''.join(map(lambda x: chr(x + ord('0')), r))

def conv_1_0_string_to_packed_binary_string(s):
    """
    '10101111' -> ('\xAF', False)

    Basically the inverse of conv_packed_binary_string_to_1_0_string,
    but also returns a flag indicating if we had to pad with leading zeros
    to get to a multiple of 8.
    """
    if not is_1_0_string(s):
        raise ValueError, "Input must be a string containing only 0's and 1's"
    
    # pad to multiple of 8
    padded = False
    rem = len(s) % 8
    if rem != 0:
        npad = 8 - rem
        s = '0' * npad + s
        padded = True

    assert len(s) % 8 == 0

    r = []
    i = 0
    while i < len(s):
        t = 0
        for j in range(8):
            t = (t << 1) | (ord(s[i + j]) - ord('0'))
        r.append(chr(t))
        i += 8
    return ''.join(r)
        

def is_1_0_string(s):
    if not isinstance(s, str):
        return False
    for ch in s:
        if not ch in ('0', '1'):
            return False
    return True

def string_to_hex_list(s):
    return map(lambda x: hex(ord(x)), s)


def hexint(mask):
  """
  Convert unsigned masks into signed ints.

  This allows us to use hex constants like 0xf0f0f0f2 when talking to
  our hardware and not get screwed by them getting treated as python
  longs.
  """
  if mask >= 2 ** 31:
     return int(mask - 2 ** 32)
  return mask

def ascii_to_bin(char):
    ascii = ord(char)
    bin = []

    while (ascii > 0):
        if (ascii & 1) == 1:
             bin.append("1")
        else:
             bin.append("0")
        ascii = ascii >> 1             
        bin.reverse()
    binary = "".join(bin)
    zerofix = (8 - len(binary)) * '0'

    return zerofix + binary

#def get_Tsimbolo(inter):
def get_Tsymbol(inter):
    """
    Obtains the OFDM parameter T_sym based on the USRP2 interpolation factor
    """
    fft_length = 64
    cp_length = 16
    Tsym = inter * (fft_length + cp_length) / 100
    return Tsym

def create_packet(header, data):
    """
    Define the packet format used for crosslayer communication
    """
    packet = {"HEADER":header, "DATA":data}
    return packet

#def enviar_a_PHY(datos, sd):
def send_to_PHY(data, sd):
    """
    Procedure to send data through a socket to the PHY
    """
    pkt = pickle.dumps(data, 1)
    sd.send(pkt)    
    
#def recibir_de_PHY(sd):
def receive_from_PHY(sd):
    """
    Procedure to receive data through a socket from the PHY
    """
    pkt = sd.recv(1000)
    info = pickle.loads(pkt)
    return info

def retry(count, CWmin):
    """ 
    Update the CWslot based on the value of the Backoff retries counter
    """
    if count == 0:
        CWslot = CWmin  # First mistake

    else:
        # Following mistakes
        CW = CWmin * (2 ** count)
        if CW > 1023:
            CW = 1023
        CWslot = random.randint(CWmin, CW) 
    return CWslot

def usrp2_node(nodo):
    """ 
    Based on the USRP2 node (1,2,3 or 4), returns its equivalent MAC address
    NOTE: This is a easy way of  assigning MAC addresses to each node  
    """
    if nodo == 1:
        mac = chr(0x00) + chr(0x50) + chr(0xc2) + chr(0x85) + chr(0x33) + chr(0x0c)
    elif nodo == 2:
        mac = chr(0x00) + chr(0x50) + chr(0xc2) + chr(0x85) + chr(0x33) + chr(0x10)
    elif nodo == 3:
        mac = chr(0x00) + chr(0x50) + chr(0xc2) + chr(0x85) + chr(0x33) + chr(0x11)
    elif nodo == 4:
        mac = chr(0x00) + chr(0x50) + chr(0xc2) + chr(0x85) + chr(0x33) + chr(0xf6)
    else:
        mac = chr(0x00) + chr(0x00) + chr(0x00) + chr(0x00) + chr(0x00) + chr(0x00) #Error 
    return mac

def which_dir(dir):
    """ 
    Based on the USRP2 MAC address, returns its USRP2 # node (1,2,3 or 4) 
    """
    if dir == chr(0x00) + chr(0x50) + chr(0xc2) + chr(0x85) + chr(0x33) + chr(0x0c):
        msg = "00:50:C2:85:33:0C"
    elif dir == chr(0x00) + chr(0x50) + chr(0xc2) + chr(0x85) + chr(0x33) + chr(0x10):
        msg = "00:50:C2:85:33:10"
    elif dir == chr(0x00) + chr(0x50) + chr(0xc2) + chr(0x85) + chr(0x33) + chr(0x11):
        msg = "00:50:C2:85:33:11"
    elif dir == chr(0x00) + chr(0x50) + chr(0xc2) + chr(0x85) + chr(0x33) + chr(0xf6):
        msg = "00:50:C2:85:33:F6"
    else:
        msg = "00:00:00:00:00:00"
    
    return msg

#def transmitir(pkt, port):
def transmit(pkt, port):
    """ 
    Procedure to send a packet to the PHY layer 
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), port))
    send_to_PHY(pkt, s)
    s.close()
    
def sense_channel(port):
#def sensar_canal(port):
    """ 
    Method that measures the power detected on a desired frequency and estimates if the channel is IDLE or BUSY.
    It also returns the time elapsed in a power measurement  
    """
    time1 = time.time()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), port))
    message_cca = create_packet("CCA", "")      # Create a Carrier Sense Request packet
    send_to_PHY(message_cca, s)                # Send the request
    sensed = receive_from_PHY(s)                 # Receive the response from the PHY
    s.close()       
    maximo = sensed["DATA"]
    maximo_dBw= 10*math.log10(maximo)           # Save the data in dBw 
    time2 = time.time()
    if maximo_dBw > -24:    # (Can be modified) Threshold value that allows determine the ocupation level of the channel
        return "OCCUPIED", time2 - time1 # Channel Busy. It also returns the CS processing time
    else:
        return "FREE", time2 - time1 # Channel Idle
    
#def actualizar_NAV(tiempo, nav, timeslot):
def update_NAV(timetick, nav, timeslot):
    """ 
    Method that keeps updated the Network Allocation Vector (NAV) of the station
    """
    if nav == 0:
        nav = 0
    else:
        time.sleep(timeslot) 
        nav = nav - (time.time() - timetick)
        if nav <= timeslot and nav >0:
            time.sleep(nav)
            nav = 0
    return nav

#def generar_pkt(header, intrp, regimen, payld):
def generate_pkt(header, intrp, regimen, payld):
    """ 
    Generates an 802.11 frame using the interpolation and OFDM coderegime values
    """
    tsymbol = get_Tsymbol(intrp)
    data = ftw_make(header, payld, regimen, tsymbol)
    return data

#def leer_capa_phy(port, header):
def read_phy_response(port, header):
    """ 
    Method used by the MAC layer to read a response from the PHY layer  
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), port))
    message_cs = create_packet("TAIL", header.upper())
    send_to_PHY(message_cs, s)
    reading = receive_from_PHY(s)
    s.close()
    if reading["HEADER"] == "YES":
        return "YES", reading["DATA"]
    else:
        return "NO", reading["DATA"]

#def eliminar_paquete_capa_superior(port):
def remove_ul_buff_packet(port):
    """ 
    Removes a packet from the upper layer buffer
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), port))
    message_cs = create_packet("remove", "")  # This message orders a packet deletion 
    send_to_PHY(message_cs, s)
    s.close()

#def copiar_paquete_capa_superior(port,paquete):
def send_ul_buff_packet(port,packet):
    """ 
    Sets a packet in the upper layer buffer
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), port))
    message_cs = create_packet("copy", packet)   # This message copies the value of 'paquete' in a buffer
    send_to_PHY(message_cs, s)
    s.close()
    
#def leer_capa_superior(port):
def read_ul_buffer(port):
    """ 
    Method used by the MAC layer to read the upper layer buffer 
    """
    time1 = time.time()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), port))
    message_cs = create_packet("no_packet", "")
    send_to_PHY(message_cs, s)
    reading = receive_from_PHY(s)
    s.close()
    time2 = time.time()
    if reading["HEADER"] == "YES":         # is a Data Packet?
        return "YES", reading["DATA"]
    elif reading["HEADER"] == "BEACON":   # is a BEACON Packet?
        return "BEACON", []
    elif reading["HEADER"] == "NO":       # is empty the buffer?
        return "NO", reading["DATA"]

#def hacer(payload, umbral):
def render(payload, threshold):
    """
    Old Method, used to fragment a payload depending on a threshold length
    """
    if len(payload) > threshold and len(payload) > 0:
        fragment = payload[0:threshold]
        return fragment, payload[threshold:len(payload)]
    else:
        fragment = payload
        return fragment, payload[threshold:len(payload)]

#def fragmentar(pay, umb):
def fragment(payload, threshold):
    """
    Method used to fragment a payload depending on a threshold length
    """
    i=0
    x=[]
    while len(payload)>0:
        frag, payload = render(payload,threshold)
        x.insert(i, frag)
        i+=1
    return x 

def seq_num(num):
    """
    Assigns a Sequence Number within the range [0,4096]
    """
    num = (num + 1) % 4096
    return num

def bin_to_str(binario):
    """Auxiliary method of calculate_seq_control(seq,frag)"""
    tmp=str(binario)
    tmp=tmp[2:len(tmp)]
    return tmp

#def completar_low(numero):
def complete_low(number):
    """Auxiliary method of calculate_seq_control(seq,frag)"""
    if len(number)<4:
        diferencia = 4-len(number)
        return diferencia*'0' + number
    else:
        return number

#def completar_high(numero):
def complete_high(number):
    """Auxiliary method of calculate_seq_control(seq,frag)"""
    if len(number)<8:
        diferencia = 8-len(number)
        return diferencia*'0' + number
    else:
        return number
    
#def calcular_seq_control(seq,frag):
def calculate_seq_control(seq,frag):
    """
    Calculates the Sequence Number value in packed binary string format
    """
    N1 = (seq & 0xf)
    N1 = bin(N1)
    N1 = bin_to_str(N1)
    N1 = complete_low(N1)
    N2 = (frag & 0xf)
    N2 = bin(N2)
    N2 = bin_to_str(N2)
    N2 = complete_low(N2)
    N3N4 = (seq&0xff0)>>4     
    N3N4 =bin(N3N4)  
    N3N4 = bin_to_str(N3N4)
    N3N4 = complete_high(N3N4)
    parte_a = conv_1_0_string_to_packed_binary_string(N1+N2)
    parte_b = conv_1_0_string_to_packed_binary_string(N3N4)
    return parte_a + parte_b

def beacon_int(timetick):
    """
    Calculates the Beacon Interval value in packed binary string format
    """
    if timetick > 67108:
        print "ERROR, Beacon interval > BI MAX (67108)"
        BI = chr(0xff)+chr(0xff)
    else:
        timetick = int(timetick / (1024e-6))+1  
        BI = chr(timetick & 0xff) + chr((timetick >> 8)& 0xff)
    return BI

def timestamp():
    """
    Calculates the timestamp value in packed binary string format
    """
    x = int(time.time())+1
    timestamp = chr(x & 0xff) + chr((x>>8) & 0xff) + chr((x>>16) & 0xff) + chr((x>>24) & 0xff) +\
                chr((x>>32) & 0xff) + chr((x>>40) & 0xff) + chr((x>>48) & 0xff) + chr((x>>56) & 0xff)
    return timestamp,x  
