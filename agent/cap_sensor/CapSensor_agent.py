import time
import os
import argparse
import warnings

from CapSensor.FDC1004 import Chip
from CapSensor.calibrate import meas_cap_builder
from statistics import mean
import csv

on_rtd = os.environ.get('READTHEDOCS') == 'True'
if not on_rtd:
    from ocs import ocs_agent, site_config
    from ocs.ocs_twisted import TimeoutLock

POLL_FREQUENCY = 300
SEND_FREQUENCY = 0.2

class CapSensor_Agent:
    def __init__(self, agent, config_file):
        self.agent = agent
        self.lock = TimeoutLock()
        self.meas_cap = meas_cap_builder(config_file)

        agg_params = {
            'frame_length': 60,
        }

        for meas, capdists in self.meas_cap.items():
            self.agent.register_feed("Cap{}".format(meas.num),
                    record=True,
                    agg_params=agg_params)
            for n, capdist in enumerate(capdists):
                for i in range(len(capdist.avgs) + 1):
                    self.agent.register_feed("Dist{}_Cal{}_Intvl{}".format(meas.num, n, i),
                        record=True,
                        agg_params=agg_params)

        self.initialized = False
        self.take_data = False
        self.f_poll = POLL_FREQUENCY
        self.send_interval = self.f_poll/SEND_FREQUENCY

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
                    for meas, capdists in self.meas_cap.items():
                        cap_data = {}
                        cap_name = "Cap{}".format(meas.num)

                        caps, timeline = meas.get_data()

                        cap_data['block_name'] = cap_name
                        cap_data['timestamps'] = timeline
                        cap_data['data'] = {meas.name: caps}
                        self.agent.publish_to_feed(cap_name, cap_data)

                        for n, capdist in enumerate(capdists):
                            if not capdist.init:
                                continue
                            capdist.fill_caps(caps, timeline)
                            dists = capdist.poll_dists()
                            for i, intvl in enumerate(dists):
                                dist_data = {}
                                dist_name = "Dist{}_Cal{}_Intvl{}".format(meas.num, n, i)
                                dist_data['block_name'] = dist_name
                                dist_data['timestamps'] = intvl[1]
                                dist_data['data'] = {capdist.name: intvl[0]}
                                self.agent.publish_to_feed(dist_name, dist_data)
                    i = 0

                time.sleep(sleep_time)
                i += 1

            for feed in self.agent.feeds.values():
                feed.flush_buffer()

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

    def offset(self, session, params):
        if not self.take_data:
            return False, 'acq should be running while calibrating'
        meas_num = params['meas_num']
        meas = self.chip.meas[meas_num]
        dist = params['dist']
        wait_time = params.get('wait_time', 10)
        min_sample = params.get('min_sample', 100)
        set_origin = params.get('set_origin', False)
        logfile = params.get('logfile', None)

        session.set_status('running')
        capdists = self.meas_cap.pop(meas)
        start_time = time.time()
        time.sleep(wait_time)

        if len(meas.data) < min_sample:
            self.meas_cap[meas] = capdists
            return False, 'too few samples'
        
        done = False
        for _ in range(10):
            try:
                avg_cap = mean(meas.data)
                done = True
                break
            except Exception:
                continue
        if not done:
            self.meas_cap[meas] = capdists
            return False, 'try again'
        
        for n, capdist in enumerate(capdists):
            capdist.set_offset(avg_cap, dist)
            if set_origin:
                capdist.set_origin(dist)
            else:
                capdist.set_origin(0)

        self.meas_cap[meas] = capdists

        if logfile is not None:
            with open(logfile, 'a') as f:
                writer = csv.writer(f)
                writer.writerow([start_time, wait_time, meas_num, dist, avg_cap, set_origin])

        return True, "Meas {} calibrated at time {}".format(meas_num, start_time)


def make_parser(parser=None):
    if parser is None:
        parser = argparse.ArgumentParser()

    pgroup = parser.add_argument_group('Agent Config')
    pgroup.add_argument('--mode', type=str, choices=['idle', 'init', 'acq'],
                        help="Starting action for the agent.")
    pgroup.add_argument('--config', type=str,
                        help="Config file for the agent.")

    return parser


def main():
    p = site_config.add_arguments()
    parser = make_parser(parser=p)

    args = parser.parse_args()

    # Interpret options in the context of site_config.
    site_config.reparse_args(args, 'CapSensorAgent')

    # Automatically acquire data if requested
    if args.mode == 'acq':
        init_params = {'auto_acquire': True}
    else:
        init_params = {'auto_acquire': False}

    agent, runner = ocs_agent.init_site_agent(args)

    kwargs = {"config_file": args.config}

    cap = CapSensor_Agent(agent, **kwargs)

    agent.register_task('init_cap', cap.init_task,
                        startup=init_params)
    agent.register_task('offset', cap.offset)
    agent.register_process('acq', cap.acq, cap.stop_acq)

    runner.run(agent, auto_reconnect=True)
    
    if args.mode != 'idle':
        agent.start('init_cap')

if __name__ == '__main__':
    main()
