"""
The :mod:`atlantic_signatures.calculate` module implements classes for
calculating the ocean current velocity and the magnetic field, and some helper
functions.
"""

from operator import itemgetter

import numpy as np


def normalize(v):
    """Return the normalized form of the vector v, safely handling the zero vector."""

    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

def remove_units(quantity):
    """Return the (unitless) magnitude a Quantity object, safely handling non-Quantity numbers."""

    return quantity.magnitude if hasattr(quantity, 'magnitude') else quantity


class Current:
    """A class for computing ocean current velocity vectors.

    To represent the North Atlantic Gyre, this model implements an
    elliptical-shaped ocean current. The ocean current velocity vector, defined
    at each point in space (except the origin) and originally given in polar
    coordinates (v_radial, v_theta), is transformed into Cartesian coordinates,
    scaled in the x- and y-dimensions by the factors s_x and s_y, and then is
    rotated by an angle theta_fluid.

    Parameters:
        s_x : float
            An x-component scaling factor for velocity, applied before rotation
        s_y : float
            A y-component scaling factor for velocity, applied before rotation
        v_theta : float
            The rotational component of velocity, before scaling and rotation
            (positive is counterclockwise)
        theta_fluid : float
            The angle of rotation, applied after scaling
        v_radial : float
            The radial component of velocity, before scaling and rotation
            (positive is outward from the origin)
    """

    SECTION = 'Current Properties'
    PARAMS = ('s_x', 's_y', 'v_theta', 'theta_fluid', 'v_radial')

    def __init__(self, s_x, s_y, v_theta, theta_fluid, v_radial=0):
        """Initializer for a new Current."""

        self._s_x = s_x
        self._s_y = s_y
        self._v_theta = v_theta
        self._theta_fluid = theta_fluid
        self._v_radial = v_radial

    def calculate(self, x, y):
        """Calculate ocean current velocity vectors.

        Arguments:
            x : float or array_like
                The x-coordinate(s) of a point or array of points
            y : float or array_like
                The y-coordinate(s) of a point or array of points

        Returns:
            v_x : float or array_like
                The x-component(s) of the velocity at each point
            v_y : float or array_like
                The y-component(s) of the velocity at each point
        """

        r = np.hypot(x, y) + 1e-4

        a = (self._s_x/r)*(self._v_radial*x - self._v_theta*y)
        b = (self._s_y/r)*(self._v_radial*y + self._v_theta*x)

        v_x = a*np.cos(self._theta_fluid) - b*np.sin(self._theta_fluid)
        v_y = a*np.sin(self._theta_fluid) + b*np.cos(self._theta_fluid)

        v_x = remove_units(v_x)
        v_y = remove_units(v_y)

        return v_x, v_y

    @classmethod
    def from_cache(cls, cache):
        """Instantiate a new Current from a config dictionary.

        Example usage:
            >>> from atlantic_signatures.calculate import Current
            >>> from atlantic_signatures.config_loader import Loader, config_to_dict
            >>> current = Current.from_cache(config_to_dict(Loader().read_config_file(config_file)))
        """

        values = itemgetter(*cls.PARAMS)(cache[cls.SECTION])
        return cls(**dict(zip(cls.PARAMS, values)))



