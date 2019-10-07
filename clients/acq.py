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

    """
    yield cap_ops['init'].start()
    yield cap_ops['init'].wait()
    yield client_t.dsleep(.05)
    """

    print("Starting Data Acquisition")
    yield cap_ops['acq'].start()

if __name__ == '__main__':
    parser = site_config.add_arguments()
    parser.add_argument('--target', default="cap")
    client_t.run_control_script2(my_script, parser=parser)
