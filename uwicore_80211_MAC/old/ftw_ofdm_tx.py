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



# Filename: ftw_ofdm_tx.py



# This is the script of the PHY layer. The original PHY code was developed by FTW (Forschungszentrum 
# Telekommunikation Wien / Telecommunications Research Center Vienna, http://www.ftw.at). The code 
# was first presented and described in the following publication:



# P.Fuxjaeger, A. Costantini, D. Valerio, P. Castiglione, G. Zacheo, T. Zemen and F. Ricciato, "IEEE 802.11p Transmission Using GNURadio" , in Proceedings of the IEEE Karlsruhe Workshop on Software Radios (WSR10), pp. 1-4, 2010.


# The Uwicore Laboratory at the University Miguel Hernandez of Elche has added additional 
# functionalities to the FTW PHY code, in particular: Carrier Sensing functions, and 
# reconfigurability of the transmission GNU radio graph to allow for the possibility to 
# transmit different MAC frames (also of varying size). In addition, the Uwicore PHY 
# contribution communicates with the MAC layer, and is capable to process requests from 
# the MAC to sense or to transmit a packet to the wireless medium. 



# The FTW OFMD code triggers the encoding procedures and sends the complex baseband 
# signal to the USRP2 sink. The Uwicore carrier sensing function, based on the example 
# 'USRP_spectrum_sense' provided by GNU Radio, estimates the power of the signal using
# the signal's Power Spectrum Density (PSD).


# Ubiquitous Wireless Communications Research Laboratory 
# Uwicore, http://www.uwicore.umh.es
# Communications Engineering Department
# University Miguel Hernandez of Elche
# Avda de la Universidad, s/n
# 03202 Elche, Spain


# Release: April 2011


# Original FTW PHY code authors:

#    Andrea Costantini 

#    Paul Fuxjaeger (fuxjaeger@ftw.at)

#    Danilo Valerio (valerio@ftw.at)

#    Paolo Castiglione (castiglione@ftw.at)

#    Giammarco Zacheo (zacheo@ftw.at)



# Authors of the PHY added functionalities:

#    Juan R. Gutierrez-Agullo (jgutierrez@umh.es)

#    Baldomero Coll-Perales (bcoll@umh.es)

#    Dr. Javier Gozalvez (j.gozalvez@umh.es)





import time, struct, sys

import socket,pickle, math

from gnuradio import gr, blks2, uhd, eng_notation, optfir, window, filter, fft

from grc_gnuradio import blks2 as grc_blks2

from gnuradio.eng_option import eng_option

from gnuradio.gr import firdes

from optparse import OptionParser

from ftw_ofdm import ftw_transmit_path

import uwicore_mpif as plcp

from buffer_lib import Pila as cola

import gnuradio.ieee802_11 as gr_ieee802_11

import random



# PHY 802.11a/g/p transmitter block

class transmitter_block(gr.top_block):

    def __init__(self, options):

        gr.top_block.__init__(self)
        #self._interface          = options.interface       # Logical network interface
        #self._mac_addr           = options.mac_addr        # USRP2 MAC address
        self._tx_freq            = options.freq            # Center frequency
        #self._interp             = options.interp          # Interpolation factor
        self._gain               = options.txgain          # Tx gain
        self._bw                 = options.bandwidth          # interpolation factor
        self.args                = options.args
        self._ant                = options.antenna
        self._spec               = options.spec

        # setup sink and connect output of transmit path to it 

        self.u = uhd.usrp_sink(device_addr=self.args, stream_args=uhd.stream_args('fc32'))
        if(self._spec):
            self.u.set_subdev_spec(self._spec, 0)

        # Set the antenna
        if(self._ant):
            self.u.set_antenna(self._ant, 0)
        self.u.set_gain(self._gain)
        self.set_freq(self._tx_freq)
        self.rate = self.u.set_samp_rate(self._bw)

        self.txpath = ftw_transmit_path(options)

        self.connect(self.txpath, self.u)

        # write final baseband signal to disk

        if options.log:	

            self.connect(self.txpath, gr.file_sink(gr.sizeof_gr_complex, "final.dat"))


    def set_freq(self, target_freq):

        """

        Set the center frequency we're interested in.



        @param target_freq: frequency in Hz

        @rtype: bool



        Tuning is a two step process.  First we ask the front-end to

        tune as close to the desired frequency as it can.  Then we use

        the result of that operation and our target_frequency to

        determine the value for the digital up converter.

        """

        tr = self.u.set_center_freq(target_freq)

        if tr == None:

        	sys.stderr.write('Failed to set center frequency\n')

        	raise SystemExit, 1

    def set_sample_rate(self, bandwidth):
        self.u.set_samp_rate(bandwidth)
        actual_bw = self.u.get_samp_rate()
        
        return actual_bw



