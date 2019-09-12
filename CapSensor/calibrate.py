#import matplotlib.pyplot as plt
import numpy as np
from CapSensor.FDC1004 import Chip, Measurement
from CapSensor.Cap import FITS
from statistics import mean, variance
import time, os, csv

CAL_DIR = "./calibration/"
POLL_DELAY = 1/300

def sample_cmd(meas_dir_name):
    ch = int(input("Input channel: [1-4] \n"))
    meas = Measurement(1)
    meas.config(ch - 1)
    chip = Chip([meas])
    chip.trigger()

    sample_t = int(input("Sample time (for each acquisition, in seconds):\n"))
    sample_i = round(sample_t / POLL_DELAY / 2.5)
    delay_t = int(input("Delay time (before each acquisition, in seconds):\n"))

    dists, caps = [], []
    while True:
        dist = input("Dist (mm): [END if finished sampling]\n")
        if dist == "END":
            print("Number of samples: {}".format(len(dists)))
            write = input("Write data to file? [Y/n]\n").upper()
            if write != "N":
                filename = meas_dir_name + "data.csv"
                if os.path.exists(filename):
                    overwrite = input("Data file {} exists. Overwrite anyway? [y/N]\n".format(filename)).upper()
                    if overwrite != "Y":
                        break
                with open(filename, "w") as f:
                    writer = csv.writer(f)
                    writer.writerows([caps, dists])
                print("Data file {} written.".format(filename))
            break
        print("Starting acquisition in {}".format(delay_t))
        time.sleep(delay_t)
        print("Start!")
        for i in range(sample_i):
            chip.poll()
            time.sleep(POLL_DELAY)
        samples, _ = meas.get_data()
        cap_sample = mean(samples)
        print("Sample mean: {}, SD: {}, size: {}".format(cap_sample, variance(samples)**0.5, len(samples)))
        cmd = input("Keep this sample?: [Y/n]\n").upper()
        if cmd != "N":
            dists.append(float(dist))
            caps.append(cap_sample)
            print("Saved")

    fit_cmd(meas_dir_name, caps, dists)

def fit_cmd(meas_dir_name, caps, dists):
    while True:
        cal_name = input("Calibration name: [END to finish calibration]\n")
        if cal_name == "END":
            return True
        cal_name.replace(" ", "_")
        while True:
            fit = input("Fit type: [OPT to show options] \n")
            if fit == "OPT":
                print("Available fit types: "+", ".join(FITS.keys()))
                continue
            cal_name += "_" + fit
            try:
                fit = FITS[fit]
            except KeyError:
                print("Fit type {} not found".format(fit))
                continue
            break
        cal = fit.generate_cmd(caps, dists)
        eval_calibration(cal, fit, caps, dists)
        plot = input("Plot the calibration? [Y/n] \n").upper()
        if plot != "N":
            try:
                plot_calibration(cal, fit, caps, dists)
            except:
                print("Error while plotting")
            #plt.close()
            #plt.clf()
            
        save = input("Save this calibration? [Y/n]\n").upper()
        if save != "N":
            filename = meas_dir_name + cal_name
            if os.path.exists(filename):
                overwrite = input("Data file {} exists. Overwrite anyway? [y/N]\n".format(filename)).upper()
                if overwrite != "Y":
                    continue
            fit.write_cal(cal, filename)
            print("Cal file {} written.".format(filename))

def examine_cmd(meas_dir_name):
    filename = meas_dir_name + "data.csv"
    try:
        with open(filename, "r") as f:
            reader = csv.reader(f)
            caps = [float(x) for x in next(reader)]
            dists = [float(x) for x in next(reader)]
    except FileNotFoundError:
        print("Error, data file \'{}\' doesn't exist.".format(filename))
        return False

    print_data = input("Print calibration data? [Y/n]\n").upper()
    if print_data != "N":
        data_str = "Calibration data: [Capacitance, Distance] \n"
        for cap, dist in zip(caps, dists):
            data_str += "{}, {}\n".format(cap, dist)
        print(data_str)
    
    add_fit = input("Add more calibrations (fits)? [y/N]\n").upper()
    if add_fit == "Y":
        fit_cmd(meas_dir_name, caps, dists)
        return True

    eval_fit = input("Examine calibrations? [Y/n]\n").upper()
    if eval_fit == "N":
        return True

    files = os.listdir(meas_dir_name)
    while True:
        cal_name = input("Calibration name: [END to stop examining]\n")
        if cal_name == "END":
            return True
        cal_name.replace(" ", "_")
        matches = [f for f in files if f.startswith(cal_name)]
        if not matches:
            print("No calibration with name: {}".format(cal_name))
        for f in matches:
            fit = f[len(cal_name) + 1:]
            print("Fit type: {}".format(fit))
            try:
                fit = FITS[fit]
            except KeyError:
                print("Fit type {} not found".format(fit))
                continue
            cal = fit.read_cal(meas_dir_name + f)
            eval_calibration(cal, fit, caps, dists)
            plot = input("Plot the calibration? [Y/n] \n").upper()
            if plot != "N":
                try:
                    plot_calibration(cal, fit, caps, dists)
                except:
                    print("Error while plotting")

    

def plot_calibration(cal, fit, caps = None, dists = None):
    if caps is not None:
        plt.plot(caps, dists, 'ro')
    offset = []
    for cap, dist in zip(caps, dists):
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

def eval_calibration(cal, fit, caps, dists):
    print("Cal: {}".format(cal))
    caps = np.array(caps) 
    dists = np.array(dists)
    offset = []
    for cap, dist in zip(caps, dists):
        offset.append(fit.cap_offset(cal, cap, dist))
    offset = mean(offset)
    squared_error = 0
    for cap, dist in zip(caps, dists):
        est = fit.dist_estimate(cal, cap - offset)
        print("Actual dist: {}, Estimate: {}".format(dist, est))
        squared_error += (dist - est)**2
    print("Average squared error: {} (mm^2)".format(squared_error/len(caps)))

if __name__ == "__main__":
    while True:
        opt = int(input("Options: [1: New calibration (of a measurement), 2: Work with existing data]\n"))
        meas_name = input("Measurement name: ")
        meas_name.replace(" ", "_")
        meas_dir_name = CAL_DIR + meas_name + '/'
        if opt == 1:
            try:
                os.mkdir(meas_dir_name)
                print("Made calibration directory {}".format(meas_dir_name)) 
            except FileExistsError:
                print("Directory {} already exists. Will double check if overwriting stuff.".format(meas_dir_name))
            sample_cmd(meas_dir_name)
        elif opt == 2:
            examine_cmd(meas_dir_name)


