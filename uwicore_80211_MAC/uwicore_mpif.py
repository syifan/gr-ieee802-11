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

# Filename: uwicore_mpif.py

# This script, developed by the Uwicore Laboratory at the University Miguel Hernandez of Elche,
# provides a set of methods used to ease the communication between layers. More detailed information
# can be found at www.uwicore.umh.es/mhop-testbeds.html or at the publication:

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
import time,sys 

# Defines the packet format used for crosslayer communication
#def crear_paquete(tipo,data):
#    packet={"TIPO":tipo,"DATOS":data}
#    return packet
#
## Method to send a packet through a socket
#def enviar_a_mac(sd,pkt):
#    paquete = pickle.dumps(pkt,1)
#    sd.send(paquete)
#
## Method to receive a packet through a socket    
#def recibir_de_mac(sd):
#    pkt = sd.recv(10000)
#    info=pickle.loads(pkt)
#    return info
#
## Method to create a beacon dictionary with the values that will be used on the Neighbor Beaconing process 
#def nuevo_beacon():
#    beacon = {"MAC":"","timestamp":0,"BI":0, "OFFSET":0}    
#    return beacon

def create_packet(header,data):
    packet={"HEADER":header,"DATA":data}
    return packet

# Method to send a packet through a socket
def send_to_mac(sd,pkt):
    packet = pickle.dumps(pkt,1)
    sd.send(packet)

# Method to receive a packet through a socket    
def receive_from_mac(sd):
    pkt = sd.recv(10000)
    info=pickle.loads(pkt)
    return info

# Method to create a beacon dictionary with the values that will be used on the Neighbor Beaconing process 
def new_beacon():
    beacon = {"MAC":"","timestamp":0,"BI":0, "OFFSET":0}    
    return beacon

