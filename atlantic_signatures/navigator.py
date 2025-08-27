"""
The :mod:`atlantic_signatures.navigator` module implements a class responsible
for making navigation decisions.
"""

from collections import deque
import numpy as np

from atlantic_signatures.calculate import Current, Field, normalize


class FinalGoalReached(Exception):
    """
    TODO
    """

    pass

class Navigator:
    """
    TODO
    """

    def __init__(self, linear_velocity, goals, r_goal, r_multi, multimodal_method, secular_variation_strategy, circuits, field, current):
        """
        Initialize a new Navigator
        """

        self._linear_velocity = linear_velocity
        self._goals = deque(goals.values())
        self._goal_count = len(goals)
        self._r_goal = r_goal
        self._r_multi = r_multi
        self._multimodal_method = multimodal_method
        self._secular_variation_strategy = secular_variation_strategy
        self._circuits = circuits

        self._field_calculator = field
        self._current_calculator = current

        # precompute magnetic signatures for all goals
        self._magnetic_signatures = deque([])
        for x_goal, y_goal in goals.values():
            beta_goal, gamma_goal = self._field_calculator.calculate(x_goal, y_goal, n=0)
            self._magnetic_signatures.append((float(beta_goal), float(gamma_goal)))

        self._current_goal_number = 0
        self._current_circuit_number = 0
        self._update_goal()

        self.net_velocity = np.vectorize(self._point_net_velocity, excluded=['self'])

    @property
    def current_goal_number(self):
        """
        The current goal number (1-indexed)
        """

        return 1 + (self._current_goal_number-1) % self._goal_count

    def check_reached_goal(self, x, y):
        """
        TODO
        """

        d_goal = np.linalg.norm([self._x_goal - x, self._y_goal - y])

        if d_goal <= self._r_goal:
            print()
            if self._circuits == 1:
                print(f'Reached goal {self.current_goal_number} of {self._goal_count}')
            else:
                print(f'Reached goal {self.current_goal_number} of {self._goal_count} (circuit {self._current_circuit_number} of {self._circuits})')
            print()
            self._update_goal()
            return True
        else:
            return False

    def _update_goal(self):
        """
        Cache the coordinates of the current goal in Cartesian and
        'Beta-Gamma' space.
        """

        if hasattr(self, '_x_goal') and hasattr(self, '_y_goal'):  # don't do this on initialization

            # before updating the goal, implement compensatory strategies for dealing with a time-varying magnetic field
            possible_strategies = ['none', 'imprint']

            match self._secular_variation_strategy:
                case 'none':
                    # NO STRATEGY
                    # do nothing to compensate for the time-varying magnetic field
                    pass

                case 'imprint':
                    # SIMPLE IMPRINT STRATEGY
                    # imprint on the current magnetic signature for the goal that was just found using the current circuit's magnetic field
                    beta_goal, gamma_goal = self._field_calculator.calculate(self._x_goal, self._y_goal, n=self._current_circuit_number-1)
                    self._magnetic_signatures.pop()  # remove the out-dated magnetic signature
                    self._magnetic_signatures.append((beta_goal, gamma_goal))

                case _:
                    raise ValueError(f"unrecognized secular variation strategy: '{self._secular_variation_strategy}', valid options: {possible_strategies}")

        self._current_goal_number += 1
        if self.current_goal_number == 1:
            self._current_circuit_number += 1

        if not self._goals or self._current_circuit_number > self._circuits:
            print('We have reached all goals...')
            raise FinalGoalReached

        self._x_goal, self._y_goal = self._goals.popleft()
        self._goals.append((self._x_goal, self._y_goal))  # add the goal to the back of the queue

        self._beta_goal, self._gamma_goal = self._magnetic_signatures.popleft()
        self._magnetic_signatures.append((self._beta_goal, self._gamma_goal))  # add the goal's magnetic signature to the back of the queue

    def _point_net_velocity(self, x, y):
        """
        TODO
        """

        x_diff, y_diff = self._x_goal - x, self._y_goal - y
        d_goal = np.linalg.norm([x_diff, y_diff])

        # Current is in units mm/s
        x_current, y_current = self._current_calculator.calculate(x, y)

        if d_goal <= self._r_multi:
            possible_methods = ['direct', 'optimized_grid_search']

            match self._multimodal_method:
                case 'direct':
                    # DIRECT PATHING METHOD
                    dx, dy = normalize([x_diff, y_diff])
                    return (self._linear_velocity * dx + x_current, self._linear_velocity * dy + y_current)

                case 'optimized_grid_search':
                    # OPTIMIZED PATHING METHOD VIA GRID SEARCH
                    c = np.array([x_current, y_current])  # ocean current vector
                    d = np.array([x_diff, y_diff])  # vector from agent to goal

                    def objective(u, c, d):
                        # given a hypothetical unit vector u, compute the agent's net
                        # velocity if it tried to travel in that direction
                        v_net = self._linear_velocity * u + c

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
                    return (self._linear_velocity * dx + x_current, self._linear_velocity * dy + y_current)

                case _:
                    raise ValueError(f"unrecognized multimodal pathing method: '{self._multimodal_method}', valid options: {possible_methods}")

        else:
            beta, gamma = self._field_calculator.calculate(x, y, n=self._current_circuit_number-1)
            dx, dy = normalize([self._beta_goal - beta, self._gamma_goal - gamma])

            return (self._linear_velocity * dx + x_current, self._linear_velocity * dy + y_current)

    @classmethod
    def from_cache(cls, cache):
        """
        TODO
        """

        goals = cache['Goal Properties'].copy()
        circuits = goals.pop('circuits', 1)  # default circuits given here
        return cls(
            linear_velocity=cache['Create Properties']['linear_velocity'],
            goals=goals,
            r_goal=cache['Create Properties']['r_goal'],
            r_multi=cache['Create Properties']['r_multi'],
            multimodal_method=cache['Create Properties']['multimodal_method'],
            secular_variation_strategy=cache['Create Properties']['secular_variation_strategy'],
            circuits=circuits,
            field=Field.from_cache(cache),
            current=Current.from_cache(cache),
            )
