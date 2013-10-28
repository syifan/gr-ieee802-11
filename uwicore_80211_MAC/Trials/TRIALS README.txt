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

# This file describes the trials carried out using the uwicore@umh_80211_MAC project.
# In order to check the correct frame generation, it has been used a Wireless 
# Network Analyzer software (WireShark) in combination with a commercial 
# IEEE 802.11a/g wireless card. More detailed about the experimental trials can 
# be found at www.uwicore.umh.es/mhop-testbeds.html or at the publication:

# J.R. Gutierrez-Agullo, B. Coll-Perales and J. Gozalvez, "An IEEE 802.11 MAC Software Defined Radio Implementation for  Experimental Wireless Communications and Networking Research", Proceedings of the 2010 IFIP/IEEE Wireless Days (WD'10), pp. 1-5, 20-22 October 2010, Venice (Italy).

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

=====================================
 1. RTS/CTS (Receiving states) TRIAL
=====================================

This trial validates the correct state transition when the station receives a RTS packet. 

1.1) Remove the comments of the following files:
	- uwicore_80211mac.py: lines (197-208) and (688-699)
	- phy_traffic.py: lines (177-180)

1.2) Set the scaling time parameter 'beta' to 20000 (uwicore_80211mac.py parameter, step 2.3).

1.3) Run PHY, MAC, etc as follows:

	$ cd ~/uwicore_MAC/	
	$ sudo ./ftw_ofdm_tx.py -f 5.2G -i 5 -d 16
	$ ./uwicore_phy_rx.py -n 1
	$ ./ul_buffer.py 
	$ ./uwicore_80211mac.py --RTS --V --retx -n 1 --regime=1 --beta=20000
	$ ./phy_traffic.py 

NOTE: It is recommended to use a Wireless Network Analyzer in this trial to capture the whole frame transmissions.


========================================
 2. RTS/CTS (Transmitting states) TRIAL
========================================

This trial validates the correct state's transition when the station has DATA from Upper Layers to transmit.

2.1) Remove the comments of the following files:
	- uwicore_80211mac.py: lines (456-468) and (594-606)
	- phy_traffic.py: lines (183-186)

2.2) Set the scaling time parameter 'beta' to 20000 (uwicore_80211mac.py parameter, step 2.3).

2.3) Run PHY, MAC, etc as follows:

	$ cd ~/uwicore_MAC/	
	$ sudo ./ftw_ofdm_tx.py -f 5.2G -i 5 -d 16
	$ ./uwicore_phy_rx.py -n 1
	$ ./ul_buffer.py 
	$ ./uwicore_80211mac.py --RTS --V --retx -n 1 --regime=1 --beta=20000
	$ ./phy_traffic.py 

NOTE: It is recommended to use a Wireless Network Analyzer in this trial.

==========================
 3. Carrier Sensing TRIAL
==========================

The Carrier Sensing trial provides a way of testing the power detected by the USRP2 at a desired 802.11a/g/p channel. The procedure used during the MAC operations to check whether the channel is busy or not is based on the script usrp2_spectrum_sense. This script, included in the folder /uwicore_MAC/trials, executes a set of power measurements using the USRP2. The number of measurements can be modified through the variable 'n_trials' (usrp2_spectrum_sense,line 275). This was the procedure to set the Carrier Sensing threshold used in the MAC operation (uwicore_mac_utils, line 1124).


3.1) Run the script usrp2_spectrum_sense, saving the measurements in an output file.

	$ cd ~/uwicore_80211_MAC/Trials/
	$ sudo ./usrp2_spectrum_sense.py >> output_file.txt

The measured power will be recorded in the specified file.

=====================================
 4. Single packet transmission TRIAL 
=====================================

It is possible to execute the MAC and force a transition to a particular state. 

4.1) Set the scaling time parameter 'beta' to 20000 (uwicore_80211mac.py parameter).

4.2) Modify the variable 'testing = True' (uwicore_80211mac.py, line 126).

4.3) The variable 'ESTADO' (uwicore_80211mac.py, line 248) allows to switch 
manually to any of the Finite State Machine's states by modifying:
	- ESTADO = TRANSMITTING_RTS --> Transmit a RTS frame
	- ESTADO = TRANSMITTING_UNICAST --> Transmit a DATA UNICAST frame
	- ESTADO = TRANSMITTING_FRAGMENTED_PACKET --> Transmit a DATA UNICAST FRAGMENTED frame
	- ESTADO = TRANSMITTING_CTS --> Transmit a CTS frame
	- ESTADO = TRANSMITTING_ACK --> Transmit an ACK frame

4.4) Run PHY, MAC as follows:
	
	$ cd ~/uwicore_MAC/	
	$ sudo ./ftw_ofdm_tx.py -f 5.2G -i 5 -d 16
	$ ./uwicore_phy_rx.py -n 1
	$ ./uwicore_80211mac.py --RTS --V --retx -n 1 --regime=1 --beta=20000

The MAC will start its behavior in the selected state.
 
NOTE: The use of a Wireless Network Analyzer in this trial allows to check whether a generated frame is properly formed.
