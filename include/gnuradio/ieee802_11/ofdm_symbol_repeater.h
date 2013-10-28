#ifndef INCLUDED_GR_IEEE802_11_OFDM_SYMBOL_REPEATER_H
#define INCLUDED_GR_IEEE802_11_OFDM_SYMBOL_REPEATER_H

#include <gnuradio/ieee802_11/api.h>
#include <gr_block.h>
#include <vector>
namespace gr {
namespace ieee802_11 {

class GR_IEEE802_11_API ofdm_symbol_repeater : virtual public gr_block
{
public:

	typedef boost::shared_ptr<ofdm_symbol_repeater> sptr;
	static sptr make(int symbol_length, int repetition, int N_symbols,bool debug = false);

};

}  // namespace ieee802_11
}  // namespace gr

#endif /* INCLUDED_GR_IEEE802_11_OFDM_SYMBOL_REPEATER_H */
