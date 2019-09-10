import matplotlib.pyplot as plt
from CapSensor.FDC1004 import Chip, Measurement
from CapSensor.Cap import FITS
import time
from statistics import mean, variance
import os

CAL_DIR = "calibration/"
POLL_DELAY = 1/300

def calibrate_meas_cmd():

    meas_name = input("Measurement name: ")
    meas_name.replace(" ", "_")
    dir_name = CAL_DIR + meas_name + '/'
    try:
        os.mkdir(dir_name)
        print("made calibration directory {}".format(dir_name)) 
    except FileExistsError:
        print("directory {} already existed, might overwrite stuff.".format(dir_name))

    ch = int(input("Input channel: [1-4] \n"))
    meas = Measurement(1)
    meas.config(ch - 1)
    #chip = Chip([meas])
    #chip.trigger()

    sample_t = int(input("Sample time (for each acquisition, in seconds): "))
    sample_i = round(sample_t / POLL_DELAY)
    delay_t = int(input("Delay time (before each acquisition, in seconds): "))

    dists, caps = [], []
    state = 1
    while True:
        if state == 1:
            dist = input("Dist (mm): [END to quit sampling]\n")
            if dist == "END":
                state = 2
                continue
            print("Starting acquisition in {}".format(delay_t))
            time.sleep(delay_t)
            print("Start!")
            for i in range(sample_i):
                #chip.poll()
                time.sleep(POLL_DELAY)
            print("Ended")
            caps, _ = meas.get_data()
            cap_sample = mean(caps)
            print("Sample mean: {}, SD: {}".format(cap_sample, variance(caps)**0.5))
            cmd = input("Keep this sample?: [Y/n]\n")
            if cmd == "Y":
                dists.append(float(dist))
                caps.append(cap_sample)
                print("Saved")
        if state == 2:
            cal_name = input("Calibration name: [END to finish calibration]")
            if cal_name == "END":
                return
            cal_name.replace(" ", "_")
            fit = input("Fit type: [OPT to show options]")
            if fit == "OPT":
                print(", ".join(FITS.keys()))
                continue
            cal_name = cal_name + fit
            fit = FITS[fit]
            cal = fit.generate_cmd(caps, dists)
            plot = input("Plot the calibration? [Y/n]")
            if plot:
                plt.plot(caps, dists, 'ro')
                offset = []
                for i in range(len(dists)):
                    offset.append(fit.cap_offset(cal, caps[i], dists[i]))
                offset = mean(offset)
                caps_sorted = sorted(caps)
                plot_min = caps_sorted[0] * 0.5
                plot_max = caps_sorted[-1] * 2
                c = np.arange(plot_min, plot_max, 0.01)
                c_offseted = np.arange(plot_min - offset, plot_max - offset, 0.01)
                d = fit.dist_estimate(cal, c_offseted)
                plt.plot(c, d)
                plt.show(block=False)
            save = input("Save this calibration? [Y/n]")
            if save:
                fit.write_cal(cal, dir_name + cal_name)
                plt.close()
                plt.clf()



if __name__ == "__main__":
    calibrate_meas_cmd()








            

