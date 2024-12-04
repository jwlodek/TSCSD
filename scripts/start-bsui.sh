#!/bin/bash

cd $(dirname "$0")/..

# export EPICS_CA_AUTO_ADDR_LIST="NO"
# export EPICS_CA_ADDR_LIST="127.0.0.1"
# export EPICS_CAS_AUTO_BEACON_ADDR_LIST="NO"
# export EPICS_CAS_BEACON_ADDR_LIST="127.0.0.1"
# export EPICS_CAS_INTF_ADDR_LIST="127.0.0.1"

# export EPICS_PVA_AUTO_ADDR_LIST="NO"
# export EPICS_PVA_ADDR_LIST="127.0.0.1"
# export EPICS_PVAS_AUTO_BEACON_ADDR_LIST="NO"
# export EPICS_PVAS_BEACON_ADDR_LIST="127.0.0.1"
# export EPICS_PVAS_INTF_ADDR_LIST="127.0.0.1"

ipython -i scripts/bs_profile.py