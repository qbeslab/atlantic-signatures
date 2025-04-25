"""

"""
from collections import deque
import json
from math import acos, atan2, copysign, cos, pi, sin, sqrt
import os
import time
import numpy as np

from atlantic_signatures.calculate import Current, Field
from atlantic_signatures.config_loader import config_to_dict, Loader
from atlantic_signatures.socket_protocol import *

SIMS_DIR = os.path.join(os.getcwd(), 'simulations')


class Simulation:
    def __init__(self, x0, y0, theta0=0.0, config_file=None):
        self._pose = {'x': x0, 'y': y0, 'theta': theta0}  # radians expected for theta0
        self._new_pose = self._pose
        self._default_v = 100
        self._config = {}

        if config_file is None:
            raise RuntimeError('No config file was provided')
        if not os.path.isabs(config_file):
            config_file = os.path.abspath(config_file)
        if not os.path.exists(config_file):
            raise FileNotFoundError('The config file: %s was not found' % config_file)
        self._config_file = config_file

        if not os.path.exists(SIMS_DIR):
            os.mkdir(SIMS_DIR)

        sim_num = 1

        for file in os.listdir(SIMS_DIR):
            if file.startswith('Simulation') and file.endswith('.csv'):
                sim_num += 1

        self._data_file = open(os.path.join(SIMS_DIR, 'Simulation-%d.csv' % sim_num), 'w')
        self.start()

    def __repr__(self):
        return f'{self.__class__.__name__}(x0={self.x0}, y0={self.y0}, theta0={self.theta0}, config_file={self._config_file})'

    ############################################################################
    # HOST METHODS                                                             #
    ############################################################################

    def start(self):
        self.send_config(self._config_file)
        self.t0 = time.time()
        self.send_loop()

    def send_loop(self):
        try:
            while True:
                # r, w, _ = select.select([self._client_sock], [self._client_sock], [])
                # if r:
                #     self.recv_close(None)
                #
                # if w:
                #     self.send_data()
                #     time.sleep(0.1)  # throttle sending data, allowing time for client to determine if it has reached the last goal and signal the end
                self.send_data()  # SIMPLIFIED FOR SIMULATION
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
            # self._sock.close()  # REMOVED FOR SIMULATION
            print('Socket has been closed')

    def send_data(self, *, level=0):
        if level > 9:
            print(
                'The Create has been occluded for the past 10 frames and is '
                'assumed to be lost'
                )
            raise BreakLoop()

        # self._vicon_client.GetFrame()
        # p_dat, p_oc = self._vicon_client.GetSegmentGlobalTranslation(*self.tracking_object)
        # a_dat, a_oc = self._vicon_client.GetSegmentGlobalRotationEulerXYZ(*self.tracking_object)
        #
        # if p_oc or a_oc:
        #     print("The object was occluded. Attempting to resend data")
        #     self.send_data(level=level+1)
        #
        # data = {i: j for i, j in zip(('x', 'y'), p_dat)}
        # data['theta'] = a_dat[2]
        data = self._new_pose  # SIMPLIFIED FOR SIMULATION
        if (data['x'] < self._config['Boundary Conditions']['x_min'] or
            data['x'] > self._config['Boundary Conditions']['x_max'] or
            data['y'] < self._config['Boundary Conditions']['y_min'] or
            data['y'] > self._config['Boundary Conditions']['y_max']):
            # break loop if the simulated robot leaves the arena
            self.send_data(level=10)

        self._data_file.write(','.join(str(param) for param in data.values()) + ',%f\n' % (time.time() - self.t0))

        try:
            # self._send(PACKETS.DATA, json.dumps(data).encode('utf-8'))
            self.recv_data(json.dumps(data).encode('utf-8'))  # SIMPLIFIED FOR SIMULATION
        except:
            self._data_file.close()
            raise

    def send_config(self, config_file):
        config = config_to_dict(Loader().read_config_file(config_file))
        print("Sending config file: %s with the following parameters:" % config_file)
        for section, params in config.items():
            for option, value in params.items():
                print("{} - {} = {}".format(section, option, value))

        try:
            with open(config_file) as f:
                self._data_file.write(f.read() + '\n')
                self._data_file.write('X (mm),\tY (mm),\tTheta (rad),\tTime (sec)\n')
            # self._send(PACKETS.CONFIG, json.dumps(config).encode('utf-8'))
            self.recv_config(json.dumps(config).encode('utf-8'))  # SIMPLIFIED FOR SIMULATION
        except:
            self._data_file.close()
            raise

    ############################################################################
    # CLIENT METHODS                                                           #
    ############################################################################

    def recv_config(self, payload):
        if not self._config:
            self._config = json.loads(payload)

        print('Configuration parameters were received:')
        for section, params in self._config.items():
            for option, value in params.items():
                print('{} - {} = {}'.format(section, option, value))

        # self._client_sock.send(bytes(PACKETS.ACKCONFIG))  # REMOVED FOR SIMULATION

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
        self._multimodal_method = self._config['Create Properties']['multimodal_method']

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
            self._beta_goal, self._gamma_goal = self._field_calculator.calculate(x, y)
            self._current_goal_number += 1
        else:
            print('We have reached all goals...')
            print('Ending connection with host')
            # self.send_close()  # REMOVED FOR SIMULATION
            raise BreakLoop

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
        # self._client_sock.send(bytes(PACKETS.ACKDATA))  # REMOVED FOR SIMULATION
        if not rotating:
            self.move_to_next_point(**self._pose)

    def move_to_next_point(self, x, y, theta):
        x_diff, y_diff = self._x_goal - x, self._y_goal - y
        d_goal = sqrt(x_diff**2 + y_diff**2)

        # Current is in units mm/s
        x_current, y_current = self._current_calculator.calculate(x, y)

        if d_goal <= self._r_goal:
            print()
            print(f'Reached goal {self._current_goal_number} of {self._goal_count}')
            print()
            time.sleep(0.3)  # ADDED FOR SIMULATION
            self._update_goal()

        elif d_goal <= self._r_multi:
            possible_methods = ['direct', 'optimized_grid_search']

            match self._multimodal_method:
                case 'direct':
                    # DIRECT PATHING METHOD
                    magnitude = d_goal
                    dx, dy = x_diff / magnitude, y_diff / magnitude
                    self.move_create(self._velocity * dx + x_current, self._velocity * dy + y_current)

                case 'optimized_grid_search':
                    # OPTIMIZED PATHING METHOD VIA GRID SEARCH
                    c = np.array([x_current, y_current])  # ocean current vector
                    d = np.array([x_diff, y_diff])  # vector from agent to goal

                    def objective(u, c, d):
                        # given a hypothetical unit vector u, compute the agent's net
                        # velocity if it tried to travel in that direction
                        v_net = self._velocity * u + c

                        # return cos(theta) of the angle between the net velocity and the
                        # vector to the goal, for maximization (thereby minimizing theta)
                        return np.dot(v_net, d) / (np.linalg.norm(v_net) * np.linalg.norm(d))

                    def optimal_heading(c, d, num_points):
                        best_objective = -np.inf
                        optimal_u = None

                        # generate a grid of points on the unit circle
                        theta = np.linspace(-np.pi, np.pi, num_points)
                        unit_circle_points = np.vstack((np.cos(theta), np.sin(theta))).T

                        # evaluate the objective function at each point
                        for u in unit_circle_points:
                            this_objective = objective(u, c, d)
                            if this_objective > best_objective:
                                best_objective = this_objective
                                optimal_u = u

                        return optimal_u

                    num_points = 360  # affects angular resolution
                    dx, dy = optimal_heading(c, d, num_points)
                    self.move_create(self._velocity * dx + x_current, self._velocity * dy + y_current)

                case _:
                    raise ValueError(f"unrecognized multimodal pathing method: '{self._multimodal_method}', valid options: {possible_methods}")

        else:
            beta, gamma = self._field_calculator.calculate(x, y)
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
            # if delta < 0:
            #     turn_v, r = -delta, 'rotate_cw'
            # else:
            #     turn_v, r = delta, 'rotate_ccw'
            # self._create._drive(max(turn_v, 30), r=r)
            self.simulate_turn(0.1 * delta)  # SIMPLIFIED FOR SIMULATION, small coefficient allows for angle_cutoff to have a more realistic effect
            # time.sleep(0.1)  # REMOVED FOR SIMULATION

        else:
            # self._create._drive(V, r='straight')
            self.simulate_straight(self._time_step * V)  # SIMPLIFIED FOR SIMULATION
            # time.sleep(self._time_step)  # REMOVED FOR SIMULATION

    ############################################################################
    # SIMULATED MOVEMENT EXECUTION                                             #
    ############################################################################

    def simulate_turn(self, angle):
        self._new_pose = self._pose
        self._new_pose['theta'] = (self._new_pose['theta'] + angle + pi) % (2*pi) - pi

    def simulate_straight(self, distance):
        self._new_pose = self._pose
        self._new_pose['x'] += distance * cos(self._pose['theta'])
        self._new_pose['y'] += distance * sin(self._pose['theta'])
