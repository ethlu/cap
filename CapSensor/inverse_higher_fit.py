import numpy as np
import csv

def generate_cmd(caps, dists):
    try:
        order = int(input("Degree of inverse polynomial: [2]\n"))
    except Exception:
        order = 2 
    inp = input("Model the object when it's floating (assuming it's currently grounded)? [y/N]\n").upper()
    cap_obj = () 
    if inp == "Y":
        try:
            c_og = float(input("Object's capacitance to ground (pF): [200]\n"))
        except Exception:
            c_og = 200 
        try:
            c_os = float(input("Object's capacitance to shield (pF): [1]\n"))
        except Exception:
            c_os = 1
        cap_obj = (c_og, c_os)
    return generate_cal(caps, dists, order, cap_obj)

def generate_cal(caps, dists, order = 2, cap_obj = ()):
    X = []
    for d in dists:
        X.append([d**(-i) for i in range(order + 1)])
    fit, res, _, _ = np.linalg.lstsq(X, caps, None) 
    fit = [round(c, 6) for c in fit]
    return fit[1:], cap_obj

def dist_estimate(cal, cap_offsetted):
    cal, cap_obj = cal
    if not cap_obj:
        p = [cap_offsetted] + [-c for c in cal]
    else:
        c_og, c_os = cap_obj
        p = [cap_offsetted*(c_og+c_os)/(c_og-cap_offsetted)] + [-c for c in cal]
    roots = np.roots(p)
    for r in roots:
        if np.isreal(r) and r>0:
            return float(r)

def cap_offsetted_estimate(cal, dist):
    cal, cap_obj = cal
    inverse_dist = 1.0/dist 
    order, ret = 1, 0
    for c in cal:
        ret += c * (inverse_dist ** order)
        order += 1
    if cap_obj:
        c_og, c_os = cap_obj
        ret = ret * c_og/(ret + c_og + c_os)
    return ret

def cap_offset(cal, cap, dist):
    return cap - cap_offsetted_estimate(cal, dist)

def write_cal(cal, cal_file):
    with open(cal_file, "w") as f:
        writer = csv.writer(f)
        writer.writerows(cal)

def read_cal(cal_file):
    with open(cal_file, "r") as f:
        reader = csv.reader(f)
        row = list(map(float, next(reader)))
        cap_obj = list(map(float, next(reader)))
        return [float(x) for x in row], cap_obj 


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

