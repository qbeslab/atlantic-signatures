# -*- coding: utf-8 -*-
"""
Created on Wed Jun 23 10:18:48 2021

@author: lucsc
"""
from __future__ import absolute_import

from collections import deque
import json
from math import acos, atan2, copysign, cos, pi, sin, sqrt
import socket
import time

from atlantic_signatures.calculate import Current, Field
from atlantic_signatures.create import Create, OPCODES
from atlantic_signatures.socket_protocol import *


class Client(Protocol):

    def __init__(self, host, **kwargs):
        self._pose = {'x': None, 'y': None, 'theta': None}
        self._host = host
        self._starting_mode = kwargs.get('starting_mode', 'full')
        self._default_v = 100
        self._started = False
        self._finished = False
        self._config = {}

        self._client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._client_sock.settimeout(kwargs.get('timeout', 10))

        self._create = Create(kwargs.get('serialport'))

        self.start()

    def start(self):
        try:
            self._client_sock.connect((self._host, PORT))
        except socket.timeout:
            self._client_sock.connect((self._host, ALT_PORT))

        while True:
            try:
                self.read_loop()
            except BreakLoop:
                break

        self._client_sock.close()
        self._create.close()

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

        if self._finished:
            raise BreakLoop()

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

        self._client_sock.send(bytes(PACKETS.ACKCONFIG))

        self._field_calculator = Field.from_cache(self._config)
        self._current_calculator = Current.from_cache(self._config)

        # Save some important parameters as attributes
        self._goals = deque(self._config['Goal Properties'].values())
        self._goal_count = len(self._goals)
        self._velocity = self._config['Create Properties']['linear_velocity']
        self._time_step = self._config['Create Properties']['agent_time_step']
        self._angle_cutoff = self._config['Create Properties']['angle_cutoff']
        self._r_goal = self._config['Create Properties']['r_goal']
        self._r_multi = self._config['Create Properties']['r_multi']

        self._current_goal_number = 0
        self._update_goal()

    def _update_goal(self):
        """
        Cache the coordinates of the current goal in Cartesian and
        'Beta-Gamma' space.
        """
        if self._goals:
            x, y = self._goals.popleft()
            self._x_goal, self._y_goal = x, y
            self._beta_goal, self._gamma_goal = self._field_calculator.mesh_calculate(x, y)
            self._current_goal_number += 1
        else:
            print('We have reached all goals...')
            print('Ending connection with host')
            self.send_close()

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
        print(data)
        self._pose.update(data)
        self._client_sock.send(bytes(PACKETS.ACKDATA))
        if not rotating:
            self.move_to_next_point(**self._pose)

    def move_to_next_point(self, x, y, theta):
        x_diff, y_diff = self._x_goal - x, self._y_goal - y
        d_goal = sqrt(x_diff**2 + y_diff**2)

        # Current is in units mm/s
        x_current, y_current = self._current_calculator.point_calculate(x, y)

        if d_goal <= self._r_goal:
            print(f'Reached goal {self._current_goal_number} of {self._goal_count}')
            self._update_goal()

        elif d_goal <= self._r_multi:
            magnitude = d_goal
            dx, dy = x_diff / magnitude, y_diff / magnitude

            self.move_create(self._velocity * dx + x_current, self._velocity * dy + y_current)
        else:
            beta, gamma = self._field_calculator.mesh_calculate(x, y)
            beta_diff, gamma_diff = self._beta_goal - beta, self._gamma_goal - gamma
            magnitude = sqrt(beta_diff**2 + gamma_diff**2)

            dx, dy = beta_diff / magnitude, gamma_diff / magnitude

            self.move_create(self._velocity * dx + x_current, self._velocity * dy + y_current)

    def move_create(self, vx, vy):
        """
        Given the components of the vector pointing to the next point the
        Create wishes to go, this function will actualize the motion to get
        there as well as modify the vector if current is on.
        """

        V = int(sqrt(vx**2 + vy**2))

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
            self._create._drive(max(turn_v, 30), r=r)
            time.sleep(0.1)

        else:
            self._create._drive(V, r='straight')
            time.sleep(1)

    def recv_start(self, payload):
        """
        The Create is started up after calling this command. It can only be
        called once.
        """
        if not (self._started and self._config):
            self._create._serial_startup(mode=self._starting_mode)
            self._started = True
        self._client_sock.send(bytes(PACKETS.ACKSTART))

    def recv_close(self, payload):
        self._client_sock.send(bytes(PACKETS.ACKCLOSE))
        print('Close packet was received and the close process has begun')
        self._client_sock.close()
        print('Client socket has been closed')
        self._create.close()
        print('Serial connection has been closed')
        self._finished = True

    @property
    def pose(self):
        return self._position


if __name__ == '__main__':
    client = Client(socket.gethostbyname('BIO-TAYLORL02-5820'))
