import inverse_segmented_fit 
from statistics import mean

class CapDist:
    def __init__(self, cal_args, time_intervals, fit=inverse_segmented_fit):
        self.fit = fit
        if len(cal_args) == 1:
            self.cal = fit.read_cal(cal_args[0])
        else:
            self.cal = fit.generate_cal(*cal_args)
        self.offset = 0
        self.origin = 0
        self.dists, self.times = [], []
        self.avgs = [self.DistAvg(i) for i in time_intervals]

    def set_offset(self, *args):
        self.offset = self.fit.cap_offset(self.cal, *args)

    def set_origin(self, origin_dist):
        self.origin = origin_dist

    def fill_caps(self, caps, times):
        self.dists += [self.dist_estimate(cap) for cap in caps]
        self.times += times

    def poll_dists(self, reset = False):
        ret = [(list(self.dists), list(self.times))]
        for avg in self.avgs:
            avg.dists += self.dists
            avg.times += self.times
            ret.append(avg.poll_dists(reset))
        self.times.clear()
        self.dists.clear()
        return ret

    def dist_estimate(self, cap):
        return self.fit.dist_estimate(self.cal, cap - self.offset) - self.origin

    def dists_estimate(self, caps):
        return self.fit.dists_estimate(self.cal, caps, self.offset)

    class DistAvg:
        time_interval_error = 0.1
        def __init__(self, time_interval):
            self.t_int = time_interval
            t_interval_err = time_interval*self.time_interval_error
            self.t_int_upper = time_interval + t_interval_err
            self.t_int_lower = time_interval - t_interval_err
            self.i_interval = 0
            self.dists, self.times = [], []

        def poll_dists(self, reset):
            if reset:
                self.i_interval = 0
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
                dists.append(mean(self.dists[i:j]))
                i = j
                j += self.i_interval
            self.times = self.times[i:]
            self.dists = self.dists[i:]
            return dists, start_times
