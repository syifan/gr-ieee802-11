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



# Filename: ftw_packet_utils.py



# This file includes all the methods used in the OFDM encoding process. The original PHY code was
# developed by FTW (Forschungszentrum  Telekommunikation Wien / Telecommunications Research 
# Center Vienna, http://www.ftw.at). The code was first presented and described in the 
# following publication:



# P.Fuxjaeger, A. Costantini, D. Valerio, P. Castiglione, G. Zacheo, T. Zemen and F. Ricciato, "IEEE 802.11p Transmission Using GNURadio", in Proceedings of the IEEE Karlsruhe Workshop on Software Radios (WSR10), pp. 1-4, 2010.



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


import struct, numpy, math, sys,time
from gnuradio import gru,gr  #,ftw
import gnuradio.ieee802_11 as gr_ieee802_11

def interleaver (payload, regime, N_cbps, N_bpsc):

	length_payload = len(payload)
	length_payload_bit = 8 * length_payload
	half_interleaved = first_permutation(payload, N_cbps, length_payload_bit)
	interleaved = second_permutation(half_interleaved, N_cbps, N_bpsc, length_payload_bit)

	return interleaved

def first_permutation(payload, N_cbps, length_payload_bit):

	app = conv_packed_binary_string_to_1_0_string(payload)
	app=list(app)
	new = ['0'] * len(app)
	if(N_cbps == 48): # Modulation "bpsk"
		j=0
		while(j < length_payload_bit/N_cbps):
			
			for k in range (0, N_cbps):
				i = (N_cbps/16) * (k%16) + int(math.floor(k/16))	
				new[i + (j*N_cbps)] = app[k + (j*N_cbps)]
			j +=1

	else:   # other modulation ---> first 48 bits alone (signal field)

		for k in range (0, 48):
			i = (48/16) * (k%16) + int(math.floor(k/float(16)))	
			new[i] = app[k]
		j = 0
		while(j < (length_payload_bit - 48) / N_cbps):
			for k in range (0, N_cbps):
				i = (N_cbps/16) * (k%16) + int(math.floor(k/float(16)))
				new[i + 48 + (j*N_cbps)] = app[k + 48 + (j*N_cbps)] 
			j +=1		
	
	new = "".join(new)
	return conv_1_0_string_to_packed_binary_string(new)


def second_permutation(half_interleaved, N_cbps, N_bpsc, length_payload_bit):

	app = conv_packed_binary_string_to_1_0_string(half_interleaved)
	app=list(app)
	new_temp = ['0'] * (len(app) - 48)
	new = app[0:48] + new_temp
	s = max(N_bpsc/2 , 1)
	k=0
	
	while (k < (length_payload_bit - 48)/N_cbps):
		for i in range (0 , N_cbps):
			j = (s * int(math.floor(i/s))) + (i + N_cbps - (int(math.floor(16*i/float(N_cbps))))) % s
			new[j + 48 + (k*N_cbps)] = app[i + 48 + (k*N_cbps)]
		k +=1
	
	new = "".join(new)
	return conv_1_0_string_to_packed_binary_string(new)


