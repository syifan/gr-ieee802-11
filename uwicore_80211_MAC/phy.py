
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

import elvOptions
from elvEvent import *;



class receiver_block(gr.top_block):
    def __init__(self, options, hostname,msgq):
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
        self.msg_sink = gr.message_sink(4,msgq,True)
        #self.message_debug = gr.message_debug()
        ##################################################
        # Connections
        ##################################################
        self.connect((self.uhd_usrp_source_0, 0), (self.gr_skiphead_0, 0))
        self.connect((self.gr_skiphead_0, 0), (self.gr_complex_to_mag_squared_0, 0))
        self.connect((self.fir_filter_xxx_0, 0), (self.msg_sink, 0))
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


class PHYLayer(object):

    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((socket.gethostname(), ElvOption.option.PHYport))
        self.server.listen(1)    # PHY is ready to attend MAC requests

        self.socket_client = None

        self.phy_rx_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.phy_rx_server.bind((socket.gethostname(), ElvOption.option.PHYRXport))
        self.phy_rx_server.listen(1)

        self.my_mac = mac.usrp2_node(ElvOption.option.Node)   # Assign the MAC address of the node
        #self.rxclient = threading.Thread(target=RX_Client, args=(options,my_mac,phy_rx_server))
        #self.rxclient.start()
        # Initial values of variables used in time measurement

        self.N_sym_prev=4             # OFDM symbols of the previous packet sent
        self.N_sensings = 0          # Number of power measurements
        self.N_packets = 0          # Number of packets sent
        self.time_socket = 0       # Instant time of socket communication
        self.t_socket_TOTAL = 0      # Total time of socket communication
        self.T_sense_USRP2 = 0     # Time of the USRP2 measuring the power
        self.T_sense_PHY = 0       # Time elapsed in PHY layer due to a carrier sensing request
        self.T_transmit_USRP2 = 0  # USRP2 TX time
        self.T_configure_USRP2 = 0  # Time due to USRP2 graph management
        self.T_transmit_PHY = 0    # Time elapsed in PHY layer due to a packet tx request

        self.msgq = gr.msg_queue(1)

        self.data = buffer()
        self.ack = buffer()
        self.rts = buffer()
        self.cts = buffer()
        self.bcn = buffer()
        self.other = buffer()




        first_time = True               # Is the first time to transmit?
        #fg_cca = sense_block(options)   # Set up the carrier sensing block for the first time.
        self.rb = receiver_block(ElvOption.option, socket.gethostname(), self.msgq)
        self.rb.start()

    def send_pkt(self, puerto, eof=False):
        return self.tb.txpath.send_pkt(puerto, eof)

    def process_data_from_device(self):
        '''Old  RX_Client function'''
        phy_rx_client, phy_rx_addr = self.phy_rx_server.accept()
        while 1:
            # PHY 802.11 frame arrival from the wireless medium
            pkt = phy_rx_client.recv(10000)
            arrived_packet=mac.parse_mac(pkt)
            ElvEvent("Received packet from receive block " + str(arrived_packet))
            print arrived_packet

            if (arrived_packet["HEADER"]=="DATA" or arrived_packet["HEADER"]=="DATA_FRAG"):
                if arrived_packet["DATA"]["INFO"]["mac_add1"] == self.my_mac:  # Is the data packet addressed to this node?
                    self.data.push(arrived_packet["DATA"])
                else:
                    self.other.push("random data")

            if (arrived_packet["HEADER"]=="ACK"):
                if arrived_packet["DATA"]["INFO"]["RX_add"] == self.my_mac:# Is the ACK addressed to this node?
                    self.ack.push(arrived_packet["DATA"])
            if (arrived_packet["HEADER"]=="RTS"):            #It is a RTS
                self.rts.push(arrived_packet["DATA"])
            if (arrived_packet["HEADER"]=="CTS"):            #It is a CTS
                self.cts.push(arrived_packet["DATA"])
            if (arrived_packet["HEADER"]=="BEACON"):         #It is a BEACON
                beacon = arrived_packet["DATA"]
                beacon = beacon["INFO"]
                msg = plcp.new_beacon()
                msg["MAC"]= beacon["mac_add2"]
                msg["timestamp"]=beacon["timestamp"]
                msg["BI"]=beacon["BI"]
                msg["OFFSET"]=time.time() - beacon["timestamp"]
                x = self.bcn.length()
                updated = False

                # Update the beacon list
                for i in range(0,x):
                    if msg["MAC"]==self.bcn.read(i)["MAC"]:
                        self.bcn.remove(i)
                        self.bcn.insert(i,msg)
                        updated = True
                if updated == False:
                    self.bcn.insert(x+1,msg)

            if (arrived_packet["HEADER"]==""):
                print "No packet arrived"

        phy_rx_client.close()

    def print_buffer_status(self):
        print "=========== BUFFER STATUS ==========="
        print "DATA [%i]"%self.data.length()
        print "ACK  [%i]"%self.ack.length()
        print "RTS  [%i]"%self.rts.length()
        print "CTS  [%i]"%self.cts.length()
        print "OTHER  [%i]"%self.other.length()
        print "====================================="
        print "\n\n"

    def print_neighbor_nodes_info(self):
        print "========= NEIGHBOR NODES INFORMATION =========="
        for i in range (0,self.bcn.length()):
            item = self.bcn.read(i)
            print "[MAC = %s]\t [Timestamp = %s]\t [Beacon Interval = %s]\t [OFFSET = %s]" %(mac.which_dir(item["MAC"]),item["timestamp"],item["BI"],item["OFFSET"])
        print "==============================================="

    def print_statistics(self):
        print "===================== Average statistics ===================="
        print "Number of Carrier Sensing Requests = ",self.N_sensings
        if self.N_sensings>0:
            print "Time spent by USRP2 on sensing channel = \t",self.T_sense_USRP2/self.N_sensings
            print "Time spent by PHY layer on sensing channel = \t",self.T_sense_PHY/self.N_sensings
        print "============================================================="
        print "Number of packets transmitted = ",self.N_packets
        if self.N_packets>1:
            print "Time spent by USRP2 on sending a packet = \t",self.T_transmit_USRP2/self.N_packets
            print "Time spent by USRP2 on configuring the graphs\t",self.T_configure_USRP2/self.N_packets
            print "Time spent by PHY on sending a packet = \t",self.T_transmit_PHY/self.N_packets
            print "Time spent on Socket Communication = \t", self.t_socket_TOTAL/self.N_packets
        print "============================================================="

    def process_request_from_mac(self):
        '''
        The Loop that process request from the MAC layers
        '''
        try:
            while 1:
                self.socket_client, conn_addr = self.server.accept()     # Waiting a request from the MAC layer
                arrived_packet=plcp.receive_from_mac(self.socket_client)  # Packet received from MAC

                ElvEvent("Receive packet from mac " + str(arrived_packet))

                if arrived_packet["HEADER"] == "PKT":
                    self.send_packet(arrived_packet);
                # Carrier sensing request
                if (arrived_packet["HEADER"]=="CCA"):
                    self.sense_carrier()
                # MAC requests an incoming packet to the PHY
                if (arrived_packet["HEADER"]=="TAIL"):
                    header_pkt = arrived_packet["DATA"]

                    len_data = self.data.length()
                    len_ack = self.ack.length()
                    len_rts = self.rts.length()
                    len_cts = self.cts.length()

                    if (header_pkt == "DATA") and len_data>0: # There are Data packets?
                        self.data.elements.reverse()
                        x = self.data.read(0)
                        phy_pkt = plcp.create_packet("YES",x)
                        self.data.pop()
                        self.data.elements.reverse()

                    elif header_pkt == "ACK" and len_ack>0:   # There are ACK packets?
                        self.ack.elements.reverse()
                        x = self.ack.read(0)
                        phy_pkt = plcp.create_packet("YES",x)
                        self.ack.pop()
                        self.ack.elements.reverse()

                    elif header_pkt == "RTS" and len_rts>0:   # There are RTS packets?
                        self.rts.elements.reverse()
                        x=self.rts.read(0)
                        phy_pkt = plcp.create_packet("YES",x)
                        self.rts.pop()
                        self.rts.elements.reverse()
                    elif header_pkt == "CTS" and len_cts>0:   # There are CTS packets?
                        self.cts.elements.reverse()
                        x=self.cts.read(0)
                        phy_pkt = plcp.create_packet("YES",x)
                        self.cts.pop()
                        self.cts.elements.reverse()
                    else:                                   # There are not packets
                        phy_pkt = plcp.create_packet("NO",[])
                    plcp.send_to_mac(self.socket_client,phy_pkt)  # Send the result (PHY packet) to MAC layer
        except Exception:
            self.socket_client.close()
            self.socket_client = None

    def sense_carrier(self):
        t_senseA = time.time()
        self.msgq.flush()
        t_reconfig = time.time()-t_senseA
        m=self.msgq.delete_head()
        t = m.to_string()
        msgdata = struct.unpack('%df' % (int(m.arg2()),), t)
        sensed_power=msgdata[0]
        t_senseB = time.time()

        # PHY responds with the power measured to the MAC
        packet=plcp.create_packet("CCA",sensed_power)
        ElvEvent("Send CCA result to MAC "+str(packet))
        if(self.socket_client):
            plcp.send_to_mac(self.socket_client,packet)
        t_senseC = time.time()
        self.T_sense_USRP2 = self.T_sense_USRP2 + (t_senseB - t_senseA)
        self.T_sense_PHY = self.T_sense_PHY + (t_senseC - t_senseA)
        self.N_sensings +=1
        #if ElvOption.option.verbose: print "Time elapsed on graph configuration (Carrier Sensing) = \t", t_reconfig

    def send_packet(self, arrived_packet):
        ElvEvent("Sending a packet " + str(arrived_packet))
        t_socket = time.time()-arrived_packet["DATA"]["INFO"]["timestamp"]
        self.t_socket_TOTAL = self.t_socket_TOTAL + t_socket  # Update the time used in the socket communication

        t_sendA = time.time()
        item = arrived_packet["DATA"]  # Copy the packet to send from the MAC message
        info = item["INFO"]
        N_sym = info["N_sym"] # Read N_sym and add N_sym to options
        mod = info["modulation"]

        ElvOption.option.nsym = N_sym
        ElvOption.option.modulation=mod


        print "Re-setting USRP2 graph!"
        self.tb = transmitter_block(ElvOption.option) # If necessary, update the transmit flow-graph depending to the new OFDM parameters
        r = gr.enable_realtime_scheduling()
        if r != gr.RT_OK:
            print "Warning: failed to enable realtime scheduling"
        t_2 = time.time()
        self.tb.start()                  # Send packet procedure starts
        t_sendB= time.time()
        self.send_pkt(item,eof=False)   # 'item' is a dictionary which contents the packet to transmit and other information
        self.send_pkt("",eof=True)
        t_sendC = time.time()
        self.tb.wait()                   # Wait until USRP2 finishes the TX-graph
        t_sendD= time.time()
        if ElvOption.option.verbose: print "Time elapsed on graph configuration (TX Packet) = \t", (t_sendB - t_2)
        self.T_transmit_USRP2 = self.T_transmit_USRP2 + t_sendC-t_sendB
        self.T_configure_USRP2 = self.T_configure_USRP2 + t_sendD-t_sendA - (t_sendC-t_sendB)
        self.T_transmit_PHY = self.T_transmit_PHY + t_sendD-t_sendA

        # set values for the next packet tx request
        first_time=False
        N_sym_prev = N_sym       # Keep a record of the OFDM symbols' Number
        self.N_packets += 1

    def run(self):
        """
            Start the threads
        """
        ElvEvent("Phy (TX) layer started")
        p1 = threading.Thread(target=self.process_data_from_device)
        p2 = threading.Thread(target=self.process_request_from_mac)
        p1.start()
        p2.start()


