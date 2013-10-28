#ifdef HAVE_CONFIG_H
#include <config.h>
#endif
#include <gnuradio/ieee802_11/crc32.h>




unsigned int
update_crc32(unsigned int crc, const unsigned char *data, size_t len)
{
  int j;
  unsigned int byte, mask;
  static unsigned int table[256];
  /* Set up the table if necesary */
  if (table[1] == 0) {
    for(byte = 0; byte <= 255; byte++) {
      crc = byte;
      for (j = 7; j >= 0; j--) {
        mask = -(crc & 1);
	crc = (crc >> 1) ^ (0xEDB88320 & mask);
      }
	table[byte] = crc;
    }
  }

  /* Calculate the CRC32*/
  size_t i = 0;
  crc = 0xFFFFFFFF;
  for (i = 0; i < len; i++) {
    byte = data[i];    //Get next byte
    crc = (crc >> 8) ^ table[(crc ^ byte) & 0xFF];
  }
  unsigned int crc_reversed;
  crc_reversed = 0x00000000;
  for (j=31; j >= 0; j--) {
    crc_reversed |= ((crc >> j) & 1) << (31 - j);
  }
  return crc_reversed;
}

unsigned int
update_crc32(unsigned int crc, const std::string s)
{
  return update_crc32(crc, (const unsigned char *) s.data(), s.size());
}

unsigned int
crc32(const unsigned char *buf, size_t len)
{
  return update_crc32(0xffffffff, buf, len) ^ 0xffffffff;
}

unsigned int
crc32(const std::string s)
{
  return crc32((const unsigned char *) s.data(), s.size());
}

