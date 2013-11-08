from optparse import OptionParser
from gnuradio.eng_option import eng_option


class ElvOption(object):

    option = None

    def __init__(self):
        self.parser = OptionParser(option_class=eng_option)
        self.parser.add_option("-a", "--args", type="string", default="",
                              help="UHD device address args [default=%default]")
        self.parser.add_option("", "--spec", type="string", default=None,
                              help="Subdevice of UHD device where appropriate")
        self.parser.add_option("-A", "--antenna", type="string", default=None,
                              help="select Rx Antenna where appropriate")
        self.parser.add_option("-f", "--freq", type="eng_float",
                              default = 5.825e9, help="set USRP2 carrier frequency, [default=%default]",
                              metavar="FREQ")
        self.parser.add_option("-w", "--window-size", type="int", default=48 ,
                            help = "set fir filter tap size [default=%default]")
        self.parser.add_option("-s", "--sync-length", type="int", default=256 ,
                            help = "sync length [default=%default]")
        self.parser.add_option("-W", "--bandwidth", type="eng_float", default=1e7,
                            help="set symbol bandwidth [default=%default]\
                                20 MHz  -> 802.11a/g, OFDM-symbol duration=4us, \
                                10 MHz -> 802.11p, OFDM-symbolduration=8us")
        self.parser.add_option("-g", "--gain", type="int", default=0 ,
                            help = "set USRP2 Rx GAIN in [dB] [default=%default]")

        self.parser.add_option("", "--regime", type="string", default="1",
                              help="set OFDM coderegime,    [default=%default]\
                                    1 -> 6 (3) Mbit/s (BPSK r=0.5), \
                                    2 -> 9 (4.5) Mbit/s (BPSK r=0.75), \
                                    3 -> 12 (6) Mbit/s (QPSK r=0.5), \
                                    4 -> 18 (9) Mbit/s (QPSK r=0.75), \
                                    5 -> 24 (12) Mbit/s (QAM16 r=0.5), \
                                    6 -> 36 (18) Mbit/s (QAM16 r=0.75), \
                                    7 -> 48 (24) Mbit/s (QAM64 r=0.66), \
                                    8 -> 54 (27) Mbit/s (QAM64 r=0.75)")

        self.parser.add_option("-G", "--txgain", type="int", default=10 ,
                            help = "set USRP2 Tx GAIN in [dB] [default=%default]")

        self.parser.add_option("-n", "--norm", type="eng_float", default=0.3 ,
                            help="set gain factor for complex baseband floats [default=%default]")
        self.parser.add_option("-N", "--Node", type="intx", default=1,
                            help="USRP2 node    [default=%default]")

        self.parser.add_option("-r", "--repetition", type="int", default=1 ,
                            help="set number of frame-copies to send, 0=infinite [default=%default] ")

        self.parser.add_option("-l", "--log", action="store_true", default=False,
                            help="write debug-output of individual blocks to disk")

        self.parser.add_option("", "--PHYRXport", type="int", default=8513 ,
                            help="Port used for PHY RX [default=%default] ")
        self.parser.add_option("", "--PHYport", type="int", default=8013 ,
                            help="Port used for MAC-->PHY communication [default=%default] ")
        self.parser.add_option("", "--MACport", type="intx", default=8001,
                          help="MAC communication socket port, [default=%default]")

        self.parser.add_option("", "--real-time", action="store_true", default=False,
                            help="Attempt to enable real-time scheduling [default=%default]")

        self.parser.add_option('-v', "--verbose", action="store_true", default=True,
                            help="Print timing information, [default=%default]")

        self.parser.add_option("", "--nsym", type="int", default=1)
        self.parser.add_option("", "--modulation", type="string", default="bpsk")

        self.parser.add_option("-i", "--interp", type="intx", default=10,
                            help="USRP2 interpolation factor value, [default=%default]\
                                    5  -> 802.11a/g, OFDM T_Symbol=4us, \
                                    10 -> 802.11p, OFDM T_Symbol=8us")

        self.parser.add_option("", "--beta", type="float", default=1e6,
                          help="Scaling Time Parameter, [default=%default]")
        self.parser.add_option("-t", "--time_slot", type="float", default=9e-6,
                          help="Time slot value, [default=%default]")
        self.parser.add_option("-B", "--BI", type="float", default=1,
                          help="Beacon Interval (BI) value in seconds, [default=%default]")
        self.parser.add_option("-S", "--SIFS", type="float", default=16e-6,
                          help="Short Inter-frame space (SIFS) value, [default=%default]")
        self.parser.add_option('', "--retx", action="store_true", default=False,
                        help="Retransmissions enabled, [default=%default]")
        self.parser.add_option('', "--RTS", action="store_true", default=True,
                        help="RTS-threshold enabled, [default=%default]")

        (self.options, self.args) = self.parser.parse_args()
        ElvOption.option = self.options

    def get_options(self):
        return self.options

