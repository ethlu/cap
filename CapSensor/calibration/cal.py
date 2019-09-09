from CapSensor.FDC1004 import Measurement
from CapSensor.Cap import CapDist
import CapSensor.inverse_segmented_fit as fit

import os
dn = os.path.dirname(os.path.realpath(__file__)) 

def meas_cap_builder():
    TIME_INTERVALS = [1 ,10]
    meas_cap = {}

    ch1 = Measurement(1)
    ch1.config(0)
    cal1 = [CapDist([dn + "/cal.csv"], TIME_INTERVALS, fit)]
    meas_cap[ch1] = cal1

    ch2 = Measurement(2)
    ch2.config(1)
    cal2 = [CapDist([dn + "/cal.csv"], TIME_INTERVALS, fit)]
    meas_cap[ch2] = cal2

    return meas_cap
