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

# Filename: uwicore_80211mac.py

# This script contains the MAC Finite State Machine (FSM) implementation developed by the Uwicore 
# Laboratory at the University Miguel Hernandez of Elche. More detailed information about the 
# FSM diagram transitions can be found at www.uwicore.umh.es/mhop-testbeds.html or at the publication:

# J.R. Gutierrez-Agullo, B. Coll-Perales and J. Gozalvez, "An IEEE 802.11 MAC Software Defined Radio Implementation for  Experimental Wireless Communications and Networking Research", Proceedings of the 2010 IFIP/IEEE Wireless Days (WD'10), pp. 1-5, 20-22 October 2010, Venice (Italy).

# Ubiquitous Wireless Communications Research Laboratory 
# Uwicore, http://www.uwicore.umh.es
# Communications Engineering Department
# University Miguel Hernandez of Elche
# Avda de la Universidad, s/n
# 03202 Elche, Spain

# Release: April 2011

# List of Authors:
#    Juan R. Gutierrez-Agullo (jgutierrez@umh.es)
#    Baldomero Coll-Perales (bcoll@umh.es)
#    Dr. Javier Gozalvez (j.gozalvez@umh.es)


from optparse import OptionParser
from gnuradio.eng_option import eng_option
import uwicore_mac_utils as MAC
import threading

import time, sys, random
import elvOptions
from elvEvent import *


