#!/usr/bin/env python

# Copyright 2005,2007 Free Software Foundation, Inc.
 
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

# Filename: usrp2_spectrum_sense.py

# This script executes a set of power measurements using the USRP2 and the uwicore_80211_MAC code. 
# It has been developed by the Uwicore Laboratory at the University Miguel Hernandez of Elche, 
# taking as starting point the example 'usrp_spectrum_sense' provided by GNU Radio. More detailed 
# information can be found at www.uwicore.umh.es/mhop-testbeds.html or at the publication:

#J.R. Gutierrez-Agullo, B. Coll-Perales and J. Gozalvez, "An IEEE 802.11 MAC Software Defined Radio Implementation for  Experimental Wireless Communications and Networking Research", Proceedings of the 2010 IFIP/IEEE Wireless Days (WD'10), pp. 1-5, 20-22 October 2010, Venice (Italy).

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


from gnuradio import gr, gru, eng_notation, optfir, window
from gnuradio import usrp2
from gnuradio.eng_option import eng_option
from optparse import OptionParser
import sys
import math, numpy
import struct,time


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
        frequency, and returns the new frequency as its result.
        """
        try:
            # We use this try block so that if something goes wrong from here 
            # down, at least we'll have a prayer of knowing what went wrong.
            # Without this, you get a very mysterious:
            #
            #   terminate called after throwing an instance of 'Swig::DirectorMethodException'
            #   Aborted
            #
            # message on stderr.  Not exactly helpful ;)

            new_freq = self.tb.set_next_freq()
            return new_freq

        except Exception, e:
            print "tune: Exception: ", e


class parse_msg(object):
    def __init__(self, msg):
        self.center_freq = msg.arg1()
        self.vlen = int(msg.arg2())
        
        assert(msg.length() == self.vlen * gr.sizeof_float)

        # FIXME consider using Numarray or NumPy vector
        t = msg.to_string()
        self.raw_data = t
        self.data = struct.unpack('%df' % (self.vlen,), t)


class my_top_block(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self)

        usage = "usage: %prog [options] min_freq max_freq"
        parser = OptionParser(option_class=eng_option, usage=usage)
        parser.add_option("-R", "--rx-subdev-spec", type="subdev", default=(0,0),
                          help="select USRP Rx side A or B (default=A)")
        parser.add_option("-g", "--gain", type="eng_float", default=None,
                          help="set gain in dB (default is midpoint)")
        parser.add_option("", "--tune-delay", type="eng_float", default=1e-4, metavar="SECS",
                          help="time to delay (in seconds) after changing frequency [default=%default]")
        parser.add_option("", "--dwell-delay", type="eng_float", default=1e-3, metavar="SECS",
                          help="time to dwell (in seconds) at a given frequncy [default=%default]")
        parser.add_option("-F", "--fft-size", type="int", default=256,
                          help="specify number of FFT bins [default=%default]")
        parser.add_option("-d", "--decim", type="intx", default=16,
                          help="set decimation to DECIM [default=%default]")
        parser.add_option("", "--real-time", action="store_true", default=False,
                          help="Attempt to enable real-time scheduling")
        parser.add_option("-f", "--freq", type="eng_float",
                          default = 5.2e9, help="set USRP2 carrier frequency, [default=%default]",
                          metavar="FREQ")
        
        (options, args) = parser.parse_args()
        #if len(args) != 2:
            #parser.print_help()
            #sys.exit(1)
        #self.min_freq = eng_notation.str_to_num(args[0])
        #self.max_freq = eng_notation.str_to_num(args[1])
        self.min_freq = options.freq
        self.max_freq = options.freq

        if self.min_freq > self.max_freq:
            self.min_freq, self.max_freq = self.max_freq, self.min_freq   # swap them

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

      #build graph
        
        self.u = usrp2.source_32fc()
        adc_rate = self.u.adc_rate()              # 64 MS/s
        usrp2_decim = options.decim
        self.u.set_decim(usrp2_decim)
        usrp2_rate = adc_rate / usrp2_decim

        #self.u.set_mux(usrp.determine_rx_mux_value(self.u, options.rx_subdev_spec))
        #self.subdev = usrp.selected_subdev(self.u, options.rx_subdev_spec)
        #print "Using RX d'board %s" % (self.subdev.side_and_name(),)


	s2v = gr.stream_to_vector(gr.sizeof_gr_complex, self.fft_size)

        mywindow = window.blackmanharris(self.fft_size)
        fft = gr.fft_vcc(self.fft_size, True, mywindow)
        power = 0
        for tap in mywindow:
            power += tap*tap
            
        c2mag = gr.complex_to_mag_squared(self.fft_size)

        # FIXME the log10 primitive is dog slow
        log = gr.nlog10_ff(10, self.fft_size,
                           -20*math.log10(self.fft_size)-10*math.log10(power/self.fft_size))
		
        # Set the freq_step to 75% of the actual data throughput.
        # This allows us to discard the bins on both ends of the spectrum.

        self.freq_step = 0.75 * usrp2_rate
        self.min_center_freq = self.min_freq + self.freq_step/2
        nsteps = math.ceil((self.max_freq - self.min_freq) / self.freq_step)
        self.max_center_freq = self.min_center_freq + (nsteps * self.freq_step)

        self.next_freq = self.min_center_freq
        
        tune_delay  = max(0, int(round(options.tune_delay * usrp2_rate / self.fft_size)))  # in fft_frames
        dwell_delay = max(1, int(round(options.dwell_delay * usrp2_rate / self.fft_size))) # in fft_frames

        self.msgq = gr.msg_queue(16)
        self._tune_callback = tune(self)        # hang on to this to keep it from being GC'd
        stats = gr.bin_statistics_f(self.fft_size, self.msgq,
                                    self._tune_callback, tune_delay, dwell_delay)

        # FIXME leave out the log10 until we speed it up
	#self.connect(self.u, s2v, fft, c2mag, log, stats)
	self.connect(self.u, s2v, fft, c2mag, stats)

        if options.gain is None:
            # if no gain was specified, use the mid-point in dB
            g = self.u.gain_range()
            #options.gain = float(g[0]+g[1])/2
            options.gain = max(min(options.gain, g[1]), g[0] )

        self.u.set_gain(options.gain)
	#print "gain =", options.gain


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
    #while 1:
    t_inicial = time.time()
    
    # Get the next message sent from the C++ code (blocking call).
    # It contains the center frequency and the mag squared of the fft
    m = parse_msg(tb.msgq.delete_head())
    a = m.data
    maximo = 0
    for i in range (0,m.vlen):
        maximo = maximo + m.data[i]
        #print "Element",i,"==",m.data[i]
    # Print center freq so we know that something is happening...
    #print "FFT size= ", tb.fft_size
    #print "", maximo
    #print "Frequency = ",m.center_freq, "\t Potencia (W) = ", maximo/tb.fft_size
    potencia = maximo/tb.fft_size
    #print "Power (dBw)", 10*math.log10(potencia), "\t Time elapsed = ",(time.time()-t_inicial)
    return potencia

	#ORIGINAL from USRP_SPECTRUM_SENSE
    #array = numpy.fromstring (m.data, numpy.float32)
    #print array
    # m.data are the mag_squared of the fft output (they are in the
    # standard order.  I.e., bin 0 == DC.)
    # You'll probably want to do the equivalent of "fftshift" on them
    # m.raw_data is a string that contains the binary floats.
    # You could write this as binary to a file.

        
if __name__ == '__main__':
    tb = my_top_block()
    n_trials = 1000     # Number of power measurements to perform
    try:
        tb.start()      # start executing flow graph in another thread...
        while n_trials>0:        
            x=main_loop(tb)
            print "Power (dBw)", 10*math.log10(x)
            n_trials-=1
        tb.stop()
        
    except KeyboardInterrupt:
        pass
