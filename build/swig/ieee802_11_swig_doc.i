
/*
 * This file was automatically generated using swig_doc.py.
 * 
 * Any changes to it will be lost next time it is regenerated.
 */




%feature("docstring") ftw_ofdm_cmap_cc "square a stream of floats.

Return a shared_ptr to a new instance of ftw_ofdm_cmap_cc.

To avoid accidental use of raw pointers, ftw_ofdm_cmap_cc's constructor is private. ftw_make_ofdm_cmap_cc is the public interface for creating new instances."

%feature("docstring") ftw_ofdm_cmap_cc::ftw_ofdm_cmap_cc "

Params: (fft_size, tones)"

%feature("docstring") ftw_ofdm_cmap_cc::~ftw_ofdm_cmap_cc "

Params: (NONE)"

%feature("docstring") ftw_ofdm_cmap_cc::general_work "

Params: (noutput_items, ninput_items, input_items, output_items)"

%feature("docstring") ftw_make_ofdm_cmap_cc "square a stream of floats.

Return a shared_ptr to a new instance of ftw_ofdm_cmap_cc.

To avoid accidental use of raw pointers, ftw_ofdm_cmap_cc's constructor is private. ftw_make_ofdm_cmap_cc is the public interface for creating new instances.

Params: (fft_size, tones)"

%feature("docstring") ftw_ofdm_mapper "take a stream of bytes in and map to a vector of complex constellation points suitable for IFFT input to be used in an ofdm modulator. Abstract class must be subclassed with specific mapping."

%feature("docstring") ftw_ofdm_mapper::ftw_ofdm_mapper "

Params: (constellation, msgq_limit, occupied_carriers, fft_length)"

%feature("docstring") ftw_ofdm_mapper::randsym "

Params: (NONE)"

%feature("docstring") ftw_ofdm_mapper::~ftw_ofdm_mapper "

Params: ()"

%feature("docstring") ftw_ofdm_mapper::msgq "

Params: (NONE)"

%feature("docstring") ftw_ofdm_mapper::work "

Params: (noutput_items, input_items, output_items)"

%feature("docstring") ftw_make_ofdm_mapper "take a stream of bytes in and map to a vector of complex constellation points suitable for IFFT input to be used in an ofdm modulator. Abstract class must be subclassed with specific mapping.

Params: (constellation, msgq_limit, occupied_carriers, fft_length)"

%feature("docstring") ftw_ofdm_pilot_cc "Return a shared_ptr to a new instance of ftw_ofdm_pilot_cc.

To avoid accidental use of raw pointers, ftw_ofdm_pilot_cc's constructor is private. ftw_make_ofdm_pilot_cc is the public interface for creating new instances."

%feature("docstring") ftw_ofdm_pilot_cc::ftw_ofdm_pilot_cc "

Params: (tones)"

%feature("docstring") ftw_ofdm_pilot_cc::~ftw_ofdm_pilot_cc "

Params: (NONE)"

%feature("docstring") ftw_ofdm_pilot_cc::general_work "

Params: (noutput_items, ninput_items, input_items, output_items)"

%feature("docstring") ftw_make_ofdm_pilot_cc "Return a shared_ptr to a new instance of ftw_ofdm_pilot_cc.

To avoid accidental use of raw pointers, ftw_ofdm_pilot_cc's constructor is private. ftw_make_ofdm_pilot_cc is the public interface for creating new instances.

Params: (tones)"



%feature("docstring") ftw_ofdm_preamble::ftw_ofdm_preamble "

Params: (symbol_length, N_symbols, preamble)"

%feature("docstring") ftw_ofdm_preamble::enter_idle "

Params: (NONE)"

%feature("docstring") ftw_ofdm_preamble::enter_first_payload_and_preamble "

Params: (NONE)"

%feature("docstring") ftw_ofdm_preamble::~ftw_ofdm_preamble "

Params: (NONE)"

%feature("docstring") ftw_ofdm_preamble::general_work "

Params: (noutput_items, ninput_items_v, input_items, output_items)"

%feature("docstring") ftw_make_ofdm_preamble "

Params: (symbol_length, N_symbols, preamble)"



%feature("docstring") ftw_repetition::ftw_repetition "

Params: (symbol_length, repetition, N_symbols)"

%feature("docstring") ftw_repetition::~ftw_repetition "

Params: (NONE)"

%feature("docstring") ftw_repetition::general_work "

Params: (noutput_items, ninput_items, input_items, output_items)"

%feature("docstring") ftw_make_repetition "

Params: (symbol_length, repetition, N_symbols)"



%feature("docstring") ftw_zerogap::ftw_zerogap "

Params: (symbol_length, N_symbols, zerogap)"

%feature("docstring") ftw_zerogap::enter_idle "

Params: (NONE)"

%feature("docstring") ftw_zerogap::enter_first_payload_and_zerogap "

Params: (NONE)"

%feature("docstring") ftw_zerogap::~ftw_zerogap "

Params: (NONE)"

%feature("docstring") ftw_zerogap::general_work "

Params: (noutput_items, ninput_items_v, input_items, output_items)"

%feature("docstring") ftw_make_zerogap "

Params: (symbol_length, N_symbols, zerogap)"

%feature("docstring") update_crc32 "update running CRC-32

Update a running CRC with the bytes buf[0..len-1] The CRC should be initialized to all 1's, and the transmitted value is the 1's complement of the final running CRC. The resulting CRC should be transmitted in big endian order.

Params: (crc, buf, len)"

%feature("docstring") crc32 "

Params: (buf, len)"

%feature("docstring") ftw_update_crc32 "update running CRC-32

Update a running CRC with the bytes buf[0..len-1] The CRC should be initialized to all 1's, and the transmitted value is the 1's complement of the final running CRC. The resulting CRC should be transmitted in big endian order.

Params: (crc, buf, len)"

%feature("docstring") ftw_crc32 "

Params: (buf, len)"



%feature("docstring") gr::ieee802_11::ofdm_carrier_mapper::make "

Params: (fft_size, tones, debug)"



%feature("docstring") gr::ieee802_11::ofdm_decode_mac::make "

Params: (debug)"



%feature("docstring") gr::ieee802_11::ofdm_decode_signal::make "

Params: (debug)"



%feature("docstring") gr::ieee802_11::ofdm_equalize_symbols::make "

Params: (debug)"



%feature("docstring") gr::ieee802_11::ofdm_parse_mac::make "

Params: (debug)"



%feature("docstring") gr::ieee802_11::ofdm_pilot_insert::make "

Params: (tones, debug)"



%feature("docstring") gr::ieee802_11::ofdm_preamble_insert::make "

Params: (symbol_length, N_symbols, preamble, debug)"



%feature("docstring") gr::ieee802_11::ofdm_symbol_mapper::make "

Params: (constellation, msgq_limit, occupied_carriers, fft_length, debug)"

%feature("docstring") gr::ieee802_11::ofdm_symbol_mapper::msgq "

Params: (NONE)"



%feature("docstring") gr::ieee802_11::ofdm_symbol_repeater::make "

Params: (symbol_length, repetition, N_symbols, debug)"



%feature("docstring") gr::ieee802_11::ofdm_sync_long::make "

Params: (sync_length, freq_est, debug)"



%feature("docstring") gr::ieee802_11::ofdm_sync_short::make "

Params: (threshold, max_samples, min_plateau, debug)"



%feature("docstring") gr::ieee802_11::ofdm_zerogap_insert::make "

Params: (symbol_length, N_symbols, zerogap, debug)"