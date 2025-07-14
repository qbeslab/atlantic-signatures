# -*- coding: utf-8 -*-
"""
Created on Wed Jun 23 10:18:48 2021

@author: lucsc
"""
from __future__ import absolute_import

import json
from math import acos, atan2, copysign, cos, sin, sqrt
import socket
import time
import numpy as np

from atlantic_signatures.create import Create, OPCODES
from atlantic_signatures.navigator import Navigator, FinalGoalReached
from atlantic_signatures.socket_protocol import *


class Client(Protocol):

    def __init__(self, host, **kwargs):
        self._pose = {'x': None, 'y': None, 'theta': None}
        self._host = host
        self._starting_mode = kwargs.get('starting_mode', 'full')
        self._default_v = 100
        self._started = False
        self._config = {}

        raise_err = False
        for port in (PORT, ALT_PORT):
            if hasattr(self, '_client_sock'):
                self._client_sock.close()

            if port == ALT_PORT:
                print(
                'Failed to connect to host at default port: %d\nAttempting '
                'connection at the alternative port: %d' % (PORT, ALT_PORT)
                )
                raise_err = True

            try:
                self._client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._client_sock.settimeout(kwargs.get('timeout', 10))
                self._client_sock.connect((self._host, port))
                print(f'Connected to host at: {host}:{port}')
                print()
                break
            except TimeoutError:
                if raise_err:
                    self._client_sock.close()
                    raise

        self._create = Create(kwargs.get('serialport'))

        self.start()

    def start(self):
        try:
            while True:
                self.read_loop()
        except BreakLoop:
            pass
        except TimeoutError:
            print('Connection to host timed out')
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
            self._client_sock.close()
            print('Client socket has been closed')

            # always cleanly close the connection to the Create
            self._create.close()
            print('Serial connection has been closed')

    def read_loop(self):
        pb, payload = self._recv()

        if pb == PACKETS.COMMAND:
            self.recv_command(payload)
        elif pb == PACKETS.CONFIG:
            self.recv_config(payload)
        elif pb == PACKETS.DATA:
            self.recv_data(payload)
        elif pb == PACKETS.START:
            self.recv_start(payload)
        elif pb == PACKETS.CLOSE:
            self.recv_close(payload)
        else:
            raise OSError("An invalid packet was received: {}".format(pb))

    def recv_command(self, payload):
        command = json.loads(payload, encoding='utf-8')
        if command['opcode'] == OPCODES.DRIVE:
            self._create._drive(v=command.get('v', self._default_v), r=command.get('r', 'straight'))
        elif command['opcode'] == OPCODES.DRIVE_DIRECT:
            self._create._drive_direct(vl=command.get('vl', self._default_v), vr=command.get('vr', self._default_v))
        self._client_sock.send(bytes(PACKETS.ACKCOMMAND))

    def recv_config(self, payload):
        if not self._config:
            self._config = json.loads(payload)

        print('Configuration parameters were received:')
        for section, params in self._config.items():
            for option, value in params.items():
                print('{} - {} = {}'.format(section, option, value))
                #setattr(self, '_%s' % option, value)
        print()

        self._client_sock.send(bytes(PACKETS.ACKCONFIG))

        # Save some important parameters as attributes
        self._time_step = self._config['Create Properties']['agent_time_step']
        self._angle_cutoff = self._config['Create Properties']['angle_cutoff']

        self._navigator = Navigator.from_cache(self._config)

    def recv_data(self, payload, *, rotating=False):
        """
        Data sent to the Create comes in a JSON encoded dictionary object where
        a pose variable (x, y, and theta) is mapped to its value.

        Both x, y are not formatted and are sent as-is from the vicon command:
        GetSegmentGlobalTranslation(2). The value of z is dropped but this
        *could* be changed if necessary. x, y, and z are in millimeters.

        The value *theta* is translated from the euler angle gamma and
        represents the number of radians between the Create's Y-axis and the
        global X-axis.
        """
        data = json.loads(payload)
        print("x: {x:+8.02f},    y: {y:+8.02f},    theta: {theta:+5.02f}".format(**data))
        self._pose.update(data)
        self._client_sock.send(bytes(PACKETS.ACKDATA))
        if not rotating:
            self.move_to_next_point(**self._pose)

    def move_to_next_point(self, x, y, theta):
        try:
            self._navigator.check_reached_goal(x, y)
        except FinalGoalReached:
            self.send_close()
        dx, dy = self._navigator.net_velocity(x, y)
        self.move_create(dx, dy)

    def move_create(self, vx, vy):
        """
        Given the components of the vector pointing to the next point the
        Create wishes to go, this function will actualize the motion to get
        there as well as modify the vector if current is on.
        """

        V = int(sqrt(vx**2 + vy**2))

        if V < 11:
            print(f'requested velocity too low, setting to min speed for Create: {V} -> 11')
            V = 11

        # Small epsilon added to vx to avoid division by zero
        if vx == 0:
            vx = 1e-6

        # First we must rotate the Create to within a certain angular error of
        # the direction vector:

        desired_angle = atan2(vy, vx)
        delta = copysign(acos(cos(desired_angle - self._pose['theta'])), sin(desired_angle - self._pose['theta']))
        if abs(delta) > self._angle_cutoff:
            if delta < 0:
                turn_v, r = -delta, 'rotate_cw'
            else:
                turn_v, r = delta, 'rotate_ccw'
            self._create._drive(max(turn_v, 30), r=r)  # TODO: figure out the exact speed and duration needed to perform a precise turn
            time.sleep(0.1)
            self._create._drive(0)  # stop moving and wait for next command

        else:
            self._create._drive(V, r='straight')
            time.sleep(self._time_step)
            self._create._drive(0)  # stop moving and wait for next command

    def recv_start(self, payload):
        """
        The Create is started up after calling this command. It can only be
        called once.
        """
        if not (self._started and self._config):
            self._create._serial_startup(mode=self._starting_mode)
            self._started = True
        self._client_sock.send(bytes(PACKETS.ACKSTART))

    @property
    def pose(self):
        return self._position


if __name__ == '__main__':
    client = Client(socket.gethostbyname('BIO-TAYLORL02-5820'))
