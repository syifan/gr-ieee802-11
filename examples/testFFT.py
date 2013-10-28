

from gnuradio import gr
from gnuradio import eng_notation
from gnuradio.eng_option import eng_option
from optparse import OptionParser

class my_top_block(gr.top_block):
    def __init__(self, options):
        gr.top_block.__init__(self)
        
        self._fft_length = 64
        win = []
        self.source = gr.file_source(gr.sizeof_gr_complex * self._fft_length, options.from_file)
        self.ifft = gr.fft_vcc(self._fft_length, True, win, False)
        self.sink = gr.file_sink(gr.sizeof_gr_complex * self._fft_length, options.to_file)
        self.connect(self.source,self.ifft,self.sink)    
        #self.connect(self.ifft, gr.file_sink(gr.sizeof_gr_complex * self._fft_length, "ofdm_ifft_test.dat"))

        



def main():    
    parser = OptionParser(option_class=eng_option, conflict_handler="resolve")
    parser.add_option("","--from-file", default="ofdm_carrier_mapper.dat",
                      help="use intput file for packet contents")
    parser.add_option("","--to-file", default="ofdm_ifft_test.dat",
                      help="Output file for modulated samples")
    (options, args) = parser.parse_args ()
    tb = my_top_block(options)
    tb.start()
    
    
    tb.wait()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
        