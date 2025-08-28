"""
The :mod:`atlantic_signatures.calculate` module implements ... TODO
"""

from operator import itemgetter

import numpy as np


def normalize(v):
    """
    TODO
    """

    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


class Current:
    """
    TODO
    """

    SECTION = 'Current Properties'
    PARAMS = ('s_x', 's_y', 'v_theta', 'theta_fluid', 'v_radial')

    def __init__(self, s_x, s_y, v_theta, theta_fluid, v_radial=0):
        """
        TODO
        """

        self._s_x = s_x
        self._s_y = s_y
        self._v_theta = v_theta
        self._theta_fluid = theta_fluid
        self._v_radial = v_radial

    def calculate(self, x, y):
        """
        TODO
        """

        r = np.hypot(x, y) + 1e-4

        a = (self._s_x/r)*(self._v_radial*x - self._v_theta*y)
        b = (self._s_y/r)*(self._v_radial*y + self._v_theta*x)

        v_x = a*np.cos(self._theta_fluid) - b*np.sin(self._theta_fluid)
        v_y = a*np.sin(self._theta_fluid) + b*np.cos(self._theta_fluid)

        v_x = self.remove_units(v_x)
        v_y = self.remove_units(v_y)

        return v_x, v_y

    @classmethod
    def from_cache(cls, cache):
        """
        TODO
        """

        values = itemgetter(*cls.PARAMS)(cache[cls.SECTION])
        return cls(**dict(zip(cls.PARAMS, values)))

    @staticmethod
    def remove_units(quantity):
        """
        TODO
        """

        return quantity.magnitude if hasattr(quantity, 'magnitude') else quantity



