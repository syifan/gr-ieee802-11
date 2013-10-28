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

# Filename: ul_buffer.py

# This script emulates the Upper Layer (above MAC) functionality developed by the Uwicore Laboratory 
# at the University Miguel Hernandez of Elche. It consists of a pair of packet buffers, the first one 
# stores the packets received from the MAC and the second one stores the packets that are going
# to be sent to the wireless medium. More detailed information can be found at 
# www.uwicore.umh.es/mhop-testbeds.html or at the publication:

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


from threading import Thread
import time, struct, sys
import socket,pickle
from gnuradio.eng_option import eng_option
from optparse import OptionParser

import uwicore_mpif as plcp
from buffer_lib import Buffer as buffer

# Class 'Client' to handle multiple packet arrival (from PHY traffic generator or from MAC)
class Client(Thread):
    def __init__(self, socket_client, data_client, cs, cs2):
        Thread.__init__(self)
        self.socket = socket_client
        self.data = data_client
        self.cs = cs
        self.cs2 = cs2

    def run(self):        
        pkt = self.socket.recv(1000)
        arrived_packet = pickle.loads(pkt)
        '''
        MAC layer checks whether there is a packet to transmit
        '''
        if ("no_packet"==arrived_packet["HEADER"]):    # check whether the queue is empty
            if self.cs.isEmpty()==True:             
                x = plcp.create_packet("NO","")
                plcp.send_to_mac(self.socket,x)
            else:      
                self.cs.elements.reverse()
                if self.cs.read(0) == "[beacon packet]": 
                    x = plcp.create_packet("BEACON","")
                else:
                    x = plcp.create_packet("YES",self.cs.read(0))
                self.cs.elements.reverse()
                plcp.send_to_mac(self.socket,x)
            
        
        if ("remove"==arrived_packet["HEADER"]):   # Remove a packet from the buffer
                self.cs.elements.reverse()
                self.cs.pop()
                self.cs.elements.reverse()
        if ("copy"==arrived_packet["HEADER"]):     # A packet arrives from MAC layer
                self.cs2.push(arrived_packet["DATA"]) 
        '''
        Upper layer has a packet to send and stores it in the buffer
        '''        
        if (arrived_packet["HEADER"]=="PAYLOAD"):        # Payload received from Upper Layer Traffic generator
            self.cs.push(arrived_packet["DATA"])                       
            self.socket.close()
        elif (arrived_packet["HEADER"]=="BEACON"):       # Beacon request arrival
            self.cs.push(arrived_packet["DATA"])                       
            self.socket.close()
            
        # Show the buffer state
        print "========== PACKETS TO TRANSMIT ============"
        print self.cs.elements
        print "==========================================="
        print "\n\n"
        print "======== RECEIVED PACKETS FROM MAC ========"
        print self.cs2.elements
        print "==========================================="
            

def main():
        
    parser = OptionParser(option_class=eng_option, conflict_handler="resolve")

    parser.add_option("", "--MACport", type="int", default=8001 , help="Socket port [default=%default] ")
    
    (options, args) = parser.parse_args ()
    
    print '\n',"--------------------------"
    print " Upper layer running ..."
    print "  (Ctrl + C) to exit"
    print "--------------------------",'\n'
        
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((socket.gethostname(), options.MACport))
    server.listen(1)
    
    cs = buffer()
    cs2 = buffer()
        
    while 1:
        socket_client, data_client = server.accept()
        threadd = Client(socket_client, data_client,cs,cs2)
        threadd.start()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

