from FDC1004 import Chip, Measurement
import inverse_segmented_fit 

class CapDist():
    def __init__(self, cal_args, time_interval=None, fit=inverse_segmented_fit):
        self.fit = fit
        if len(cal_args) == 1:
            self.cal = fit.read_cal(cal_args[0])
        else:
            self.cal = fit.generate_cal(*cal_args)
        self.interval = time_interval
        self.offset = 0
        self.caps, self.dists, self.times = []*3

    def offset(self, *args):
        self.offset = self.fit.cap_offset(self.cal, *args)

    def dist_estimate(self, cap):
        return self.fit.dist_estimate(self.cal, cap - self.offset)

    def fill_caps(self, caps, times):
        self.caps += caps
        self.times += times

    def get_dists(
    
class InverseSegmentedFit():
    @staticmethod
    def generate_cal(caps, dists, regions):

        
    @staticmethod
    def write_cal(cal, cal_file):

    @staticmethod
    def read_cal(cal_file):
        with open(cal_file, "r") as f:
            self.cal =  

    @staticmethod
    def offset(cal, cap, dist):

    @staticmethod
    def dist(cal, cap):


