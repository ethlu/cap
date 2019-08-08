from FDC1004 import Chip, Measurement
import inverse_segmented_fit 
from statistics import mean

class CapDist():
    time_interval_error = 0.1
    def __init__(self, cal_args, time_interval, fit=inverse_segmented_fit):
        self.fit = fit
        if len(cal_args) == 1:
            self.cal = fit.read_cal(cal_args[0])
        else:
            self.cal = fit.generate_cal(*cal_args)
        self.t_int = time_interval
        t_interval_err = time_interval*CapDist.time_interval_error
        self.t_int_upper = time_interval + t_interval_err
        self.t_int_lower = time_interval - t_interval_err
        self.i_interval = 0
        self.offset = 0
        self.caps, self.times = [], []

    def set_offset(self, *args):
        self.offset = self.fit.cap_offset(self.cal, *args)

    def fill_caps(self, caps, times):
        self.caps += caps
        self.times += times

    def poll_dists(self, forced = False):
        i, j = 0, self.i_interval 
        j_max = len(self.times)
        start_times = []
        dists = []
        while j < j_max:
            t_interval = self.times[j] - self.times[i]
            if t_interval < self.t_int_lower:
                j += 1
                while True:
                    if j == j_max:
                        self.i_interval = j - i
                        break
                    if self.times[j] - self.times[i] < self.t_int:
                        j += 1
                    else: 
                        self.i_interval = j - i
                        break
                continue
            if t_interval > self.t_int_upper:
                j -= 1
                while self.times[j] - self.times[i] > self.t_int:
                    j -= 1
                self.i_interval = j - i
            start_times.append(self.times[i])
            dists.append(mean(self.dists_estimate(self.caps[i:j])))
            i = j
            j += self.i_interval
        if forced or self.times[-1] - self.times[i] >= self.t_int_lower:
            start_times.append(self.times[i])
            dists.append(mean(self.dists_estimate(self.caps[i:])))
            self.times.clear()
            self.caps.clear()
        else:
            self.times = self.times[i:]
            self.caps = self.caps[i:]
        return dists, start_times

    def dist_estimate(self, cap):
        return self.fit.dist_estimate(self.cal, cap - self.offset)
    
    def dists_estimate(self, caps):
        return self.fit.dists_estimate(self.cal, caps, self.offset)


