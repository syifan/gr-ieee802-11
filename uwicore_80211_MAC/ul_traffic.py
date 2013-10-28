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

# Filename: ul_traffic.py

# This script, developed by the Uwicore Laboratory at the University Miguel Hernandez of Elche, 
# simulates the arrival of different packets to transmit from the upper layers. The payload is 
# a plain ASCII string, but in future versions might be a packet from OSI upper layers, such as
# IP, TCP or UDP. More detailed information can be found at www.uwicore.umh.es/mhop-testbeds.html 
# or at the publication:

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


if __name__ == '__main__':
    
    def create_packet(header,data):
        packet={"HEADER":header,"DATA":data}
        return packet
    
    pkt_time_arrival = 5 # Time interval between packet generation in seconds (can be modified)
    packet_N = 10        # Modify the number of packets to send
    
    print '\n',"-------------------------------"
    print " Upper Layer traffic generator"
    print " (Ctrl + C) to exit"
    print "-------------------------------",'\n'
    
    while packet_N > 0:
        '''
        Pseudo-random packets generated that are sent to the Upper layer buffer
        every 'pkt_time_arrival' interval (in seconds).
        '''
        packet_N-=1
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((socket.gethostname(), 8001))
        
        num = random.randint(0,3)
        if num == 0:
            pkt = create_packet("PAYLOAD","PAQUETE_CAPA_SUPERIOR_1")
        elif num == 1:
            pkt = create_packet("PAYLOAD","PAQUETE_CAPA_SUPERIOR_2")
        elif num == 2:
            pkt = create_packet("PAYLOAD","PAQUETE_CAPA_SUPERIOR_3")
        elif num == 3:
            pkt = create_packet("PAYLOAD","PAQUETE_CAPA_SUPERIOR_4")
        
        packet = pickle.dumps(pkt,1)
        s.send(packet)
        s.close()
        time.sleep(pkt_time_arrival)
