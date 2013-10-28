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

# Filename: uwicore_phy_rx.py

# This script, developed by the Uwicore Laboratory at the University Miguel Hernandez of Elche, 
# emulates the behavior of an OFDM receiver through a queue implemented at the PHY layer. The 
# received packets in the queue are passed to the MAC layer through the MAC to PHY Interface. 
# This script also keeps a record of the beacon packets. More detailed information can be found
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


from threading import Thread
import time, struct, sys, os
import socket,pickle
from gnuradio.eng_option import eng_option
from optparse import OptionParser

import uwicore_mpif as plcp
import uwicore_mac_utils as mac
from buffer_lib import Pila as cola   

# Class 'Cliente' handles multiple packet arrival (from PHY traffic generator or from MAC)
class Cliente(Thread):
    def __init__(self, socket_cliente, datos_cliente, data, ack, rts, cts,bcn,my_mac):
        Thread.__init__(self)
        self.socket = socket_cliente
        self.datos = datos_cliente
        self.data = data
        self.ack = ack
        self.rts = rts
        self.cts = cts
        self.bcn = bcn
        self.my_mac = my_mac

    def run(self):        
        pkt = self.socket.recv(1000)
        paquete_llegada = pickle.loads(pkt)
        
        # MAC requests an incoming packet to the PHY
        if (paquete_llegada["TIPO"]=="COLA"): 
            tipo_pkt = paquete_llegada["DATOS"]
            
            len_data = self.data.longitud()
            len_ack = self.ack.longitud()
            len_rts = self.rts.longitud()
            len_cts = self.cts.longitud()
            
            if (tipo_pkt == "DATA") and len_data>0: # There are Data packets?
                self.data.elementos.reverse()
                x=self.data.read(0)
                phy_pkt = plcp.crear_paquete("SI",x)
                self.data.pop()
                self.data.elementos.reverse()
                           
            elif tipo_pkt == "ACK" and len_ack>0:   # There are ACK packets?
                self.ack.elementos.reverse()
                x=self.ack.read(0)
                phy_pkt = plcp.crear_paquete("SI",x)
                self.ack.pop()
                self.ack.elementos.reverse()
                       
            elif tipo_pkt == "RTS" and len_rts>0:   # There are RTS packets?
                self.rts.elementos.reverse()
                x=self.rts.read(0)
                phy_pkt = plcp.crear_paquete("SI",x)
                self.rts.pop()
                self.rts.elementos.reverse()           
            elif tipo_pkt == "CTS" and len_cts>0:   # There are CTS packets?
                self.cts.elementos.reverse()
                x=self.cts.read(0)
                phy_pkt = plcp.crear_paquete("SI",x)
                self.cts.pop()
                self.cts.elementos.reverse()
            else:                                   # There are not packets
                phy_pkt = plcp.crear_paquete("NO",[])
            plcp.enviar_a_mac(self.socket,phy_pkt)  # Send the result (PHY packet) to MAC layer
            self.socket.close()

        # PHY packet generator script. It sends an 802.11 frame simulating its arrival from the wireless medium
        if (paquete_llegada["TIPO"]=="DATA" or paquete_llegada["TIPO"]=="DATA_FRAG"):
            if paquete_llegada["DATOS"]["INFO"]["mac_add1"] == self.my_mac:  # Is the data packet addressed to this node? 
                self.data.push(paquete_llegada["DATOS"])                       
            self.socket.close()
        if (paquete_llegada["TIPO"]=="ACK"):
            if paquete_llegada["DATOS"]["INFO"]["RX_add"] == self.my_mac:# Is the ACK addressed to this node?
                self.ack.push(paquete_llegada["DATOS"])
            self.socket.close()
        if (paquete_llegada["TIPO"]=="RTS"):            #It is a RTS
            self.rts.push(paquete_llegada["DATOS"])                       
            self.socket.close()
        if (paquete_llegada["TIPO"]=="CTS"):            #It is a CTS
            self.cts.push(paquete_llegada["DATOS"])                       
            self.socket.close()
        if (paquete_llegada["TIPO"]=="BEACON"):         #It is a BEACON
            beacon = paquete_llegada["DATOS"]
            beacon = beacon["INFO"]
            msg = plcp.nuevo_beacon()
            msg["MAC"]= beacon["mac_add2"]
            msg["timestamp"]=beacon["timestamp"]
            msg["BI"]=beacon["BI"]
            msg["OFFSET"]=time.time() - beacon["timestamp"] 
            x = self.bcn.longitud()
            actualizado = False
            
            # Update the beacon list
            for i in range(0,x):
                if msg["MAC"]==self.bcn.read(i)["MAC"]:
                    self.bcn.quitar(i)
                    self.bcn.insert(i,msg)
                    actualizado = True
            if actualizado == False:
                self.bcn.insert(x+1,msg)
                    
        if (paquete_llegada["TIPO"]=="OTHER"):               
            #print "No  packet arrived"
            self.socket.close()
        
        #DEBUG
        print "=========== BUFFER STATUS ==========="
        print "DATA [%i]"%self.data.longitud()
        print "ACK  [%i]"%self.ack.longitud()
        print "RTS  [%i]"%self.rts.longitud()
        print "CTS  [%i]"%self.cts.longitud()
        print "====================================="
        print "\n\n"
        
        # Beacon list
        print "========= NEIGHBOR NODES INFORMATION =========="
        for i in range (0,self.bcn.longitud()):
            leido = self.bcn.read(i)
            print "[MAC = %s]\t [Timestamp = %s]\t [Beacon Interval = %s]\t [OFFSET = %s]" %(mac.which_dir(leido["MAC"]),leido["timestamp"],leido["BI"],leido["OFFSET"])
        print "==============================================="
            
# /////////////////////////////////////////////////////////////////////////////
#                                   main
# /////////////////////////////////////////////////////////////////////////////

def main():
        
    parser = OptionParser(option_class=eng_option, conflict_handler="resolve")

    parser.add_option("", "--PHYport", type="int", default=8500 , help="Socket port [default=%default] ")
    parser.add_option("-n", "--node", type="intx", default=1, help="USRP2 node    [default=%default]")
    (options, args) = parser.parse_args ()
    
    print '\n',"----------------------------"
    print " PHY (RX) layer running ..."
    print "  (Ctrl + C) to exit"
    print "----------------------------",'\n'
        
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((socket.gethostname(), options.PHYport))
    server.listen(1)
    
    # Launch all the buggers
    data = cola()
    ack = cola()
    rts = cola()
    cts = cola()
    bcn = cola()
    my_mac = mac.usrp2_node(options.node)   # Assign the MAC address of the node

        
    while 1:
        socket_cliente, datos_cliente = server.accept()
        hilo = Cliente(socket_cliente, datos_cliente,data,ack,rts,cts,bcn,my_mac)
        hilo.start()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

