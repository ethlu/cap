import matplotlib.pyplot as plt
import numpy as np
from CapSensor.FDC1004 import Chip, Measurement
from CapSensor.Cap import FITS, CapDist
from statistics import mean, variance
import time, os, csv, yaml 

CAL_DIR = os.path.dirname(os.path.realpath(__file__)) + "/calibration/"
POLL_DELAY = 1/300

def sample_cmd(meas_dir_name):
    ch = int(input("Input channel: [1-4] \n"))
    meas = Measurement(1)
    meas.config(ch - 1)
    chip = Chip([meas])
    chip.trigger()

    try:
        sample_t = float(input("Sample time (for each acquisition, in seconds): [3]\n"))
    except Exception:
        sample_t = 3
    sample_i = round(sample_t / chip.poll_delay / 2.5)
    try:
        delay_t = float(input("Delay time (before each acquisition, in seconds): [0]\n"))
    except Exception:
        delay_t = 0
    inc = input("Sample in fixed increments? [y/N]\n").upper()
    if inc == "Y":
        inc = float(input("Increment (mm):\n"))
        dist = float(input("Start distance (mm):\n")) - inc
    else:
        inc = None

    dists, caps = [], []
    while True:
        if inc is None:
            dist = input("Dist (mm): [END if finished sampling]\n")
        else:
            dist = round(dist+inc, 8)
            adj = input("Next dist is {} mm. Proceed? [Y/n]\n".format(dist)).upper()
            if adj == "N":
                newdist = input("Dist (mm): [END if finished sampling, Return if same as last]\n")
                if newdist != "END":
                    dist -= inc
                    if newdist:
                        dist = float(newdist)
                    newinc = input("Increment (mm): [Return if same]\n")
                    if newinc:
                        inc = float(newinc)
                        if newdist:
                            dist -= inc
                    else:
                        dist -= inc
                    continue
                else:
                    dist = "END"

        if dist == "END":
            print("Number of samples: {}".format(len(dists)))
            plot_data = input("Plot calibration data? [Y/n]\n").upper()
            if plot_data != "N":
                try:
                    plot_calibration(caps = caps, dists = dists)
                except Exception as e:
                    print("Error while plotting: {}".format(e))
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
        try:
            dist = float(dist)
        except Exception:
            print("invalid dist")
            continue
        print("Starting acquisition in {}".format(delay_t))
        time.sleep(delay_t)
        print("Start!")
        samples = chip.acq(sample_i)[1]
        try:
            cap_sample = mean(samples)
        except Exception:
            print("mean failed (not enough sample?)")
            continue
        print("Sample mean: {}, SD: {}, size: {}".format(cap_sample, variance(samples)**0.5, len(samples)))
        cmd = input("Keep this sample?: [Y/n]\n").upper()
        if cmd != "N":
            dists.append(dist)
            caps.append(cap_sample)
            print("Saved")

    print("Finished the measurement; now fitting it")
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
            if fit in FITS:
                cal_name += "_" + fit
                fit = FITS[fit]
            else:
                print("Fit type {} not found".format(fit))
                continue
            break
        try:
            cal = fit.generate_cmd(caps, dists)
        except Exception as e:
            print(e)
            continue
        eval_calibration(cal, fit, caps, dists)
        plot = input("Plot the calibration? [Y/n] \n").upper()
        if plot != "N":
            try:
                plot_calibration(cal, fit, caps, dists)
            except Exception as e:
                print("Error while plotting: {}".format(e))
            
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

    plot_data = input("Plot calibration data? [Y/n]\n").upper()
    if plot_data != "N":
        try:
            plot_calibration(caps = caps, dists = dists)
        except Exception as e:
            print("Error while plotting: {}".format(e))

    
    while True:
        opt = int(input("Options: [1: Add calibrations (fits), 2: Examine existing calibrations, 3. Return to main menu]\n"))
        if opt == 3:
            return True
        if opt == 1:
            fit_cmd(meas_dir_name, caps, dists)
        else:
            files = os.listdir(meas_dir_name)
            while True:
                while True:
                    cal_name = input("Calibration name: [END to stop examining, ls to list existing]\n")
                    if cal_name != "ls":
                        break
                    print([f[:f.rfind('_')] for f in files if f.rfind('_') != -1])
                if cal_name == "END":
                    break
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
                        except Exception as e:
                            print("Error while plotting: {}".format(e))

