from FDC1004 import Chip, Measurement
import inverse_segmented_fit as fit
from Cap import CapDist
import time
from statistics import mean, variance
import struct, csv, time, operator
import numpy as np

def save_caps(meas_nums, f, sec):
    i = 1
    singles = [[],[],[],[]]
    means = [[],[],[],[]]
    mean_n = 100
    while i<=sec/chip.poll_delay/5/mean_n:
        d = chip.acq(mean_n)
        for n in meas_nums:
            print("Channel "+str(n))
            data = d[n]
            print(mean(data), variance(data)**0.5)
            #print(chip.meas[n].CAPDAC)
            singles[n-1]+=data
            means[n-1].append(mean(data))
        i+=1
    with open(f, "w+") as f:
        writer = csv.writer(f)
        writer.writerow(["individual data"])
        writer.writerows(singles)
        writer.writerow(["means"])
        writer.writerows(means)

def ds_dc_two(sens_meas, cap_meas, chip, nognd = None, num_sample = 300):
    if nognd is None:
        input("Return to proceed with no ground")
        data = chip.acq(num_sample)
        cap_min = mean(data[cap_meas])
        sens_min = mean(data[sens_meas])
        print("cap: {}, sens: {}".format(cap_min, sens_min))
    else:
        sens_min, cap_min = nognd 

    input("Return to proceed with ground")
    data = chip.acq(num_sample)
    cap_max = mean(data[cap_meas])
    sens_max = mean(data[sens_meas])
    print("cap: {}, sens: {}".format(cap_max, sens_max))
    ds_dc = (sens_max-sens_min)/(cap_max-cap_min)
    print("ds_dc: ", ds_dc)
    return ds_dc, sens_min, cap_min, sens_max, cap_max

def ds_dc_reg(sens_meas, cap_meas, chip):
    input("ds_dc_reg: Return to proceed")
    time.sleep(1)
    print("start")
    cap_means, sens_means = [], []
    for _ in range(15):
        data = chip.acq(100)
        cap_means.append(mean(data[cap_meas]))
        sens_means.append(mean(data[sens_meas]))
    print("sens extremas: {}, {}".format(min(sens_means), max(sens_means)))
    A = np.vstack([cap_means, np.ones(len(cap_means))]).T
    reg = np.linalg.lstsq(A, sens_means, rcond = None)
    print(reg[0][0])
    print(reg[0][1])
    rms = (reg[1][0]/len(cap_means))**0.5
    print(rms)
    return (reg[0][0], reg[0][1], rms), (sens_means, cap_means)

def print_caps(meas_nums, calibrate = None):
    i = 1
    means = [[],[],[],[]]
    cap_mean = None
    while True:
        chip.poll()
        i+=1
        time.sleep(1/POLL_FREQ)
        if calibrate is not None: 
            if i<300:
                continue
            cap_mean = mean(chip.get_data(meas_nums[1])[0])
            sens_mean = mean(chip.get_data(meas_nums[0])[0])
            ds_dc = calibrate
            calibrate = None
            print("calibrated")
            i = 1
        if not i%300:
            if cap_mean is not None:
                sens_data = chip.get_data(meas_nums[0])[0]
                cap_data = chip.get_data(meas_nums[1])[0]
                offsets = [(c - cap_mean)*ds_dc for c in cap_data]
                calibrated = list(map(operator.sub, sens_data, offsets))
                print("raw sensor: ", mean(sens_data), variance(sens_data)**0.5)
                print("calib sensor: ", mean(calibrated), variance(calibrated)**0.5)
                print("diff raw sensor: ", mean(sens_data) - sens_mean)
                print("diff calib sensor: ", mean(calibrated) - sens_mean)

            else:
                for n in meas_nums:
                    print("Channel "+str(n))
                    data = chip.get_data(n)[0]
                    print(mean(data), variance(data)**0.5)
                    means[n-1].append(mean(data))
                    """
                    if n == 2:
                        ch3 = data
                    if n == 4:
                        diff = list(map(operator.sub, ch3, data))
                        print("diff:", mean(diff), variance(diff)**0.5)
                    """

        """
        if not i%500:
            for n in meas_nums:
                print("Channel "+str(n))
                print(means[n-1])
                print("SD of means", variance(means[n-1])**0.5)
                """

def test_capdist():
    cap = CapDist("calibration/captest/1_inverse.csv", [1,0.4], fit)
    i = 1
    init = 0
    while True:
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
        time.sleep(1/POLL_FREQ)
        
if __name__ == "__main__":
    channel1 = Measurement(1)
    channel1.config(0)
    channel2 = Measurement(2)
    channel2.config(1)
    channel3 = Measurement(3)
    channel3.config(2)
    #channel3.config(0,2)
    channel4 = Measurement(4)
    channel4.config(3)
    chip = Chip([channel1, channel2, channel3,channel4])
    #chip.remove_meas(4)
    #chip.trigger_single(1)
    chip.trigger()

    POLL_FREQ = 300
    #ds_dc_two(1,3,chip)
    #print_caps([1,2,3,4])
    #print_caps([1])
    #print_caps([1, 3], .144)
    while 1!=1:
        """
        ds_dc_two(1, 3, chip)
        ds_dc_reg(1, 3, chip)
        """
        data = chip.acq(300)
        print("sens ",mean(data[2]))
        print("cap ",mean(data[3]))
        print("sens sd ",variance(data[2])**0.5)
        print("cap sd ",variance(data[3])**0.5)
    save_caps([1,2, 3, 4], "parasitic.csv", 2000)

