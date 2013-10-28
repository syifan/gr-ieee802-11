
#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <gnuradio/ieee802_11/ofdm_zerogap_insert.h>
#include <gnuradio/gr_io_signature.h>
#include <stdexcept>
#include <iostream>
#include <string.h>

using namespace gr::ieee802_11;

class ofdm_zerogap_insert_impl : public ofdm_zerogap_insert
{

public:

  ofdm_zerogap_insert_impl(int symbol_length, int N_symbols, const std::vector<std::vector<gr_complex> > &zerogap,bool debug)
              : gr_block("ofdm_zerogap_insert",
				gr_make_io_signature2(2, 2, sizeof(gr_complex)*(symbol_length), sizeof(char)),
				gr_make_io_signature2(1, 2, sizeof(gr_complex)*symbol_length, sizeof(char))),
				d_symbol_length(symbol_length),
				d_N_symbols(N_symbols),
				d_zerogap(zerogap),
				d_state(ST_IDLE),
				d_nsymbols_output(0),
				d_pending_flag(0)
  {
	 set_output_multiple(d_N_symbols + 5);   // (320 samples training sequences + 80 samples first signal ofdm symbol = 400)--> 400 / 80 = 5
	 enter_idle();
  }

  ~ofdm_zerogap_insert_impl(){}

  int general_work (int noutput_items,
			gr_vector_int &ninput_items_v,
			gr_vector_const_void_star &input_items,
		        gr_vector_void_star &output_items){
	  const gr_complex *in_sym = (const gr_complex *) input_items[0];
	  const unsigned char *in_flag = (const unsigned char *) input_items[1];
	  gr_complex *out_sym = (gr_complex *) output_items[0];

	  int no = 0;	// number items output
	  int ni = 0;	// number items read from input

	  switch(d_state){
	    case ST_IDLE:
	      //if (in_flag[ni])	// this is the first symbol of the new payload
		enter_first_payload_and_zerogap();
	      break;
	      //else
		std::cout << "PROBLEM!" << "\n";
		ni++;			// eat one input symbol
	      break;


	    case ST_FIRST_PAYLOAD_AND_POSTAMBLE:
	      while(no < noutput_items){
	      // copy first payload symbol from input to output
	        memcpy(&out_sym[no * d_symbol_length],&in_sym[ni * d_symbol_length],d_symbol_length * sizeof(gr_complex));
	        no++;
	        ni++;
	      }
	      // (80*13) 1020 zeros will be added in the end of the frame (in the standard they must be 640)
	      for(int temp=0; temp<13; temp++)
	      {
	         memcpy(&out_sym[no * d_symbol_length],&d_zerogap[d_nsymbols_output][0],d_symbol_length * sizeof(gr_complex));
	         no++;
	      }
	      break;


	    default:
	      std::cerr << "gr_zerogap: (can't happen) invalid state, resetting\n";
	      enter_idle();
	  }
	  consume_each(ni);
	  return no;

  }

private:
  enum state_t {
    ST_IDLE,
    ST_FIRST_PAYLOAD_AND_POSTAMBLE,
  };

  int						d_symbol_length;
  int						d_N_symbols;
  const std::vector<std::vector<gr_complex> > 	d_zerogap;
  state_t					d_state;
  int						d_nsymbols_output;
  int						d_pending_flag;


  void enter_idle(){
	  d_state = ST_IDLE;
	  d_nsymbols_output = 0;
	  d_pending_flag = 0;
  }
  void enter_first_payload_and_zerogap(){
	  d_state = ST_FIRST_PAYLOAD_AND_POSTAMBLE;
  }


};

ofdm_zerogap_insert::sptr
ofdm_zerogap_insert::make(int symbol_length, int N_symbols,
		  const std::vector<std::vector<gr_complex> > &zerogap,bool debug) {
	return gnuradio::get_initial_sptr(new ofdm_zerogap_insert_impl(symbol_length,N_symbols,zerogap,debug));
}