def plot_calibration(cal = None, fit = None, caps = None, dists = None):
    plt.figure(1)
    plt.ylabel('dists (mm)')
    plt.xlabel('caps (pF)')
    plt.figure(2)
    plt.xlabel('dists (mm)')
    plt.ylabel('caps (pF)')
    if caps is not None:
        plt.figure(1)
        plt.plot(caps, dists, 'ro')
        plt.figure(2)
        plt.plot(dists, caps, 'ro')
    if cal is not None:
        offset = []
        for cap, dist in zip(caps, dists):
            offset.append(fit.cap_offset(cal, cap, dist))
        offset = mean(offset)
        plot_min = offset + fit.cap_offsetted_estimate(cal, max(dists) * 1.5)
        plot_max = offset + (max(caps) - offset) * 1.5
        step = (plot_max - plot_min) / 100
        c = np.arange(plot_min, plot_max, step)
        c_offseted = np.linspace(plot_min - offset, plot_max - offset, len(c))
        dist_func = np.vectorize(fit.dist_estimate, excluded=['cal'])
        d = dist_func(cal=cal, cap_offsetted=c_offseted)
        plt.figure(1)
        plt.plot(c, d)
        plt.figure(2)
        plt.plot(d, c)
    print("Close Figures to Proceed")
    plt.show()

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
        if est is None or est < 0:
            print("Nonsensical estimate, ignored")
            continue
        squared_error += (dist - est)**2
    print("RMS error w/ mean offset: {} (mm)".format((squared_error/len(caps))**0.5))

    mid_ind = int(len(caps)/2)
    offset = fit.cap_offset(cal, caps[mid_ind], dists[mid_ind]) 
    squared_error = 0
    for cap, dist in zip(caps, dists):
        est = fit.dist_estimate(cal, cap - offset)
        print("Actual dist: {}, Estimate: {}".format(dist, est))
        if est is None or est < 0:
            print("Nonsensical estimate, ignored")
            continue
        squared_error += (dist - est)**2
    print("RMS error w/ single offset: {} (mm)".format((squared_error/len(caps))**0.5))

def meas_cap_builder(config_file):
    meas_cap = {}
    with open(CAL_DIR + config_file, "r") as f:
        config = yaml.safe_load(f)
    for meas_num in range(1, 5):
        meas_config = config.get(meas_num)
        if meas_config is not None:
            meas_name = meas_config["meas_name"]
            meas_dir_name = CAL_DIR + meas_name + '/'
            files = os.listdir(meas_dir_name)
            meas = Measurement(meas_num, meas_name)
            meas.config(meas_config["channel"] - 1)
            t_intervals = meas_config["t_intervals"]
            cals = []
            for cal_name in meas_config["cal_names"]:
                cal_name.replace(" ", "_")
                matches = [f for f in files if f.startswith(cal_name)]
                for f in matches:
                    fit = f[len(cal_name) + 1:]
                    fit = FITS[fit]
                    cals.append(CapDist(meas_dir_name + f, t_intervals, fit, cal_name))
            meas_cap[meas] = cals
    return meas_cap


if __name__ == "__main__":
    while True:
        opt = int(input("Menu: [1: New measurement, 2: Check out existing measurement]\n"))
        while True:
            meas_name = input("Measurement name: [ls to list existing]\n")
            if meas_name != "ls":
                break
            print([f.name for f in os.scandir(CAL_DIR) if f.is_dir()])

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


