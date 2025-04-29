"""

"""
from collections import deque
import numpy as np

from atlantic_signatures.calculate import Current, Field, normalize


class FinalGoalReached(Exception):
    pass

class Navigator:
    def __init__(self, linear_velocity, goals, r_goal, r_multi, multimodal_method, field, current):
        self._linear_velocity = linear_velocity
        self._goals = deque(goals.values())
        self._goal_count = len(goals)
        self._r_goal = r_goal
        self._r_multi = r_multi
        self._multimodal_method = multimodal_method

        self._field_calculator = field
        self._current_calculator = current

        self._current_goal_number = 0
        self._update_goal()

        self.net_velocity = np.vectorize(self._point_net_velocity, excluded=['self'])

    def check_reached_goal(self, x, y):
        d_goal = np.linalg.norm([self._x_goal - x, self._y_goal - y])

        if d_goal <= self._r_goal:
            print()
            print(f'Reached goal {self._current_goal_number} of {self._goal_count}')
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
        if self._goals:
            x, y = self._goals.popleft()
            self._x_goal, self._y_goal = x, y
            self._beta_goal, self._gamma_goal = self._field_calculator.calculate(x, y)
            self._current_goal_number += 1
        else:
            print('We have reached all goals...')
            raise FinalGoalReached

    def _point_net_velocity(self, x, y):
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
            beta, gamma = self._field_calculator.calculate(x, y)
            dx, dy = normalize([self._beta_goal - beta, self._gamma_goal - gamma])

            return (self._linear_velocity * dx + x_current, self._linear_velocity * dy + y_current)

    @classmethod
    def from_cache(cls, cache):
        return cls(
            linear_velocity=cache['Create Properties']['linear_velocity'],
            goals=cache['Goal Properties'],
            r_goal=cache['Create Properties']['r_goal'],
            r_multi=cache['Create Properties']['r_multi'],
            multimodal_method=cache['Create Properties']['multimodal_method'],
            field=Field.from_cache(cache),
            current=Current.from_cache(cache),
            )