class Field:
    """
    TODO
    """

    SECTION = 'Field Properties'
    REQ_PARAMS = ('a_inc', 'b_inc', 'c_inc', 'a_int', 'b_int', 'c_int', 'eta')
    SPECIAL_PARAMS = ('theta_inc', 'theta_int', 'lambda')
    OPT_PARAMS = dict(beta_0=[0,0,0], gamma_0=[0,0,0],
                      delta_x_inc=0, delta_x_int=0,
                      delta_y_inc=0, delta_y_int=0,
                      delta_theta_inc=0, delta_theta_int=0)

    def __init__(self, a_inc, b_inc, c_inc, a_int, b_int, c_int, eta, **kwargs):
        """
        TODO
        """

        self._a_inc = a_inc
        self._b_inc = b_inc
        self._c_inc = c_inc
        self._a_int = a_int
        self._b_int = b_int
        self._c_int = c_int
        self._eta   = eta

        _theta_inc = kwargs.get('theta_inc')
        _theta_int = kwargs.get('theta_int')
        _lambda    = kwargs.get('lambda')

        if _theta_inc is not None and _theta_int is not None and _lambda is not None:
            raise ValueError('Error all three values: theta_inc, theta_int, '
                             'and lambda are defined')

        # Taylor et al. 2021 Bioinspir. Biomim., Eq. 8:
        #     delta = -(90 deg - theta - lambda)
        # where for this code
        #     delta --> theta_inc
        #     theta --> theta_int
        # Therefore:
        #     theta_inc = -(90 deg - theta_int - lambda)
        # and
        #     theta_int = theta_inc - lambda - 90 deg

        elif _theta_inc is not None and _lambda is not None:
            _theta_int = _theta_inc - _lambda - np.pi/2

        elif _theta_int is not None and _lambda is not None:
            _theta_inc = -(np.pi/2 - _theta_int - _lambda)

        elif _theta_inc is not None and _theta_int is not None:
            pass

        else:
            raise ValueError('Error: Two values out of the three: theta_inc, '
                             'theta_int, and lambda should be defined')

        self._theta_inc = _theta_inc
        self._theta_int = _theta_int

        self._beta_0 = kwargs.get('beta_0', self.OPT_PARAMS['beta_0'])
        self._gamma_0 = kwargs.get('gamma_0', self.OPT_PARAMS['gamma_0'])

        self._delta_x_inc = kwargs.get('delta_x_inc', self.OPT_PARAMS['delta_x_inc'])
        self._delta_x_int = kwargs.get('delta_x_int', self.OPT_PARAMS['delta_x_int'])
        self._delta_y_inc = kwargs.get('delta_y_inc', self.OPT_PARAMS['delta_y_inc'])
        self._delta_y_int = kwargs.get('delta_y_int', self.OPT_PARAMS['delta_y_int'])
        self._delta_theta_inc = kwargs.get('delta_theta_inc', self.OPT_PARAMS['delta_theta_inc'])
        self._delta_theta_int = kwargs.get('delta_theta_int', self.OPT_PARAMS['delta_theta_int'])

    def calculate(self, x, y, n):
        """
        Calculate the (beta, gamma) magnetic signature at this (x, y) coordinate at time n.
        """

        d_beta  = sum(i*j for i, j in zip(self._beta_0, (self._a_inc, self._b_inc, self._c_inc)))
        d_gamma = sum(i*j for i, j in zip(self._gamma_0, (self._a_int, self._b_int, self._c_int)))

        def _func(a, b, c, d, e, t, dx, dy, dt):
            return (e/c)*(d - a*((x+dx*n)*np.cos(t+dt*n) + (y+dy*n)*np.sin(t+dt*n)) - b*((y+dy*n)*np.cos(t+dt*n) - (x+dx*n)*np.sin(t+dt*n)))

        beta = _func(self._a_inc, self._b_inc, self._c_inc, d_beta, self._eta, self._theta_inc, self._delta_x_inc, self._delta_y_inc, self._delta_theta_inc)
        gamma = _func(self._a_int, self._b_int, self._c_int, d_gamma, 1, self._theta_int, self._delta_x_int, self._delta_y_int, self._delta_theta_int)  # gamma's eta is always 1 -- negated sensing affects beta only

        beta = self.remove_units(beta)
        gamma = self.remove_units(gamma)

        return beta, gamma

    def inverse(self, beta, gamma, n):
        """
        Find the (x, y) coordinate that give this (beta, gamma) magnetic signature at time n.

        Because the linearized magnetic field can be solved analytically, closed-form exact
        solutions can be calculated here (Mathematica was used to produce this code). In the
        general case of an arbitrary magnetic field, numerical techniques will likely be
        needed (e.g., scipy.optimize.fsolve).
        """

        x = (self._a_inc * (self._a_int * self._gamma_0[0] + self._b_int * self._gamma_0[1] - self._c_int * gamma) * self._eta * np.sin(
                n * self._delta_theta_inc + self._theta_inc) +
            np.cos(n * self._delta_theta_int +
            self._theta_int) * (self._b_int * self._c_inc * beta -
                self._b_int * (self._a_inc * self._beta_0[0] + self._b_inc * self._beta_0[1]) * self._eta -
                n * (self._b_inc * self._b_int * self._delta_x_inc +
                    self._a_inc * self._a_int * self._delta_x_int +
                    self._a_inc * self._b_int * (-self._delta_y_inc + self._delta_y_int
            )) * self._eta * np.sin(
                    n * self._delta_theta_inc + self._theta_inc)) + (self._a_int * self._c_inc *
            beta - self._a_int * (self._a_inc * self._beta_0[0] + self._b_inc * self._beta_0[1]) * self._eta +
                n * (self._a_inc * self._b_int * self._delta_x_int -
                    self._a_int * (self._b_inc * self._delta_x_inc - self._a_inc * self._delta_y_inc +
                        self._a_inc * self._delta_y_int)) * self._eta * np.sin(
                    n * self._delta_theta_inc + self._theta_inc)) * np.sin(
                n * self._delta_theta_int + self._theta_int) + self._eta * np.cos(
                n * self._delta_theta_inc + self._theta_inc) * (self._b_inc * (self._a_int * self._gamma_0[0] +
                    self._b_int * self._gamma_0[1] - self._c_int * gamma) +
                n * (self._a_inc * self._b_int * self._delta_x_inc -
                    self._b_inc * (self._a_int * self._delta_x_int +
                        self._b_int * (-self._delta_y_inc + self._delta_y_int))) * np.cos(
                    n * self._delta_theta_int + self._theta_int) +
                n * (self._a_inc * self._a_int * self._delta_x_inc +
                    self._b_inc * self._b_int * self._delta_x_int +
                    self._a_int * self._b_inc * (self._delta_y_inc - self._delta_y_int)) * np.sin(
                    n * self._delta_theta_int + self._theta_int))) / ((self._a_int * self._b_inc -
                self._a_inc * self._b_int) * self._eta * np.cos(
                n * (self._delta_theta_inc - self._delta_theta_int) +
            self._theta_inc - self._theta_int) + (self._a_inc * self._a_int + self._b_inc * self._b_int) * self._eta * np.sin(
                n * (self._delta_theta_inc - self._delta_theta_int) +
            self._theta_inc - self._theta_int))

        y = (self._b_inc * (self._a_int * self._gamma_0[0] + self._b_int * self._gamma_0[1] - self._c_int * gamma) * self._eta * np.sin(
                n * self._delta_theta_inc + self._theta_inc) +
            np.cos(n * self._delta_theta_int + self._theta_int) * (self._a_int * (-self._c_inc *
            beta + self._a_inc * self._beta_0[0] * self._eta + self._b_inc * self._beta_0[1] * self._eta) +
                n * (self._a_int * self._b_inc * (self._delta_x_inc - self._delta_x_int) -
                    self._a_inc * self._a_int * self._delta_y_inc -
                    self._b_inc * self._b_int * self._delta_y_int) * self._eta * np.sin(
                    n * self._delta_theta_inc + self._theta_inc)) + (self._b_int * self._c_inc *
            beta - self._b_int * (self._a_inc * self._beta_0[0] + self._b_inc * self._beta_0[1]) * self._eta +
                n * (self._a_inc * self._b_int * self._delta_y_inc -
                    self._b_inc * (self._b_int * self._delta_x_inc - self._b_int * self._delta_x_int +
                        self._a_int * self._delta_y_int)) * self._eta * np.sin(
                    n * self._delta_theta_inc + self._theta_inc)) * np.sin(
                n * self._delta_theta_int + self._theta_int) + self._eta * np.cos(
                n * self._delta_theta_inc + self._theta_inc) * (-self._a_inc * (self._a_int * self._gamma_0[0] +
                    self._b_int * self._gamma_0[1] - self._c_int * gamma) +
                n * (self._a_inc * self._a_int * (-self._delta_x_inc + self._delta_x_int) -
                    self._a_int * self._b_inc * self._delta_y_inc +
                    self._a_inc * self._b_int * self._delta_y_int) * np.cos(
                    n * self._delta_theta_int + self._theta_int) +
                n * (self._a_inc * self._b_int * (self._delta_x_inc - self._delta_x_int) +
                    self._b_inc * self._b_int * self._delta_y_inc +
                    self._a_inc * self._a_int * self._delta_y_int) * np.sin(
                    n * self._delta_theta_int + self._theta_int))) / ((self._a_int * self._b_inc -
                self._a_inc * self._b_int) * self._eta * np.cos(
                n * (self._delta_theta_inc - self._delta_theta_int) +
            self._theta_inc - self._theta_int) + (self._a_inc * self._a_int + self._b_inc * self._b_int) * self._eta * np.sin(
                n * (self._delta_theta_inc - self._delta_theta_int) +
            self._theta_inc - self._theta_int))

        x = self.remove_units(x)
        y = self.remove_units(y)

        return x, y

    @classmethod
    def from_cache(cls, cache):
        """
        TODO
        """

        values = itemgetter(*cls.REQ_PARAMS)(cache[cls.SECTION])

        kwargs = {i: j for i, j in cache[cls.SECTION].items() if i in cls.SPECIAL_PARAMS + tuple(cls.OPT_PARAMS)}
        kwargs.update({i: j for i, j in zip(cls.REQ_PARAMS, values)})

        return cls(**kwargs)

    @staticmethod
    def remove_units(quantity):
        """
        TODO
        """

        return quantity.magnitude if hasattr(quantity, 'magnitude') else quantity