def conv_encoder(pkt, Length, regime, N_cbps, N_bpsc, N_sym, N_rate):

	Real_num_of_bits = N_sym * N_cbps    # We could have more then correct number we need 
					     # See  Tail and pad in ftw_make function	 
	app = conv_packed_binary_string_to_1_0_string(pkt)
	app = list(app)
	encoded = ['0'] * (2 * len(app)) 
	g0 = 0x5b   # Generator polynomial (133 base 8)
	g1 = 0x79   # Generator polynomial (171 base 8)
	outA = 0
	outB = 0
 	register = 0
	for i in range (0, len(app)):
		if(app[i] == '1'):
			register = register >> 1     # Shift the status in the conv encoder  
			register = register | 0x40   # push 1 in the first element in the register after the shift
		else:
			register = register >> 1
		
		modA = modB = 0	
		for k in range (0,8):
			modA += (((register & g0) >> k) & (0x01))     # Parity check (count the number of 1s)
			modB += (((register & g1) >> k) & (0x01))     # Parity check
			
		outA     =  modA % 2  # Modulo 2 sum
		outB     =  modB % 2
		encoded[2 * i]   = str(outA)
		encoded[2 * i + 1] = str(outB)

	# Puncturing operations-----------------------------------------------
	if (regime == "1" or regime== "3" or regime == "5"):
		encoded = encoded[0:48 + Real_num_of_bits]
		encoded = "".join(encoded)
		
		return conv_1_0_string_to_packed_binary_string(encoded)

	elif (regime == "2" or regime == "4" or regime == "6" or regime == "8"):
		signal_coded = encoded[0:48]
		data_coded = encoded[48:]
		dynamic_offset = 0	
		new = data_coded[0:3]
		while dynamic_offset + 9 < len(data_coded)-1 :
			new = new + data_coded[5 + dynamic_offset : 9 + dynamic_offset]
			dynamic_offset += 6
		new.append(data_coded[5 + dynamic_offset])
		new = new[0:Real_num_of_bits]
		new = signal_coded + new
		encoded = "".join(new)
		return conv_1_0_string_to_packed_binary_string(encoded)

	elif (regime == "7"): 
		dinamic_offset = 0
		signal_coded = encoded[0:48]
		data_coded = encoded[48:]
		new = data_coded[0:3]
		while dinamic_offset + 4 < len(data_coded) -1 :
			new = new + data_coded[4 + dinamic_offset : 7 + dinamic_offset]
			dinamic_offset += 4
		new = new[0:Real_num_of_bits]		
		new = signal_coded + new
		encoded = "".join(new)
		return conv_1_0_string_to_packed_binary_string(encoded)	
			

def scrambler(pkt, Length_data):

	scrambling_seq = [0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1,\
                          0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1,\
                          0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1,\
                          0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1];

	app = conv_packed_binary_string_to_1_0_string(pkt)
	app = list(app)
	zero_forcing_index = Length_data * 8
	scrambled = app[0:24]

	# Start from 24 because SIGNAL symbol mustn't be scrambled
	for k in range (24 , len(app)):              
		scrambled.append(str(int(app[k])^(scrambling_seq[(k-24) % 127])))
	
	# Force six bit to "0" in return to 0 state at last
	for i in range (23 + zero_forcing_index +17 , 23 + zero_forcing_index + 22 + 1):
		scrambled[i] = '0'

	scrambled = "".join(scrambled)

	return conv_1_0_string_to_packed_binary_string(scrambled) , Length_data

def insert_preamble(length, N_sym):
	ftw_preamble= [list(fft_preamble)]
	preamble = gr_ieee802_11.ofdm_preamble_insert(length, N_sym, ftw_preamble)
	return preamble 

def insert_zerogap(length, N_sym):
	gap = [list(gap_sample)]
	ftw_zerogap = gr_ieee802_11.ofdm_zerogap_insert(length, N_sym, gap)
	return ftw_zerogap

def qam16(self):
	return gray_const_qam16
	
def qam64(self):
	return gray_const_qam64

def qpsk(self):
	return gray_const_qpsk

def bpsk(self):
	return gray_const_bpsk

def conv_packed_binary_string_to_1_0_string(s):
    """
    '\xAF' --> '10101111'
    """
    r = []
    for ch in s:
        x = ord(ch)
        for i in range(7,-1,-1):
            t = (x >> i) & 0x1
            r.append(t)

    return ''.join(map(lambda x: chr(x + ord('0')), r))