# PHY Carrier Sensing class

class tune(gr.feval_dd):

    """

    This class allows C++ code to callback into python.

    """

    def __init__(self, tb):

        gr.feval_dd.__init__(self)

        self.tb = tb



    def eval(self, ignore):

        """

        This method is called from gr.bin_statistics_f when it wants to change

        the center frequency.  This method tunes the front end to the new center

        frequency, and returns the new frequency as its result. This method has been

        modified in order to perform only one measurement. 

        """

        try:
            new_freq = self.tb.set_next_freq()
            return new_freq

        except Exception, e:

            print "tune: Exception: ", e



# PHY Carrier Sensing class

class parse_msg(object):

    def __init__(self, msg):

        self.center_freq = msg.arg1()

        self.vlen = int(msg.arg2())

        assert(msg.length() == self.vlen * gr.sizeof_float)

        # FIXME consider using Numarray or NumPy vector
        t = msg.to_string()

        self.raw_data = t

        self.data = struct.unpack('%df' % (self.vlen,), t)



# PHY Carrier Sensing block

class sense_block(gr.top_block):



    def __init__(self,options):

        gr.top_block.__init__(self)

        self.min_freq = options.freq 

        self.max_freq = options.freq    #Only one power's measurement at one frequency

        if self.min_freq > self.max_freq:

            self.min_freq, self.max_freq = self.max_freq, self.min_freq   # Swap them

        self.fft_size = options.fft_size

        if not options.real_time:

            realtime = False

        else:

            # Attempt to enable realtime scheduling

            r = gr.enable_realtime_scheduling()

            if r == gr.RT_OK:

                realtime = True

            else:

                realtime = False

            print "Note: failed to enable realtime scheduling"

        # Build carrier sensing graph

        #self.u = usrp2.source_32fc()
        self.u = uhd.usrp_source(device_addr=options.args, stream_args=uhd.stream_args('fc32'))
        #adc_rate = self.u.adc_rate()
        usrp_decim = options.decim
        #self.u.set_decim(usrp2_decim)
        usrp_rate = 1e8 / usrp_decim
        self.u.set_samp_rate(usrp_rate)



        s2v = gr.stream_to_vector(gr.sizeof_gr_complex, self.fft_size)

        # Blackman-Harris was the default window type of the original application 'USRP Spectrum Sense'
        mywindow = window.blackmanharris(self.fft_size)  
        fft = gr.fft_vcc(self.fft_size, True, mywindow)
        power = 0
        for tap in mywindow:
            power += tap*tap

        c2mag = gr.complex_to_mag_squared(self.fft_size)

        # FIXME the log10 primitive is slow
        log = gr.nlog10_ff(10, self.fft_size,
                           -20*math.log10(self.fft_size)-10*math.log10(power/self.fft_size))

        # Set the freq_step to 75% of the actual data throughput.
        # This allows us to discard the bins on both ends of the spectrum.

        self.freq_step = 0.75 * usrp_rate
        self.min_center_freq = self.min_freq + self.freq_step/2
        nsteps = math.ceil((self.max_freq - self.min_freq) / self.freq_step)
        self.max_center_freq = self.min_center_freq + (nsteps * self.freq_step)

        self.next_freq = self.min_center_freq

        tune_delay  = max(0, int(round(options.tune_delay * usrp_rate / self.fft_size)))  # in fft_frames
        dwell_delay = max(1, int(round(options.dwell_delay * usrp_rate / self.fft_size))) # in fft_frames

        self.msgq = gr.msg_queue(16)
        self._tune_callback = tune(self)        
        stats = gr.bin_statistics_f(self.fft_size, self.msgq,
                                    self._tune_callback, tune_delay, dwell_delay)

        self.connect(self.u, s2v, fft, c2mag, stats)

        if options.gain is None:
            # if no gain was specified, use the USRP2 mid-point in dB
            g = self.u.gain_range()
            options.gain = max(min(options.gain, g[1]), g[0] )

        self.u.set_gain(options.gain)


    def set_next_freq(self):
        
        target_freq = self.next_freq

        self.next_freq = self.next_freq + self.freq_step
        if self.next_freq >= self.max_center_freq:
            self.next_freq = self.min_center_freq

        if not self.set_freq(target_freq):
            print "Failed to set frequency to", target_freq

        return target_freq


    def set_freq(self, target_freq):

        """

        Set the center frequency we're interested in.



        @param target_freq: frequency in Hz

        @rypte: bool



        Tuning is a two step process.  First we ask the front-end to

        tune as close to the desired frequency as it can.  Then we use

        the result of that operation and our target_frequency to

        determine the value for the digital down converter.

        """
        return self.u.set_center_freq(target_freq)


    def set_gain(self, gain):
        self.u.set_gain(gain)





