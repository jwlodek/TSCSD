#!./bin/linux-x86_64/tscsd

############################################################################
# Limit EPICS traffic to localhost network only.
#
epicsEnvSet("EPICS_CA_AUTO_ADDR_LIST",         "NO")
epicsEnvSet("EPICS_CA_ADDR_LIST",              "127.0.0.1")
epicsEnvSet("EPICS_CAS_AUTO_BEACON_ADDR_LIST", "NO")
epicsEnvSet("EPICS_CAS_BEACON_ADDR_LIST",      "127.0.0.1")
epicsEnvSet("EPICS_CAS_INTF_ADDR_LIST",        "127.0.0.1")

epicsEnvSet("EPICS_PVA_AUTO_ADDR_LIST",         "NO")
epicsEnvSet("EPICS_PVA_ADDR_LIST",              "127.0.0.1")
epicsEnvSet("EPICS_PVAS_AUTO_BEACON_ADDR_LIST", "NO")
epicsEnvSet("EPICS_PVAS_BEACON_ADDR_LIST",      "127.0.0.1")
epicsEnvSet("EPICS_PVAS_INTF_ADDR_LIST",        "127.0.0.1")
#
############################################################################
#
# Setup necessary environment variables
#
epicsEnvSet("TSCSD", ".")
epicsEnvSet("PORT", "TSCSD1")
epicsEnvSet("PREFIX", "DEV:TSCSD1:")
#
############################################################################
#
# Define search path for stream protocol file
#
epicsEnvSet("STREAM_PROTOCOL_PATH", "$(TSCSD)/protocol")
#
############################################################################
#
# Load EPICS database definition file
#
dbLoadDatabase("$(TSCSD)/dbd/tscsd.dbd",0,0)
tscsd_registerRecordDeviceDriver(pdbbase)
#
############################################################################
#
# Configure the TCP socket connection to the simulation
#
drvAsynIPPortConfigure("$(PORT)", "127.0.0.1:8888")
asynOctetSetOutputEos("$(PORT)", 0, "\n")
asynOctetSetInputEos("$(PORT)", 0, "\n")
############################################################################
#
# Load a generic asyn record database for low level I/O
#
dbLoadRecords("$(TSCSD)/db/asynRecord.db", "PORT=$(PORT), P=$(PREFIX), R=Asyn, ADDR=0, OMAX=0, IMAX=0")
#
############################################################################
#
# Load databases for the device and each channel.
#
dbLoadTemplate("$(TSCSD)/db/tscsd.substitutions")
#
############################################################################
#
# Configure certain environment variables
#
iocInit()
#
############################################################################
#
# Initialization of EPICS IOC for TSCSD complete!
#

dbl