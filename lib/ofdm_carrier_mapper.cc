#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/ieee802_11/ofdm_carrier_mapper.h>
#include <gnuradio/gr_io_signature.h>
#include <iostream>
#include <stdexcept>
#include <string.h>

using namespace gr::ieee802_11;
/*
 * Specify constraints on number of input and output streams.
 * This info is used to construct the input and output signatures
 * (2nd & 3rd args to gr_block's constructor).  The input and
 * output signatures are used by the runtime system to
 * check that a valid number and type of inputs and outputs
 * are connected to this block.  In this case, we accept
 * only 1 input and 1 output.
 */
static const int MIN_IN = 1;	// mininum number of input streams
static const int MAX_IN = 1;	// maximum number of input streams
static const int MIN_OUT = 1;	// minimum number of output streams
static const int MAX_OUT = 1;	// maximum number of output streams


class ofdm_carrier_mapper_impl : public ofdm_carrier_mapper
{
public:
	ofdm_carrier_mapper_impl (int fft_size, int tones, bool debug) // tones should be 48 subcarriers + 4 pilots + dc = 53
	  : gr_block ("ofdm_carrier_mapper",
		      gr_make_io_signature (MIN_IN, MAX_IN, tones * sizeof (gr_complex)),
		      gr_make_io_signature (MIN_OUT, MAX_OUT, fft_size * sizeof (gr_complex))),
		      d_fft_size(fft_size),
		      d_tones(tones)
	{

	}

  ~ofdm_carrier_mapper_impl (){}	// public destructor

  // Where all the action really happens

  int general_work (int noutput_items,
		    gr_vector_int &ninput_items,
		    gr_vector_const_void_star &input_items,
		    gr_vector_void_star &output_items){

	  const gr_complex *in = (const gr_complex *) input_items[0];
	  gr_complex *out = (gr_complex *) output_items[0];
	  int counter=0;
	  int i=0;

	  //gr_complex *app = new gr_complex(0);

	  /*
	        * Sanity check
	  */
	  if(d_fft_size != 64){
	    throw std::invalid_argument("ofdm_carrier_mapper: For IEEE 802.11p fft_length must be 64 ");
	  }

	  while(counter < noutput_items) {
	    for (i = 0; i <= 26; i++)
	      out[i + (counter * d_fft_size)] = in[i+26 + (counter * d_tones)];
	    for (i = 27 ; i <= 37 ; i++)
	      out[i + (counter * d_fft_size)] = 0;
	    for (i = 38; i < d_fft_size ; i++)
	      out[i + (counter * d_fft_size)] = in[i-38 + (counter * d_tones)];
	    counter++;
	  }

	  // Tell runtime system how many input items we consumed on
	  // each input stream.

	  consume_each (noutput_items);

	  // Tell runtime system how many output items we produced.
	  return noutput_items;

  }


private:
  int d_fft_size;
  int d_tones;
};


ofdm_carrier_mapper::sptr
ofdm_carrier_mapper::make(int fft_size, int tones,bool debug) {
	return gnuradio::get_initial_sptr(new ofdm_carrier_mapper_impl(fft_size,tones,debug));
}