def main_loop(tb):

    # This is the main loop of carrier sensing block. It measures the power

    # detected on a desired frequency, using the magnitude squared of the fft

    # Get the next message sent from the C++ code (blocking call).
    m = parse_msg(tb.msgq.delete_head())
    maximo = 0
    for i in range (0,m.vlen):
        maximo = maximo + m.data[i]
    potencia = maximo/tb.fft_size # Power estimation (W) using the Power Spectral Density

    return potencia


# /////////////////////////////////////////////////////////////////////////////

#                                   main

# /////////////////////////////////////////////////////////////////////////////



def main():

    def send_pkt(puerto, eof=False):
        return tb.txpath.send_pkt(puerto, eof)

    parser = OptionParser(option_class=eng_option, conflict_handler="resolve")
    parser.add_option("-a", "--args", type="string", default="",
                          help="UHD device address args [default=%default]")
    parser.add_option("", "--spec", type="string", default=None,
                          help="Subdevice of UHD device where appropriate")
    parser.add_option("-A", "--antenna", type="string", default=None,
                          help="select Rx Antenna where appropriate")

    parser.add_option("-f", "--freq", type="eng_float",
                          default = 2.412e9, help="set USRP2 carrier frequency, [default=%default]",
                          metavar="FREQ")

    parser.add_option("-W", "--bandwidth", type="eng_float",
                          default=10000000,
                          help="set symbol bandwidth [default=%default]\
                20 MHz  -> 802.11a/g, OFDM-symbolduration=4us, \
                10 MHz -> 802.11p, OFDM-symbolduration=8us")

    parser.add_option("", "--regime", type="string", default="1",
                          help="set OFDM coderegime,    [default=%default]\
                        1 -> 6 (3) Mbit/s (BPSK r=0.5), \
                        2 -> 9 (4.5) Mbit/s (BPSK r=0.75), \
                        3 -> 12 (6) Mbit/s (QPSK r=0.5), \
                        4 -> 18 (9) Mbit/s (QPSK r=0.75), \
                          5 -> 24 (12) Mbit/s (QAM16 r=0.5), \
                        6 -> 36 (18) Mbit/s (QAM16 r=0.75), \
                        7 -> 48 (24) Mbit/s (QAM64 r=0.66), \
                        8 -> 54 (27) Mbit/s (QAM64 r=0.75)")

    parser.add_option("-G", "--txgain", type="int", default=10 , help = "set USRP2 Tx GAIN in [dB] [default=%default]")

    parser.add_option("-g", "--gain", type="int", default=30 , help = "set USRP2 Rx GAIN in [dB] [default=%default]")

    parser.add_option("-n", "--norm", type="eng_float", default=0.3 , help="set gain factor for complex baseband floats [default=%default]")

    parser.add_option("-r", "--repetition", type="int", default=1 , help="set number of frame-copies to send, 0=infinite [default=%default] ")

    parser.add_option("-l", "--log", action="store_true", default=False, help="write debug-output of individual blocks to disk")

    parser.add_option("", "--PHYport", type="int", default=8000 , help="Port used for MAC-->PHY communication [default=%default] ")

    parser.add_option("", "--tune-delay", type="eng_float", default=1e-4, metavar="SECS",
                      help="Carrier sensing parameter. Time to delay (in seconds) after changing frequency [default=%default]")

    parser.add_option("", "--dwell-delay", type="eng_float", default=1e-3, metavar="SECS",
                      help="Carrier sensing parameter. Time to dwell (in seconds) at a given frequncy [default=%default]")

    parser.add_option("-F", "--fft-size", type="int", default=256,
                      help="specify number of FFT bins [default=%default]")

    parser.add_option("-d", "--decim", type="intx", default=16,
                      help="set the decimation value [default=%default]")

    parser.add_option("", "--real-time", action="store_true", default=False,
                      help="Attempt to enable real-time scheduling")

    parser.add_option('-v', "--verbose", action="store_true", default=False,
                        help="Print timming information, [default=%default]")

    (options, args) = parser.parse_args ()

    # Stream sockets to ensure no packet loss during PHY<-->MAC communication

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((socket.gethostname(), options.PHYport))
    s_cca = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.listen(1)    # PHY is ready to attend MAC requests

    

    print '\n',"-------------------------"
    print " PHY (TX) layer running ..."
    print " (Ctrl + C) to exit"
    print "-------------------------",'\n'

    

    # Initial values of variables used in time measurement

    N_sym_ant=4             # OFDM symbols of the previous packet sent

    N_sensados = 0          # Number of power measurements

    N_paquetes = 0          # Number of packets sent

    tiempo_socket = 0       # Instant time of socket communication

    t_socket_TOTAL = 0      # Total time of socket communication

    T_sensado_USRP2 = 0     # Time of the USRP2 measuring the power

    T_sensado_PHY = 0       # Time elapsed in PHY layer due to a carrier sensing request 

    T_transmitir_USRP2 = 0  # USRP2 TX time 

    T_configurar_grafo = 0  # Time due to USRP2 graph management

    T_transmitir_PHY = 0    # Time elapsed in PHY layer due to a packet tx request



    first_time = True               # Is the first time to transmit?

    fg_cca = sense_block(options)   # Set up the carrier sensing block for the first time.

     

    while 1:      

        socket_cliente, datos_cliente = server.accept()     # Waiting a request from the MAC layer

        paquete_llegada=plcp.recibir_de_mac(socket_cliente) # Packet received from MAC

        if (paquete_llegada["TIPO"]=="PKT"): 

            t_socket = time.time()-paquete_llegada["DATOS"]["INFO"]["timestamp"]

            t_socket_TOTAL =t_socket_TOTAL + t_socket   #Update the time used in the socket communication.

         

        # If it is a 'send packet' request, it checks if the TX graph needs a reconfiguration

        if (paquete_llegada["TIPO"]=="PKT") and first_time == False and (N_sym_ant == paquete_llegada["DATOS"]["INFO"]["N_sym"]) == False:

            tb.stop()   # It is necessary to switch the USRP2 functionality (802.11 transmitter or Carrier Sensing Function)

        

        # Carrier sensing request

        if (paquete_llegada["TIPO"]=="CCA"):

            t_sensadoA = time.time()

            fg_cca.start()

            t_reconfig = time.time()-t_sensadoA 

            potencia_sensada=main_loop(fg_cca)  # Power measurement

            fg_cca.stop()

            fg_cca.wait()                       # Wait until the USRP2 returns the Power measurement

            t_sensadoB = time.time()

            

            # PHY responds with the power measured to the MAC

            paquete=plcp.crear_paquete("CCA",potencia_sensada)

            plcp.enviar_a_mac(socket_cliente,paquete)

            t_sensadoC = time.time()

            T_sensado_USRP2 = T_sensado_USRP2 + (t_sensadoB - t_sensadoA)

            T_sensado_PHY = T_sensado_PHY + (t_sensadoC - t_sensadoA)

            N_sensados +=1 

            if options.verbose: print "Time elapsed on graph configuration (Carrier Sensing) = \t", t_reconfig

        

        # Send packet request

        if (paquete_llegada["TIPO"]=="PKT"):

            t_enviarA = time.time()

            leido=paquete_llegada["DATOS"]  # Copy the packet to send from the MAC message 

            info = leido["INFO"]

            N_sym=info["N_sym"] # Read N_sym and add N_sym to options

            mod = info["modulation"]    

            

            # FIX ME! Another way to update N_sym and modulation values?

            parser.add_option("-T", "--nsym", type="int", default=N_sym)

            parser.add_option("", "--modulation", type="string", default=mod)

            (options, args) = parser.parse_args ()

            

            # Check if the OFDM code regime or the amount of OFDM symbols to transmit differs from the last packet sent

            if first_time == True or (N_sym_ant == paquete_llegada["DATOS"]["INFO"]["N_sym"]) == False:

                #print "Re-setting USRP2 graph!"

                tb = transmitter_block(options) # If necessary, update the transmit flow-graph depending to the new OFDM parameters

                r = gr.enable_realtime_scheduling()    

                if r != gr.RT_OK:

                    print "Warning: failed to enable realtime scheduling" 

            t_2 = time.time()

            

            tb.start()                  # Send packet procedure starts

            t_enviarB= time.time()

            send_pkt(leido,eof=False)   # 'leido' is a dictionary which contents the packet to transmit and other information 

            send_pkt("",eof=True)

            t_enviarC = time.time()     

            tb.wait()                   # Wait until USRP2 finishes the TX-graph 

            t_enviarD= time.time()

            if options.verbose: print "Time elapsed on graph configuration (TX Packet) = \t", (t_enviarB - t_2)

            T_transmitir_USRP2 = T_transmitir_USRP2 + t_enviarC-t_enviarB

            T_configurar_grafo = T_configurar_grafo + t_enviarD-t_enviarA - (t_enviarC-t_enviarB)

            T_transmitir_PHY = T_transmitir_PHY + t_enviarD-t_enviarA 

                     

            # set values for the next packet tx request

            first_time=False

            N_sym_ant = N_sym       # Keep a record of the OFDM symbols' Number

            N_paquetes += 1

        

        if options.verbose:

            

            print "===================== Average statistics ===================="

            print "Number of Carrier Sensing Requests = ",N_sensados

            if N_sensados>0:

                print "Time spent by USRP2 on sensing channel = \t",T_sensado_USRP2/N_sensados

                print "Time spent by PHY layer on sensing channel = \t",T_sensado_PHY/N_sensados

            print "============================================================="

            print "Number of packets transmitted = ",N_paquetes

            if N_paquetes>1:

                print "Time spent by USRP2 on sending a packet = \t",T_transmitir_USRP2/N_paquetes 

                print "Time spent by USRP2 on configuring the graphs\t",T_configurar_grafo/N_paquetes

                print "Time spent by PHY on sending a packet = \t",T_transmitir_PHY/N_paquetes

                print "Time spent on Socket Communication = \t", t_socket_TOTAL/N_paquetes

            print "============================================================="



              

if __name__ == '__main__':

    try:

        main()

    except KeyboardInterrupt:

        pass

