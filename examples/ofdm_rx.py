#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Ofdm Rx
# Generated: Thu Sep 26 17:45:34 2013
##################################################

from gnuradio import eng_notation
from gnuradio import fft
from gnuradio import filter
from gnuradio import gr
from gnuradio import uhd
from gnuradio import window
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio.gr import firdes
from gnuradio.wxgui import forms
from grc_gnuradio import wxgui as grc_wxgui
from optparse import OptionParser
import gnuradio.ieee802_11 as gr_ieee802_11
import wx

class ofdm_rx(grc_wxgui.top_block_gui):

	def __init__(self):
		grc_wxgui.top_block_gui.__init__(self, title="Ofdm Rx")

		##################################################
		# Variables
		##################################################
		self.window_size = window_size = 48
		self.sync_length = sync_length = 320 - 64
		self.samp_rate = samp_rate = 10e6
		self.gain = gain = 0
		self.freq = freq = 5.825e9

		##################################################
		# Blocks
		##################################################
		self._samp_rate_chooser = forms.radio_buttons(
			parent=self.GetWin(),
			value=self.samp_rate,
			callback=self.set_samp_rate,
			label="Sample Rate",
			choices=[10e6, 20e6],
			labels=["10 Mhz", "20 Mhz"],
			style=wx.RA_HORIZONTAL,
		)
		self.Add(self._samp_rate_chooser)
		_gain_sizer = wx.BoxSizer(wx.VERTICAL)
		self._gain_text_box = forms.text_box(
			parent=self.GetWin(),
			sizer=_gain_sizer,
			value=self.gain,
			callback=self.set_gain,
			label='gain',
			converter=forms.float_converter(),
			proportion=0,
		)
		self._gain_slider = forms.slider(
			parent=self.GetWin(),
			sizer=_gain_sizer,
			value=self.gain,
			callback=self.set_gain,
			minimum=0,
			maximum=100,
			num_steps=100,
			style=wx.SL_HORIZONTAL,
			cast=float,
			proportion=1,
		)
		self.Add(_gain_sizer)
		self._freq_chooser = forms.drop_down(
			parent=self.GetWin(),
			value=self.freq,
			callback=self.set_freq,
			label="Channel",
			choices=[2412000000.0, 2417000000.0, 2422000000.0, 2427000000.0, 2432000000.0, 2437000000.0, 2442000000.0, 2447000000.0, 2452000000.0, 2457000000.0, 2462000000.0, 2467000000.0, 2472000000.0, 2484000000.0, 5170000000.0, 5180000000.0, 5190000000.0, 5200000000.0, 5210000000.0, 5220000000.0, 5230000000.0, 5240000000.0, 5260000000.0, 5280000000.0, 5300000000.0, 5320000000.0, 5500000000.0, 5520000000.0, 5540000000.0, 5560000000.0, 5580000000.0, 5600000000.0, 5620000000.0, 5640000000.0, 5660000000.0, 5680000000.0, 5700000000.0, 5745000000.0, 5765000000.0, 5785000000.0, 5805000000.0, 5825000000.0, 5860000000.0, 5870000000.0, 5880000000.0, 5890000000.0, 5900000000.0, 5910000000.0, 5920000000.0],
			labels=['  1 | 2412.0 | 11g', '  2 | 2417.0 | 11g', '  3 | 2422.0 | 11g', '  4 | 2427.0 | 11g', '  5 | 2432.0 | 11g', '  6 | 2437.0 | 11g', '  7 | 2442.0 | 11g', '  8 | 2447.0 | 11g', '  9 | 2452.0 | 11g', ' 10 | 2457.0 | 11g', ' 11 | 2462.0 | 11g', ' 12 | 2467.0 | 11g', ' 13 | 2472.0 | 11g', ' 14 | 2484.0 | 11g', ' 34 | 5170.0 | 11a', ' 36 | 5180.0 | 11a', ' 38 | 5190.0 | 11a', ' 40 | 5200.0 | 11a', ' 42 | 5210.0 | 11a', ' 44 | 5220.0 | 11a', ' 46 | 5230.0 | 11a', ' 48 | 5240.0 | 11a', ' 52 | 5260.0 | 11a', ' 56 | 5280.0 | 11a', ' 58 | 5300.0 | 11a', ' 60 | 5320.0 | 11a', '100 | 5500.0 | 11a', '104 | 5520.0 | 11a', '108 | 5540.0 | 11a', '112 | 5560.0 | 11a', '116 | 5580.0 | 11a', '120 | 5600.0 | 11a', '124 | 5620.0 | 11a', '128 | 5640.0 | 11a', '132 | 5660.0 | 11a', '136 | 5680.0 | 11a', '140 | 5700.0 | 11a', '149 | 5745.0 | 11a', '153 | 5765.0 | 11a', '157 | 5785.0 | 11a', '161 | 5805.0 | 11a', '165 | 5825.0 | 11a', '172 | 5860.0 | 11p', '174 | 5870.0 | 11p', '176 | 5880.0 | 11p', '178 | 5890.0 | 11p', '180 | 5900.0 | 11p', '182 | 5910.0 | 11p', '184 | 5920.0 | 11p'],
		)
		self.Add(self._freq_chooser)
		self.uhd_usrp_source_0 = uhd.usrp_source(
			device_addr="",
			stream_args=uhd.stream_args(
				cpu_format="fc32",
				channels=range(1),
			),
		)
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
		self.gr_socket_pdu_0 = gr.socket_pdu("UDP_SERVER", "", "12345", 10000)
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
		self._samp_rate_chooser.set_value(self.samp_rate)

	def get_gain(self):
		return self.gain

	def set_gain(self, gain):
		self.gain = gain
		self.uhd_usrp_source_0.set_gain(self.gain, 0)
		self._gain_slider.set_value(self.gain)
		self._gain_text_box.set_value(self.gain)

	def get_freq(self):
		return self.freq

	def set_freq(self, freq):
		self.freq = freq
		self.uhd_usrp_source_0.set_center_freq(self.freq, 0)
		self._freq_chooser.set_value(self.freq)

if __name__ == '__main__':
	parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
	(options, args) = parser.parse_args()
	tb = ofdm_rx()
	tb.Run(True)

