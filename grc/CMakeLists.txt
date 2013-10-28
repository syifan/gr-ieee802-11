
install(FILES 
	ieee802_11_ofdm_decode_mac.xml
	ieee802_11_ofdm_decode_signal.xml
	ieee802_11_ofdm_equalize_symbols.xml
	ieee802_11_ofdm_parse_mac.xml
	ieee802_11_ofdm_sync_long.xml
	ieee802_11_ofdm_sync_short.xml
	ieee802_11_ofdm_symbol_mapper.xml
	ieee802_11_ofdm_pilot_insert.xml
	ieee802_11_ofdm_carrier_mapper.xml
	ieee802_11_ofdm_preamble_insert.xml
	ieee802_11_ofdm_zerogap_insert.xml
	ieee802_11_ofdm_symbol_repeater.xml
	DESTINATION share/gnuradio/grc/blocks
)
