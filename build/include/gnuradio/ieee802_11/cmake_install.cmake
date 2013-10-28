# Install script for directory: /home/yifansun/gr-ieee802-11/include/gnuradio/ieee802_11

# Set the install prefix
IF(NOT DEFINED CMAKE_INSTALL_PREFIX)
  SET(CMAKE_INSTALL_PREFIX "/usr/local")
ENDIF(NOT DEFINED CMAKE_INSTALL_PREFIX)
STRING(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
IF(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  IF(BUILD_TYPE)
    STRING(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  ELSE(BUILD_TYPE)
    SET(CMAKE_INSTALL_CONFIG_NAME "Release")
  ENDIF(BUILD_TYPE)
  MESSAGE(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
ENDIF(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)

# Set the component getting installed.
IF(NOT CMAKE_INSTALL_COMPONENT)
  IF(COMPONENT)
    MESSAGE(STATUS "Install component: \"${COMPONENT}\"")
    SET(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  ELSE(COMPONENT)
    SET(CMAKE_INSTALL_COMPONENT)
  ENDIF(COMPONENT)
ENDIF(NOT CMAKE_INSTALL_COMPONENT)

# Install shared libraries without execute permission?
IF(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  SET(CMAKE_INSTALL_SO_NO_EXE "1")
ENDIF(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)

IF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "ieee802_11_devel")
  FILE(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/gnuradio/ieee802_11" TYPE FILE FILES
    "/home/yifansun/gr-ieee802-11/include/gnuradio/ieee802_11/api.h"
    "/home/yifansun/gr-ieee802-11/include/gnuradio/ieee802_11/ofdm_decode_mac.h"
    "/home/yifansun/gr-ieee802-11/include/gnuradio/ieee802_11/ofdm_decode_signal.h"
    "/home/yifansun/gr-ieee802-11/include/gnuradio/ieee802_11/ofdm_equalize_symbols.h"
    "/home/yifansun/gr-ieee802-11/include/gnuradio/ieee802_11/ofdm_parse_mac.h"
    "/home/yifansun/gr-ieee802-11/include/gnuradio/ieee802_11/ofdm_sync_long.h"
    "/home/yifansun/gr-ieee802-11/include/gnuradio/ieee802_11/ofdm_sync_short.h"
    "/home/yifansun/gr-ieee802-11/include/gnuradio/ieee802_11/ofdm_symbol_mapper.h"
    "/home/yifansun/gr-ieee802-11/include/gnuradio/ieee802_11/ofdm_pilot_insert.h"
    "/home/yifansun/gr-ieee802-11/include/gnuradio/ieee802_11/ofdm_carrier_mapper.h"
    "/home/yifansun/gr-ieee802-11/include/gnuradio/ieee802_11/ofdm_preamble_insert.h"
    "/home/yifansun/gr-ieee802-11/include/gnuradio/ieee802_11/ofdm_zerogap_insert.h"
    "/home/yifansun/gr-ieee802-11/include/gnuradio/ieee802_11/ofdm_symbol_repeater.h"
    "/home/yifansun/gr-ieee802-11/include/gnuradio/ieee802_11/crc32.h"
    )
ENDIF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "ieee802_11_devel")

