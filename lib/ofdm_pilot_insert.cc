#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/ieee802_11/ofdm_pilot_insert.h>
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
int i=0;

class ofdm_pilot_insert_impl : public ofdm_pilot_insert
{
private:
    int d_tones;
    int offset;
public:
	ofdm_pilot_insert_impl (int tones,bool debug)
	  : gr_block ("ofdm_pilot_insert",
		      gr_make_io_signature (MIN_IN, MAX_IN, tones * sizeof (gr_complex)),
		      gr_make_io_signature (MIN_OUT, MAX_OUT, (5 + tones) * sizeof (gr_complex))),
		      d_tones(tones),
		      offset(0)
	{

	}
	~ofdm_pilot_insert_impl ()
	{}



	int general_work (int noutput_items,
				       gr_vector_int &ninput_items,
				       gr_vector_const_void_star &input_items,
				       gr_vector_void_star &output_items)
	{
	  const gr_complex *in = (const gr_complex *) input_items[0];
	  gr_complex *out = (gr_complex *) output_items[0];



	  static gr_complex polarity[127] =
	    { 1, 1, 1, 1,-1,-1,-1, 1,-1,-1,-1,-1, 1, 1,-1, 1,
	     -1,-1, 1, 1,-1, 1, 1,-1, 1, 1, 1, 1, 1, 1,-1, 1,
	      1, 1,-1, 1, 1,-1,-1, 1, 1, 1,-1, 1,-1,-1,-1, 1,
	     -1, 1,-1,-1, 1,-1,-1, 1, 1, 1, 1, 1,-1,-1, 1, 1,
	     -1,-1, 1,-1, 1,-1, 1, 1,-1,-1,-1, 1, 1,-1,-1,-1,
	     -1, 1,-1,-1, 1,-1, 1, 1, 1, 1,-1, 1,-1, 1,-1, 1,
	     -1,-1,-1,-1,-1, 1,-1, 1, 1,-1, 1,-1, 1, 1, 1,-1,
	     -1, 1,-1,-1,-1, 1, 1, 1,-1,-1,-1,-1,-1,-1,-1 };

	  int count = 0;
	  /*
	   * Sanity check
	   */
	  if(d_tones != 48)
	    throw std::invalid_argument("ftw_ofdm_pilot_cc: IEEE 802.11p requires 48 subcarriers\n");

	  while (count < noutput_items) {
		unsigned int out_offset = count * (d_tones + 5);
		unsigned int in_offset = count * d_tones;
		unsigned int pilot_offset = (count + offset) % 127;

	    // Subcarriers -26 to -22
	    for(i = 0 ; i <= 4 ; i++)
	  	  out[i + out_offset] = in[i + in_offset];

	    // Pilot 1 (-21)
	    out[5 + out_offset] = polarity[pilot_offset];

	    // Subcarriers -20 to -8
	    for(i = 6 ; i <= 18; i++)
	  	  out[i + out_offset] = in[i - 1 + in_offset];

	    // Pilot 2 (-7)
	    out[19 + ((count)*(d_tones + 5))] = polarity[pilot_offset];

	    // Subcarriers -6 to -1
	    for(i = 20 ; i <= 25 ; i++)
	  	  out[i + out_offset] = in[i - 2 + in_offset];

	    // DC (always zero)
	    out[26 + out_offset] = 0;

	    // Subcarriers 1 to 6
	    for(i = 27 ; i <= 32 ; i++)
	      out[i + out_offset] = in[i - 3 + in_offset];

	    //Pilot 3 (7)
	    out[33 + out_offset] = polarity[pilot_offset];

	    // Subcarriers 8 to 20
	    for(i = 34 ; i <= 46 ; i++)
	      out[i + out_offset] = in[i - 4 + in_offset];

	    // Pilot 4 (21)
	    out[47 + out_offset] = -polarity[pilot_offset];

	    //Subcarriers 22 to 26
	    for(i = 48 ; i <= 52; i++)
	  	  out[i + out_offset] = in[i - 5 + in_offset];

	    count++;
	  }
	  offset += count;

	  // Tell runtime system how many input items we consumed on
	  // each input stream.
	  consume_each (noutput_items);
	  // Tell runtime system how many output items we produced.
	  return noutput_items;
	}
};

ofdm_pilot_insert::sptr
ofdm_pilot_insert::make(int tones,bool debug) {
	return gnuradio::get_initial_sptr(new ofdm_pilot_insert_impl(tones,debug));
}
