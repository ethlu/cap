import numpy as np
from scipy.optimize import curve_fit
import csv

def generate_cmd(caps, dists):
    order = int(input("Degree of inverse polynomial: \n"))
    cons = ([],[])
    p0 = []
    for o in range(order+1):
        inp = input("Bounds and initial value on {}th order coefficient: "
        "[min max initial] (default is non-negative and 1)\n".format(o))
        if not inp:
            cons[0].append(0)
            cons[1].append(np.inf)
            p0.append(1)
        else:
            lower = float(inp.split()[0])
            upper = float(inp.split()[1])
            if lower == upper:
                upper += 1E-10
            cons[0].append(lower)
            cons[1].append(upper)
            p0.append(float(inp.split()[2]))
    return generate_cal(caps, dists, order, cons, p0)

def generate_cal(caps, dists, order = 3, cons = (0, np.inf), p0 = None):
    if p0 is None:
        p0 = np.ones(order+1)
    def func(*argv):
        argv = list(argv)
        p = np.poly1d(argv[:0:-1])
        return p(argv[0])
    inverse_dists = np.reciprocal(dists)
    fit, _ = curve_fit(func, inverse_dists, caps, p0, bounds = cons)
    fit = [c if abs(c) > 1E-10 else 0 for c in fit]
    return fit[1:]

def dist_estimate(cal, cap_offsetted):
    p = [cap_offsetted] + [-c for c in cal]
    roots = np.roots(p)
    for r in roots:
        if np.isreal(r) and r>0:
            return float(r)

def cap_offsetted_estimate(cal, dist):
    inverse_dist = 1.0/dist 
    order, ret = 1, 0
    for c in cal:
        ret += c * (inverse_dist ** order)
        order += 1
    return ret

def cap_offset(cal, cap, dist):
    return cap - cap_offsetted_estimate(cal, dist)

def write_cal(cal, cal_file):
    with open(cal_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(cal)

def read_cal(cal_file):
    with open(cal_file, "r") as f:
        reader = csv.reader(f)
        row = next(reader)
        return [float(x) for x in row]


if __name__ == "__main__":
    dists = [14.4, 13.595, 12.79, 12.3875, 11.98, 11.58, 11.18, 10.775, 10.375, 9.972, 9.57, \
            9.1675]
    caps = [2.622, 2.628, 2.632, 2.634, 2.636, 2.638, 2.641, 2.643, 2.6465, 2.65, 2.652, 2.656]

    cal= generate_cal(caps, dists)
    
    oe = cap_offset(cal, 2.656, 9.16)

    print(cal)
    print(oe)
    print(dist_estimate(cal, 2.622-oe))

    csvfile = "cal.csv"
    write_cal(cal, csvfile)