class Field:
    """A class for computing magnetic field inclination and intensity.

    To represent Earth's magnetic field in the North Atlantic, this model
    implements a linearized simplification of the magnetic field. The level sets
    of two intersecting planes are used to model lines of constant
    inclination/beta and intensity/gamma. Here, "inclination" and "beta" are
    used interchangeably with one another, as are "intensity" and "gamma".

    Typical parameters are as follows. We set the inclination/beta plane's
    unrotated normal vector to align with the x-axis (i.e., [a_inc, b_inc,
    c_inc] = [1, 0, 1]). We set the intensity/gamma plane's unrotated normal
    vector to align with the y-axis (i.e., [a_int, b_int, c_int] = [0, -1, 1]).
    This means that with no rotation, lines of constant inclination/beta are
    parallel to the y-axis and increase as one moves in the direction of -x;
    lines of constant intensity/gamma are parallel to the x-axis and increase as
    one moves in the direction of +y. The sign of the inclination/beta plane can
    be inverted for "negated sensing" by setting eta to -1, causing the plane to
    increase in the direction of +x instead. These planes can be rotated by
    adjusting theta_inc, theta_int, and/or lambda (e.g., theta_int = 10 degrees
    and lambda = 5 degrees, causing the level sets of the planes to be close to
    parallel).

    The magnetic field can evolve with time (secular variation). The six delta
    parameters control increments in the planes' position and angle of rotation.
    In multi-circuit (multi-migration) experiments, these increments are applied
    after each circuit.

    Parameters:
        a_inc : float
            The x-component of the normal vector to the inclination/beta plane
        b_inc : float
            The y-component of the normal vector to the inclination/beta plane
        c_inc : float
            The z-component of the normal vector to the inclination/beta plane
        a_int : float
            The x-component of the normal vector to the intensity/gamma plane
        b_int : float
            The y-component of the normal vector to the intensity/gamma plane
        c_int : float
            The z-component of the normal vector to the intensity/gamma plane
        eta : float
            A scaling factor for the inclination/beta plane, conventionally
            taking the value of +1 (for "regular sensing") or -1 (for
            "negated sensing").

    Special keyword parameters: *Exactly two of these three must be provided*
        theta_inc : float
            The absolute angle of rotation of the inclination/beta plane
            (positive is counterclockwise)
        theta_int : float
            The absolute angle of rotation of the intensity/gamma plane
            (positive is counterclockwise)
        lambda : float
            The angle of rotation of the unspecified plane relative to the
            specified plane

    Optional keyword parameters:
        beta_0 : list of three floats
            A point in 3D space that the inclination/beta plane passes through
            (default: [0, 0, 0])
        gamma_0 : list of three floats
            A point in 3D space that the intensity/gamma plane passes through
            (default: [0, 0, 0])
        delta_x_inc : float
            An increment to the x-position of the inclination/beta plane,
            applied after each completed circuit/migration (default: 0)
        delta_x_int : float
            An increment to the x-position of the intensity/gamma plane,
            applied after each completed circuit/migration (default: 0)
        delta_y_inc : float
            An increment to the y-position of the inclination/beta plane,
            applied after each completed circuit/migration (default: 0)
        delta_y_int : float
            An increment to the y-position of the intensity/gamma plane,
            applied after each completed circuit/migration (default: 0)
        delta_theta_inc : float
            An increment to the angle of rotation of the inclination/beta plane,
            applied after each completed circuit/migration (default: 0)
        delta_theta_int : float
            An increment to the angle of rotation of the intensity/gamma plane,
            applied after each completed circuit/migration (default: 0)
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
        Initializer for a new Field.
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
        """Calculate magnetic signatures.

        Arguments:
            x : float or array_like
                The x-coordinate(s) of a point or array of points
            y : float or array_like
                The y-coordinate(s) of a point or array of points
            n : int
                The circuit/migration number (0 corresponds to the first
                circuit)

        Returns:
            beta : float or array_like
                The inclination/beta value(s) of the magnetic signature at each
                point
            gamma : float or array_like
                The intensity/gamma value(s) of the magnetic signature at each
                point
        """

        d_beta  = sum(i*j for i, j in zip(self._beta_0, (self._a_inc, self._b_inc, self._c_inc)))
        d_gamma = sum(i*j for i, j in zip(self._gamma_0, (self._a_int, self._b_int, self._c_int)))

        def _func(a, b, c, d, e, t, dx, dy, dt):
            return (e/c)*(d - a*((x+dx*n)*np.cos(t+dt*n) + (y+dy*n)*np.sin(t+dt*n)) - b*((y+dy*n)*np.cos(t+dt*n) - (x+dx*n)*np.sin(t+dt*n)))

        beta = _func(self._a_inc, self._b_inc, self._c_inc, d_beta, self._eta, self._theta_inc, self._delta_x_inc, self._delta_y_inc, self._delta_theta_inc)
        gamma = _func(self._a_int, self._b_int, self._c_int, d_gamma, 1, self._theta_int, self._delta_x_int, self._delta_y_int, self._delta_theta_int)  # gamma's eta is always 1 -- negated sensing affects beta only

        beta = remove_units(beta)
        gamma = remove_units(gamma)

        return beta, gamma

    def inverse(self, beta, gamma, n):
        """Find locations of magnetic signatures.

        Because the linearized magnetic field can be solved analytically,
        closed-form exact solutions can be calculated here (Mathematica was used
        to produce this code). In the general case of an arbitrary magnetic
        field, numerical techniques will likely be needed (e.g.,
        scipy.optimize.fsolve).

        Arguments:
            beta : float or array_like
                The inclination/beta value(s) of a magnetic signature or array
                of magnetic signatures
            gamma : float or array_like
                The intensity/gamma value(s) of a magnetic signature or array of
                magnetic signatures
            n : int
                The circuit/migration number (0 corresponds to the first
                circuit)

        Returns:
            x : float or array_like
                The x-coordinate(s) of the point(s) corresponding to each
                magnetic signature
            y : float or array_like
                The y-coordinate(s) of the point(s) corresponding to each
                magnetic signature
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

        x = remove_units(x)
        y = remove_units(y)

        return x, y

    @classmethod
    def from_cache(cls, cache):
        """Instantiate a new Field from a config dictionary.

        Example usage:
            >>> from atlantic_signatures.calculate import Field
            >>> from atlantic_signatures.config_loader import Loader, config_to_dict
            >>> field = Field.from_cache(config_to_dict(Loader().read_config_file(config_file)))
        """

        values = itemgetter(*cls.REQ_PARAMS)(cache[cls.SECTION])

        kwargs = {i: j for i, j in cache[cls.SECTION].items() if i in cls.SPECIAL_PARAMS + tuple(cls.OPT_PARAMS)}
        kwargs.update({i: j for i, j in zip(cls.REQ_PARAMS, values)})

        return cls(**kwargs)
