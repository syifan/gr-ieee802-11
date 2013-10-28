from gnuradio import eng_notation
from gnuradio import fft
from gnuradio import filter
from gnuradio import gr
from gnuradio import uhd
from gnuradio import window
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio.gr import firdes
from optparse import OptionParser
import gnuradio.ieee802_11 as gr_ieee802_11
#import pmt_swig as pmt
import socket

class real_phy_rx(gr.top_block):
    def __init__(self, options, hostname):
        gr.top_block.__init__(self)

        ##################################################
        # Variables
        ##################################################
        window_size = options.window_size
        sync_length = options.sync_length
        gain = options.gain
        freq = options.freq
        samp_rate = options.bandwidth
        self.uhd_usrp_source_0 = uhd.usrp_source(device_addr="", stream_args=uhd.stream_args(cpu_format="fc32", channels=range(1)))

        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_center_freq(freq, 0)
        self.uhd_usrp_source_0.set_gain(gain, 0)
        self.ieee802_1_ofdm_sync_short_0 = gr_ieee802_11.ofdm_sync_short(0.8, 80 * 80, 2, False)
        self.ieee802_1_ofdm_sync_long_0 = gr_ieee802_11.ofdm_sync_long(sync_length, 100, False)
        self.ieee802_1_ofdm_equalize_symbols_0 = gr_ieee802_11.ofdm_equalize_symbols(False)
        self.ieee802_1_ofdm_decode_signal_0 = gr_ieee802_11.ofdm_decode_signal(False)
        self.ieee802_1_ofdm_decode_mac_0 = gr_ieee802_11.ofdm_decode_mac(False)
        self.ieee802_11_ofdm_parse_mac_0 = gr_ieee802_11.ofdm_parse_mac(True)
        self.gr_stream_to_vector_0 = gr.stream_to_vector(gr.sizeof_gr_complex*1, 64)
        self.gr_socket_pdu_0 = gr.socket_pdu("TCP_CLIENT", hostname, str(options.PHYport), 10000)
        self.gr_skiphead_0 = gr.skiphead(gr.sizeof_gr_complex*1, 20000000)
        self.gr_multiply_xx_0 = gr.multiply_vcc(1)
        self.gr_divide_xx_0 = gr.divide_ff(1)
        self.gr_delay_0_0 = gr.delay(gr.sizeof_gr_complex*1, sync_length)
        self.gr_delay_0 = gr.delay(gr.sizeof_gr_complex*1, 16)
        self.gr_conjugate_cc_0 = gr.conjugate_cc()
        self.gr_complex_to_mag_squared_0 = gr.complex_to_mag_squared(1)
        self.gr_complex_to_mag_0 = gr.complex_to_mag(1)
        self.fir_filter_xxx_0_0 = filter.fir_filter_ccf(1, ([1]*window_size))
        self.fir_filter_xxx_0 = filter.fir_filter_fff(1, ([1]*window_size))
        self.fft_vxx_0 = fft.fft_vcc(64, True, (), True, 1)
        self.message_debug = gr.message_debug()
        ##################################################
        # Connections
        ##################################################
        self.connect((self.uhd_usrp_source_0, 0), (self.gr_skiphead_0, 0))
        self.connect((self.gr_skiphead_0, 0), (self.gr_complex_to_mag_squared_0, 0))
        self.connect((self.fir_filter_xxx_0, 0), (self.gr_divide_xx_0, 1))
        self.connect((self.gr_complex_to_mag_squared_0, 0), (self.fir_filter_xxx_0, 0))
        self.connect((self.gr_skiphead_0, 0), (self.gr_multiply_xx_0, 0))
        self.connect((self.gr_conjugate_cc_0, 0), (self.gr_multiply_xx_0, 1))
        self.connect((self.gr_complex_to_mag_0, 0), (self.gr_divide_xx_0, 0))
        self.connect((self.gr_multiply_xx_0, 0), (self.fir_filter_xxx_0_0, 0))
        self.connect((self.fir_filter_xxx_0_0, 0), (self.gr_complex_to_mag_0, 0))
        self.connect((self.gr_skiphead_0, 0), (self.gr_delay_0, 0))
        self.connect((self.gr_delay_0, 0), (self.gr_conjugate_cc_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.ieee802_1_ofdm_equalize_symbols_0, 0))
        self.connect((self.ieee802_1_ofdm_equalize_symbols_0, 0), (self.ieee802_1_ofdm_decode_signal_0, 0))
        self.connect((self.ieee802_1_ofdm_decode_signal_0, 0), (self.ieee802_1_ofdm_decode_mac_0, 0))
        self.connect((self.ieee802_1_ofdm_sync_short_0, 0), (self.gr_delay_0_0, 0))
        self.connect((self.gr_delay_0, 0), (self.ieee802_1_ofdm_sync_short_0, 0))
        self.connect((self.gr_divide_xx_0, 0), (self.ieee802_1_ofdm_sync_short_0, 1))
        self.connect((self.gr_delay_0_0, 0), (self.ieee802_1_ofdm_sync_long_0, 1))
        self.connect((self.ieee802_1_ofdm_sync_short_0, 0), (self.ieee802_1_ofdm_sync_long_0, 0))
        self.connect((self.ieee802_1_ofdm_sync_long_0, 0), (self.gr_stream_to_vector_0, 0))
        self.connect((self.gr_stream_to_vector_0, 0), (self.fft_vxx_0, 0))

        ##################################################
        # Asynch Message Connections
        ##################################################
        self.msg_connect(self.ieee802_1_ofdm_decode_mac_0, "out", self.ieee802_11_ofdm_parse_mac_0, "in")
        self.msg_connect(self.ieee802_11_ofdm_parse_mac_0, "out", self.gr_socket_pdu_0, "pdus")
        #self.msg_connect(self.ieee802_11_ofdm_parse_mac_0, "out", self.message_debug, "print")
	#self.msg_connect(self.ieee802_11_ofdm_parse_mac_0, "out", self.message_debug, "store")
            

    def get_window_size(self):
        return self.window_size

    def set_window_size(self, window_size):
        self.window_size = window_size
        self.fir_filter_xxx_0_0.set_taps(([1]*self.window_size))
        self.fir_filter_xxx_0.set_taps(([1]*self.window_size))

    def get_sync_length(self):
        return self.sync_length

    def set_sync_length(self, sync_length):
        self.sync_length = sync_length
        self.gr_delay_0_0.set_delay(self.sync_length)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.uhd_usrp_source_0.set_gain(self.gain, 0)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.uhd_usrp_source_0.set_center_freq(self.freq, 0)

