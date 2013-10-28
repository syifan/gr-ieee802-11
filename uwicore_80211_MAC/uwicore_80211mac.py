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
#	Juan R. Gutierrez-Agullo (jgutierrez@umh.es)
#	Baldomero Coll-Perales (bcoll@umh.es)
#	Dr. Javier Gozalvez (j.gozalvez@umh.es)


from optparse import OptionParser
from gnuradio.eng_option import eng_option
import uwicore_mac_utils as MAC

import time, sys, random

# Finite State Machine MAC main
def main():
    parser = OptionParser(option_class=eng_option, conflict_handler="resolve")
    parser.add_option("", "--PHYport", type="intx", default=8013,
                          help="PHY communication socket port, [default=%default]")
    parser.add_option("", "--MACport", type="intx", default=8001,
                          help="MAC communication socket port, [default=%default]")
    parser.add_option("-i", "--interp", type="intx", default=10,
                          help="USRP2 interpolation factor value, [default=%default]\
                5  -> 802.11a/g, OFDM T_Symbol=4us, \
                10 -> 802.11p, OFDM T_Symbol=8us")
    parser.add_option("", "--regime", type="string", default="1",
                          help="OFDM regimecode    [default=%default]\
                        1 -> 6 (3) Mbit/s (BPSK r=0.5), \
                        2 -> 9 (4.5) Mbit/s (BPSK r=0.75), \
                        3 -> 12 (6) Mbit/s (QPSK r=0.5), \
                        4 -> 18 (9) Mbit/s (QPSK r=0.75), \
                          5 -> 24 (12) Mbit/s (QAM16 r=0.5), \
                        6 -> 36 (18) Mbit/s (QAM16 r=0.75), \
                        7 -> 48 (24) Mbit/s (QAM64 r=0.66), \
                        8 -> 54 (27) Mbit/s (QAM64 r=0.75)")
    parser.add_option("-n", "--node", type="intx", default=1,
                          help="Number of USRP2 node, [default=%default]")
    parser.add_option("", "--beta", type="float", default=10000,
                          help="Scaling Time Parameter, [default=%default]")
    parser.add_option("-t", "--time_slot", type="float", default=9e-6,
                          help="Time slot value, [default=%default]")
    parser.add_option("-B", "--BI", type="float", default=1,
                          help="Beacon Interval (BI) value in seconds, [default=%default]")
    parser.add_option("-S", "--SIFS", type="float", default=16e-6,
                          help="Short Inter-frame space (SIFS) value, [default=%default]")
    parser.add_option('', "--retx", action="store_true", default=False,
                        help="Retransmissions enabled, [default=%default]")
    parser.add_option('', "--RTS", action="store_true", default=False,
                        help="RTS-threshold enabled, [default=%default]")
    parser.add_option('-v', "--V", action="store_true", default=False,
                        help="Print debug information, [default=%default]")
    (options, args) = parser.parse_args ()
            
    my_mac = MAC.usrp2_node(options.node)   # MAC address for this node
    dest_mac = MAC.usrp2_node(2)            # Dummy value (updated when an incoming packet arrives)
     
    """
    IEEE 802.11-a MAC parameters
    """
    beta = options.beta # scaling time parameter
    tslot = options.time_slot * beta
    SIFS = options.SIFS * beta
    DIFS = SIFS + 2 * tslot
    Preamble = DIFS #16e-6
    PLCP_header = 4e-6 * beta
    ACK_time = Preamble + PLCP_header
    CW_min = 15
    CW_max = 1023
    RTS_THRESHOLD = 150
    dot11FragmentationTh = 1036

    # TX time estimation for a CTS and an ACK packet
    empty_values = {"duration":0, "mac_ra":my_mac, "timestamp":time.time()}  
    CTS_empty = MAC.generate_pkt("CTS", options.interp, options.regime, empty_values)
    T_cts = CTS_empty["INFO"]["txtime"]
    ACK_empty = MAC.generate_pkt("ACK", options.interp, options.regime, empty_values)
    T_ack = ACK_empty["INFO"]["txtime"]
    
    # Set socket ports
    PHY_port = options.PHYport
    #PHYRX_port = options.PHYRXport
    MAC_port = options.MACport
    
    # Variables involving MAC tests
    testing = False                         # Testing mode active, used to conduct trials
    N_TESTS = 1000                          # Number of tests
    N_TESTS_INI = N_TESTS           
    LONG_TESTS = 20                         # Payload length for tests
    payload_test = "0000" + LONG_TESTS*'1'  # Payload for tests
    test_with_sensing = True                 # Carrier Sensing (CS) allowed during the test
    total_processing_time = 0          # Total processing time
    t_sense_mean = 0                     # CS average time
    t_csense = 0                           # CS time
    t_MAC = 0                               # MAC time
    t_MAC_mean = 0                         # MAC average time
    packet_i=0                             # Packets sent counter
    n_sensing = 0                           # Number of CS performed
    
    # 'State' controls the state of the MAC
    State = "IDLE" 
    
    # Initial Conditions of the Finite State Machine
    NAV = 0                 # Network Allocation Vector           
    N_RETRIES = 0           # Retries to send a packet counter
    busy_in_wfd = False  # Busy in Wait_for_DIFS state
    BO_frozen = "NO"     # Backoff frozen    
    TX_attempts = 0             # Tries to send a packet counter
    CTS_failed = False      # CTS reception failed
    chan = "FREE"          # Channel state = IDDLE
    N_SEQ = 0               # Sequence number counter
    N_FRAG = 0              # Fragment number counter
    first_tx = True         # Is the first attempt to send a packet?
    frag_count = 0         # Counter used during fragmentation
    data_temp_reass = ""     # Initial variable to perform de re-assembly process
    verbose = True          # Shows when the MAC is in 'IDDLE' state
    beaconing = False       # Is ON the Beaconing process?
    fragmenting = 0         # Is the packet received a fragment?
    
    if options.V:
        print "============================================="
        print " \t  MAC layer: DCF + RTS/CTS"
        print "============================================="
        print "MAC address:",MAC.which_dir(my_mac)
        print "Rate = ",options.regime
        print "tslot(s): %f \t SIFS(s): %f"%(tslot,SIFS)
        print "DIFS(s): %f \t T_ACK(s): %f"%(DIFS, ACK_time)
        print "pseudo-random exp. BACKOFF [%i,%i]"%(CW_min, CW_max)
        if options.RTS: 
            print "RTS/CTS: enabled"
            print "\t with RTS Threshold(Bytes): %i \t" %RTS_THRESHOLD
        else: print "RTS/CTS: disabled"
        print "Fragmentation Threshold (Bytes):",dot11FragmentationTh
        if options.retx: print "Retransmissions: enabled"
        else: print "Retransmissions: disabled"
        print "Scaling time parameter = ",beta
        print "============================================="
    
    """
    Starts the MAC operation
    """
    while 1:
        #IDLE STATE
        if State == "IDLE":
            # Is a RTS?
            reply_phy1, packet_phy1 = MAC.read_phy_response(PHY_port, "RTS")
            #print State
            if reply_phy1 == "YES":
                verbose = True          # Show when the MAC is IDLE
                copied = packet_phy1  # Copy the received packet from the PHY
                x = copied["INFO"]     # Copy the 802.11 frame included in the received packet from PHY
                if my_mac == x["RX_add"]:
                    print "[R]-[%s]-[DA: %s]-[SA: %s]-[duration: %f]-[IFM:1]" %(copied["HEADER"],MAC.which_dir(x["RX_add"]),MAC.which_dir(x["TX_add"]),x["txtime"])
                    dest_mac = (x["TX_add"])        # Receiver Address of the CTS frame
                    RTS_duration = x["txtime"]      # Value of RTS' TX time 
                    if options.V: print "| IDLE | RTS received | TRANSMITTING_CTS |"    
                    """
                    #============================================================
                    # /TEST/ UNCOMMENT TO CHECK RTS/CTS FUNCTIONALITY
                    #============================================================
                    # STEP 1/4: Node 1 --> RTS
                    values = {"duration":x["txtime"], "mac_ra":x["RX_add"], "mac_ta":x["TX_add"], "timestamp":time.time()}  
                    RTS_forced = MAC.generate_pkt("RTS", options.interp, options.regime, values)
                    packet_RTS_forced = MAC.create_packet("PKT", RTS_forced)
                    MAC.transmit(packet_RTS_forced, PHY_port)
                    time.sleep(tslot)
                    #============================================================
                    """
                    State = "TRANSMITTING_CTS"
                else:
                    print "[R]-[%s]-[DA:%s]-[SA:%s]-[duration:%f]-[IFM:0]" %(copied["HEADER"],MAC.which_dir(x["RX_add"]),MAC.which_dir(x["TX_add"]),x["txtime"])  
                    tiempo = x["txtime"] / (1.0e3)    # Divided by 1e3 because txtime is on milliseconds
                    if options.V: print "| IDLE | RTS captured (update NAV) | IDLE |"
                    NAV = MAC.update_NAV(time.time(), tiempo, tslot)
                    State = "IDLE"
                                        
            # Check upper layer buffer for data to send
            else:
                reply_up, PAYLOAD = MAC.read_ul_buffer(MAC_port)
                if reply_up == "YES":
                    verbose = True
                    if options.V: print "| IDLE | MAC has DATA to Tx | WAIT_FOR_NAV |"
                    State = "WAIT_FOR_NAV"
                elif reply_up == "BEACON":
                    beaconing = True
                    if options.V: print "| IDLE | Transmit BEACON FRAME | WAIT_FOR_NAV |"
                    State = "TRANSMITTING_RTS"
                elif reply_up == "NO":   
                    # is a CTS?                       
                    reply_phy2, packet_phy2 = MAC.read_phy_response(PHY_port, "CTS")
                    if reply_phy2 == "YES":
                        verbose = True
                        copied = packet_phy2
                        x = copied["INFO"]
                        print "[R]-[%s]-[DA:%s]-[duration:%f]-[IFM:0]" %(copied["HEADER"],MAC.which_dir(x["RX_add"]),x["txtime"])
                        tiempo = x["txtime"]/1.0e3 
                        if options.V: print "| IDLE | CTS captured (update NAV) | IDLE |"
                        NAV = MAC.update_NAV(time.time(), tiempo, tslot)
                        State = "IDLE"
                    else:
                        if verbose == True: 
                            print "\n| IDLE |\n"
                        verbose = False
                        State = "IDLE"
            if testing == True: # if True, it allows to switch manually to any state 
                t_testA = time.time() 
                packet_i +=1
                State = "WAIT_FOR_NAV" # Edit the state to switch to 
            
            if State == "IDLE": time.sleep(tslot)   # Time-slotted MAC
        
        
        #WAIT_FOR_NAV STATE
        elif State == "WAIT_FOR_NAV":
            #print State
            NAV = MAC.update_NAV(time.time(), NAV, tslot)
            if NAV > 0:
                if options.V: print "| WAIT_FOR_NAV | NAV > 0 | WAIT_FOR_NAV |"
                State = "WAIT_FOR_NAV"
            else:
                if options.V: print "| WAIT_FOR_NAV | NAV = 0 | WAIT_FOR_DIFS |"
                State = "WAIT_FOR_DIFS"
                chan = "FREE"
                
        #WAIT_FOR_DIFS STATE
        elif State == "WAIT_FOR_DIFS":
            # This state performs the channel sensing process and decides whether the channel is BUSY or IDLE
            #print State
            t_inicial=time.time()
            t_final=t_inicial + DIFS
            n_sensing=0
            while n_sensing < 2:
                t_testB = time.time()
                channel_in_wfd, t = MAC.sense_channel(PHY_port)
                t_testC = time.time()
                assert (tslot - (t_testC-t_testB) >=0),"Timing Error. Please increase the beta parameter."
                time.sleep(tslot-(t_testC-t_testB))
                if channel_in_wfd == "OCCUPIED":
                    chan = "OCCUPIED"
                t_csense = t_csense + (t_testC - t_testB)
                n_sensing +=1          
            assert (t_final - time.time() >=0),"Timing Error. Please increase the beta parameter."
            time.sleep(t_final - time.time())
            t_csense = t_csense/3
            # print "Wait_for_DIFS operation time = ", (time.time()-t_inicial) # DEBUG
            
            if chan == "FREE":
                if BO_frozen == "NO" and busy_in_wfd == False and CTS_failed == False:
                    BACKOFF = 0 # Channel IDLE for the first time, BOtimer = 0
                State = "BACKING_OFF"
                if options.V: print "| WAIT_FOR_DIFS | Channel idle | BACKING_OFF |"            
            else:
                if BO_frozen == "NO" and CTS_failed == False:  # If it is the 1st time, set the CW
                    BACKOFF = MAC.retry(TX_attempts, CW_min)
                    TX_attempts = TX_attempts + 1
                    #BO_frozen=="YES"
                    BO_first_time = 1
                State = "IDLE"
                chan = "FREE"
                if options.V: print "| WAIT_FOR_DIFS | Channel busy | IDLE |"
        
        
        #BACKING_OFF STATE
        elif State == "BACKING_OFF":
            #print State
            busy_in_wfd = False
            if BACKOFF == 0:
                BO_first_time = 1
                State = "TRANSMITTING_RTS"
            else:
                tx = time.time()                
                canal_en_bo, t = MAC.sense_channel(PHY_port)
                
                if canal_en_bo == "FREE": # Channel idle
                    BACKOFF = BACKOFF - 1
                    BO_first_time = 0 # Backoff process started, freeze CW value!
                    if BACKOFF > 0:    
                        if options.V: print "| BACKING_OFF | Channel idle (CW = %i) | BACKING_OFF |"%BACKOFF
                        State = "BACKING_OFF"
                    else:
                        if options.V: print "| BACKING_OFF | Channel idle (CW = %i) | TRANSMITTING_RTS |"%BACKOFF 
                        State = "TRANSMITTING_RTS"
                        busy_in_wfd = False
                        
                else:   # Channel busy
                    BACKOFF = BACKOFF - 1
                    BO_first_time = 0 # Channel busy, CW frozen
                    BO_frozen = "YES"
                    State = "IDLE"
                    if options.V:
                        if options.V: print "| BACKING_OFF | Channel busy (CW = %i) | IDLE |"%BACKOFF 
                ty = time.time()
                assert (tslot - (ty - tx) >=0),"Timing Error. Please increase the beta parameter."
                time.sleep(tslot - (ty - tx))
        
        #TRANSMITTING_RTS STATE
        elif State == "TRANSMITTING_RTS":
            #print State
            #TX_attempts = 0 # DEBUG
            BO_first_time = 1 # Update backoff status for the next time
            
            # Work out TX time of the packet to send
            if testing == True:
                N_TESTS -= 1
                N_SEQ +=1 
                values = {"payload":payload_test, "address1":dest_mac, "address2":my_mac, "N_SEQ":N_SEQ, "N_FRAG":0,"timestamp":time.time()}
                test = MAC.generate_pkt("DATA", options.interp, options.regime, values)
                packet_TEST = MAC.create_packet("PKT", test)
                t_testD = time.time()
                                
                # Send the packet to PHY
                MAC.transmit(packet_TEST, PHY_port)
                
                t_MAC = t_MAC + (t_testD-t_testA)
                t_MAC_mean = t_MAC/packet_i
                t_sense_mean = t_sense_mean + t_csense
                print "=============== Packet %i ==================="%(packet_i)
                print "MAC processing time = ",(t_testD-t_testA)
                print "MAC processing time (average) = ", t_MAC_mean
                print "Carrier sensing time = ",(t_testC - t_testB)
                print "Carrier sensing time (average) = ",t_sense_mean/packet_i
                print "============================================="
                
                if N_TESTS == 0: 
                    sys.stderr.write("End of Test. Press ENTER to exit")
                    z=raw_input()
                    sys.exit(0)
            
            # Not a Beacon to TX
            elif beaconing == False:    
                values = {"payload":PAYLOAD, "address1":dest_mac, "address2":my_mac, "N_SEQ":N_SEQ, "N_FRAG":N_FRAG, "timestamp":time.time()}
                packet = MAC.generate_pkt("DATA", options.interp, options.regime, values)
                T_data = packet["INFO"]["txtime"]
                '''
                 Value of RTS fields:
                 Duration = T_cts + T_ack + 3*SIFS + T_data
                 mac_ra = dest_mac
                 mac_ta = my_mac
                '''
                if options.RTS == True:
                    if PAYLOAD > RTS_THRESHOLD:
                        if first_tx == True: 
                            retx_retries = 7
                            fail_tx = False
                        first_tx = False
                        duration = (3 * SIFS) + (T_cts + T_ack + T_data) / 1000     #Txtime in milliseconds
                        mac_ra = dest_mac
                        mac_ta = my_mac
                        values = {"duration":duration, "mac_ra":mac_ra, "mac_ta":mac_ta,"timestamp":time.time()}  
                        RTS = MAC.generate_pkt("RTS", options.interp, options.regime, values)
                        packet_RTS = MAC.create_packet("PKT", RTS)
                        MAC.transmit(packet_RTS, PHY_port)
                        print "[T]-[RTS]-[SA:%s]-[DA=%s]-[duration:%i]" %(MAC.which_dir(my_mac),MAC.which_dir(mac_ta),duration)
                        WFC_first_time = 1  # First time in WAITING_FOR_CTS state
                        State = "WAITING_FOR_CTS"
                        if options.V: print "| TRANSMITTING_RTS | (PAYLOAD > RTS_Th) Send RTS | WAITING_FOR_CTS |"
                    else:
                        if first_tx == True: 
                            retx_retries = 4
                            fail_tx = False
                        first_tx = False
                        State = "TRANSMITTING_UNICAST"
                        if options.V: print "| TRANSMITTING_RTS | (PAYLOAD < RTS_Th) Send DATA | TRANSMITTING_UNICAST |"
                else:
                    if first_tx == True: 
                        retx_retries = 4
                        fail_tx = False
                    first_tx = False
                    if options.V: print "| TRANSMITTING_RTS | (RTS OFF) Send DATA | TRANSMITTING_UNICAST |"
                    State = "TRANSMITTING_UNICAST"
            else:
                values = {"address2":my_mac, "N_SEQ":N_SEQ,"N_FRAG":0 ,"BI":options.BI, "timestamp":time.time()}
                print "[T]-[BEACON]-[SA:%s]-[BI=%f]-[#seq:%i]" %(MAC.which_dir(my_mac),options.BI,N_SEQ)
                if options.V: print "| TRANSMITTING_RTS | Send BEACON | IDLE |"
                BEACON = MAC.generate_pkt("BEACON", options.interp, options.regime, values)
                packet_BEACON = MAC.create_packet("PKT", BEACON)
                MAC.transmit(packet_BEACON, PHY_port)
                MAC.remove_ul_buff_packet(MAC_port)
                N_SEQ += 1
                beaconing = False
                verbose = True
                State = "IDLE"
                
        #TRANSMITTING_UNICAST STATE
        elif State == "TRANSMITTING_UNICAST":
            '''
            Send packet to PHY for its transmission using the USRP2
            packet = [MPDU][LENGHT][INFO]  
            pkt = [Header: PKT][Data: packet]
            '''
            #print State
            #if options.V: print "[%s]\t: TX DATA packet to PHY" % State
            if len(PAYLOAD) > dot11FragmentationTh:
                if options.V: print "| TRANSMITTING_UNICAST | Send Fragmented Data | TRANSMITTING_FRAGMENTED_PACKET |"
                State = "TRANSMITTING_FRAGMENTED_PACKET"
                first_time_fg = True
                WF_ACK_FG_first_time = True
            else:
                values = {"payload":PAYLOAD, "address1":dest_mac, "address2":my_mac, "N_SEQ":N_SEQ, "N_FRAG":N_FRAG, "timestamp":time.time()}
                print "[T]-[DATA]-[DA:%s]-[SA:%s]-[MF:0]-[#seq:%i]-[Payload = %s]" %(MAC.which_dir(dest_mac),MAC.which_dir(my_mac),N_SEQ,PAYLOAD)
                if options.V: print "| TRANSMITTING_UNICAST | Send DATA | WAITING_FOR_ACK |"
                N_SEQ += 1
                N_FRAG = 0
                if fail_tx == False:
                    packet = MAC.generate_pkt("DATA", options.interp, options.regime, values)
                else:
                     packet = MAC.generate_pkt("DATA_RETX", options.interp, options.regime, values)
                pkt = MAC.create_packet("PKT", packet)
                MAC.transmit(pkt, PHY_port)
                WF_ACK_first_time = 1 # First time in WAITING_FOR_ACK state 
                State = "WAITING_FOR_ACK"
    
        # WAITING_FOR_CTS STATE
        elif State == "WAITING_FOR_CTS":
            #print State
            if WFC_first_time == 1:
                CTS_time = SIFS
                CTS_fin = 0 
            t0 = time.time()
            no_packet, packet_phy = MAC.read_phy_response(PHY_port, "CTS")
            
            '''
            #============================================================
            # /TEST/ UNCOMMENT TO CHECK RTS/CTS FUNCTIONALITY
            #============================================================
            # STEP 2/4: Node 2 --> CTS
            mac_ra = my_mac
            values = {"duration":0, "mac_ra":mac_ra,"timestamp":time.time()}  
            CTS_forced = MAC.generate_pkt("CTS", options.interp, options.regime, values)
            packet_CTS_forced = MAC.create_packet("PKT", CTS_forced)
            MAC.transmit(packet_CTS_forced, PHY_port)
            time.sleep(tslot)
            #============================================================
            '''
            if no_packet == "YES":
                # Is the CTS frame for this station? 
                copied = packet_phy["INFO"]
                if copied["RX_add"] == my_mac:
                    WFC_first_time = 1
                    State = "TRANSMITTING_UNICAST"
                    CTS_fin = 1
                    TX_attempts = 0
                    CTS_failed = False
                    if options.V:
                        print "[R]-[CTS]-[RA: %s]-[duration: %f]-[IFM:1]" %(MAC.which_dir(copied["RX_add"]),copied["txtime"])
                        if options.V: print "| WAITING_FOR_CTS | CTS received | TRANSMITTING_UNICAST |"    
                else:
                    CTS_fin = 1 # CTS captured! Transmission aborted to avoid a collision
                    print "[R]-[CTS]-[RA:%s]-[duration:%f]-[IFM:0]" %(MAC.which_dir(copied["RX_add"]),copied["txtime"])
                    State = "IDLE"
                    nuevo_NAV = copied["txtime"]/1e3
                    NAV = MAC.update_NAV(time.time(),nuevo_NAV , tslot)
                    if options.V: print "| WAITING_FOR_CTS | CTS captured (Update NAV = %f) | IDLE |"%NAV

            else:
                State = "WAITING_FOR_CTS"  
                WFC_first_time = 0    
                #CTS_fin = 0
            t1 = time.time()
            CTS_time = CTS_time - (t1 - t0)
            
            if CTS_fin == 0:
                if CTS_time > 0:
                    State = "WAITING_FOR_CTS"  
                else:
                    TX_attempts = TX_attempts + 1
                    BACKOFF = MAC.retry(TX_attempts, CW_min)
                    State = "IDLE"             # Timer expired and CTS hasn't been received
                    if options.V:
                        if options.V: print "| WAITING_FOR_CTS | CTS not received | IDLE |"
                    CTS_failed = True
        

        #TRANSMITTING_FRAGMENTED_PACKET STATE
        elif State == "TRANSMITTING_FRAGMENTED_PACKET":
            #print State
            if first_time_fg == True:
                fragments = MAC.fragment(PAYLOAD, dot11FragmentationTh) #fragment the PAYLOAD based on a fragmentation threshold
                first_time_fg = False
            else:
                if len(fragments) > 1:
                    payload_tmp = fragments[0]
                    #Create packet with MORE FRAGMENT = 1 and payload = payload_tmp
                    values = {"payload":payload_tmp, "address1":dest_mac, "address2":my_mac, "N_SEQ":N_SEQ, "N_FRAG":N_FRAG, "timestamp":time.time()}
                    packet = MAC.generate_pkt("DATA_FRAG", options.interp, options.regime, values)
                    N_SEQ += 1
                    N_FRAG += 1
                    pkt = MAC.create_packet("PKT", packet)                   
                    print "[T]-[FRAGMENTED DATA]-[DA:%s]-[SA:%s]-[MF:1]-[#seq:%i]-[#frag:%i]-[Payload = %s]" %(MAC.which_dir(dest_mac),MAC.which_dir(my_mac),N_SEQ,N_FRAG,payload_tmp)
                    if options.V: print "| TRANSMITTING_FRAGMENTED_PACKET | Send DATA FRAG | WAIT_ACK_FRAGMENTED |"
                    MAC.transmit(pkt, PHY_port)
                    fragments.pop(0)   #FIXME Retransmission for Fragmented packets is required
                    fin_wait_ack_fragmented = False
                    State = "WAIT_ACK_FRAGMENTED"
                elif len(fragments) == 1:
                    payload_tmp = fragments[0]
                    #Create packet with MORE FRAGMENT = 0 and payload = payload_tmp
                    values = {"payload":payload_tmp, "address1":dest_mac, "address2":my_mac, "N_SEQ":N_SEQ, "N_FRAG":N_FRAG, "timestamp":time.time()}
                    N_SEQ += 1
                    N_FRAG += 1
                    N_FRAG = 0
                    print "[T]-[DATA]-[DA:%s]-[SA:%s]-[MF:0]-[#seq:%i]-[Payload = %s]" %(MAC.which_dir(dest_mac),MAC.which_dir(my_mac),N_SEQ, payload_tmp)
                    if options.V: print "| TRANSMITTING_FRAGMENTED_PACKET | Send DATA FRAG (last fragment) | WAIT_ACK_FRAGMENTED |"
                    packet = MAC.generate_pkt("DATA", options.interp, options.regime, values) 
                    pkt = MAC.create_packet("PKT", packet)                   
                    MAC.transmit(pkt, PHY_port)
                    fin_wait_ack_fragmented = True
                    State = "WAIT_ACK_FRAGMENTED" 

        #WAIT_ACK_FRAGMENTED STATE          
        elif State == "WAIT_ACK_FRAGMENTED":
            #print State
            if WF_ACK_FG_first_time == 1:
                T_ACK = SIFS
            ta1 = time.time()
            no_packet, packet_phy = MAC.read_phy_response(PHY_port, "ACK")
            if no_packet == "YES": # ACK addressed to this station
                x = packet_phy["INFO"]
                print "[R]-[%s]-[DA: %s]-[duration:%f]-[IFM:1]" %(packet_phy["HEADER"],MAC.which_dir(x["RX_add"]),x["txtime"])
                if fin_wait_ack_fragmented == True:  # Last fragment sent
                    if options.V: print "| WAIT_ACK_FRAGMENTED | All fragments acknowledged  | IDLE |"
                    State = "IDLE"
                    MAC.remove_ul_buff_packet(MAC_port)    # Remove the packet from upper layers
                    first_tx = True
                else:
                    print "[R]-[%s]-[DA:%s]-[duration:%f]-[IFM:1]" %(packet_phy["HEADER"],MAC.which_dir(x["RX_add"]),x["txtime"])
                    if options.V: print "| WAIT_ACK_FRAGMENTED | ACK received | TRANSMITTING_FRAGMENTED_PACKET |"
                    State = "TRANSMITTING_FRAGMENTED_PACKET"
                BACKOFF = 0
                WF_ACK_FG_first_time = 1
                ACK_FG_fin = 1 
            else:
                State = "WAIT_ACK_FRAGMENTED"  # Not an ACK
                WF_ACK_FG_first_time = 0
                ACK_FG_fin = 0
            ta2=time.time()
            
            assert (tslot - (ta2 - ta1) >=0),"Timing Error. Please increase the beta parameter."
            time.sleep(tslot - (ta2 - ta1))
            tb = time.time()
            T_ACK = T_ACK - (tb - ta1)
            if ACK_FG_fin == 0:
                if T_ACK > 0:
                    if options.V: print "| WAIT_ACK_FRAGMENTED | ACK not received yet | WAIT_ACK_FRAGMENTED |"
                    State = "WAIT_ACK_FRAGMENTED"
                else: 
                    if options.V: print "| WAIT_ACK_FRAGMENTED | ACK not received | IDLE |"
                    State = "IDLE"
                    MAC.remove_ul_buff_packet(MAC_port)    # ACK not received within the Waiting_for_ack interval
                    first_tx = True
            

        #WAITING_FOR_ACK STATE                        
        elif State == "WAITING_FOR_ACK":
            #print State
            if WF_ACK_first_time == 1:
                T_ACK = SIFS
            ta = time.time()
            no_packet, packet_phy = MAC.read_phy_response(PHY_port, "ACK")
            if no_packet == "YES":
                x = packet_phy["INFO"]            
                print "[R]-[%s]-[DA:%s]-[duration:%f]-[IFM:1]" %(packet_phy["HEADER"],MAC.which_dir(x["RX_add"]),x["txtime"])
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
                if options.V: print "| WAITING_FOR_ACK | ACK received | IDLE |"
                State = "IDLE"
                BACKOFF = 0
                WF_ACK_first_time = 1
                ACK_fin = 1 
                MAC.remove_ul_buff_packet(MAC_port)    # Packet acknoweledged, remove from upper layers
                first_tx = True
                            
            else:
                State = "WAITING_FOR_ACK"  # Not an ACK
                WF_ACK_first_time = 0
                ACK_fin = 0
            
            ta_fin = time.time()
            assert (tslot - (ta_fin - ta) >=0),"Timing Error. Please increase the beta parameter."
            time.sleep(tslot - (ta_fin - ta))
            tb = time.time()
            T_ACK = T_ACK - (tb - ta)
            if ACK_fin == 0:
                if T_ACK > 0:
                    if options.V: print "| WAITING_FOR_ACK | ACK not received yet | WAITING_FOR_ACK |"
                    State = "WAITING_FOR_ACK"
                else:
                    # Not ACK yet, Reset CW to CWmin and go to IDLE
                    if options.retx == True:
                        retx_retries = retx_retries - 1
                        if retx_retries < 0:
                            CW = CW_min 
                            State = "IDLE"
                            MAC.remove_ul_buff_packet(MAC_port)
                            first_tx = True
                            if options.V: print "| WAITING_FOR_ACK | Remove packet from upper layers | IDLE |"
                            N_FRAG = 0 
                            fail_tx = False
                        else:
                            if options.V: print "| WAITING_FOR_ACK | ACK not received (retries left = %i) | IDLE |"%retx_retries
                            State = "IDLE"
                            fail_tx = True
                    else: 
                        State = "IDLE"
                        if options.V: print "| WAITING_FOR_ACK | Remove packet from upper layers | IDLE |"
                        MAC.remove_ul_buff_packet(MAC_port)    # No Re-TX!
                        first_tx = True
        
        #TRANSMITTING_CTS STATE        
        elif State == "TRANSMITTING_CTS":
            '''
            RTS received. NAV allows channel access.
            Send CTS to PHY for its transmission.
                - packet = [CTS][LENGHT][INFO]
                - pkt = [Header: PKT][Data: packet]
            '''
            #print State
            NAV = MAC.update_NAV(time.time(), NAV, tslot)
            if NAV > 0:
                if options.V: print "| TRANSMITTING_CTS | NAV > 0 | TRANSMITTING_CTS |"
                State = "TRANSMITTING_CTS"
            else:
                duration = RTS_duration - (2 * T_cts) / 10 - SIFS 
                mac_ra = dest_mac
                values = {"duration":duration, "mac_ra":mac_ra, "timestamp":time.time()}  
                CTS = MAC.generate_pkt("CTS", options.interp, options.regime, values)
                packet_CTS = MAC.create_packet("PKT", CTS)
                print "[T]-[CTS]-[DA:%s]-[duration=%f]" %(MAC.which_dir(mac_ra),duration)
                if options.V: print "| TRANSMITTING_CTS | CTS sent | WAITING_FOR_DATA |"
                MAC.transmit(packet_CTS, PHY_port)
                WF_DATA_first_time = 1
                State = "WAITING_FOR_DATA"
                
        #WAITING_FOR_DATA STATE              
        elif State == "WAITING_FOR_DATA":
            '''
           Once the CTS is transmitted, wait for Data arrival
                -> If a data packet arrives, go to TRANSMITTING_ACK
                -> If no, go to IDLE
            '''
            #print State
            if WF_DATA_first_time == 1:
                T_DATA = SIFS
            t_1 = time.time()
            no_packet, packet_phy = MAC.read_phy_response(PHY_port, "DATA")
            if no_packet == "YES":
                x = packet_phy["INFO"] # DATA packet addressed to this station
                '''
                #============================================================
                # /TEST/ UNCOMMENT TO CHECK RTS/CTS FUNCTIONALITY
                #============================================================
                # STEP 3/4: Node 1 --> DATA
                values = {"payload":"Paquete_que_llega12", "address1":x["mac_add1"], "address2":x["mac_add2"], "N_SEQ":N_SEQ, "N_FRAG":0, "timestamp":time.time()}  
                DATA_forced = MAC.generate_pkt("DATA", options.interp, options.regime, values)
                packet_DATA_forced = MAC.create_packet("PKT", DATA_forced)
                MAC.transmit(packet_DATA_forced, PHY_port)
                time.sleep(2*tslot)
                #============================================================
                '''
                dest_mac = x["mac_add2"]
                if x["MF"]==0:  #More Fragments = 0
                    if fragmenting == 0:    # Not a fragmented packet
                        print "[R]-[DATA]-[DA:%s]-[SA:%s]-[MF:0]-[IFM:1]-[PAYLOAD = %s]" %(MAC.which_dir(x["mac_add1"]),MAC.which_dir(x["mac_add2"]),x["PAYLOAD"])
                        if options.V: print "| WAITING_FOR_DATA | DATA received | TRANSMITTING_ACK |"
                        State = "TRANSMITTING_ACK"
                        WF_DATA_first_time = 1 
                        DATA_ok = 1
                        frag_count = 0
                        MAC.send_ul_buff_packet(MAC_port, x["PAYLOAD"])
                    else:   # Last fragmented packet
                        fragmenting = 0
                        frag_count +=1
                        print "[R]-[FRAGMENTED DATA]-[DA:%s]-[SA:%s]-[MF:0]-[#seq:%i]-[#frag:%i]-[IFM:1]-[PAYLOAD = %s]" %(MAC.which_dir(x["mac_add2"]),MAC.which_dir(my_mac),x["N_SEQ"],x["N_FRAG"],x["PAYLOAD"])
                        test_seq = x["N_FRAG"]+1 - frag_count
                        if test_seq == 0:
                            dato_leido = data_temp_reass + x["PAYLOAD"]
                            State = "TRANSMITTING_ACK"
                            WF_DATA_first_time = 1
                            frag_count = 0 
                            DATA_ok = 1
                            fragmenting = 0
                            if options.V: print "| WAITING_FOR_DATA | DATA_FRAG received  (MF = 0)| TRANSMITTING_ACK |"
                            MAC.send_ul_buff_packet(MAC_port, dato_leido)
                        else: 
                            State = "IDLE"
                            WF_DATA_first_time = 1 
                            DATA_ok = 0
                            frag_count = 0
                            fragmenting = 0
                            if options.V: print "| WAITING_FOR_DATA | Error: one or more fragments not received | TRANSMITTING_ACK |"
                else: # More Fragments = 1. It's a fragment
                    print "[R]-[FRAGMENTED DATA]-[DA:%s]-[SA:%s]-[MF:1]-[#seq:%i]-[#frag:%i]-[IFM:1]-[PAYLOAD = %s]" %(MAC.which_dir(x["mac_add2"]),MAC.which_dir(my_mac),x["N_SEQ"],x["N_FRAG"],x["PAYLOAD"])
                    if options.V: print "| WAITING_FOR_DATA | DATA_FRAG received  (MF = 1)| TRANSMITTING_ACK |"
                    fragmenting = 1
                    frag_count +=1
                    DATA_ok = 1
                    data_temp_reass = data_temp_reass + x["PAYLOAD"]
                    State = "TX_ACK_FG"                          
            else:
                DATA_ok = 0
                State = "WAITING_FOR_DATA"  # Not a DATA packet
                WF_DATA_first_time = 0
            tdiff = (time.time() - t_1)
            assert (tslot - tdiff >=0),"Timing Error. Please increase the beta parameter."
            time.sleep(tslot - tdiff)
            T_DATA = T_DATA - (time.time() - t_1)
            if DATA_ok == 0:
                if T_DATA > 0:
                    if options.V: print "| WAITING_FOR_DATA | DATA not received yet | WAITING_FOR_DATA |"
                    State = "WAITING_FOR_DATA"
                else:
                    # DATA didn't arrive, go to IDLE
                    State = "IDLE"
                    if options.V: print "| WAITING_FOR_DATA | DATA not received  | IDLE |"
                    DATA_ok = 1 
        
        #TX_ACK_FG STATE     
        elif State == "TX_ACK_FG":
            #print State
            values = {"duration":0, "mac_ra":dest_mac, "timestamp":time.time()} #dest_mac value copied from the previous Data packet
            print "[T]-[ACK]-[duration=%f]-[DA:%s]" %(values["duration"],MAC.which_dir(dest_mac))
            if options.V: print "| TX_ACK_FG | ACK sent | WAITING_FOR_DATA |"
            ACK = MAC.generate_pkt("ACK", options.interp, options.regime, values)
            packet_ACK = MAC.create_packet("PKT", ACK)
            MAC.transmit(packet_ACK, PHY_port)
            State = "WAITING_FOR_DATA"
        
        #TRANSMITTING_ACK STATE  
        elif State == "TRANSMITTING_ACK":
            #print State
            values = {"duration":0, "mac_ra":dest_mac, "timestamp":time.time()} #dest_mac value copied from the previous Data packet
            ACK = MAC.generate_pkt("ACK", options.interp, options.regime, values)
            packet_ACK = MAC.create_packet("PKT", ACK)
            print "[T]-[ACK]-[duration=%f]-[DA:%s]" %(values["duration"], MAC.which_dir(dest_mac))
            MAC.transmit(packet_ACK, PHY_port)
            State = "IDLE"
            if options.V: print "| TRANSMITTING_ACK | ACK sent | IDLE |"

        
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
