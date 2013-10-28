
#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <gnuradio/ieee802_11/ofdm_symbol_repeater.h>
#include <gnuradio/gr_io_signature.h>
#include <stdexcept>
#include <iostream>
#include <string.h>

using namespace gr::ieee802_11;
class ofdm_symbol_repeater_impl : public ofdm_symbol_repeater
{

private:
  int d_symbol_length;
  int d_repetition;
  int d_N_symbols;


public:
	ofdm_symbol_repeater_impl (int symbol_length, int repetition, int N_symbols,bool debug)
	    :	gr_block("repetition",
	    	gr_make_io_signature(1, 1, sizeof(gr_complex)*(symbol_length)),
	    	gr_make_io_signature(1, 1, sizeof(gr_complex)*symbol_length)),
	    	d_symbol_length(symbol_length),
	    	d_repetition(repetition),d_N_symbols(N_symbols)
	{
	  set_output_multiple((d_N_symbols + 5 + 13));
	}
  ~ofdm_symbol_repeater_impl(){}
  int general_work (int noutput_items,
		  gr_vector_int &ninput_items_v,
		  gr_vector_const_void_star &input_items,
		  gr_vector_void_star &output_items)
  {
	const gr_complex *in_sym = (const gr_complex *) input_items[0];

	gr_complex *out_sym = (gr_complex *) output_items[0];
	int no = 0;	// number of output items
	int ni = 0;	// number of items read from input
	int counter=0;
	while(no < noutput_items){
		memcpy(&out_sym[no * d_symbol_length],
		&in_sym[(ni %(d_N_symbols + 5 + 13)) * d_symbol_length],
		d_symbol_length * sizeof(gr_complex));
		no++;
		ni++;
	}
	counter++;
	if ((counter==d_repetition)&&(d_repetition!=0))
		consume_each(d_N_symbols + 5 + 13);
	return no ;
  }

};


ofdm_symbol_repeater::sptr
ofdm_symbol_repeater::make(int symbol_length, int repetition, int N_symbols,bool debug) {
	return gnuradio::get_initial_sptr(new ofdm_symbol_repeater_impl(symbol_length,repetition,N_symbols,debug));
}