def conv_1_0_string_to_packed_binary_string(s):
    """
    '10101111' -> ('\xAF', False)

    Basically the inverse of conv_packed_binary_string_to_1_0_string,
    but also returns a flag indicating if we had to pad with leading zeros
    to get to a multiple of 8.
    """
    if not is_1_0_string(s):
        raise ValueError, "Input must be a string containing only 0's and 1's"
    
    # pad to multiple of 8
    padded = False
    rem = len(s) % 8
    if rem != 0:
        npad = 8 - rem
        s = '0' * npad + s
        padded = True

    assert len(s) % 8 == 0

    r = []
    i = 0
    while i < len(s):
        t = 0
        for j in range(8):
            t = (t << 1) | (ord(s[i + j]) - ord('0'))
        r.append(chr(t))
        i += 8
    return ''.join(r)
        

def is_1_0_string(s):
    if not isinstance(s, str):
        return False
    for ch in s:
        if not ch in ('0', '1'):
            return False
    return True

def string_to_hex_list(s):
    return map(lambda x: hex(ord(x)), s)


def hexint(mask):
  """
  Convert unsigned masks into signed ints.

  This allows us to use hex constants like 0xf0f0f0f2 when talking to
  our hardware and not get screwed by them getting treated as python
  longs.
  """
  if mask >= 2**31:
     return int(mask-2**32)
  return mask


def ascii_to_bin(char):
	ascii = ord(char)
	bin = []

	while (ascii > 0):
		if (ascii & 1) == 1:
		     bin.append("1")
		else:
		     bin.append("0")
		ascii = ascii >> 1             
        bin.reverse()
	binary = "".join(bin)
	zerofix = (8 - len(binary)) * '0'

	return zerofix + binary


#////////////////////////////////////////////////////////////////////////////////
#                                Static tables
#///////////////////////////////////////////////////////////////////////////////

gray_const_bpsk = (-1+0j, +1+0j)

gray_const_qpsk = (-0.7071 - 0.7071j, -0.7071 + 0.7071j, +0.7071 - 0.7071j, +0.7071 + 0.7071j)

gray_const_qam16 = (-0.9487 - 0.9487j,-0.9487 - 0.3162j,-0.9487 + 0.9487j,-0.9487 + 0.3162j,-0.3162 - 0.9487j,-0.3162 - 0.3162j,-0.3162 + 0.9487j,-0.3162 + 0.3162j,0.9487 - 0.9487j, 0.9487 - 0.3162j, 0.9487 + 0.9487j, 0.9487 + 0.3162j, 0.3162 - 0.9487j, 0.3162 - 0.3162j, 0.3162 + 0.9487j, 0.3162 + 0.3162j)

gray_const_qam64 = (-1.0801 - 1.0801j,  -1.0801 - 0.7715j,  -1.0801 - 0.1543j,  -1.0801 - 0.4629j, -1.0801 + 1.0801j,  -1.0801 + 0.7715j,  -1.0801 + 0.1543j,  -1.0801 + 0.4629j, -0.7715 - 1.0801j,  -0.7715 - 0.7715j,  -0.7715 - 0.1543j,  -0.7715 - 0.4629j, -0.7715 + 1.0801j,  -0.7715 + 0.7715j,    -0.7715 + 0.1543j,  -0.7715 + 0.4629j, -0.1543 - 1.0801j,  -0.1543 - 0.7715j,  -0.1543 - 0.1543j,  -0.1543 - 0.4629j, -0.1543 + 1.0801j,  -0.1543 + 0.7715j,  -0.1543 + 0.1543j,  -0.1543 + 0.4629j, -0.4629 - 1.0801j,  -0.4629 - 0.7715j,  -0.4629 - 0.1543j,  -0.4629 - 0.4629j, -0.4629 + 1.0801j,   -0.4629 + 0.7715j,  -0.4629 + 0.1543j,  -0.4629 + 0.4629j, 1.0801 - 1.0801j,   1.0801 - 0.7715j,   1.0801 - 0.1543j,   1.0801 - 0.4629j, 1.0801 + 1.0801j,   1.0801 + 0.7715j,   1.0801 + 0.1543j,   1.0801 + 0.4629j, 0.7715 - 1.0801j,   0.7715 - 0.7715j,   0.7715 - 0.1543j,   0.7715 - 0.4629j,
0.7715 + 1.0801j,   0.7715 + 0.7715j,   0.7715 + 0.1543j,   0.7715 + 0.4629j, 0.1543 - 1.0801j,   0.1543 - 0.7715j,   0.1543 - 0.1543j, 0.1543 - 0.4629j,
0.1543 + 1.0801j,   0.1543 + 0.7715j,   0.1543 + 0.1543j,   0.1543 + 0.4629j, 0.4629 - 1.0801j,   0.4629 - 0.7715j,   0.4629 - 0.1543j,   0.4629 - 0.4629j,
0.4629 + 1.0801j,   0.4629 + 0.7715j,   0.4629 + 0.1543j,   0.4629 + 0.4629j)

