
import time, struct, sys
import socket,pickle, math
from gnuradio import gr, blks2, uhd, eng_notation, optfir, window, filter, fft
from grc_gnuradio import blks2 as grc_blks2
from gnuradio.eng_option import eng_option
from gnuradio.gr import firdes
from gnuradio.filter import firdes
from optparse import OptionParser
from ftw_ofdm import ftw_transmit_path
import uwicore_mpif as plcp
from buffer_lib import Buffer as buffer
import uwicore_mac_utils as mac
import gnuradio.ieee802_11 as gr_ieee802_11
import random
import threading



class receiver_block(gr.top_block):
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
        self.gr_socket_pdu_0 = gr.socket_pdu("TCP_CLIENT", hostname, str(options.PHYRXport), 10000)
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


def RX_Client(options,my_mac,phy_rx_server):
    
    phy_rx_client, phy_rx_addr = phy_rx_server.accept()
    while 1:
        #phy_rx_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #phy_rx_client.connect((socket.gethostname(), options.PHYRXport))

        # PHY 802.11 frame arrival from the wireless medium
        pkt = phy_rx_client.recv(10000)
        arrived_packet=mac.parse_mac(pkt)

        if (arrived_packet["HEADER"]=="DATA" or arrived_packet["HEADER"]=="DATA_FRAG"):
            if arrived_packet["DATA"]["INFO"]["mac_add1"] == my_mac:  # Is the data packet addressed to this node? 
                data.push(arrived_packet["DATA"])        
            else:
                other.push("random data")
                               
        if (arrived_packet["HEADER"]=="ACK"):
            if arrived_packet["DATA"]["INFO"]["RX_add"] == my_mac:# Is the ACK addressed to this node?
                ack.push(arrived_packet["DATA"])
        if (arrived_packet["HEADER"]=="RTS"):            #It is a RTS
            rts.push(arrived_packet["DATA"])                       
        if (arrived_packet["HEADER"]=="CTS"):            #It is a CTS
            cts.push(arrived_packet["DATA"])                       
        if (arrived_packet["HEADER"]=="BEACON"):         #It is a BEACON
            beacon = arrived_packet["DATA"]
            beacon = beacon["INFO"]
            msg = plcp.new_beacon()
            msg["MAC"]= beacon["mac_add2"]
            msg["timestamp"]=beacon["timestamp"]
            msg["BI"]=beacon["BI"]
            msg["OFFSET"]=time.time() - beacon["timestamp"] 
            x = bcn.length()
            updated = False
            
            # Update the beacon list
            for i in range(0,x):
                if msg["MAC"]==bcn.read(i)["MAC"]:
                    bcn.remove(i)
                    bcn.insert(i,msg)
                    updated = True
            if updated == False:
                bcn.insert(x+1,msg)
                    
        if (arrived_packet["HEADER"]==""):   
            print "No packet arrived"
        
        #DEBUG
        print "=========== BUFFER STATUS ==========="
        print "DATA [%i]"%data.length()
        print "ACK  [%i]"%ack.length()
        print "RTS  [%i]"%rts.length()
        print "CTS  [%i]"%cts.length()
        print "OTHER  [%i]"%other.length()
        print "====================================="
        print "\n\n"
        
        # Beacon list
        print "========= NEIGHBOR NODES INFORMATION =========="
        for i in range (0,bcn.length()):
            item = bcn.read(i)
            print "[MAC = %s]\t [Timestamp = %s]\t [Beacon Interval = %s]\t [OFFSET = %s]" %(mac.which_dir(item["MAC"]),item["timestamp"],item["BI"],item["OFFSET"])
        print "==============================================="                    
    phy_rx_client.close()



data = buffer()
ack = buffer()
rts = buffer()
cts = buffer()
bcn = buffer()
other=buffer()

def main():
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    parser.add_option("-a", "--args", type="string", default="",
                          help="UHD device address args [default=%default]")
    parser.add_option("", "--spec", type="string", default=None,
                          help="Subdevice of UHD device where appropriate")
    parser.add_option("-A", "--antenna", type="string", default=None,
                          help="select Rx Antenna where appropriate")
    parser.add_option("-f", "--freq", type="eng_float",
                          default = 5.825e9, help="set USRP2 carrier frequency, [default=%default]",
                          metavar="FREQ")
    parser.add_option("-w", "--window-size", type="int", default=48 , help = "set fir filter tap size [default=%default]")
    parser.add_option("-s", "--sync-length", type="int", default=256 , help = "sync length [default=%default]")
    parser.add_option("-W", "--bandwidth", type="eng_float", default=1e7, help="set symbol bandwidth [default=%default]\
                20 MHz  -> 802.11a/g, OFDM-symbol duration=4us, 10 MHz -> 802.11p, OFDM-symbolduration=8us")
    parser.add_option("-g", "--gain", type="int", default=0 , help = "set USRP2 Rx GAIN in [dB] [default=%default]")

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

    parser.add_option("-n", "--norm", type="eng_float", default=0.3 , help="set gain factor for complex baseband floats [default=%default]")
    parser.add_option("-N", "--Node", type="intx", default=1, help="USRP2 node    [default=%default]")

    parser.add_option("-r", "--repetition", type="int", default=1 , help="set number of frame-copies to send, 0=infinite [default=%default] ")

    parser.add_option("-l", "--log", action="store_true", default=False, help="write debug-output of individual blocks to disk")

    parser.add_option("", "--PHYRXport", type="int", default=8513 , help="Port used for PHY RX [default=%default] ")
    parser.add_option("", "--PHYport", type="int", default=8013 , help="Port used for MAC-->PHY communication [default=%default] ")

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
                        help="Print timing information, [default=%default]")
    
    parser.add_option("", "--nsym", type="int", default=1)
    parser.add_option("", "--modulation", type="string", default="bpsk")
    (options, args) = parser.parse_args()


    phy_rx_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    phy_rx_server.bind((socket.gethostname(), options.PHYRXport))
    phy_rx_server.listen(1)

    my_mac = mac.usrp2_node(options.Node)   # Assign the MAC address of the node
    rxclient = threading.Thread(target=RX_Client, args=(options,my_mac,phy_rx_server))
    rxclient.start()

    rb = receiver_block(options,socket.gethostname())
    rb.start()

    while 1:
        len_other=other.length()
        if (len_other>0): 
            other.elements.reverse()
            x=other.read(0)
            other.pop()
            other.elements.reverse()
            print x
            #rb.stop()
            #rb.wait()
            #rb.start()

            
    rb.stop()
    rb.wait()
        

if __name__ == '__main__':

    try:

        main()

    except KeyboardInterrupt:

        pass
