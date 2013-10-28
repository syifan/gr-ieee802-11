#!/usr/bin/env python
#
# Copyright 2005, 2006 Free Software Foundation, Inc.
# 
# This file is part of GNU Radio
# 
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
# 
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.


# Projectname: ftw_80211_ofdm_tx 
#
# Filename: ftw_ofdm_tx.py
#
# This is the main script that triggers the encoding procedures and 
# sends the complex baseband signal to the USRP2 sink. 
#
# List of Contributors: Andrea Costantini, 
#                       Paul Fuxjaeger, (fuxjaeger@ftw.at) 
#                       Danilo Valerio, (valerio@ftw.at)
#                       Paolo Castiglione, (castiglione@ftw.at)
#                       Giammarco Zacheo, (zacheo@ftw.at)


# Forschungszentrum Telekommunikation Wien
# Telecommunications Research Center Vienna
# (http://www.ftw.at)
# December 2009

import time, struct, sys
from gnuradio import gr, blks2, uhd, eng_notation
from gnuradio.eng_option import eng_option
from optparse import OptionParser
from ieee802_11_ofdm import ieee802_11_transmit_path

class my_top_block(gr.top_block):
    def __init__(self, count, options, payload=''):
        gr.top_block.__init__(self)

        #self._interface          = options.interface       # logical network interface
        #self._mac_addr           = options.mac_addr        # MAC address
        self._tx_freq            = options.freq            # center frequency
        self._bw                 = options.bandwidth          # interpolation factor
        self._gain               = options.gain            # Tx gain
        #print "Requested freq %f" % self._tx_freq
        self.args = options.args
        self._ant  = options.antenna
        self._spec = options.spec

        # setup sink and connect output of transmitpath to it 
        #self._setup_usrp_sink()
        self.u = uhd.usrp_sink(device_addr=self.args, stream_args=uhd.stream_args('fc32'))
        #print "Does it get here at all?!!"
        #self.connect(self, self.u)
        if(self._spec):
            self.u.set_subdev_spec(self._spec, 0)

        # Set the antenna
        if(self._ant):
            self.u.set_antenna(self._ant, 0)
        self.u.set_gain(self._gain)
        self.set_freq(self._tx_freq)
        self.rate = self.u.set_samp_rate(self._bw)
        self.txpath = ieee802_11_transmit_path(count,options, payload)
        self.connect(self.txpath, self.u)
	
        # write final baseband signal to disk
        if options.log:	
            self.connect(self.txpath, gr.file_sink(gr.sizeof_gr_complex, "final"+count+".dat"))
        
    def _setup_usrp_sink(self):
        """
        Creates a USRP sink, determines the settings for best bitrate,
        and attaches to the transmitter's subdevice.
        """
        #self.u = usrp2.sink_32fc(self._interface, self._mac_addr)
        # Set up the UHD interface as a transmitter
        self.u = uhd.usrp_sink(device_addr=self.args, stream_args=uhd.stream_args('fc32'))
        #print "Does it get here at all?!!"
        print self.u.get_subdev_spec()
        #self.connect(self, self.u)
        #self.u.set_interp(self._interp)
        if(self._spec):
            self.u.set_subdev_spec(self._spec, 0)

        # Set the antenna
        if(self._ant):
            self.u.set_antenna(self._ant, 0)
        self.u.set_gain(self._gain)
        self.set_freq(self._tx_freq)
        #sps = self.u.get_samp_rate()/self._interp
        print self.set_samp_rate(self._bw)

    def set_gain(self, gain=None):
        if gain is None:
            # if no gain was specified, use the mid-point in dB
            g = self.u.get_gain_range()
            gain = float(g.start()+g.stop())/2
            print "\nNo gain specified."
            print "Setting gain to %f (from [%f, %f])" % \
                (gain, g.start(), g.stop())
        
        self.u.set_gain(gain, 0)
        return gain

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
   
# /////////////////////////////////////////////////////////////////////////////
#                                   main
# /////////////////////////////////////////////////////////////////////////////

