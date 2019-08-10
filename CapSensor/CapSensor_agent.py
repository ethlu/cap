import time
import os
import argparse
import warnings

from FDC1004 import Chip, Measurement
from Cap import CapDist
import inverse_segmented_fit

on_rtd = os.environ.get('READTHEDOCS') == 'True'
if not on_rtd:
    from ocs import ocs_agent, site_config
    from ocs.ocs_twisted import TimeoutLock

TIME_INTERVALS = [1 ,10]
CAL_FILES = ["cal1.csv", "cal2.csv"]
POLL_FREQUENCY = 300
SEND_FREQEUNCY = 1
CHANNELS = 2

class CapSensor_Agent:
    def __init__(self, agent):
        self.agent: ocs_agent.OCSAgent = agent
        self.lock = TimeoutLock()
        self.meas_cap = {}
        for i in range(CHANNELS):
            ch = Measurement(i + 1)
            ch.config(i)
            self.meas_cap[ch] = CapDist([CAL_FILES[i]], TIME_INTERVALS)
        self.initialized = False
        self.take_data = False
        self.f_poll = POLL_FREQUENCY
        self.send_interval = self.f_poll/SEND_FREQUENCy
        self.caps, self.timeline = [], []

    def init_task(self, session, params=None):
        if params is None:
            params = {}

        auto_acquire = params.get('auto_acquire', False)

        if self.initialized:
            return True, "Already Initialized Chip"

        with self.lock.acquire_timeout(0, job='init') as acquired:
            if not acquired:
                self.log.warn("Could not start init because "
                              "{} is already running".format(self.lock.job))
                return False, "Could not acquire lock."

            session.set_status('starting')

            self.chip = Chip(self.meas_cap.keys())
            self.chip.trigger()

        self.initialized = True

        # Start data acquisition if requested
        if auto_acquire:
            self.agent.start('acq')

        return True, 'Cap chip initialized.'


    def acq(self, session, params=None):
        """acq(params=None)

        Task to start data acquisition.

        Args:

            sampling_frequency (float):
                Sampling frequency for data collection. Defaults to 2.5 Hz

        """
        if params is None:
            params = {}

        sleep_time = 1/self.f_poll

        with self.lock.acquire_timeout(0, job='acq') as acquired:
            if not acquired:
                self.log.warn("Could not start acq because {} is already running"
                              .format(self.lock.job))
                return False, "Could not acquire lock."

            session.set_status('running')

            self.take_data = True
            i = 0
            while self.take_data:
                self.chip.poll(time.time())
                if i == self.send_interval:
                    data = {}

                    data = {
                        'timestamps': 
                        'block_name': 'temps',
                        'data': {}
                    }
                    for meas, capdist in self.meas_cap.items():
                        caps, timeline = meas.get_data()
                        cap_name = "Cap Meas {}".format(
                        capdist.fill_caps(caps)
                        
                     

                    for chan in self.module.channels:
                        chan_string = "Channel {}".format(chan.channel_num)
                        data['data'][chan_string + ' T'] = chan.get_reading(unit='K')
                        data['data'][chan_string + ' V'] = chan.get_reading(unit='S')

                    self.agent.publish_to_feed('temperatures', data)

                time.sleep(sleep_time)

            self.agent.feeds['temperatures'].flush_buffer()

        return True, 'Acquisition exited cleanly.'

    def stop_acq(self, session, params=None):
        """
        Stops acq process.
        """
        if self.take_data:
            self.take_data = False
            return True, 'requested to stop taking data.'
        else:
            return False, 'acq is not currently running'

