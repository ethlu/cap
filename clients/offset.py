import ocs
from ocs import client_t, site_config


def my_script(app, pargs):
    root = 'observatory'

    # Register addresses and operations
    cap_instance = pargs.target
    cap_address = '{}.{}'.format(root, cap_instance)
    cap_ops = {
        'init': client_t.TaskClient(app, cap_address, 'init_cap'),
        'acq': client_t.ProcessClient(app, cap_address, 'acq'),
        'offset': client_t.TaskClient(app, cap_address, 'offset')
    }

    if pargs.origin.upper() == "Y":
        origin = True
    else:
        origin = False

    offset_params = {
        'meas_num': pargs.meas, 
        'dist': pargs.dist,
        'wait_time': pargs.time,
        'set_origin': origin,
        'logfile': pargs.logfile,
    }

    print("Start offsetting")
    yield cap_ops['offset'].start(params = offset_params)
    yield cap_ops['offset'].wait()
    status = yield cap_ops['offset'].status()
    print(status[2]["messages"])

if __name__ == '__main__':
    parser = site_config.add_arguments()
    parser.add_argument('--target', default="cap")
    parser.add_argument('--meas', type=int, default = 1)
    parser.add_argument('--dist', type=float, default=5.0)
    parser.add_argument('--time', type=float, default=5.0)
    parser.add_argument('--origin',  default = 'N')
    parser.add_argument('--logfile', default = None)
    client_t.run_control_script2(my_script, parser=parser)