class MACLayer(object):

    def __init__(self):
        self.my_mac = MAC.usrp2_node(ElvOption.option.Node)   # MAC address for this node
        self.dest_mac = MAC.usrp2_node(2)            # Dummy value (updated when an incoming packet arrives)

        self.beta = ElvOption.option.beta # scaling time parameter
        self.tslot = ElvOption.option.time_slot * self.beta

        self.SIFS = ElvOption.option.SIFS * self.beta
        self.DIFS = self.SIFS + 2 * self.tslot
        self.Preamble = self.DIFS #16e-6
        self.PLCP_header = 4e-6 * self.beta
        self.ACK_time = self.Preamble + self.PLCP_header
        self.CW_min = 15
        self.CW_max = 1023
        self.RTS_THRESHOLD = 150
        self.dot11FragmentationTh = 1036

        # TX time estimation for a CTS and an ACK packet
        self.empty_values = {"duration":0, "mac_ra":self.my_mac, "timestamp":time.time()}
        self.CTS_empty = MAC.generate_pkt("CTS", ElvOption.option.interp, ElvOption.option.regime, self.empty_values)


        self.T_cts = self.CTS_empty["INFO"]["txtime"]
        self.ACK_empty = MAC.generate_pkt("ACK", ElvOption.option.interp, ElvOption.option.regime, self.empty_values)
        self.T_ack = self.ACK_empty["INFO"]["txtime"]

        # Set socket ports
        self.PHY_port = ElvOption.option.PHYport
        #PHYRX_port = options.PHYRXport
        self.MAC_port = ElvOption.option.MACport

        # Variables involving MAC tests
        self.testing = False                         # Testing mode active, used to conduct trials
        self.N_TESTS = 1000                          # Number of tests
        self.N_TESTS_INI = self.N_TESTS
        self.LONG_TESTS = 20                         # Payload length for tests
        self.payload_test = "0000" + self.LONG_TESTS*'1'  # Payload for tests
        self.test_with_sensing = True                 # Carrier Sensing (CS) allowed during the test
        self.total_processing_time = 0          # Total processing time
        self.t_sense_mean = 0                     # CS average time
        self.t_csense = 0                           # CS time
        self.t_MAC = 0                               # MAC time
        self.t_MAC_mean = 0                         # MAC average time
        self.packet_i=0                             # Packets sent counter
        self.n_sensing = 0                           # Number of CS performed

        # 'State' controls the state of the MAC
        self.State = "IDLE"

        self.BACKOFF = 0;

        # Initial Conditions of the Finite State Machine
        self.NAV = 0                 # Network Allocation Vector
        self.N_RETRIES = 0           # Retries to send a packet counter
        self.busy_in_wfd = False  # Busy in Wait_for_DIFS state
        self.BO_frozen = "NO"     # Backoff frozen
        self.TX_attempts = 0             # Tries to send a packet counter
        self.CTS_failed = False      # CTS reception failed
        self.chan = "FREE"          # Channel state = IDDLE
        self.N_SEQ = 0               # Sequence number counter
        self.N_FRAG = 0              # Fragment number counter
        self.first_tx = True         # Is the first attempt to send a packet?
        self.frag_count = 0         # Counter used during fragmentation
        self.data_temp_reass = ""     # Initial variable to perform de re-assembly process
        self.verbose = True          # Shows when the MAC is in 'IDDLE' state
        self.beaconing = False       # Is ON the Beaconing process?
        self.fragmenting = 0         # Is the packet received a fragment?
        self.retx_retries = 0;
        self.WF_ACK_first_time = 1;
        self.BO_first_time = 1;

    def mac_loop(self):
        try:
            while 1:
                #IDLE STATE
                
                if self.State == "IDLE":
                    ElvEvent("In State IDLE")
                    # Is there a DATA?
                    reply_phy1, packet_phy1 = MAC.read_phy_response(self.PHY_port, "DATA")

                    if reply_phy1 == "YES":
                        ElvEvent("Get a packet from PHY layer " + str(reply_phy1))

                        #verbose = True          # Show when the MAC is IDLE
                        x = packet_phy1["INFO"]  # DATA packet addressed to this station

                        self.dest_mac = x["mac_add2"]
                        if x["MF"]==0:  #More Fragments = 0
                            if self.fragmenting == 0:    # Not a fragmented packet
                                #print "[R]-[DATA]-[DA:%s]-[SA:%s]-[MF:0]-[IFM:1]-[PAYLOAD = %s]" %(MAC.which_dir(x["mac_add1"]),MAC.which_dir(x["mac_add2"]),x["PAYLOAD"])
                                #if options.V: print "| WAITING_FOR_DATA | DATA received | TRANSMITTING_ACK |"
                                self.State = "TRANSMITTING_ACK"
                                self.WF_DATA_first_time = 1
                                self.frag_count = 0
                                MAC.send_ul_buff_packet(self.MAC_port, x["PAYLOAD"])
                            else:   # Last fragmented packet
                                self.fragmenting = 0
                                self.frag_count +=1
                                print "[R]-[FRAGMENTED DATA]-[DA:%s]-[SA:%s]-[MF:0]-[#seq:%i]-[#frag:%i]-[IFM:1]-[PAYLOAD = %s]" %(MAC.which_dir(x["mac_add2"]),MAC.which_dir(self.my_mac),x["N_SEQ"],x["N_FRAG"],x["PAYLOAD"])
                                test_seq = x["N_FRAG"]+1 - self.frag_count
                                if test_seq == 0:
                                    dato_leido = self.data_temp_reass + x["PAYLOAD"]
                                    self.State = "TRANSMITTING_ACK"
                                    self.WF_DATA_first_time = 1
                                    self.frag_count = 0
                                    self.fragmenting = 0
                                    #if options.V: print "| WAITING_FOR_DATA | DATA_FRAG received  (MF = 0)| TRANSMITTING_ACK |"
                                    MAC.send_ul_buff_packet(self.MAC_port, dato_leido)
                                else:
                                    self.WF_DATA_first_time = 1
                                    self.frag_count = 0
                                    self.fragmenting = 0
                                    #if options.V: print "| WAITING_FOR_DATA | Error: one or more fragments not received | IDLE |"
                        else: # More Fragments = 1. It's a fragment
                            #print "[R]-[FRAGMENTED DATA]-[DA:%s]-[SA:%s]-[MF:1]-[#seq:%i]-[#frag:%i]-[IFM:1]-[PAYLOAD = %s]" %(MAC.which_dir(x["mac_add2"]),MAC.which_dir(my_mac),x["N_SEQ"],x["N_FRAG"],x["PAYLOAD"])
                            #if options.V: print "| WAITING_FOR_DATA | DATA_FRAG received  (MF = 1)| TRANSMITTING_ACK |"
                            self.fragmenting = 1
                            self.frag_count +=1
                            self.data_temp_reass = self.data_temp_reass + x["PAYLOAD"]
                            self.State = "TX_ACK_FG"


                    # Check upper layer buffer for data to send
                    else:
                        reply_up, PAYLOAD = MAC.read_ul_buffer(self.MAC_port)
                        if reply_up == "YES":
                            ElvEvent(
                                "Get a packet from UL buffer " 
                                + str(reply_up) + " Payload: " 
                                + str(PAYLOAD)
                            )
                            # verbose = True
                            #if options.V: print "| IDLE | MAC has DATA to Tx | WAIT_FOR_NAV |"
                            self.State = "WAIT_FOR_NAV"
                        elif reply_up == "BEACON":
                            ElvEvent("Get a packet from UL buffer (beacon) " + str(reply_up))
                            self.beaconing = True
                            values = {
                                "address2": self.my_mac,
                                "N_SEQ": self.N_SEQ,
                                "N_FRAG":0,
                                "BI":ElvOption.option.BI,
                                "timestamp": time.time()
                            }
                            print "[T]-[BEACON]-[SA:%s]-[BI=%f]-[#seq:%i]"\
                                %(
                                    MAC.which_dir(self.my_mac),
                                    ElvOption.option.BI,
                                    self.N_SEQ
                                )
                            #if options.V: print "| IDLE | Send BEACON | IDLE |"
                            BEACON = MAC.generate_pkt(
                                "BEACON", ElvOption.option.interp,
                                ElvOption.option.regime,
                                values
                            )
                            packet_BEACON = MAC.create_packet("PKT", BEACON)
                            MAC.transmit(packet_BEACON, self.PHY_port)
                            MAC.remove_ul_buff_packet(self.MAC_port)
                            self.N_SEQ += 1
                            self.beaconing = False
                    if self.testing == True: # if True, it allows to switch manually to any state
                        t_testA = time.time()
                        self.packet_i +=1
                        self.State = "WAIT_FOR_NAV" # Edit the state to switch to

                    if self.State == "IDLE":
                        time.sleep(self.tslot)   # Time-slotted MAC


                #WAIT_FOR_NAV STATE
                elif self.State == "WAIT_FOR_NAV":
                    ElvEvent("In state WAIT_FOR_NAV");
                    self.NAV = MAC.update_NAV(time.time(), self.NAV, self.tslot)
                    if self.NAV > 0:
                        #if options.V: print "| WAIT_FOR_NAV | NAV > 0 | WAIT_FOR_NAV |"
                        self.State = "WAIT_FOR_NAV"
                    else:
                        #if options.V: print "| WAIT_FOR_NAV | NAV = 0 | WAIT_FOR_DIFS |"
                        self.State = "WAIT_FOR_DIFS"
                        self.chan = "FREE"

                #WAIT_FOR_DIFS STATE
                elif self.State == "WAIT_FOR_DIFS":
                    # This state performs the channel sensing process and decides whether the channel is BUSY or IDLE
                    ElvEvent("In state WAIT_FOR_DIFS")
                    t_initial=time.time()
                    t_final=t_initial + self.DIFS
                    n_sensing = 0
                    while n_sensing < 2:
                        
                        channel_in_wfd, t = MAC.sense_channel(self.PHY_port)
                        
                        assert (self.tslot - t >=0), \
                            "Timing Error. Please increase the beta parameter."
                        time.sleep(self.tslot-t)

                        if channel_in_wfd == "OCCUPIED":
                            self.chan = "OCCUPIED"

                        ElvEvent(
                            "Conduct a carrier sensing and PHY returns " 
                            + self.chan
                        )

                        self.t_csense = self.t_csense + t
                        n_sensing +=1
                    #########################################################3
                    # The carrier sensing scheme is not reliable enough
                    ##########################################################
                    assert (t_final - time.time() >=0),\
                        "Timing Error. Please increase the beta parameter."
                    time.sleep(t_final - time.time())
                    self.t_csense = self.t_csense/3

                    if self.chan == "FREE":
                        if self.BO_frozen == "NO" \
                        and self.busy_in_wfd == False \
                        and self.CTS_failed == False:
                            self.BACKOFF = 0 # Channel IDLE for the first time, BOtimer = 0
                        self.State = "BACKING_OFF"
                        #if options.V: print "| WAIT_FOR_DIFS | Channel idle | BACKING_OFF |"
                    else:
                        if self.BO_frozen == "NO" \
                        and self.CTS_failed == False:  # If it is the 1st time, set the CW
                            self.BACKOFF = MAC.retry(self.TX_attempts, self.CW_min)
                            self.TX_attempts = self.TX_attempts + 1
                            #BO_frozen=="YES"
                            self.BO_first_time = 1
                        self.State = "IDLE"
                        self.chan = "FREE"
                        #if options.V: print "| WAIT_FOR_DIFS | Channel busy | IDLE |"

                #BACKING_OFF STATE
                elif self.State == "BACKING_OFF":
                    ElvEvent("In state BACKING_OFF");
                    self.busy_in_wfd = False
                    if self.BACKOFF == 0:
                        self.BO_first_time = 1
                        self.State = "TRANSMITTING_UNICAST"
                    else:
                        tx = time.time()
                        ch_status, t = MAC.sense_channel(self.PHY_port)

                        if ch_status == "FREE": # Channel idle
                            self.BACKOFF = self.BACKOFF - 1
                            self.BO_first_time = 0 # Backoff process started, freeze CW value!
                            if self.BACKOFF > 0:
                                #if options.V: print "| BACKING_OFF | Channel idle (CW = %i) | BACKING_OFF |"%BACKOFF
                                self.State = "BACKING_OFF"
                            else:
                                #if options.V: print "| BACKING_OFF | Channel idle (CW = %i) | TRANSMITTING_UNICAST |"%BACKOFF
                                self.State = "TRANSMITTING_UNICAST"
                                busy_in_wfd = False

                        else:   # Channel busy
                            self.BACKOFF = self.BACKOFF - 1
                            self.BO_first_time = 0 # Channel busy, CW frozen
                            self.BO_frozen = "YES"
                            self.State = "IDLE"
                            #if options.V:
                            #    if options.V: print "| BACKING_OFF | Channel busy (CW = %i) | IDLE |"%BACKOFF
                        ty = time.time()
                        assert (self.tslot - (ty - tx) >=0),\
                            "Timing Error. Please increase the beta parameter."
                        time.sleep(self.tslot - (ty - tx))


                #TRANSMITTING_UNICAST STATE
                elif self.State == "TRANSMITTING_UNICAST":
                    '''
                    Send packet to PHY for its transmission using the USRP2
                    packet = [MPDU][LENGHT][INFO]
                    pkt = [Header: PKT][Data: packet]
                    '''
                    ElvEvent("In state TRANSMITTING_UNICAST")
                    fail_tx = False
                    #if options.V: print "[%s]\t: TX DATA packet to PHY" % State
                    if len(PAYLOAD) > self.dot11FragmentationTh:
                        #if options.V: print "| TRANSMITTING_UNICAST | Send Fragmented Data | TRANSMITTING_FRAGMENTED_PACKET |"
                        self.State = "TRANSMITTING_FRAGMENTED_PACKET"
                        first_time_fg = True
                        WF_ACK_FG_first_time = True
                    else:
                        values = {
                            "payload": PAYLOAD,
                            "address1":self.dest_mac,
                            "address2":self.my_mac,
                            "N_SEQ": self.N_SEQ,
                            "N_FRAG": self.N_FRAG,
                            "timestamp": time.time()
                        }
                        print "[T]-[DATA]-[DA:%s]-[SA:%s]-[MF:0]-[#seq:%i]-[Payload = %s]" \
                            %(
                                MAC.which_dir(self.dest_mac),
                                MAC.which_dir(self.my_mac),
                                self.N_SEQ,
                                PAYLOAD
                            )
                        #if options.V: print "| TRANSMITTING_UNICAST | Send DATA | WAITING_FOR_ACK |"
                        self.N_SEQ += 1
                        self.N_FRAG = 0
                        if fail_tx == False:
                            packet = MAC.generate_pkt(
                                "DATA",
                                ElvOption.option.interp,
                                ElvOption.option.regime,
                                values
                            )
                        else:
                            packet = MAC.generate_pkt(
                                "DATA_RETX",
                                ElvOption.option.interp,
                                ElvOption.option.regime,
                                values
                            )
                        pkt = MAC.create_packet("PKT", packet)
                        MAC.transmit(pkt, self.PHY_port)
                        self.WF_ACK_first_time = 1 # First time in WAITING_FOR_ACK state
                        self.State = "WAITING_FOR_ACK"

                #WAITING_FOR_ACK STATE
                elif self.State == "WAITING_FOR_ACK":
                    ElvEvent("In state WAITING_FOR_ACK")
                    if self.WF_ACK_first_time == 1:
                        T_ACK = self.SIFS
                    ta = time.time()
                    any_packet, packet_phy = MAC.read_phy_response(self.PHY_port, "ACK")
                    if any_packet == "YES":
                        x = packet_phy["INFO"]
                        #print "[R]-[%s]-[DA:%s]-[duration:%f]-[IFM:1]" %(packet_phy["HEADER"],MAC.which_dir(x["RX_add"]),x["txtime"])
                        print "[R]-[ACK]-[DA:%s]-[IFM:1]" %(MAC.which_dir(x["RX_add"]))
                        '''
                        #============================================================
                        # /TEST/ UNCOMMENT TO CHECK RTS/CTS FUNCTIONALITY
                        #============================================================
                        # STEP 4/4: Node 2 --> ACK
                        mac_ra = my_mac
                        values = {"duration":x["txtime"], "mac_ra":mac_ra,"timestamp":time.time()}
                        ACK_forced = MAC.generate_pkt("ACK", options.interp, options.regime, values)
                        packet_ACK_forced = MAC.create_packet("PKT", ACK_forced)
                        MAC.transmit(packet_ACK_forced, PHY_port)
                        time.sleep(tslot)
                        #============================================================
                        '''
                        #if options.V: print "| WAITING_FOR_ACK | ACK received | IDLE |"
                        self.State = "IDLE"
                        self.BACKOFF = 0
                        self.WF_ACK_first_time = 1
                        ACK_fin = 1
                        MAC.remove_ul_buff_packet(self.MAC_port)    # Packet acknoweledged, remove from upper layers
                        first_tx = True

                    else:
                        self.State = "WAITING_FOR_ACK"  # Not an ACK
                        self.WF_ACK_first_time = 0
                        ACK_fin = 0

                    ta_fin = time.time()
                    assert (self.tslot - (ta_fin - ta) >=0),\
                        "Timing Error. Please increase the beta parameter."
                    time.sleep(self.tslot - (ta_fin - ta))
                    tb = time.time()
                    T_ACK = T_ACK - (tb - ta)
                    
                    if ACK_fin == 0:
                        if T_ACK > 0:
                            #if options.V: print "| WAITING_FOR_ACK | ACK not received yet | WAITING_FOR_ACK |"
                            ElvEvent("ACK not received, due in " + str(T_ACK))
                            self.State = "WAITING_FOR_ACK"
                        else:
                            # Not ACK yet, Reset CW to CWmin and go to IDLE
                            ElvEvent("Fail to receive ACK! ");
                            if ElvOption.option.retx == True:
                                self.retx_retries = self.retx_retries - 1
                                if self.retx_retries < 0:
                                    CW = self.CW_min
                                    
                                    self.State = "IDLE"
                                    MAC.remove_ul_buff_packet(self.MAC_port)  # drop the packet after maximum number of retries
                                    first_tx = True
                                    #if options.V: print "| WAITING_FOR_ACK | Remove packet from upper layers | IDLE |"
                                    N_FRAG = 0
                                    fail_tx = False
                                else:
                                    #if options.V: print "| WAITING_FOR_ACK | ACK not received (retries left = %i) | IDLE |"%retx_retries
                                    self.State = "IDLE"
                                    fail_tx = True
                            else:
                                self.State = "IDLE"
                                #if options.V: print "| WAITING_FOR_ACK | Remove packet from upper layers | IDLE |"
                                MAC.remove_ul_buff_packet(self.MAC_port)    # No Re-TX!
                                self.first_tx = True

                #TRANSMITTING_FRAGMENTED_PACKET STATE
                elif self.State == "TRANSMITTING_FRAGMENTED_PACKET":
                    print self.State
                    if self.first_time_fg == True:
                        fragments = MAC.fragment(PAYLOAD, self.dot11FragmentationTh) #fragment the PAYLOAD based on a fragmentation threshold
                        first_time_fg = False
                    else:
                        if len(fragments) > 1:
                            payload_tmp = fragments[0]
                            #Create packet with MORE FRAGMENT = 1 and payload = payload_tmp
                            values = {
                                "payload":payload_tmp,
                                "address1":self.dest_mac,
                                "address2":self.my_mac,
                                "N_SEQ":self.N_SEQ,
                                "N_FRAG":self.N_FRAG,
                                "timestamp":time.time()
                            }
                            packet = MAC.generate_pkt("DATA_FRAG", ElvOption.option.interp, ElvOption.option.regime, values)
                            self.N_SEQ += 1
                            self.N_FRAG += 1
                            pkt = MAC.create_packet("PKT", packet)
                            print "[T]-[FRAGMENTED DATA]-[DA:%s]-[SA:%s]-[MF:1]-[#seq:%i]-[#frag:%i]-[Payload = %s]" \
                                %(
                                    MAC.which_dir(self.dest_mac),
                                    MAC.which_dir(self.my_mac),
                                    self.N_SEQ,
                                    self.N_FRAG,
                                    payload_tmp
                                )
                            #if options.V: print "| TRANSMITTING_FRAGMENTED_PACKET | Send DATA FRAG | WAIT_ACK_FRAGMENTED |"
                            MAC.transmit(pkt, self.PHY_port)
                            fragments.pop(0)   #FIXME Retransmission for Fragmented packets is required
                            fin_wait_ack_fragmented = False
                            self.State = "WAIT_ACK_FRAGMENTED"
                        elif len(fragments) == 1:
                            payload_tmp = fragments[0]
                            #Create packet with MORE FRAGMENT = 0 and payload = payload_tmp
                            values = {
                                "payload":payload_tmp,
                                "address1":self.dest_mac,
                                "address2":self.my_mac,
                                "N_SEQ":self.N_SEQ,
                                "N_FRAG":self.N_FRAG,
                                "timestamp":time.time()
                            }
                            self.N_SEQ += 1
                            self.N_FRAG += 1
                            self.N_FRAG = 0
                            print "[T]-[DATA]-[DA:%s]-[SA:%s]-[MF:0]-[#seq:%i]-[Payload = %s]" \
                                %(
                                    MAC.which_dir(self.dest_mac),
                                    MAC.which_dir(self.my_mac),
                                    self.N_SEQ,
                                    payload_tmp
                                )
                            #if options.V: print "| TRANSMITTING_FRAGMENTED_PACKET | Send DATA FRAG (last fragment) | WAIT_ACK_FRAGMENTED |"
                            packet = MAC.generate_pkt("DATA", ElvOption.option.interp, ElvOption.option.regime, values)
                            pkt = MAC.create_packet("PKT", packet)
                            MAC.transmit(pkt, self.PHY_port)
                            fin_wait_ack_fragmented = True
                            self.State = "WAIT_ACK_FRAGMENTED"

                #WAIT_ACK_FRAGMENTED STATE
                elif self.State == "WAIT_ACK_FRAGMENTED":
                    print self.State
                    if self.WF_ACK_FG_first_time == 1:
                        T_ACK = self.SIFS
                    ta1 = time.time()
                    no_packet, packet_phy = MAC.read_phy_response(self.PHY_port, "ACK")
                    if no_packet == "YES": # ACK addressed to this station
                        x = packet_phy["INFO"]
                        print "[R]-[ACK-FRAG]-[DA: %s]-[IFM:1]" %(MAC.which_dir(x["RX_add"]))
                        if fin_wait_ack_fragmented == True:  # Last fragment sent
                            #if options.V: print "| WAIT_ACK_FRAGMENTED | All fragments acknowledged  | IDLE |"
                            self.State = "IDLE"
                            MAC.remove_ul_buff_packet(self.MAC_port)    # Remove the packet from upper layers
                            first_tx = True
                        else:
                            print "[R]-[ACK-FRAG]-[DA:%s]-[IFM:1]" %(MAC.which_dir(x["RX_add"]))
                            #if options.V: print "| WAIT_ACK_FRAGMENTED | ACK received | TRANSMITTING_FRAGMENTED_PACKET |"
                            self.State = "TRANSMITTING_FRAGMENTED_PACKET"
                        self.BACKOFF = 0
                        WF_ACK_FG_first_time = 1
                        ACK_FG_fin = 1
                    else:
                        self.State = "WAIT_ACK_FRAGMENTED"  # Not an ACK
                        WF_ACK_FG_first_time = 0
                        ACK_FG_fin = 0
                    ta2=time.time()

                    assert (self.tslot - (ta2 - ta1) >=0),"Timing Error. Please increase the beta parameter."
                    time.sleep(self.tslot - (ta2 - ta1))
                    tb = time.time()
                    T_ACK = T_ACK - (tb - ta1)
                    if ACK_FG_fin == 0:
                        if T_ACK > 0:
                            #if options.V: print "| WAIT_ACK_FRAGMENTED | ACK not received yet | WAIT_ACK_FRAGMENTED |"
                            self.State = "WAIT_ACK_FRAGMENTED"
                        else:
                            #if options.V: print "| WAIT_ACK_FRAGMENTED | ACK not received | IDLE |"
                            self.State = "IDLE"
                            MAC.remove_ul_buff_packet(self.MAC_port)    # ACK not received within the Waiting_for_ack interval
                            first_tx = True

                #TX_ACK_FG STATE
                elif self.State == "TX_ACK_FG":
                    print self.State
                    values = {"duration":0, "mac_ra":self.dest_mac, "timestamp":time.time()} #dest_mac value copied from the previous Data packet
                    print "[T]-[ACK]-[duration=%f]-[DA:%s]" %(values["duration"],MAC.which_dir(self.dest_mac))
                    #if options.V: print "| TX_ACK_FG | ACK sent | WAITING_FOR_DATA |"
                    ACK = MAC.generate_pkt("ACK", ElvOption.option.interp, ElvOption.option.regime, values)
                    packet_ACK = MAC.create_packet("PKT", ACK)
                    MAC.transmit(packet_ACK, self.PHY_port)
                    self.State = "WAITING_FOR_DATA"

                #TRANSMITTING_ACK STATE
                elif self.State == "TRANSMITTING_ACK":
                    print self.State
                    #time.sleep(SIFS)
                    values = {"duration":0, "mac_ra":self.dest_mac, "timestamp":time.time()} #dest_mac value copied from the previous Data packet
                    ACK = MAC.generate_pkt("ACK", ElvOption.option.interp, ElvOption.option.regime, values)
                    packet_ACK = MAC.create_packet("PKT", ACK)
                    print "[T]-[ACK]-[duration=%f]-[DA:%s]" %(values["duration"], MAC.which_dir(self.dest_mac))
                    MAC.transmit(packet_ACK, self.PHY_port)
                    self.State = "IDLE"
                    #if options.V: print "| TRANSMITTING_ACK | ACK sent | IDLE |"
        except Exception as e:
            print e

    def run(self):
        ElvEvent("MAC layer started")
        p1 = threading.Thread(target=self.mac_loop)
        p1.start()

# Finite State Machine MAC main
def main():
    elvOptions.ElvOption()
            
    mac = MACLayer()
    mac.run()
     


    
    #if options.V:
    #    print "============================================="
    #    print " \t  MAC layer: DCF + RTS/CTS"
    #    print "============================================="
    #    print "MAC address:",MAC.which_dir(my_mac)
    #    print "Rate = ",options.regime
    #    print "tslot(s): %f \t SIFS(s): %f"%(tslot,SIFS)
    #    print "DIFS(s): %f \t T_ACK(s): %f"%(DIFS, ACK_time)
    #    print "pseudo-random exp. BACKOFF [%i,%i]"%(CW_min, CW_max)
    #    if options.RTS:
    #        print "RTS/CTS: enabled"
    #        print "\t with RTS Threshold(Bytes): %i \t" %RTS_THRESHOLD
    #    else: print "RTS/CTS: disabled"
    #    print "Fragmentation Threshold (Bytes):",dot11FragmentationTh
    #    if options.retx: print "Retransmissions: enabled"
    #    else: print "Retransmissions: disabled"
    #    print "Scaling time parameter = ",beta
    #    print "============================================="
    
    """
    Starts the MAC operation
    """


        
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