def test_send_packet(phy):
    packet = {
        'HEADER': 'PKT',
        'DATA': {
            'INFO': {
                'N_cbps': 48,
                'N_pad': 2,
                'timestamp': 1383849429.010515,
                'modulation': 'bpsk',
                'txtime': 186,
                'N_sym': 18,
                'N_data': 432,
                'packet': '\x08\x00\x00\xba\x00P\xc2\x853\x10\x00P\xc2\x853\x0c\xff\xff\xff\xff\xff\xff\x00\x00PAQUETE_CAPA_SUPERIOR_3',
                'rate': 0.5,
                'MF': 0,
                'packet_len': 51,
                'mac_add1': '\x00P\xc2\x853\x10',
                'N_bpsc': 1,
                'mac_duration': '\x00\xba',
               'mac_add2': '\x00P\xc2\x853\x0c',
                'N_dbps': 24,
                'N_SEQ': 0,
                'PAYLOAD': 'PAQUETE_CAPA_SUPERIOR_3',
                'N_FRAG': 0
            },
            'HEADER': 'DATA',
            'MPDU': '\xd6`@\x00\x00\x10\x00\x00]\x00\nC\xa1\xcc\x08\x00\nC\xa1\xcc0\xff\xff\xff\xff\xff\xff\x00\x00\n\x82\x8a\xaa\xa2*\xa2\xfa\xc2\x82\n\x82\xfa\xca\xaa\n\xa2J\x92\xf2J\xfa\xcc,\x9b\xd0<\x00',
            'LENGTH': 51
        }
    }
    phy.send_packet(packet)

def main():
    parser = elvOptions.ElvOption()
    #options = parser.get_options()
    phy = PHYLayer()
    phy.run()
    while 1:
        test_send_packet(phy)
        #phy.sense_carrier()
        time.sleep(5)


if __name__ == '__main__':

    try:

        main()

    except KeyboardInterrupt:

        pass
