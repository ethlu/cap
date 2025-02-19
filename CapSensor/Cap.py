from statistics import mean
from CapSensor import inverse_segmented_fit, inverse_higher_fit
FITS = {"segmented": inverse_segmented_fit,
        "higher": inverse_higher_fit}

class CapDist:
    def __init__(self, cal_file, time_intervals, fit, name = None):
        self.fit = fit
        self.cal = fit.read_cal(cal_file)
        if name is None:
            self.name = "capdist"
        else:
            self.name = name
        self.init = False
        self.offset = 0
        self.origin = 0
        self.caps, self.times = [], []
        self.avgs = [self.DistAvg(i, self) for i in time_intervals]

    def set_offset(self, *args):
        self.offset = self.fit.cap_offset(self.cal, *args)
        self.init = True

    def set_origin(self, origin_dist):
        self.origin = origin_dist

    def fill_caps(self, caps, times):
        self.caps += caps 
        self.times += times

    def poll_dists(self, reset = False):
        ret = []
        for avg in self.avgs:
            avg.caps += self.caps
            avg.times += self.times
            ret.append(avg.poll_dists(reset))
        self.times.clear()
        self.caps.clear()
        return ret

    def dist_estimate(self, cap):
        return self.fit.dist_estimate(self.cal, cap - self.offset) - self.origin

    class DistAvg:
        time_interval_error = 0.1
        def __init__(self, time_interval, capdist):
            self.t_int = time_interval
            self.capdist = capdist
            t_interval_err = time_interval*self.time_interval_error
            self.t_int_upper = time_interval + t_interval_err
            self.t_int_lower = time_interval - t_interval_err
            self.i_interval = 0
            self.caps, self.times = [], []

        def poll_dists(self, reset):
            if reset:
                self.i_interval = 0
            i, j = 0, self.i_interval 
            j_max = len(self.times)
            start_times = []
            caps = []
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
                try:
                    caps.append(mean(self.caps[i:j]))
                    start_times.append(self.times[i])
                except Exception:
                    pass 
                i = j
                j += self.i_interval
            self.times = self.times[i:]
            self.caps = self.caps[i:]
            dists = [self.capdist.dist_estimate(cap) for cap in caps]
            return dists, start_times
