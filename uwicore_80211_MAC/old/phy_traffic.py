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

# Filename: phy_traffic.py

# This script, developed by the Uwicore Laboratory at the University Miguel Hernandez of Elche, 
# generates different 802.11 frames and sends them to the PHY layer receiver. The purpose of this 
# script is to validate the different functionalities of the IEEE 802.11 MAC implemented 
# (RTS/CTS procedure, Acknowledgment of Data packets, etc.). More detailed information can be found
# at www.uwicore.umh.es/mhop-testbeds.html or at the publication:

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


import socket, pickle
import time, random
import uwicore_mpif as plcp
import uwicore_mac_utils as MAC
from gnuradio.eng_option import eng_option
from optparse import OptionParser

# PHY traffic generator main
def main():
    parser = OptionParser(option_class=eng_option, conflict_handler="resolve")
    parser.add_option("-n", "--node", type="intx", default=1, help="USRP2 node    [default=%default]")
    (options, args) = parser.parse_args ()
    def crear_paquete(tipo,data):
        packet={"TIPO":tipo,"DATOS":data}
        return packet
    #for loop used to test the correct RTS/CTS functionality, this limits the number of packets that arrived to the station
    n_packets = 0   
    print '\n',"-------------------------"
    print " PHY traffic generator ..."
    print " (Ctrl + C) to exit"
    print "-------------------------",'\n'
    for i in range (1,100):
        while n_packets < 100:  # ADJUST THE NUMBER OF PACKETS GENERATED 
            #n_packets+=1        # NOTE: commented to force infinite packet generation
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((socket.gethostname(), 8500))
            N_SEQ = random.randint(0,4095)  # Assign sequence and fragment number
            N_FRAG = 0
            
            # Values for different frames based on the MAC address of each USRP2
            
            valores_B1 = {"address2":MAC.usrp2_node(1), "N_SEQ":N_SEQ,"N_FRAG":0 ,"BI":1,"timestamp":time.time()}
            valores_B2 = {"address2":MAC.usrp2_node(2), "N_SEQ":N_SEQ,"N_FRAG":0 ,"BI":1,"timestamp":time.time()}
            valores_B3 = {"address2":MAC.usrp2_node(3), "N_SEQ":N_SEQ,"N_FRAG":0 ,"BI":1,"timestamp":time.time()}
            valores_B4 = {"address2":MAC.usrp2_node(4), "N_SEQ":N_SEQ,"N_FRAG":0 ,"BI":1,"timestamp":time.time()}
                
            valores_CTS1 = {"duration":0, "mac_ra":MAC.usrp2_node(1),"timestamp":time.time()}
            valores_CTS2 = {"duration":0, "mac_ra":MAC.usrp2_node(2),"timestamp":time.time()}
            valores_CTS3 = {"duration":0, "mac_ra":MAC.usrp2_node(3),"timestamp":time.time()}
            valores_CTS4 = {"duration":0, "mac_ra":MAC.usrp2_node(4),"timestamp":time.time()}
            
            valores_ACK1 = {"duration":0, "mac_ra": MAC.usrp2_node(1),"timestamp":time.time()}
            valores_ACK2 = {"duration":0, "mac_ra": MAC.usrp2_node(2),"timestamp":time.time()}
            valores_ACK3 = {"duration":0, "mac_ra": MAC.usrp2_node(3),"timestamp":time.time()}
            valores_ACK4 = {"duration":0, "mac_ra": MAC.usrp2_node(4),"timestamp":time.time()} 
            
            valores_DATA12={"payload":"Paquete_que_llega12", "address1":MAC.usrp2_node(2),"address2":MAC.usrp2_node(1),"N_SEQ":N_SEQ, "N_FRAG":N_FRAG, "timestamp":time.time()}
            valores_DATA13={"payload":"Paquete_que_llega13", "address1":MAC.usrp2_node(3),"address2":MAC.usrp2_node(1),"N_SEQ":N_SEQ, "N_FRAG":N_FRAG, "timestamp":time.time()}
            valores_DATA14={"payload":"Paquete_que_llega14", "address1":MAC.usrp2_node(4),"address2":MAC.usrp2_node(1),"N_SEQ":N_SEQ, "N_FRAG":N_FRAG, "timestamp":time.time()}
            
            valores_DATA21={"payload":"Paquete_que_llega21", "address1":MAC.usrp2_node(1),"address2":MAC.usrp2_node(2),"N_SEQ":N_SEQ, "N_FRAG":N_FRAG, "timestamp":time.time()}
            valores_DATA23={"payload":"Paquete_que_llega23", "address1":MAC.usrp2_node(3),"address2":MAC.usrp2_node(2),"N_SEQ":N_SEQ, "N_FRAG":N_FRAG, "timestamp":time.time()}
            valores_DATA24={"payload":"Paquete_que_llega24", "address1":MAC.usrp2_node(4),"address2":MAC.usrp2_node(2),"N_SEQ":N_SEQ, "N_FRAG":N_FRAG, "timestamp":time.time()}
            
            valores_DATA31={"payload":"Paquete_que_llega31", "address1":MAC.usrp2_node(1),"address2":MAC.usrp2_node(3),"N_SEQ":N_SEQ, "N_FRAG":N_FRAG, "timestamp":time.time()}
            valores_DATA32={"payload":"Paquete_que_llega32", "address1":MAC.usrp2_node(2),"address2":MAC.usrp2_node(3),"N_SEQ":N_SEQ, "N_FRAG":N_FRAG, "timestamp":time.time()}
            valores_DATA34={"payload":"Paquete_que_llega34", "address1":MAC.usrp2_node(4),"address2":MAC.usrp2_node(3),"N_SEQ":N_SEQ, "N_FRAG":N_FRAG, "timestamp":time.time()}
            
            valores_DATA41={"payload":"Paquete_que_llega41", "address1":MAC.usrp2_node(1),"address2":MAC.usrp2_node(4),"N_SEQ":N_SEQ, "N_FRAG":N_FRAG, "timestamp":time.time()}
            valores_DATA42={"payload":"Paquete_que_llega42", "address1":MAC.usrp2_node(2),"address2":MAC.usrp2_node(4),"N_SEQ":N_SEQ, "N_FRAG":N_FRAG, "timestamp":time.time()}
            valores_DATA43={"payload":"Paquete_que_llega43", "address1":MAC.usrp2_node(3),"address2":MAC.usrp2_node(4),"N_SEQ":N_SEQ, "N_FRAG":N_FRAG, "timestamp":time.time()}
            
            valores_RTS12 = {"duration":0, "mac_ra":MAC.usrp2_node(2), "mac_ta":MAC.usrp2_node(1),"timestamp":time.time()}
            valores_RTS13 = {"duration":0, "mac_ra":MAC.usrp2_node(3), "mac_ta":MAC.usrp2_node(1),"timestamp":time.time()}
            valores_RTS14 = {"duration":0, "mac_ra":MAC.usrp2_node(4), "mac_ta":MAC.usrp2_node(1),"timestamp":time.time()}
            
            valores_RTS21 = {"duration":0, "mac_ra":MAC.usrp2_node(1), "mac_ta":MAC.usrp2_node(2),"timestamp":time.time()}
            valores_RTS23 = {"duration":0, "mac_ra":MAC.usrp2_node(3), "mac_ta":MAC.usrp2_node(2),"timestamp":time.time()}
            valores_RTS24 = {"duration":0, "mac_ra":MAC.usrp2_node(4), "mac_ta":MAC.usrp2_node(2),"timestamp":time.time()}
            
            valores_RTS31 = {"duration":0, "mac_ra":MAC.usrp2_node(1), "mac_ta":MAC.usrp2_node(3),"timestamp":time.time()}
            valores_RTS32 = {"duration":0, "mac_ra":MAC.usrp2_node(2), "mac_ta":MAC.usrp2_node(3),"timestamp":time.time()}
            valores_RTS34 = {"duration":0, "mac_ra":MAC.usrp2_node(4), "mac_ta":MAC.usrp2_node(3),"timestamp":time.time()}
            
            valores_RTS41 = {"duration":0, "mac_ra":MAC.usrp2_node(1), "mac_ta":MAC.usrp2_node(4),"timestamp":time.time()}
            valores_RTS42 = {"duration":0, "mac_ra":MAC.usrp2_node(2), "mac_ta":MAC.usrp2_node(4),"timestamp":time.time()}
            valores_RTS43 = {"duration":0, "mac_ra":MAC.usrp2_node(3), "mac_ta":MAC.usrp2_node(4),"timestamp":time.time()}
                    
            # Packet generation with the selected values
            # FIX ME! By default, coderate = "1", which means 6 Mbps
            paquete1=MAC.ftw_make("DATA",valores_DATA12,"1",4)      # valores_DATA12 means node 1 sends a Data packet to node 2
            paquete2=MAC.ftw_make("DATA",valores_DATA13,"1",4)
            paquete3=MAC.ftw_make("DATA",valores_DATA14,"1",4)
            paquete4=MAC.ftw_make("DATA",valores_DATA21,"1",4)
            paquete5=MAC.ftw_make("DATA",valores_DATA23,"1",4)
            paquete6=MAC.ftw_make("DATA",valores_DATA24,"1",4)
            paquete7=MAC.ftw_make("DATA",valores_DATA31,"1",4)
            paquete8=MAC.ftw_make("DATA",valores_DATA32,"1",4)
            paquete9=MAC.ftw_make("DATA",valores_DATA34,"1",4)
            paquete10=MAC.ftw_make("DATA",valores_DATA41,"1",4)
            paquete11=MAC.ftw_make("DATA",valores_DATA42,"1",4)
            paquete12=MAC.ftw_make("DATA",valores_DATA43,"1",4)
    
            paquete13=MAC.ftw_make("RTS",valores_RTS12,"1",4)       # valores_RTS12 means node 1 sends a RTS packet to node 2
            paquete14=MAC.ftw_make("RTS",valores_RTS13,"1",4)
            paquete15=MAC.ftw_make("RTS",valores_RTS14,"1",4)
            paquete16=MAC.ftw_make("RTS",valores_RTS21,"1",4)
            paquete16=MAC.ftw_make("RTS",valores_RTS23,"1",4)
            paquete17=MAC.ftw_make("RTS",valores_RTS24,"1",4)
            paquete18=MAC.ftw_make("RTS",valores_RTS31,"1",4)
            paquete19=MAC.ftw_make("RTS",valores_RTS32,"1",4)
            paquete20=MAC.ftw_make("RTS",valores_RTS34,"1",4)
            paquete21=MAC.ftw_make("RTS",valores_RTS41,"1",4)
            paquete22=MAC.ftw_make("RTS",valores_RTS42,"1",4)
            paquete23=MAC.ftw_make("RTS",valores_RTS43,"1",4)        
            
            paquete24=MAC.ftw_make("CTS",valores_CTS1,"1",4)        # valores_CTS1 means Receiver Addres = Node 1 MAC 
            paquete25=MAC.ftw_make("CTS",valores_CTS2,"1",4)
            paquete26=MAC.ftw_make("CTS",valores_CTS3,"1",4)
            paquete27=MAC.ftw_make("CTS",valores_CTS4,"1",4)
            
            paquete28=MAC.ftw_make("ACK",valores_ACK1,"1",4)        # valores_ACK1 means Receiver Addres = Node 1 MAC
            paquete29=MAC.ftw_make("ACK",valores_ACK2,"1",4)
            paquete30=MAC.ftw_make("ACK",valores_ACK3,"1",4)
            paquete31=MAC.ftw_make("ACK",valores_ACK4,"1",4)
            
            paquete32=MAC.ftw_make("BEACON",valores_B1,"1",4)       # valores_B1 means a BEACON generated by node 1
            paquete33=MAC.ftw_make("BEACON",valores_B2,"1",4)
            paquete34=MAC.ftw_make("BEACON",valores_B3,"1",4)
            paquete35=MAC.ftw_make("BEACON",valores_B4,"1",4)
            
            random.seed(time.time())
            
            # modify 'numero' in order to force the arrival of a selected packet to the PHY RX layer
            numero = random.randint(0,33)
            
            #DEBUG: used to test the correct RTS/CTS functionality   (MAC RX-side)
            #if n_packets == 1: numero = 12  
            #if n_packets == 2: numero = 24  
            #if n_packets == 3: numero = 0   
            #if n_packets == 4: numero = 28 
            
            #DEBUG: used to test the correct RTS/CTS functionality (MAC TX-side)
            #if n_packets == 1: numero = 15  
            #if n_packets == 2: numero = 23  
            #if n_packets == 3: numero = 3   
            #if n_packets == 4: numero = 27        
            
            # Select which type of frame is going to be generated 
            if numero == 0:
                pkt = crear_paquete("DATA",paquete1)
            elif numero == 1:
                pkt = crear_paquete("DATA",paquete2)
            elif numero == 2:
                pkt = crear_paquete("DATA",paquete3)
            elif numero == 3:
                pkt = crear_paquete("DATA",paquete4)
            elif numero == 4:
                pkt = crear_paquete("DATA",paquete5)
            elif numero == 5:
                pkt = crear_paquete("DATA",paquete6)
            elif numero == 6:
                pkt = crear_paquete("DATA",paquete7)
            elif numero == 7:
                pkt = crear_paquete("DATA",paquete8)
            elif numero == 8:
                pkt = crear_paquete("DATA",paquete9)
            elif numero == 9:
                pkt = crear_paquete("DATA",paquete10)
            elif numero == 10:
                pkt = crear_paquete("DATA",paquete11)
            elif numero == 11:
                pkt = crear_paquete("DATA",paquete12)
            elif numero == 12:
                pkt = crear_paquete("RTS",paquete13) 
            elif numero == 13:
                pkt = crear_paquete("RTS",paquete14) 
            elif numero == 14:
                pkt = crear_paquete("RTS",paquete15)
            elif numero == 15:
                pkt = crear_paquete("RTS",paquete16)
            elif numero == 16:
                pkt = crear_paquete("RTS",paquete17)
            elif numero == 17:
                pkt = crear_paquete("RTS",paquete18)
            elif numero == 18:
                pkt = crear_paquete("RTS",paquete19)
            elif numero == 19:
                pkt = crear_paquete("RTS",paquete20)
            elif numero == 20:
                pkt = crear_paquete("RTS",paquete21)
            elif numero == 21:
                pkt = crear_paquete("RTS",paquete22)
            elif numero == 22:
                pkt = crear_paquete("RTS",paquete23)
            elif numero == 23:
                pkt = crear_paquete("CTS",paquete24)
            elif numero == 24:
                pkt = crear_paquete("CTS",paquete25)
            elif numero == 25:
                pkt = crear_paquete("CTS",paquete26)
            elif numero == 26:
                pkt = crear_paquete("CTS",paquete27)
            elif numero == 27:
                pkt = crear_paquete("ACK",paquete28)
            elif numero == 28:
                pkt = crear_paquete("ACK",paquete29)
            elif numero == 29:
                pkt = crear_paquete("ACK",paquete30)
            elif numero == 30:
                pkt = crear_paquete("ACK",paquete31)
            elif numero == 31:
                if MAC.usrp2_node(options.node) == MAC.usrp2_node(1):
                    pkt = crear_paquete("OTHER",[])
                else:
                    pkt = crear_paquete("BEACON",paquete32)
            elif numero == 32:
                if MAC.usrp2_node(options.node) == MAC.usrp2_node(2):
                    pkt = crear_paquete("OTHER",[])
                else:
                    pkt = crear_paquete("BEACON",paquete33)
            elif numero == 33:
                if MAC.usrp2_node(options.node) == MAC.usrp2_node(3):
                    pkt = crear_paquete("OTHER",[])
                else:
                    pkt = crear_paquete("BEACON",paquete34)
            elif numero == 34:
                if MAC.usrp2_node(options.node) == MAC.usrp2_node(4):
                    pkt = crear_paquete("OTHER",[])
                else:
                    pkt = crear_paquete("BEACON",paquete35)
            elif numero >35:
                pkt = crear_paquete("OTHER",[])
                n_packets -= 1
            #n_packets += 1
            
            paquete = pickle.dumps(pkt,1)
            s.send(paquete)
            s.close()
            time.sleep(0.1)    # Packet arrival interval
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

        
        