def main():
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    parser.add_option("-f", "--freq", type="eng_float",
                          default = 5.825e9, help="set USRP2 carrier frequency, [default=%default]",
                          metavar="FREQ")
    parser.add_option("-w", "--window-size", type="int", default=48 , help = "set fir filter tap size [default=%default]")
    parser.add_option("-s", "--sync-length", type="int", default=256 , help = "sync length [default=%default]")
    parser.add_option("-W", "--bandwidth", type="eng_float", default=1e7, help="set symbol bandwidth [default=%default]\
                20 MHz  -> 802.11a/g, OFDM-symbol duration=4us, 10 MHz -> 802.11p, OFDM-symbolduration=8us")
    parser.add_option("-g", "--gain", type="int", default=0 , help = "set USRP2 Rx GAIN in [dB] [default=%default]")
    parser.add_option("", "--PHYport", type="int", default=8500 , help="Socket port [default=%default] ")
    (options, args) = parser.parse_args()

    s = socket.socket()
    host = socket.gethostname() # Get local machine name
#    port = options.PHYport                # Reserve a port for your service.
#    s.bind(("", port))
#    s.listen(1)
    
    tb = real_phy_rx(options,host)
    tb.start()
    #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #s.connect((socket.gethostname(), 12345))
    #i = 0
    #while True:
    #    if tb.message_debug.num_messages() <=i :
    #        print tb.message_debug.num_messages()
    #        continue
    #    i = i + 1
    #    print i	
    #    paquete = self.message_debug.get_message(i)
    #    s.send(paquete)
#    while 1:
#        server,data=s.accept()
#        data= server.recv(65536)
#        print data
#        if data == "0000":
#            print "close session command received"
#            server.close()
#            s.close()
#            break                     # Close the socket when done
    tb.wait()

if __name__ == '__main__':

    try:

        main()

    except KeyboardInterrupt:

        pass
