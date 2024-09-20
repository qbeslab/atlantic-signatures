"""

"""
import argparse
import os
import os.path
import socket
import sys

from atlantic_signatures.client import Client
from atlantic_signatures.host import Host


RUNNING_AS_HOST = os.environ.get('RUNNING_AS_HOST', sys.platform == 'win32')


def host_run(args):
    return Host(config_file=args.config_file, objectname=args.objectname, host=args.host, timeout=args.timeout)


def client_run(args):
    return Client(host=args.host)


def get_parser():
    parser = argparse.ArgumentParser(description='CLI for controlling the Create')

    parser.add_argument(
        'run',
        help='Run a test'
    )

    if RUNNING_AS_HOST:
        DEFAULT_IP = Host.get_proper_ip()

        parser.add_argument(
            '--file', '-f',
            dest='config_file',
            default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'demo.cfg'),
            help='The file containing all test parameters',
        )
        parser.add_argument(
            '--object', '-o',
            dest='objectname',
            help="The name of the object to track. Defaults to any available Create object"
        )
        parser.add_argument(
            '--host',
            default=DEFAULT_IP,
            help="Alternative IP address of the host. Defaults to: %s" % DEFAULT_IP
        )
        parser.add_argument(
            '--timeout', '-t',
            type=float,
            default=10,
            help="The number of seconds communication can be unresponsive before the program times out and subsequently closes"
        )
        parser.set_defaults(func=host_run)

    else:
        def get_host_addr():
            try:
                return socket.gethostbyname('BIO-TAYLORL02-5820')
            except socket.error:
                return '192.168.0.12'
        parser.add_argument(
            '--host',
            default=get_host_addr(),
            help='IP address for the host computer'
        )
        parser.set_defaults(func=client_run)

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
