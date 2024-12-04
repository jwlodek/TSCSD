from ophyd import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO
from ophyd import Component as Cpt
from ophyd.status import SubscriptionStatus
from bluesky.callbacks.tiled_writer import TiledWriter
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.run_engine import RunEngine
from bluesky.protocols import Movable

from bluesky.plan_stubs import mv
from bluesky.plans import count, scan, grid_scan
import time as ttime

from tiled.client import from_uri

# Wait a few seconds for IOC to start
ttime.sleep(3)

def dump_doc_to_stdout(name, doc):
    print("========= Emitting Doc =============")
    print(f"{name = }")
    print(f"{doc = }")
    print("============ Done ============")

RE = RunEngine({})
# RE.subscribe(dump_doc_to_stdout)

bec = BestEffortCallback()
RE.subscribe(bec)

tiled_client = from_uri("http://localhost:8000", api_key="TSCSD")

tw = TiledWriter(tiled_client)

RE.subscribe(tw)

class TSCSDChannel(Device, Movable):

    ramp_rate_set = Cpt(EpicsSignal, "RR:SET", name="ramp_rate", kind="config")
    setpoint = Cpt(EpicsSignal, "SP:SET", name="ramp_rate", kind="config")
    ramp_rate = Cpt(EpicsSignal, "RR", name="ramp_rate", kind="hinted")
    value = Cpt(EpicsSignal, "RB", name="value", kind="hinted")
    at_setpoint = Cpt(EpicsSignalRO, "ATSP", name="at_setpoint", kind="omitted")

    def set(self, value):

        def is_at_rest_callback(value, old_value, **kwargs):
            if value == 1 and old_value == 0:
                return True
            return False
        
        status = SubscriptionStatus(self.at_setpoint, run=False, callback=is_at_rest_callback)
        self.setpoint.put(value)
        return status

class TSCSD(Device):
    chan_1 = Cpt(TSCSDChannel, "1:", name="chan_1")
    chan_2 = Cpt(TSCSDChannel, "2:", name="chan_2")
    chan_3 = Cpt(TSCSDChannel, "3:", name="chan_3")
    chan_4 = Cpt(TSCSDChannel, "4:", name="chan_4")


tscsd = TSCSD("DEV:TSCSD1:", name="tscsd")