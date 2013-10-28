#ifndef INCLUDED_GR_IEEE802_11_OFDM_SYMBOL_MAPPER_H
#define INCLUDED_GR_IEEE802_11_OFDM_SYMBOL_MAPPER_H

#include <gnuradio/ieee802_11/api.h>
#include <gr_sync_block.h>
#include <gr_message.h>
#include <gr_msg_queue.h>

// crc32 headers
#include <string>
#include <gr_types.h>

namespace gr {
namespace ieee802_11 {

class GR_IEEE802_11_API ofdm_symbol_mapper : virtual public gr_sync_block
{
public:

	typedef boost::shared_ptr<ofdm_symbol_mapper> sptr;
	static sptr make(const std::vector<gr_complex> &constellation, unsigned msgq_limit,
			   unsigned occupied_carriers, unsigned int fft_length,bool debug = false);
	gr_msg_queue_sptr msgq() const { return d_msgq; }

protected:
  gr_msg_queue_sptr d_msgq;

};

}  // namespace ieee802_11
}  // namespace gr

#endif /* INCLUDED_GR_IEEE802_11_OFDM_SYMBOL_MAPPER_H */

