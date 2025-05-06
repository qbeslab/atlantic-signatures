"""

"""
import argparse
import os
import os.path
import socket
import sys
from pathlib import Path
import tempfile
import re
import glob

from atlantic_signatures.client import Client
from atlantic_signatures.host import Host


# assume we are running as host if the OS is Windows
RUNNING_AS_HOST = os.environ.get('RUNNING_AS_HOST', sys.platform == 'win32')


def host_run(args):
    print()
    return Host(config_file=args.config_file, objectname=args.objectname, host=args.host, timeout=args.timeout)


def client_run(args):
    print()
    return Client(host=args.host)


def sim_run(args):
    from math import pi
    from atlantic_signatures.simulation import Simulation
    theta0_radians = args.theta0 * pi / 180  # convert degrees to radians
    sim = Simulation(x0=args.x0, y0=args.y0, theta0=theta0_radians, config_file=args.config_file)


def plot_run(args):
    files = []
    for file in args.file:
        files += glob.glob(file)

    for file in files:
        file = Path(file)
        print(f'Reading "{file}"')

        with (open(file, 'r', buffering=1) as input_file,
              tempfile.TemporaryFile(mode='w', delete_on_close=False) as config_file,
              tempfile.TemporaryFile(mode='w', delete_on_close=False) as csv_file):

            # walk through the input file to where the CSV content starts,
            # copying what comes before into a temporary config file, and what
            # comes after into a temporary CSV file
            CSV_HEADER_RE = re.compile(r'([a-zA-Z]+\s\([a-zA-Z]+\)\s*,*\s*)+')
            csv_header_found = False
            for line in input_file:
                if not csv_header_found:
                    csv_header_found = (CSV_HEADER_RE.match(line) is not None)
                if not csv_header_found:
                    config_file.write(line)
                else:
                    csv_file.write(line)

            # close the temp files so that they can be read by the plotters
            config_file.close()
            csv_file.close()

            if args.plot_type in ['all', 'static']:
                print(f'Plotting "{file}"')
                from atlantic_signatures.plotter.plot import Plot
                fig = Plot(config_file.name, csv_file.name)
                out_file = str(file.parent / (file.stem + '.png'))
                fig.save(out_file)
                print(f'Saved "{out_file}"')

            if args.plot_type in ['all', 'animated']:
                print(f'Animating "{file}"')
                from atlantic_signatures.plotter.plot import AnimatedPlot
                anim = AnimatedPlot(config_file.name, csv_file.name, t_multi=10, n=args.n)
                out_file = str(file.parent / (file.stem + '.gif'))
                anim.save(out_file, fps=10)
                print(f'Saved "{out_file}"')

        print()


def get_parser():
    main_parser = argparse.ArgumentParser(description='CLI for controlling the Create and generating plots')
    command_subparser = main_parser.add_subparsers(title='commands', required=True)

    if RUNNING_AS_HOST:
        run_parser = command_subparser.add_parser('run', description='Run an experiment as the host', help='Run an experiment as the host')

        DEFAULT_IP = Host.get_proper_ip()

        run_parser.add_argument(
            '--file', '-f',
            dest='config_file',
            default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'demo.cfg'),
            help='The file containing all test parameters',
        )
        run_parser.add_argument(
            '--object', '-o',
            dest='objectname',
            help="The name of the object to track. Defaults to any available Create object"
        )
        run_parser.add_argument(
            '--host',
            default=DEFAULT_IP,
            help="Alternative IP address of the host. Defaults to: %s" % DEFAULT_IP
        )
        run_parser.add_argument(
            '--timeout', '-t',
            type=float,
            default=10,
            help="The number of seconds communication can be unresponsive before the program times out and subsequently closes"
        )
        run_parser.set_defaults(func=host_run)

    else:
        run_parser = command_subparser.add_parser('run', description='Run an experiment as the client', help='Run an experiment as the client')

        def get_host_addr():
            try:
                return socket.gethostbyname('BIO-TAYLORL02-5820')
            except socket.error:
                return '192.168.0.12'
        run_parser.add_argument(
            '--host',
            default=get_host_addr(),
            help='IP address for the host computer'
        )
        run_parser.set_defaults(func=client_run)

    sim_parser = command_subparser.add_parser('sim', description='Run a simulation of an experiment', help='Run a simulation of an experiment')
    sim_parser.add_argument('x0', type=float, help='Initial x-coordinate of the simulated robot (in millimeters)')
    sim_parser.add_argument('y0', type=float, help='Initial y-coordinate of the simulated robot (in millimeters)')
    sim_parser.add_argument('theta0', type=float, nargs='?', default=0.0, help='(Optional) Initial heading of the simulated robot (in degrees; default: 0, East)')
    sim_parser.add_argument(
        '--file', '-f',
        dest='config_file',
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'demo.cfg'),
        help='The file containing all test parameters',
    )
    sim_parser.set_defaults(func=sim_run)

    plot_parser = command_subparser.add_parser('plot', description='Generate plots of an experiment', help='Generate plots of an experiment')
    plot_parser.add_argument('file', nargs='+', help='The input file to plot, created by an experiment (multiple files and/or wildcards allowed)')
    plot_parser.add_argument(
        '--type', '-t',
        dest='plot_type',
        default='all',
        choices=['all', 'static', 'animated'],
        help='The type of plot to generate (default: all)',
    )
    plot_parser.add_argument('--n', '-n', type=int, nargs='?', default=5, help='Animate every n-th data point (default: 5)')
    plot_parser.set_defaults(func=plot_run)

    return main_parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
