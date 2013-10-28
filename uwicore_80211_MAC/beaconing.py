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

# Filename: beaconing.py

# This script executes the Beacon packet transmission procedure developed by the Uwicore 
# Laboratory at the University Miguel Hernandez of Elche. More detailed information can 
# be found at www.uwicore.umh.es/mhop-testbeds.html or at the publication:

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
from optparse import OptionParser
from gnuradio.eng_option import eng_option

# Beacon packet generator main
if __name__ == '__main__':
    
    parser = OptionParser(option_class=eng_option, conflict_handler="resolve")
    parser.add_option("-B", "--BI", type="float", default=10, 
                      help="802.11 Beacon Interval (seconds), [default=%default]")
    (options, args) = parser.parse_args ()
    def create_packet(header,data):
        packet={"HEADER":header,"DATA":data}
        return packet
    
    print '\n',"-------------------------"
    print " Beaconing Functionality "
    print " (Ctrl + C) to exit"
    print "-------------------------",'\n'
    
    while 1:
        '''
        Generate and send a Beacon frame to the MAC layer
        every Beacon Interval through a TCP socket
        '''
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((socket.gethostname(), 8001))
        pkt = create_packet("BEACON","[beacon packet]") #FIXME Update the Beacon header with the correct BI value
        packet = pickle.dumps(pkt,1)
        s.send(packet)
        s.close()
        time.sleep(options.BI)