def main():

    def send_pkt(payload='', eof=False):
        return tb.txpath.send_pkt(payload, eof)
  
    parser = OptionParser(option_class=eng_option, conflict_handler="resolve")

    parser.add_option("-a", "--args", type="string", default="",
                          help="UHD device address args [default=%default]")
    parser.add_option("", "--spec", type="string", default=None,
                          help="Subdevice of UHD device where appropriate")
    parser.add_option("-A", "--antenna", type="string", default=None,
                          help="select Rx Antenna where appropriate")
    #parser.add_option("-e", "--interface", type="string", default="eth0",
    #                      help="set ethernet interface, [default=%default]")

    #parser.add_option("-m", "--mac-addr", type="string", default="",
    #                      help="set USRP2 MAC address, [default=auto-select]")

    parser.add_option("-f", "--freq", type="eng_float",
                          default = 5.825e9, help="set USRP2 carrier frequency, [default=%default]",
                          metavar="FREQ")
    
    #parser.add_option("-i", "--interp", type="intx", default=5,
    #                      help="set USRP2 interpolation factor, [default=%default]\
	#			5  -> 802.11a/g, OFDM-symbolduration=4us, \
	#			10 -> 802.11p, OFDM-symbolduration=8us")
    parser.add_option("-W", "--bandwidth", type="eng_float",
                          default=1e7,
                          help="set symbol bandwidth [default=%default]\
                20 MHz  -> 802.11a/g, OFDM-symbolduration=4us, \
                10 MHz -> 802.11p, OFDM-symbolduration=8us")

    parser.add_option("-g", "--gain", type="int", default=10 , help = "set USRP2 Tx GAIN in [dB] [default=%default]")

    parser.add_option("", "--regime", type="string", default="1",
                          help="set OFDM coderegime:	[default=%default]\
						1 -> 6 (3) Mbit/s (BPSK r=0.5), \
						2 -> 9 (4.5) Mbit/s (BPSK r=0.75), \
						3 -> 12 (6) Mbit/s (QPSK r=0.5), \
						4 -> 18 (9) Mbit/s (QPSK r=0.75), \
			  			5 -> 24 (12) Mbit/s (QAM16 r=0.5), \
						6 -> 36 (18) Mbit/s (QAM16 r=0.75), \
						7 -> 48 (24) Mbit/s (QAM64 r=0.66), \
						8 -> 54 (27) Mbit/s (QAM64 r=0.75)")

    parser.add_option("-n", "--norm", type="eng_float", default=0.3 , help="set gain factor for complex baseband floats [default=%default]")
		
    parser.add_option("-r", "--repetition", type="int", default=1 , help="set number of frame-copies to send, 0=infinite [default=%default] ")

    parser.add_option("-l", "--log", action="store_true", default=False, help="write debug-output of individual blocks to disk")

    parser.add_option("-p", "--payload", type="string", default="HelloWorld",
                          help="payload ASCII-string to send, [default=%default]")
	
    parser.add_option("", "--lag", type="eng_float", default=0.1,
                          help="lag between contiguous packets being sent, [default=%default]")
    parser.add_option("-b", "--burst-length", type="int", default=1000,
                          help="number of packets being sent in a burst, [default=%default]")
    parser.add_option("-s", "--size", type="eng_float", default=10,
                      help="set packet size [default=%default]")
    parser.add_option("-M", "--megabytes", type="eng_float", default=1.0,
                      help="set megabytes to transmit [default=%default]")
    parser.add_option("","--discontinuous", action="store_true", default=False,
                      help="enable discontinuous mode")
    parser.add_option("","--from-file", default=None,
                      help="use intput file for packet contents")

    (options, args) = parser.parse_args ()

    # This is the ASCII encoded message that will be put into the MSDU (you have to build IP headers on your own if you need them!)
    # Use monitor (promiscuous) mode on the receiver side to see this kind of non-IP frame.
    my_msg = "some arbitrary text as MSDU ASCII payload" #options.payload
    #my_msg = 'A'*1500;

    # build the graph    


    # start flow graph

    # send frame
    n = 0
    while n < options.burst_length:
        n = n + 1         
        tb = my_top_block("1",options, str(n)+my_msg)
        r = gr.enable_realtime_scheduling()
        if r != gr.RT_OK:
            print "Warning: failed to enable realtime scheduling"
        tb.start()
        send_pkt(str(n)+my_msg , eof = False)
        send_pkt("",eof=True)
        tb.wait()    
        time.sleep(options.lag)
    #send_pkt(my_msg , eof = False)
    #send_pkt("",eof = True)

    # wait for it to finish
    
    #tb.stop()    
    #time.sleep(10)
    #my_msg = my_msg + " zzz"
    #tb = my_top_block("2",options, my_msg)
    #tb.start()
    #send_pkt(my_msg , eof = False)
    #send_pkt("",eof = True)
    #tb.wait()

    #tb.stop()    
    #time.sleep(2)
    #my_msg = my_msg + " zzz"
    #tb = my_top_block("2",options, my_msg)
    #tb.start()
    #send_pkt(my_msg , eof = False)
    #send_pkt("",eof = True)
    #tb.wait()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
