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



# Filename: ftw_ofdm.py



# This Python file contains the classes 'ofdm_mod' and 'ftw_transmit_path' necessary to create
# the 802.11a/g/p OFDM encoder flow-graph. The original PHY code was developed by FTW 
# (Forschungszentrum Telekommunikation Wien / Telecommunications Research Center Vienna, 
# http://www.ftw.at). The code was first presented and described in the following publication:



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

#	Andrea Costantini 

#	Paul Fuxjaeger (fuxjaeger@ftw.at)

#	Danilo Valerio (valerio@ftw.at)

#	Paolo Castiglione (castiglione@ftw.at)

#	Giammarco Zacheo (zacheo@ftw.at)



# Authors of the PHY added functionalities:

#	Juan R. Gutierrez-Agullo (jgutierrez@umh.es)

#	Baldomero Coll-Perales (bcoll@umh.es)

#	Dr. Javier Gozalvez (j.gozalvez@umh.es)



import copy, math, sys, time
from gnuradio import gr, gru, uhd, eng_notation  #, ftw
import gnuradio.ieee802_11 as gr_ieee802_11
import gnuradio.gr.gr_threading as _threading
#from gnuradio.blks2impl import psk, qam
import ftw_packet_utils as ofdm_packet_utils
from gnuradio.digital import digital_swig
import uwicore_mpif as plcp 


# sets up the transmit path
class ftw_transmit_path(gr.hier_block2): 
    def __init__(self, options):
	gr.hier_block2.__init__(self, "transmit_path",
				gr.io_signature(0, 0, 0), # Input signature
				gr.io_signature(1, 1, gr.sizeof_gr_complex)) # Output signature

	# the modulator itself
	self.ofdm_tx       = ofdm_mod(options, msgq_limit=2, pad_for_usrp=False)

	# static value to make sure we do not exceed +-1 for the floats being sent to the sink
	self._norm         = options.norm        
	self.amp = gr.multiply_const_cc(self._norm)

        # setup basic connections
        self.connect(self.ofdm_tx, self.amp, self)
        
    def send_pkt(self, mac_msg, eof=False):
        return self.ofdm_tx.send_pkt(mac_msg, eof)
    

        
# main modulator class
class ofdm_mod(gr.hier_block2):
    """
    Modulates an OFDM stream. Based on the options fft_length, occupied_tones, and
    cp_length, this block creates OFDM symbols using a specified modulation option.
    
    Send packets by calling send_pkt
    """
    def __init__(self, options, msgq_limit=2, pad_for_usrp=False):
        """
	Hierarchical block for sending packets

        Packets to be sent are enqueued by calling send_pkt.
        The output is the complex modulated signal at baseband.

        @param options: pass modulation options from higher layers (fft length, occupied tones, etc.)
        @param msgq_limit: maximum number of messages in message queue
        @type msgq_limit: int
        @param pad_for_usrp: If true, packets are padded such that they end up a multiple of 128 samples
        """

	gr.hier_block2.__init__(self, "ofdm_mod",
				gr.io_signature(0, 0, 0),       # Input signature
				gr.io_signature(1, 1, gr.sizeof_gr_complex)) # Output signature
	
    
        self._fft_length          = 64
        self._total_sub_carriers  = 53
	self._data_subcarriers    = 48
	self._cp_length           = 16
 	self._regime              = options.regime
	self._symbol_length       = self._fft_length + self._cp_length
	
	# assuming we have 100Ms/s going to the USRP2 and 80 samples per symbol
	# we can calculate the OFDM symboltime (in microseconds) 
	# depending on the interpolation factor 
	self._symbol_time      = 100000000*(self._symbol_length )/(100*options.bandwidth)
        self._n_sym = options.nsym
	
        win = []
        self._modulation = options.modulation
        if self._modulation == "bpsk":
            rotated_const = ofdm_packet_utils.bpsk(self)
        elif self._modulation == "qpsk":
            rotated_const = ofdm_packet_utils.qpsk(self)
        elif self._modulation == "qam16":
            rotated_const = ofdm_packet_utils.qam16(self)
        elif self._modulation == "qam64":
            rotated_const = ofdm_packet_utils.qam64(self)

#	if(self._regime == "1" or self._regime == "2"):
#	    rotated_const = ofdm_packet_utils.bpsk(self)
 #       
  #      elif (self._regime == "3" or self._regime == "4"):	
	#    rotated_const = ofdm_packet_utils.qpsk(self)
#
 #       elif(self._regime == "5" or self._regime == "6"):
  #          rotated_const = ofdm_packet_utils.qam16(self) 
