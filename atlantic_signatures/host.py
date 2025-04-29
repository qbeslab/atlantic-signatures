"""

"""
from __future__ import absolute_import, print_function
import os
import os.path
import json
import select
import socket
import sys
import time


from atlantic_signatures.config_loader import config_to_dict, Loader
from atlantic_signatures.socket_protocol import *

DATA_DIR = os.path.join(os.getcwd(), 'data')


def lazy_load_vicon():
    global ViconDataStream
    from vicon_dssdk import ViconDataStream


class Host(Protocol):
    def __init__(self, config_file=None, objectname=None, host=None, timeout=30):
        if config_file is None:
            raise RuntimeError('No config file was provided')
        if not os.path.isabs(config_file):
            config_file = os.path.abspath(config_file)
        if not os.path.exists(config_file):
            raise FileNotFoundError('The config file: %s was not found' % config_file)
        self._config_file = config_file

        lazy_load_vicon()

        # Real create object name is: 'Create2'
        if objectname is not None:
            self.tracking_object = (objectname, objectname)

        self._timeout = timeout
        self._host = self.get_proper_ip() if host is None else host

        if not isinstance(self._host, str):
            raise OSError('Invalid wireless address')

        if not os.path.exists(DATA_DIR):
            os.mkdir(DATA_DIR)

        test_num = 1

        for file in os.listdir(DATA_DIR):
            if file.startswith('Test') and file.endswith('.csv'):
                test_num += 1

        self._data_file = open(os.path.join(DATA_DIR, 'Test-%d.csv' % test_num), 'w')
        print(f'Writing data to file: {self._data_file.name}')
        print()
        self.start()


    def start(self):
        self._start_vicon()
        self._start_host()
        self._vicon_client.GetFrame()

        if not hasattr(self, 'tracking_object'):
            possible_objects = self._vicon_client.GetSubjectNames()
            for obj in possible_objects:
                if obj.lower().startswith('create'):
                    self.tracking_object = (obj, obj)
                    break
            else:
                self._sock.close()
                self._data_file.close()
                raise RuntimeError('No tracker objects were provided and/or could be found')

        self.send_config(self._config_file)
        self.t0 = time.time()
        self.send_loop()

    def send_loop(self):
        try:
            print('Sending data to client periodically')
            print()
            while True:
                r, w, _ = select.select([self._client_sock], [self._client_sock], [])
                if r:
                    self.recv_close(None)

                if w:
                    self.send_data()
                    time.sleep(0.1)  # throttle sending data, allowing time for client to determine if it has reached the last goal and signal the end
        except BreakLoop:
            pass
        except TimeoutError:
            print('Connection to client timed out')
        except KeyboardInterrupt:
            print('KeyboardInterrupt issued by user')
        except Exception as err:
            show_traceback = True
            if not show_traceback:
                print(f'Unexpected exception raised: {err}')
            else:
                raise
        finally:
            # always cleanly close the socket
            self._sock.close()
            print('Socket has been closed')

    def _start_host(self):
        raise_err = False

        for port in (PORT, ALT_PORT):
            if hasattr(self, '_sock'):
                self._sock.close()

            if port == ALT_PORT:
                print(
                'The client never connected at default port: %d\nAwaiting '
                'connection at the alternative port: %d' % (PORT, ALT_PORT)
                )

                raise_err = True

            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(self._timeout)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self._sock.bind((self._host, port))
            self._sock.listen(1)

            try:
                self._client_sock, addr = self._sock.accept()
                print(f'Connected to client at: {addr}')
                print()
                break
            except TimeoutError as err:
                if raise_err:
                    self._sock.close()
                    err.args = ("Some connection error occured", )
                    raise


    def _start_vicon(self):
        try:
            self._vicon_client = ViconDataStream.Client()
            self._vicon_client.Connect('BIO-TAYLORL02-5820:801')

            print(
                'Successfully connected to the Vicon system. Running Data '
                'Stream SDK version-%s' % '.'.join(str(i) for i in self._vicon_client.GetVersion())
                )
            print()

            self._vicon_client.SetBufferSize(1)
            self._vicon_client.EnableSegmentData()
            self._vicon_client.EnableMarkerData()
            self._vicon_client.EnableUnlabeledMarkerData()
            self._vicon_client.SetStreamMode(ViconDataStream.Client.StreamMode.EServerPush)

        except ViconDataStream.DataStreamException as err:
            print(
                'An error occured with the Vicon System during startup. '
                'Please make sure the system is connected.'
                )
            if hasattr(self, '_sock'):
                self._sock.close()
            sys.exit(1)

    def send_data(self, *, level=0):
        if level > 9:
            print(
                'The Create has been occluded for the past 10 frames and is '
                'assumed to be lost'
                )
            self.send_close()

        self._vicon_client.GetFrame()
        p_dat, p_oc = self._vicon_client.GetSegmentGlobalTranslation(*self.tracking_object)
        a_dat, a_oc = self._vicon_client.GetSegmentGlobalRotationEulerXYZ(*self.tracking_object)

        if p_oc or a_oc:
            print("The object was occluded. Attempting to resend data")
            self.send_data(level=level+1)

        data = {i: j for i, j in zip(('x', 'y'), p_dat)}
        data['theta'] = a_dat[2]

        self._data_file.write(','.join(str(param) for param in data.values()) + ',%f\n' % (time.time() - self.t0))

        try:
            self._send(PACKETS.DATA, json.dumps(data).encode('utf-8'))
        except:
            self._data_file.close()
            raise

    def send_config(self, config_file):
        config = config_to_dict(Loader().read_config_file(config_file))
        print("Sending config file: %s with the following parameters:" % config_file)
        for section, params in config.items():
            for option, value in params.items():
                print("{} - {} = {}".format(section, option, value))
        print()

        try:
            with open(config_file) as f:
                self._data_file.write(f.read() + '\n')
                self._data_file.write('X (mm),\tY (mm),\tTheta (rad),\tTime (sec)\n')
            self._send(PACKETS.CONFIG, json.dumps(config).encode('utf-8'))
        except:
            self._data_file.close()
            raise

    @staticmethod
    def get_proper_ip():
        """
        The Host computer will most likely be connected to three networks:
            UNC eduroam internet (ethernet)
            Vicon network        (ethernet)
            Lab network          (wireless)

        This is problematic since if we bind our socket to the wrong ip address
        then all communications will be sent through the wrong network.

        Normally using socket.gethostbyname(socket.gethostname()) works but in
        all tests this method returns the Vicon network ip address:
        (192.168.10.1). The more complex method below finds the correct ip
        address and returns it.
        """

        networks = socket.gethostbyname_ex(socket.gethostname())[2]
        lan_addrs = [network for network in networks if network.startswith('192.168')]

        if len(lan_addrs) == 1:
            return lan_addrs[0]
        else:
            for network in networks:
                if network.startswith('192.168.0'):
                    return network


if __name__ == '__main__':
    Host()
