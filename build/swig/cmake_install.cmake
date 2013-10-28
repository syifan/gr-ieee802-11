# Install script for directory: /home/yifansun/gr-ieee802-11/swig

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

IF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "ieee802_11_python")
  IF(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/python2.7/dist-packages/gnuradio/ieee802_11/_ieee802_11_swig.so" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/python2.7/dist-packages/gnuradio/ieee802_11/_ieee802_11_swig.so")
    FILE(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/python2.7/dist-packages/gnuradio/ieee802_11/_ieee802_11_swig.so"
         RPATH "")
  ENDIF()
  FILE(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python2.7/dist-packages/gnuradio/ieee802_11" TYPE MODULE FILES "/home/yifansun/gr-ieee802-11/build/swig/_ieee802_11_swig.so")
  IF(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/python2.7/dist-packages/gnuradio/ieee802_11/_ieee802_11_swig.so" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/python2.7/dist-packages/gnuradio/ieee802_11/_ieee802_11_swig.so")
    FILE(RPATH_REMOVE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/python2.7/dist-packages/gnuradio/ieee802_11/_ieee802_11_swig.so")
    IF(CMAKE_INSTALL_DO_STRIP)
      EXECUTE_PROCESS(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/python2.7/dist-packages/gnuradio/ieee802_11/_ieee802_11_swig.so")
    ENDIF(CMAKE_INSTALL_DO_STRIP)
  ENDIF()
ENDIF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "ieee802_11_python")

IF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "ieee802_11_python")
  FILE(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python2.7/dist-packages/gnuradio/ieee802_11" TYPE FILE FILES "/home/yifansun/gr-ieee802-11/build/swig/ieee802_11_swig.py")
ENDIF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "ieee802_11_python")

IF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "ieee802_11_python")
  FILE(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python2.7/dist-packages/gnuradio/ieee802_11" TYPE FILE FILES
    "/home/yifansun/gr-ieee802-11/build/swig/ieee802_11_swig.pyc"
    "/home/yifansun/gr-ieee802-11/build/swig/ieee802_11_swig.pyo"
    )
ENDIF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "ieee802_11_python")

IF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "ieee802_11_swig")
  FILE(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/gnuradio/ieee802_11/swig" TYPE FILE FILES
    "/home/yifansun/gr-ieee802-11/swig/ieee802_11_swig.i"
    "/home/yifansun/gr-ieee802-11/swig/ieee802_11_factory.i"
    "/home/yifansun/gr-ieee802-11/swig/ieee802_11_ofdm_decode_mac.i"
    "/home/yifansun/gr-ieee802-11/swig/ieee802_11_ofdm_decode_signal.i"
    "/home/yifansun/gr-ieee802-11/swig/ieee802_11_ofdm_equalize_symbols.i"
    "/home/yifansun/gr-ieee802-11/swig/ieee802_11_ofdm_parse_mac.i"
    "/home/yifansun/gr-ieee802-11/swig/ieee802_11_ofdm_sync_long.i"
    "/home/yifansun/gr-ieee802-11/swig/ieee802_11_ofdm_sync_short.i"
    "/home/yifansun/gr-ieee802-11/swig/ieee802_11_ofdm_symbol_mapper.i"
    "/home/yifansun/gr-ieee802-11/swig/ieee802_11_ofdm_pilot_insert.i"
    "/home/yifansun/gr-ieee802-11/swig/ieee802_11_ofdm_carrier_mapper.i"
    "/home/yifansun/gr-ieee802-11/swig/ieee802_11_ofdm_preamble_insert.i"
    "/home/yifansun/gr-ieee802-11/swig/ieee802_11_ofdm_zerogap_insert.i"
    "/home/yifansun/gr-ieee802-11/swig/ieee802_11_ofdm_symbol_repeater.i"
    "/home/yifansun/gr-ieee802-11/swig/ieee802_11_crc32.i"
    "/home/yifansun/gr-ieee802-11/build/swig/ieee802_11_swig_doc.i"
    )
ENDIF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "ieee802_11_swig")

