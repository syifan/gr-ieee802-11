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

# Filename: phy_frag_traffic.py

# This script generates an 802.11 fragmented Data packet and sends it to the PHY layer. 
# It was developed by the Uwicore Laboratory at the University Miguel Hernandez of 
# Elche in order to validate the Fragmentation and Re-assembly functionalities of the 
# 802.11 MAC implemented (Similar to phy_traffic.py). More detailed information can be found 
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
from optparse import OptionParser
from gnuradio.eng_option import eng_option
import uwicore_mac_utils as MAC 


# PHY DATA fragmented traffic generator main
if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, conflict_handler="resolve")
    parser.add_option("-n", "--node", type="intx", default=1, help="USRP2 node   [default=%default]")
    (options, args) = parser.parse_args ()
    
    def crear_paquete(tipo,data):           # Format packet for MAC<-->PHY communication
        packet={"TIPO":tipo,"DATOS":data}
        return packet
    numero = 1          # number of tests to perform
    test = True
    
    print '\n',"----------------------------------"
    print " PHY Fragmented traffic generator"
    print " (Ctrl + C) to exit"
    print "----------------------------------",'\n'
    
    while test== True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((socket.gethostname(), 8500))
        N_SEQ = random.randint(0,4095)  # Assign randomly a sequence number
        N_FRAG = 0                      # First fragment will always be 0
        
        # Values for Fragmented Data packets
        valores_DATA12={"payload":"HELLO_WO", "address1":MAC.usrp2_node(1),"address2":MAC.usrp2_node(2),"N_SEQ":500, "N_FRAG":0,"timestamp":time.time()}
        valores_DATA13={"payload":"RLD_FRAG", "address1":MAC.usrp2_node(1),"address2":MAC.usrp2_node(3),"N_SEQ":501, "N_FRAG":1,"timestamp":time.time()}
        valores_DATA14={"payload":"MENT_TX_", "address1":MAC.usrp2_node(1),"address2":MAC.usrp2_node(4),"N_SEQ":502, "N_FRAG":2,"timestamp":time.time()}
        valores_DATA4={"payload":"TEST!!", "address1":MAC.usrp2_node(1),"address2":MAC.usrp2_node(4),"N_SEQ":499, "N_FRAG":0,"timestamp":time.time()}
        
        # Generate the Fragmented Data packets with the selected values
        paquete1=MAC.ftw_make("DATA_FRAG",valores_DATA12,"1",4)
        paquete2=MAC.ftw_make("DATA_FRAG",valores_DATA13,"1",4)
        paquete3=MAC.ftw_make("DATA",valores_DATA14,"1",4)
        paquete4=MAC.ftw_make("DATA",valores_DATA4,"1",4)
        
        # Transmitting sequence
        if numero == 0:
            pkt = crear_paquete("DATA",paquete4)
            numero += 4
        elif numero == 1:
            pkt = crear_paquete("DATA_FRAG",paquete1)
            numero += 1
        elif numero == 2:
            pkt = crear_paquete("DATA_FRAG",paquete2)
            numero += 1
        elif numero == 3:
            pkt = crear_paquete("DATA",paquete3)
            numero += 1
            test = False
        paquete = pickle.dumps(pkt,1)       # Pickle the data before sending it through the socket
        s.send(paquete)
        s.close()
        time.sleep(0.05)                    # Time between packets 
        
        
