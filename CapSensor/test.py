from FDC1004 import Chip, Measurement
import inverse_segmented_fit as fit
from Cap import CapDist
import time
from statistics import mean, variance
import struct, csv, time

channel1 = Measurement(1)
channel1.config(0)
channel2 = Measurement(2)
channel2.config(1)
channel3 = Measurement(3)
channel3.config(2)
channel4 = Measurement(4)
channel4.config(3)
chip = Chip([channel1, channel2, channel3,channel4])
#chip.trigger_single(1)
chip.trigger()
chip.remove_meas(1)
chip.trigger()

"""
print (chip.meas.keys())
time.sleep(3)
print("poll")
chip.poll(time.time())
data2, timeline = chip.get_data(1)
data1, timeline = chip.get_data(1)
print("3 data", data2)
print("2 data", data1)

"""
cap = CapDist(["calibration/cal.csv"], [1,0.4], fit)
POLL_FREQ = 100

i = 1
init = 0
while True:
    time.sleep(1/POLL_FREQ)
    print(chip.poll(time.time()))

    if not (i%10): 
        #data, timeline = chip.get_data(1)
        data2, timeline = chip.get_data(2)
        cap.fill_caps(data2, timeline)
        print("freq: ", len(timeline)/(timeline[-1] - timeline[0]))
        if not init:
            cap.set_offset(mean(data2), 10)
            init = 1
        #print("2 data", data)
        #print("2 data", timeline)
        #print("3 data", data2)
        #print("3 time", timeline)
        if not i%300: 
            dists = cap.poll_dists()
            for d in dists:
                print("caps", d)
    i+=1
    
