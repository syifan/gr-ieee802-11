#ifndef INCLUDED_GR_IEEE802_11_OFDM_CARRIER_MAPPER_H
#define INCLUDED_GR_IEEE802_11_OFDM_CARRIER_MAPPER_H

#include <gnuradio/ieee802_11/api.h>
#include <gr_block.h>


namespace gr {
namespace ieee802_11 {

class GR_IEEE802_11_API ofdm_carrier_mapper : virtual public gr_block
{
public:

	typedef boost::shared_ptr<ofdm_carrier_mapper> sptr;
	static sptr make(int fft_size, int tones,bool debug = false);

};

}  // namespace ieee802_11
}  // namespace gr

#endif /* INCLUDED_GR_IEEE802_11_OFDM_CARRIER_MAPPER_H */

