# Copyright 2005, 2006 Free Software Foundation, Inc.

# This file is part of GNU Radio

# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.

# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.


# Projectname: uwicore@umh_80211_MAC

# Ubiquitous Wireless Communications Research Laboratory 
# Uwicore, http://www.uwicore.umh.es
# Communications Engineering Department
# University Miguel Hernandez of Elche
# Avda de la Universidad, s/n
# 03202 Elche, Spain

# Release: April 2011

# List of Authors:
#	Juan R. Gutierrez-Agullo (jgutierrez@umh.es)
#	Baldomero Coll-Perales (bcoll@umh.es)
#	Dr. Javier Gozalvez (j.gozalvez@umh.es)

========
 README
========
This readme describes the 'uwicore@umh_80211_MAC' project and explains the procedures to compile,
install and execute it. Finally, it enumerates an example of usage of the software.

This tarball includes:
	- uwicore@umh_80211_MAC project source code.
	- ftw_ofdm_tx project source code.
	- A set of trials that can be carried out using this project.

=====================
 Project description
=====================
The project mHOP has developed an 802.11 MAC SDR implementation for experimental communications and networking research. The MAC layer has been implemented using as starting point the Physical (PHY) layer developed by the Telecommunications Research Center Vienna FTW. The FTW source code is available at the Comprehensive GNU Radio Archive Network (CGRAN) project folder (https://www.cgran.org/wiki/ftw80211ofdmtx). Due to the lack of an 802.11a/g/p OFDM receiver implementation for USRP2, the receiver functionality from the PHY layer has been simulated to check the correct MAC layer operation. The source code provided by mHOP includes the initial release of the source code for the uwicore@umh_80211_MAC project, licensed under the GPLv3. The attached files also include the ftw_ofdm_tx project code (developed by FTW) since it is necessary to run the uwicore@umh_80211_MAC software.

The MAC layer has been implemented following a Finite State Machine scheme using the Python programming language. It includes the next 802.11 mandatory functionalities: Request-to-Send-Clear-to-Send (CSMA/CA based), Carrier Sensing based on power measurement, Packet Retransmission, Packet Acknowledgment, Beaconing process and Packet Fragmentation and Re-assembly. Taking as example the procedure designed by FTW group to define a DATA UNICAST frame, there have been defined new frame types used by the MAC layer (RTS, CTS, ACK, Beacon, Data). All the MAC frames defined in the present project are correctly formed and transmitted, and they can be captured using a commercial 802.11a/g wireless card which allows to set up the card in promiscuous mode. It is important to notice that all the 802.11 time parameters (time-slot and DCF Interframe Spacing Interval) are multiplied by a 'beta' factor, in order to adapt the MAC timing to the USRP2 timing. This factor is modifiable (uwicore_80211mac.py), depending on the speed of the processor which executes the software.Finally, the communication between layers (PHY<->MAC<->Upper Layer) has been done through stream sockets to ensure the transmission and ease the message interchange procedure between layers.

It is important to note that the MAC code provided by the Uwicore laboratory has been tested on:
Ubuntu 9.10 desktop (32 bit)
Kernel Version: 2.6.31-20-generic
Platform: x86_32
GNURadio Version: 3.3.0
USRP2 HW revision number: 0x0400
USRP2 Firmware revision number: r11370
Daughterboard model: XCVR2450

==========
 Citation
==========
For reference purposes, and in order to comply with our sponsor guidelines, we would appreciate if any publication using the uwicore@umh_80211_MAC software includes the following citation:

J.R. Gutierrez-Agullo, B. Coll-Perales and J. Gozalvez, "An IEEE 802.11 MAC Software Defined Radio Implementation for  Experimental Wireless Communications and Networking Research", Proceedings of the 2010 IFIP/IEEE Wireless Days (WD'10), pp. 1-5, 20-22 October 2010, Venice (Italy).

==============================
 Compilation and Installation
==============================
1. INSTALL GNU RADIO

This package requires that gnuradio-core is already installed. For a more detailed GNU Radio installation check out the official website (http://gnuradio.org/redmine/wiki/gnuradio/BuildGuide)

If you are building from CVS, you will need to use this sequence:

	$ ./bootstrap
	$ ./configure
	$ make

To build it from the tarball (http://ftp.gnu.org/gnu/gnuradio/gnuradio-3.3.0.tar.gz):

	$ ./configure
	$ make

2. INSTALL FTW 802.11a/g/p OFDM ENCODER

Once GNU Radio has been installed, it is necessary to install the ftw_ofdm_tx project.

2.1. Obtain the FTW code (included in the uwicore@umh_80211_MAC tarball) and extract it in a selected folder.

2.2. Change to the FTW project directory 

	$ cd ~/ftw_80211_ofdm_tx

2.3. Launch the configure file of the FTW project, compile it with make and install it.

	$ ./configure
	$ make
	$ sudo make install

3. INSTALL UWICORE 802.11 MAC

At this point, FTW is already installed. The next step is to install the Uwicore 802.11 MAC.

3.1. Copy the content of the folder uwicore@umh_80211_MAC from the tarball to ~/ftw_80211_ofdm_tx/branches.

	$ cp -r ~/uwicore@umh_80211_MAC/uwicore_80211_MAC/ ~/ftw_ofdm_tx/branches/

============
 How To Run
============
Steps to run the code:

0. Go to the uwicore_80211_MAC folder
		
	$ cd ~/ftw_80211_ofdm_tx/branches/uwicore_80211_MAC/

1. Open a new terminal window and execute the PHY TX layer

	$ sudo ./ftw_ofdm_tx.py [options]
	Options:
	  -h, --help            show this help message and exit
	  -e INTERFACE, --interface=INTERFACE
				set ethernet interface, [default=eth0]
	  -m MAC_ADDR, --mac-addr=MAC_ADDR
				set USRP2 MAC address, [default=auto-select]
	  -f FREQ, --freq=FREQ  set USRP2 carrier frequency, [default=2412000000.0]
	  -i INTERP, --interp=INTERP
				set USRP2 interpolation factor, [default=5]
				5  -> 802.11a/g, OFDM-symbolduration=4us,
				10 -> 802.11p, OFDM-symbolduration=8us
	  --regime=REGIME       set OFDM coderegime,    [default=1]
				1 -> 6 (3) Mbit/s (BPSK r=0.5),
				2 -> 9 (4.5) Mbit/s (BPSK r=0.75),
				3 -> 12 (6) Mbit/s (QPSK r=0.5),
				4 -> 18 (9) Mbit/s (QPSK r=0.75),
				5 -> 24 (12) Mbit/s (QAM16 r=0.5),
				6 -> 36 (18) Mbit/s (QAM16 r=0.75),
				7 -> 48 (24) Mbit/s (QAM64 r=0.66),
				8 -> 54 (27) Mbit/s (QAM64 r=0.75)
	  -G TXGAIN, --txgain=TXGAIN
				set USRP2 Tx GAIN in [dB] [default=10]
	  -g GAIN, --gain=GAIN  set USRP2 Rx GAIN in [dB] [default=46]
	  -n NORM, --norm=NORM  set gain factor for complex baseband floats
				[default=0.3]
	  -s, --swapIQ          swap IQ components before sending to USRP2 sink
				[default=False]
	  -l, --log             write debug-output of individual blocks to disk
	  --PHYport=PHYPORT     Port used for MAC-->PHY communication [default=8000]
	  --tune-delay=SECS     Carrier sensing parameter. Time to delay (in seconds)
				after changing frequency [default=0.0001]
	  --dwell-delay=SECS    Carrier sensing parameter. Time to dwell (in seconds)
				at a given frequncy [default=0.001]
	  -F FFT_SIZE, --fft-size=FFT_SIZE
				specify number of FFT bins [default=256]
	  -d DECIM, --decim=DECIM
				set the decimation value [default=16]
	  --real-time           Attempt to enable real-time scheduling
	  -v, --verbose         Print timming information, [default=False]

1.1. Open a new terminal (or a console tab, with Ctr+Shift+T) and execute the PHY RX layer

	$ ./uwicore_phy_rx.py [options]
	Options:
	  -h, --help            show this help message and exit
	  --PHYport=PHYPORT     Socket port [default=8500]
	  -n NODE, --node=NODE  USRP2 node    [default=1]

2. Open a new terminal (or a console tab) and execute the Upper layer (UL) buffers
	
	$ ./ul_buffer.py [options]
	Options:
	  -h, --help         show this help message and exit
	  --MACport=MACPORT  Socket port [default=8001]

3.Run the MAC in a new console window
	
	$ ./uwicore_80211mac.py [options]
	Options:
	  -h, --help            show this help message and exit
	  --PHYport=PHYPORT     PHY communication socket port, [default=8000]
	  --MACport=MACPORT     MAC communication socket port, [default=8001]
	  --PHYRXport=PHYRXPORT Socket port, [default=8500]
	  -i INTERP, --interp=INTERP
			        USRP2 interpolation factor value, [default=5]
			        5  -> 802.11a/g, OFDM T_Symbol=4us,                 
				10 -> 802.11p, OFDM T_Symbol=8us
	  --regime=REGIME       OFDM regimecode    [default=1]
			        1 -> 6 (3) Mbit/s (BPSK r=0.5),
			        2 -> 9 (4.5) Mbit/s (BPSK r=0.75),
			        3 -> 12 (6) Mbit/s (QPSK r=0.5),
			        4 -> 18 (9) Mbit/s (QPSK r=0.75),
			        5 -> 24 (12) Mbit/s (QAM16 r=0.5),
			        6 -> 36 (18) Mbit/s (QAM16 r=0.75),
			        7 -> 48 (24) Mbit/s (QAM64 r=0.66),
			        8 -> 54 (27) Mbit/s (QAM64 r=0.75)
	  -n NODE, --node=NODE  Number of USRP2 node, [default=1]
	  --beta=BETA           Scaling Time Parameter, [default=20000]
	  -t TIME_SLOT, --time_slot=TIME_SLOT
			        Time slot value, [default=9e-06]
	  -B BI, --BI=BI        Beacon Interval (BI) value in seconds, [default=1]
	  -S SIFS, --SIFS=SIFS  Short Inter-frame space (SIFS) value,
			        [default=1.6e-05]
	  --retx                Retransmissions enabled, [default=False]
	  --RTS                 RTS-threshold enabled, [default=False]
	  --V                   Print debug information, [default=False]

NOTE: Remember that 'beta' parameter is the factor that multiplies all the timing parameters.

4.In a new window, start the PHY traffic to generate the arrival of frames (the number of generated frames can be modified through the code)
	
	$ ./phy_traffic.py [options]
	Options:
	  -h, --help            show this help message and exit
	  -n NODE, --node=NODE  USRP2 node    [default=1]

OPTIONAL: In order to test the re-assembly functonality, run the following script that generates a stream of fragmented Data.
		
		$./phy_frag_traffic.py [options]	
		Options:
		  -h, --help            show this help message and exit
		  -n NODE, --node=NODE  USRP2 node   [default=1]

5.Start the Upper layer traffic generator (Number of frames modifialbe through the code)

	$ ./ul_traffic.py

6.Initialize the 802.11 Beaconing process
	
	$ ./beaconing.py

	Options:
	  -h, --help      show this help message and exit
	  -B BI, --BI=BI  802.11 Beacon Interval (seconds), [default=1]

=================
 Important notes
=================
- It is necessary to install the FTW project before using this software. 
- This code represents a first approach of a MAC implementation compatible with USRP2, but there are still some features that need to be improved in order to complete a full 802.11 node.

======
 TODO
======
1.Integration of an 802.11a/g/p OFDM receiver in order to use the project as a full 802.11a/g/p programmable node.
2.Add and complete functionalities above MAC layer.
3.Optimize the timing operation of the PHY and MAC layers.
