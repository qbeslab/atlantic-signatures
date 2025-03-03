"""

"""
import math
from operator import itemgetter

import numpy as np


class Current:

    SECTION = 'Current Properties'
    PARAMS = ('s_x', 's_y', 'v_theta', 'theta_fluid', 'v_radial')

    def __init__(self, s_x, s_y, v_theta, theta_fluid, v_radial=0):
        self._s_x = s_x
        self._s_y = s_y
        self._v_theta = v_theta
        self._theta_fluid = theta_fluid
        self._v_radial = v_radial

    def point_calculate(self, x, y):
        """
        Given the parameters for current in the North Atlantic Signatures
        paper, return a 2-tuple: (v_x, v_y).
        """
        r = math.sqrt(x**2 + y**2) + 1e-4

        a = (self._s_x/r)*(self._v_radial*x - self._v_theta*y)
        b = (self._s_y/r)*(self._v_radial*y + self._v_theta*x)

        v_x = a*math.cos(self._theta_fluid) - b*math.sin(self._theta_fluid)
        v_y = a*math.sin(self._theta_fluid) + b*math.cos(self._theta_fluid)

        return v_x, v_y

    def mesh_calculate(self, X, Y):
        R = np.hypot(X, Y) + 1e-4

        a = (self._s_x/R)*(self._v_radial*X - self._v_theta*Y)
        b = (self._s_y/R)*(self._v_radial*Y + self._v_theta*X)

        V_X = a*np.cos(self._theta_fluid) - b*math.sin(self._theta_fluid)
        V_Y = a*np.sin(self._theta_fluid) + b*math.cos(self._theta_fluid)

        return V_X, V_Y


    @classmethod
    def from_cache(cls, cache):
        values = itemgetter(*cls.PARAMS)(cache[cls.SECTION])
        return cls(**{i: j for i, j in zip(cls.PARAMS, values)})





class Field:

    SECTION = 'Field Properties'
    REQ_PARAMS = ('a_inc', 'b_inc', 'c_inc', 'a_int', 'b_int', 'c_int', 'eta')
    SPECIAL_PARAMS = ('theta_inc', 'theta_int', 'lambda')
    OPT_PARAMS = dict(beta_0=[0,0,0], gamma_0=[0,0,0])

    def __init__(self, a_inc, b_inc, c_inc, a_int, b_int, c_int, eta, **kwargs):
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

        if _theta_inc and _theta_int and _lambda:
            raise ValueError('Error all three values: theta_inc, theta_int, '
                             'and lambda are defined')

        elif _theta_inc and _lambda:
            _theta_int = _theta_inc - _lambda

        elif _theta_int and _lambda:
            _theta_inc = _theta_int + _lambda

        elif _theta_inc and _theta_int:
            pass

        else:
            raise ValueError('Error: Two values out of the three: theta_inc, '
                             'theta_int, and lambda should be defined')

        self._theta_inc = _theta_inc
        self._theta_int = _theta_int

        self._beta_0 = kwargs.get('beta_0', self.OPT_PARAMS['beta_0'])
        self._gamma_0 = kwargs.get('gamma_0', self.OPT_PARAMS['gamma_0'])


    def point_calculate(self, x, y):
        pass

    def mesh_calculate(self, X, Y):
        d_beta  = sum(i*j for i, j in zip(self._beta_0, (self._a_inc, self._b_inc, self._c_inc)))
        d_gamma = sum(i*j for i, j in zip(self._gamma_0, (self._a_int, self._b_int, self._c_int)))

        def _func(a, b, c, d, t):
            return (self._eta/c)*(d - a*(X*math.cos(t) + Y*math.sin(t)) - b*(Y*math.cos(t) - X*math.sin(t)))

        Beta = _func(self._a_inc, self._b_inc, self._c_inc, d_beta, self._theta_inc)
        Gamma = _func(self._a_int, self._b_int, self._c_int, d_gamma, self._theta_int)

        return Beta, Gamma



    @classmethod
    def from_cache(cls, cache):
        values = itemgetter(*cls.REQ_PARAMS)(cache[cls.SECTION])

        kwargs = {i: j for i, j in cache[cls.SECTION].items() if i in cls.SPECIAL_PARAMS}
        kwargs.update({i: j for i, j in zip(cls.REQ_PARAMS, values)})

        return cls(**kwargs)
