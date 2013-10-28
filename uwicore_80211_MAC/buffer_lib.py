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

# Filename: buffer_lib.py

# This Python file, developed by the Uwicore Laboratory at the University Miguel Hernandez
# of Elche, includes the class used by other scripts to implement buffer. 
# More detailed information can be found at www.uwicore.umh.es/mhop-testbeds.html or 
# at the publication:

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


import time
import uwicore_mac_utils as uwicore_utils
import socket, pickle, time
from gnuradio.eng_option import eng_option
from optparse import OptionParser
#class Pila:
class Buffer:
    '''
    This class implements a buffer
    '''
    def __init__(self) :
        self.elements = []
    def push(self, element) :                      #insert an element (1st position)
        self.elements.insert(0, element)
    def insert(self, position,element) :           #insert an element (any position)
        self.elements.insert(position, element)
#    def quitar(self,position):                      #remove an element (any position)
    def remove(self,position):
        self.elements.pop(position)    
    def pop(self) :                                 #remove an element (1st position)
        self.elements.reverse()
        self.elements.pop()
        self.elements.reverse()
    def isEmpty(self) :                         
        if self.length() == 0: return True
        else: return False 
    def read(self,n):                               #read the elements of the buffer
        return self.elements[n]
#    def longitud(self):                             #buffer length    
    def length(self):
        return self.elements.__len__()
    def add_tail(self,start,end):                   #OLD method
        if end.length:
            len=end.length()
            for i in range (0,len):
                len2=start.length()
                start.elements.reverse()
                start.elements.insert(len2,end.elements[i])
                start.elements.reverse()
        return start
    
#    def vaciar(self,tail):                          #remove all the elements of the queue
    def empty(self,tail):
        tail.elements = []
        return tail 
#    def actualizar(self,longitud):                  # OLD method (Updates the buffer)
    def update(self,length):
        data = Buffer()
        ack = Buffer()
        rts = Buffer()
        cts = Buffer()
        for i in range (0,length):
            item = self.read(i)
            if item["HEADER"] == "DATA":
                data.push(self.elements[i])
            elif item["HEADER"] == "ACK":
                ack.push(self.elements[i])
            elif item["HEADER"] == "RTS":
                rts.push(self.elements[i])
            elif item["HEADER"] == "CTS":
                cts.push(self.elements[i])
        for i in range (0,length):
            self.pop()  
        if data.length() == 0 and ack.length() == 0 and rts.length() == 0 and cts.length() == 0: 
            return False
        return True, data, ack, rts, cts
#    def buscar(self,tipo,length):                 # OLD method (Looks for a kind of element)
    def search(self,header,length):
        found = []
        for i in range (0,length):
            item = self.read(i)
            if item["HEADER"] == header:
                #print "%s found!" %tipo
                found.insert(0,self.elements[i])
        if found.__len__() == 0: 
            #print "No %s in the buffer" %tipo
            return False, found
        return True, found

def create_packet(header,data):                       #create a packet for cross-layer messaging 
    packet={"HEADER":header,"DATA":data}
    return packet

def send_to_mac(datos,sd):                         #send data to MAC layer 
    pkt = pickle.dumps(datos,1)
    sd.send(pkt)    
    
def receive_from_mac(sd):                             #receive data from MAC
    pkt = sd.recv(1000)
    info=pickle.loads(pkt)
    return info
