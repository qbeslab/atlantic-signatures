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

from atlantic_signatures.client import Client
from atlantic_signatures.host import Host


# assume we are running as host if the OS is Windows
RUNNING_AS_HOST = os.environ.get('RUNNING_AS_HOST', sys.platform == 'win32')


def host_run(args):
    return Host(config_file=args.config_file, objectname=args.objectname, host=args.host, timeout=args.timeout)


def client_run(args):
    return Client(host=args.host)


def plot_animated(args):
    from atlantic_signatures.plotter.plot import AnimatedPlot
    for file in args.file:
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

            # close the temp files so that they can be read by AnimatedPlot
            config_file.close()
            csv_file.close()

            print(f'Animating "{file}"')
            x = AnimatedPlot(config_file.name, csv_file.name, t_multi=10)

            out_file = str(file.parent / (file.stem + '.gif'))
            x.save(out_file, fps=10)
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

    plot_parser = command_subparser.add_parser('plot', description='Generate an animated plot of an experiment', help='Generate an animated plot of an experiment')
    plot_parser.add_argument('file', nargs='+', help='The input file to plot, created by an experiment (multiple files allowed)')
    plot_parser.set_defaults(func=plot_animated)

    return main_parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