#
 #       elif(self._regime == "7" or self._regime == "8"):
 #           rotated_const = ofdm_packet_utils.qam64(self)
	
        # map groups of bits to complex symbols
        self._pkt_input = gr_ieee802_11.ofdm_symbol_mapper(rotated_const, msgq_limit, self._data_subcarriers, self._fft_length)
        
        # insert pilot symbols
        self.pilot = gr_ieee802_11.ofdm_pilot_insert(self._data_subcarriers)
	
        # move subcarriers to their designated place and insert DC  
        self.cmap  = gr_ieee802_11.ofdm_carrier_mapper(self._fft_length, self._total_sub_carriers)        

	# inverse fast fourier transform
        self.ifft = gr.fft_vcc(self._fft_length, False, win, False)

        # add cyclic prefix
        self.cp_adder = digital_swig.ofdm_cyclic_prefixer(self._fft_length, self._symbol_length)
        
        # scale accordingly
        self.scale = gr.multiply_const_cc(1.0 / math.sqrt(self._fft_length))
      
	# we need to know the number of OFDM data symbols for preamble and zerogap
    
    # MODIFIED FROM ORIGINAL
    # Instead of having the OFDM data symbols recorded in a python dictionary, the value of N_sym is updated when the class ofdm_mod invoked. 
	N_sym             = self._n_sym
    
	
	# add training sequence
        self.preamble= ofdm_packet_utils.insert_preamble(self._symbol_length, N_sym)

        # append zero samples at the end (receiver needs that to decode)
	self.zerogap    = ofdm_packet_utils.insert_zerogap(self._symbol_length, N_sym)
        
        # repeat the frame a number of times 
        self.repeat = gr_ieee802_11.ofdm_symbol_repeater(self._symbol_length, options.repetition, N_sym)

	self.s2v = gr.stream_to_vector(gr.sizeof_gr_complex , self._symbol_length)
	self.v2s = gr.vector_to_stream(gr.sizeof_gr_complex , self._symbol_length)
	
	# swap real and immaginary component before sending (GNURadio/USRP2 bug!)
	self.gr_complex_to_imag_0 = gr.complex_to_imag(1)
	self.gr_complex_to_real_0 = gr.complex_to_real(1)
	self.gr_float_to_complex_0 = gr.float_to_complex(1)
	self.connect((self.v2s, 0), (self.gr_complex_to_imag_0, 0))
	self.connect((self.v2s, 0), (self.gr_complex_to_real_0, 0))
	self.connect((self.gr_complex_to_imag_0, 0), (self.gr_float_to_complex_0, 1))
	self.connect((self.gr_complex_to_real_0, 0), (self.gr_float_to_complex_0, 0))
	self.connect((self.gr_float_to_complex_0, 0), (self))
		
        # connect the blocks
	self.connect((self._pkt_input, 0), (self.pilot, 0))
	self.connect((self._pkt_input,1), (self.preamble, 1))
	self.connect((self.preamble,1), (self.zerogap, 1))
	
	#if options.repetition == 1:
	self.connect(self.pilot, self.cmap, self.ifft, self.cp_adder, self.scale, self.s2v, \
        self.preamble, self.zerogap, self.v2s)
                
	#elif options.repetition > 1:
	#self.connect(self.pilot, self.cmap, self.ifft, self.cp_adder, self.scale, self.s2v, self.preamble, self.zerogap, self.repeat, self.v2s)
    
	#else:
	#	print"Error: repetiton must be a integer number >= 1 \n"
	#	sys.exit(1)

        if options.log:
            self.connect((self._pkt_input), gr.file_sink(gr.sizeof_gr_complex * self._data_subcarriers, "ofdm_mapper.dat"))
	    self.connect(self.pilot, gr.file_sink(gr.sizeof_gr_complex * (5 + self._data_subcarriers), "ofdm_pilot.dat"))
	    self.connect(self.cmap, gr.file_sink(gr.sizeof_gr_complex * self._fft_length, "ofdm_cmap.dat"))	
            self.connect(self.ifft, gr.file_sink(gr.sizeof_gr_complex * self._fft_length, "ofdm_ifft.dat"))
            self.connect(self.cp_adder, gr.file_sink(gr.sizeof_gr_complex, "ofdm_cp_adder.dat"))	   
	    self.connect(self.scale, gr.file_sink(gr.sizeof_gr_complex, "ofdm_scale.dat"))
            self.connect(self.preamble, gr.file_sink(gr.sizeof_gr_complex * self._symbol_length, "ofdm_preamble.dat"))
            self.connect(self.zerogap, gr.file_sink(gr.sizeof_gr_complex * self._symbol_length, "ofdm_zerogap.dat"))

    def send_pkt(self, mac_msg, eof=False):
        """
        Send the payload.

        @param payload: data to send
        @type payload: string
        """
        if eof:
            msg = gr.message(1)             # tell self._pkt_input we're not sending any more packets
            
        else: 
            info = mac_msg["INFO"]              # this dictionary vector contains tx information that will be used during the encoding process                     
	    N_cbps            = info["N_cbps"]     # Upload the number of Coded bits per OFDM Symbol
	    N_bpsc            = info["N_bpsc"]     # Upload the number of Coded bits per sub-carrier
            N_rate            = info["rate"]   # Upload the data rate code
	    N_sym             = info["N_sym"]      # Upload the OFDM Symbols' number
        
        # MODIFIED FROM ORIGINAL
        # It is necessary to update the payload and length field on every packet transmitted 
            (pkt,Length) = mac_msg["MPDU"], mac_msg["LENGTH"] 

            
            #print"Txtime in microseconds:",info["txtime"]
            #print"Length of MPDU in bytes = ", info["packet_len"]
            #print"Number of DATA OFDM symbols = ", info["N_sym"]    
            #print"Number of padding bits = ", info["N_pad"]

         
        # Encoding operations
	    (pkt_scrambled,Length) = ofdm_packet_utils.scrambler(pkt,Length)
	    pkt_coded = ofdm_packet_utils.conv_encoder(pkt_scrambled, Length, self._regime, N_cbps, N_bpsc, N_sym, N_rate)
	    pkt_interleaved = ofdm_packet_utils.interleaver(pkt_coded , self._regime, N_cbps, N_bpsc)
	    msg = gr.message_from_string(pkt_interleaved)
        self._pkt_input.msgq().insert_tail(msg)
        
        

