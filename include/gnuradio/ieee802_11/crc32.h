#ifndef INCLUDED_CRC32_H
#define INCLUDED_CRC32_H

#include <gnuradio/ieee802_11/api.h>
#include <string>
#include <gr_types.h>

/*!
 * \brief update running CRC-32
 * \ingroup misc
 *
 * Update a running CRC with the bytes buf[0..len-1] The CRC should be
 * initialized to all 1's, and the transmitted value is the 1's
 * complement of the final running CRC.  The resulting CRC should be
 * transmitted in big endian order.
 */


GR_IEEE802_11_API unsigned int
update_crc32(unsigned int crc, const unsigned char *buf, size_t len);

GR_IEEE802_11_API unsigned int
update_crc32(unsigned int crc, const std::string buf);

GR_IEEE802_11_API unsigned int
crc32(const unsigned char *buf, size_t len);

GR_IEEE802_11_API unsigned int
crc32(const std::string buf);


#endif /* INCLUDED_CRC32_H */