fft_preamble = (0.3680 + 0.3680j, -1.0596 + 0.0187j, -0.1078 - 0.6282j, 1.1421 - 0.1012j, 0.7360, 1.1421 - 0.1012j, -0.1078 - 0.6282j, -1.0596 + 0.0187j, 0.3680 + 0.3680j, 0.0187 - 1.0596j, -0.6282 - 0.1078j,-0.1012 + 1.1421j, 0 + 0.7360j, -0.1012 + 1.1421j, -0.6282 - 0.1078j, 0.0187 - 1.0596j, 0.3680 + 0.3680j, -1.0596 + 0.0187j, -0.1078 - 0.6282j, 1.1421 - 0.1012j, 0.7360, 1.1421 - 0.1012j, -0.1078 - 0.6282j, -1.0596 + 0.0187j, 0.3680 + 0.3680j, 0.0187 - 1.0596j, -0.6282 - 0.1078j, -0.1012 + 1.1421j, 0 + 0.7360j, -0.1012 + 1.1421j, -0.6282 - 0.1078j, 0.0187 - 1.0596j,0.3680 + 0.3680j, -1.0596 + 0.0187j, -0.1078 - 0.6282j, 1.1421 - 0.1012j, 0.7360, 1.1421 - 0.1012j, -0.1078 - 0.6282j, -1.0596 + 0.0187j, 0.3680 + 0.3680j, 0.0187 - 1.0596j, -0.6282 - 0.1078j,-0.1012 + 1.1421j, 0 + 0.7360j, -0.1012 + 1.1421j, -0.6282 - 0.1078j, 0.0187 - 1.0596j, 0.3680 + 0.3680j, -1.0596 + 0.0187j, -0.1078 - 0.6282j, 1.1421 - 0.1012j, 0.7360, 1.1421 - 0.1012j, -0.1078 - 0.6282j, -1.0596 + 0.0187j, 0.3680 + 0.3680j, 0.0187 - 1.0596j, -0.6282 - 0.1078j, -0.1012 + 1.1421j, 0 + 0.7360j, -0.1012 + 1.1421j, -0.6282 - 0.1078j, 0.0187 - 1.0596j, 0.3680 + 0.3680j, -1.0596 + 0.0187j, -0.1078 - 0.6282j, 1.1421 - 0.1012j, 0.7360, 1.1421 - 0.1012j, -0.1078 - 0.6282j, -1.0596 + 0.0187j, 0.3680 + 0.3680j, 0.0187 - 1.0596j, -0.6282 - 0.1078j,-0.1012 + 1.1421j, 0 + 0.7360j, -0.1012 + 1.1421j, -0.6282 - 0.1078j, 0.0187 - 1.0596j, 0.3680 + 0.3680j, -1.0596 + 0.0187j, -0.1078 - 0.6282j, 1.1421 - 0.1012j, 0.7360, 1.1421 - 0.1012j, -0.1078 - 0.6282j, -1.0596 + 0.0187j, 0.3680 + 0.3680j, 0.0187 - 1.0596j, -0.6282 - 0.1078j, -0.1012 + 1.1421j, 0 + 0.7360j, -0.1012 + 1.1421j, -0.6282 - 0.1078j, 0.0187 - 1.0596j, 0.3680 + 0.3680j, -1.0596 + 0.0187j, -0.1078 - 0.6282j, 1.1421 - 0.1012j, 0.7360, 1.1421 - 0.1012j, -0.1078 - 0.6282j, -1.0596 + 0.0187j, 0.3680 + 0.3680j, 0.0187 - 1.0596j, -0.6282 - 0.1078j,-0.1012 + 1.1421j, 0 + 0.7360j, -0.1012 + 1.1421j, -0.6282 - 0.1078j, 0.0187 - 1.0596j, 0.3680 + 0.3680j, -1.0596 + 0.0187j, -0.1078 - 0.6282j, 1.1421 - 0.1012j, 0.7360, 1.1421 - 0.1012j, -0.1078 - 0.6282j, -1.0596 + 0.0187j, 0.3680 + 0.3680j, 0.0187 - 1.0596j, -0.6282 - 0.1078j, -0.1012 + 1.1421j, 0 + 0.7360j, -0.1012 + 1.1421j, -0.6282 - 0.1078j, 0.0187 - 1.0596j, 0.3680 + 0.3680j, -1.0596 + 0.0187j, -0.1078 - 0.6282j, 1.1421 - 0.1012j, 0.7360, 1.1421 - 0.1012j, -0.1078 - 0.6282j, -1.0596 + 0.0187j, 0.3680 + 0.3680j, 0.0187 - 1.0596j, -0.6282 - 0.1078j,-0.1012 + 1.1421j, 0 + 0.7360j, -0.1012 + 1.1421j, -0.6282 - 0.1078j, 0.0187 - 1.0596j, 0.3680 + 0.3680j, -1.0596 + 0.0187j, -0.1078 - 0.6282j, 1.1421 - 0.1012j, 0.7360, 1.1421 - 0.1012j, -0.1078 - 0.6282j, -1.0596 + 0.0187j, 0.3680 + 0.3680j, 0.0187 - 1.0596j, -0.6282 - 0.1078j, -0.1012 + 1.1421j, 0 + 0.7360j, -0.1012 + 1.1421j, -0.6282 - 0.1078j, 0.0187 - 1.0596j,-1.2500, 0.0983 - 0.7808j, 0.7337 - 0.8470j, -0.7351 - 0.9210j, -0.0224 - 0.4302j, 0.6006 + 0.5923j, -1.0186 + 0.1640j, -0.9751 + 0.1325j, -0.2803 + 1.2071j, -0.4516 + 0.1744j, -0.4825 - 0.6503j, 0.5565 - 0.1130j, 0.6577 - 0.7389j, -1.0501 - 0.5218j, -0.4577 - 0.3144j, 0.2953 - 0.7868j, 0.5000 + 0.5000j, 0.9539 + 0.0328j, -0.1799 - 1.2853j, 0.4694 + 0.1195j, 0.1958 + 0.4683j, -1.0944 + 0.3790j, 0.0079 + 0.9200j,  0.4267 - 0.0326j, 0.7803 + 0.2071j, -0.3065 + 0.8494j, -0.9210 + 0.4414j, 0.4786 + 0.7017j, 0.1689 - 0.2231j, 0.7747 - 0.6624j, 0.3180 + 0.8893j, -0.0410 + 0.9626j, 1.2500, -0.0410 - 0.9626j, 0.3180 - 0.8893j, 0.7747 + 0.6624j, 0.1689 + 0.2231j, 0.4786 - 0.7017j, -0.9210 - 0.4414j, -0.3065 - 0.8494j, 0.7803 - 0.2071j, 0.4267 + 0.0326j, 0.0079 - 0.9200j, -1.0944 - 0.3790j, 0.1958 - 0.4683j, 0.4694 - 0.1195j, -0.1799 + 1.2853j, 0.9539 - 0.0328j, 0.5000 - 0.5000j, 0.2953 + 0.7868j, -0.4577 + 0.3144j, -1.0501 + 0.5218j, 0.6577 + 0.7389j, 0.5565 + 0.1130j, -0.4825 + 0.6503j, -0.4516 - 0.1744j, -0.2803 - 1.2071j, -0.9751 - 0.1325j, -1.0186 - 0.1640j, 0.6006 - 0.5923j, -0.0224 + 0.4302j, -0.7351 + 0.9210j, 0.7337 + 0.8470j, 0.0983 + 0.7808j,-1.2500, 0.0983 - 0.7808j, 0.7337 - 0.8470j, -0.7351 - 0.9210j, -0.0224 - 0.4302j, 0.6006 + 0.5923j, -1.0186 + 0.1640j, -0.9751 + 0.1325j, -0.2803 + 1.2071j, -0.4516 + 0.1744j, -0.4825 - 0.6503j, 0.5565 - 0.1130j, 0.6577 - 0.7389j, -1.0501 - 0.5218j, -0.4577 - 0.3144j, 0.2953 - 0.7868j, 0.5000 + 0.5000j, 0.9539 + 0.0328j, -0.1799 - 1.2853j, 0.4694 + 0.1195j, 0.1958 + 0.4683j, -1.0944 + 0.3790j, 0.0079 + 0.9200j,  0.4267 - 0.0326j, 0.7803 + 0.2071j, -0.3065 + 0.8494j, -0.9210 + 0.4414j, 0.4786 + 0.7017j, 0.1689 - 0.2231j, 0.7747 - 0.6624j, 0.3180 + 0.8893j, -0.0410 + 0.9626j, 1.2500, -0.0410 - 0.9626j, 0.3180 - 0.8893j, 0.7747 + 0.6624j, 0.1689 + 0.2231j, 0.4786 - 0.7017j, -0.9210 - 0.4414j, -0.3065 - 0.8494j, 0.7803 - 0.2071j, 0.4267 + 0.0326j, 0.0079 - 0.9200j, -1.0944 - 0.3790j, 0.1958 - 0.4683j, 0.4694 - 0.1195j, -0.1799 + 1.2853j, 0.9539 - 0.0328j, 0.5000 - 0.5000j, 0.2953 + 0.7868j, -0.4577 + 0.3144j, -1.0501 + 0.5218j, 0.6577 + 0.7389j, 0.5565 + 0.1130j, -0.4825 + 0.6503j, -0.4516 - 0.1744j, -0.2803 - 1.2071j, -0.9751 - 0.1325j, -1.0186 - 0.1640j, 0.6006 - 0.5923j, -0.0224 + 0.4302j, -0.7351 + 0.9210j, 0.7337 + 0.8470j, 0.0983 + 0.7808j,-1.2500, 0.0983 - 0.7808j, 0.7337 - 0.8470j, -0.7351 - 0.9210j, -0.0224 - 0.4302j, 0.6006 + 0.5923j, -1.0186 + 0.1640j, -0.9751 + 0.1325j, -0.2803 + 1.2071j, -0.4516 + 0.1744j, -0.4825 - 0.6503j, 0.5565 - 0.1130j, 0.6577 - 0.7389j, -1.0501 - 0.5218j, -0.4577 - 0.3144j, 0.2953 - 0.7868j, 0.5000 + 0.5000j, 0.9539 + 0.0328j, -0.1799 - 1.2853j, 0.4694 + 0.1195j, 0.1958 + 0.4683j, -1.0944 + 0.3790j, 0.0079 + 0.9200j,  0.4267 - 0.0326j, 0.7803 + 0.2071j, -0.3065 + 0.8494j, -0.9210 + 0.4414j, 0.4786 + 0.7017j, 0.1689 - 0.2231j, 0.7747 - 0.6624j, 0.3180 + 0.8893j, -0.0410 + 0.9626j)

gap_sample = (0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j,0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j,0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j,0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j,0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j,0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j,0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j)

