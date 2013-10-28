#ifndef INCLUDED_GR_IEEE802_11_OFDM_PILOT_INSERT_H
#define INCLUDED_GR_IEEE802_11_OFDM_PILOT_INSERT_H

#include <gnuradio/ieee802_11/api.h>
#include <gr_block.h>

namespace gr {
namespace ieee802_11 {

class GR_IEEE802_11_API ofdm_pilot_insert : virtual public gr_block
{
public:

	typedef boost::shared_ptr<ofdm_pilot_insert> sptr;
	static sptr make(int tones,bool debug = false);

};

}  // namespace ieee802_11
}  // namespace gr

#endif /* INCLUDED_GR_IEEE802_11_OFDM_PILOT_INSERT_H */
