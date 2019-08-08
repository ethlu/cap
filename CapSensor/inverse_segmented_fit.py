import numpy as np
import csv


def generate_cal(caps, dists, regions, minimum_sample):
    """regions are each region's lower bound (of distance), in descending order"""
    decrease_dist_data = sorted(zip(caps, dists),reverse = True, key = lambda x: x[1])
    data = np.array(decrease_dist_data).T
    caps = data[0]
    dists = data[1]
    inverse_dists = np.reciprocal(data[1])

    r, i, j = 0, 0, 0
    r_max = len(regions)
    j_max = dists.size
    A = []
    while r < r_max and j < j_max:
        if dists[j] >= regions[r]:
            j += 1
        else:
            if j - i < minimum_sample:
                raise Exception('too few samples at: {}'.format(regions[r]))
            A.append(np.polyfit(inverse_dists[i:j], caps[i:j],1)[0])
            i = j
            r += 1

    if r == r_max - 1:
        if j - i < minimum_sample:
            raise Exception('too few samples at: {}'.format(regions[r]))
        A.append(np.polyfit(inverse_dists[i:j], caps[i:j],1)[0])
    elif r < r_max:
        raise Exception('no sample beyond: {}'.format(regions[r]))

    B = [0]
    for i in range(1, r_max):
        B.append((A[i-1] - A[i])/regions[i-1] + B[-1])
    C = [A[i]/regions[i] + B[i] for i in range(r_max)]

    return (A, B, C, regions)

def dist_estimate(cal, cap_offsetted):
    A, B, C, D = cal
    if cap_offsetted >= C[-1]:
        raise Exception('cap too high')
    i = 0
    while cap_offsetted >= C[i]:
        i += 1
    return A[i]/(cap_offsetted - B[i])

def dists_estimate(cal, caps, offset):
    A, B, C, D = cal
    if caps[0] >= C[-1]:
        raise Exception('cap too high')
    i = 0
    while caps[0] >= C[i]:
        i += 1
    a, b = A[i], B[i]
    return [a/(cap - offset- b) for cap in caps]

def cap_offsetted_estimate(cal, dist):
    A, B, C, D= cal
    if dist <= D[-1]:
        raise Exception('dist too short')
    i = 0
    while dist <= D[i]:
        i += 1
    return A[i]/dist + B[i]

def cap_offset(cal, cap, dist):
    return cap - cap_offsetted_estimate(cal, dist)

def write_cal(cal, cal_file):
    with open(cal_file, "w") as f:
        writer = csv.writer(f)
        writer.writerows(cal)

def read_cal(cal_file):
    with open(cal_file, "r") as f:
        reader = csv.reader(f)
        return [[float(x) for x in row] for row in reader]


if __name__ == "__main__":
    dists = [14.4, 13.595, 12.79, 12.3875, 11.98, 11.58, 11.18, 10.775, 10.375, 9.972, 9.57, \
            9.1675]
    caps = [2.622, 2.628, 2.632, 2.634, 2.636, 2.638, 2.641, 2.643, 2.6465, 2.65, 2.652, 2.656]

    cal= generate_cal(caps, dists, [10.5, 0], 3)
    oe = cap_offset(cal, 2.656, 9.16)

    print(cal)
    print(oe)
    print(dist_estimate(cal, 2.65-oe))
    print(dists_estimate(cal, (2.64-oe, 2.65-oe)))

    csvfile = "cal.csv"
    write_cal(cal, csvfile)

