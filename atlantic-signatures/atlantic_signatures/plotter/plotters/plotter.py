

import configparser
import csv
import linecache
import math
import os
import os.path
import re

import numpy as np
import matplotlib.pyplot as plt

import pint
from pint import UnitRegistry

from mycreate_plotter.north_atlantic_signatures.config import *

ureg = UnitRegistry()

curdir = os.path.dirname(os.path.abspath(__file__))





csv_head_temp = re.compile(
        r"[xX][\[\(](?P<x_units>[a-zA-Z]+)[\]\)]\s*,\s*"
        "[yY][\[\(](?P<y_units>[a-zA-Z]+)[\]\)]\s*,\s*"
        "[tT]heta[\[\(](?P<theta_units>[a-zA-Z]+)[\]\)]\s*,\s*"
        "[tT]ime[\[\(](?P<t_units>[a-zA-Z]+)[\]\)]")


config = configparser.ConfigParser()
HEADER_END = 0


def get_conversion_constant(unit):
    q = ureg.Quantity(1, unit)
    for base_unit in ('mm', 's', 'rad', 'mm/s'):
        if q.is_compatible_with(base_unit):
            return q.to(base_unit).m
    return 1


def get_sec_opts(section):
    return config[section]


def read_header(file):
    global HEADER_END, config
    i = 0
    header = ''
    while True:
        line = linecache.getline(file, i)
        if csv_head_temp.match(line):
            break
        header += line
        i += 1
    HEADER_END = i
    config.read_string(header)



def read_data(file):
    """
    Given a file and the final line number of the header in that file, return
    four flattened ndarrays that represent the state vector of the Roomba:
    x, y, theta, time
    """
    return np.loadtxt(file, skiprows=HEADER_END, delimiter=',').T

def _set_boundaries(ax):
    x_bounds, y_bounds = [-2743.2, 2743.2], [-2743.2, 2743.2]

    for name, value in config.items('Boundary Conditions'):
        try:
            value, unit = value.split(' ')
            value = get_conversion_constant(unit) * float(value)
        except:
            # If invalid for some reason. Default to 9 feet (2.7432 meters)
            pass

        index = 0 if name.endswith('min') else 1
        if name.startswith('x'):
            x_bounds[index] = value
        else:
            y_bounds[index] = value

    ax.set_xlim(*x_bounds)
    ax.set_ylim(*y_bounds)


def _set_title(ax, **kwds):
    title = kwds.get('title')
    fontdict = {}
    fontdict['fontsize'] = int(kwds.get('fontsize', 16))
    fontdict['fontweight'] = int(kwds.get('fontweight', 100))

    if not isinstance(title, str):
        # If the title is None, default to 'Roomba Trajectory (test date) (test number)'
        number = os.path.basename(file).split('.')[0]
        date = os.path.basename(os.path.dirname(file))
        title = 'Roomba Trajectory (%s) (%s)' % (date, number)

    ax.set_title(title, fontdict=fontdict)


def _set_axes(ax, **kwds):
    ax.set_xlabel('X (mm)', fontsize=12)
    ax.set_ylabel('Y (mm)', fontsize=12)


def _set_ticks(ax, **kwds):
    ax.set_xticks(np.linspace(*ax.get_xlim(), num=5))
    ax.set_yticks(np.linspace(*ax.get_ylim(), num=5))

def _plot_goals(ax, **kwds):
    for goal, value in config.items('Goal Properties'):
        x, y, unit = value.split(' ')
        x, y = float(x.strip(',')), float(y.strip(','))

        goal_num = int(goal.split('_')[1])

        constant = get_conversion_constant(unit)
        x *= constant
        y *= constant

        ax.plot(x, y, 'go', )
        ax.annotate('Goal %d' % goal_num, (x, y), [x-100, y+300])

def _add_beta_gamma(ax, **kwds):
    sec = 'Field Properties'
    a_inc, b_inc, c_inc = config.getfloat(sec, 'a_inc'), config.getfloat(sec, 'b_inc'), config.getfloat(sec, 'c_inc')
    a_int, b_int, c_int = config.getfloat(sec, 'a_int'), config.getfloat(sec, 'b_int'), config.getfloat(sec, 'c_int')
    eta = config.getfloat(sec, 'eta')

    _theta_value, _theta_unit = config[sec]['theta_int'].split(' ')
    _theta_value = float(_theta_value) * get_conversion_constant(_theta_unit)

    _lambda_value, _lambda_unit = config[sec]['lambda'].split(' ')
    _lambda_value = float(_lambda_value) * get_conversion_constant(_lambda_unit)

    theta_inc = (math.pi / 2) + _theta_value + _lambda_value
    theta_int = _theta_value

    x = np.arange(*ax.get_xlim(), 5)
    y = np.arange(*ax.get_ylim(), 5)
    X, Y = np.meshgrid(x, y)

    d_beta, d_gamma = 0.0, 0.0

    beta  = (eta / c_inc) * (d_beta  - a_inc * (X*np.cos(theta_inc) + Y*np.sin(theta_inc)) - b_inc * (Y*np.cos(theta_inc) - X*np.sin(theta_inc)))
    gamma = (eta / c_int) * (d_gamma - a_int * (X*np.cos(theta_int) + Y*np.sin(theta_int)) - b_int * (Y*np.cos(theta_int) - X*np.sin(theta_int)))

    Cb = ax.contour(X, Y, beta, linestyles='dashed', cmap=ListedColormap(green_colors))
    Cg = ax.contour(X, Y, gamma, cmap=ListedColormap(purple_colors))
    #ax.clabel(Cb, inline=True, fontsize=10)

def _add_current(ax, **kwds):
    sec = 'Current Properties'

    s_x = config.getfloat(sec, 's_x')
    s_y = config.getfloat(sec, 's_y')

    _v_theta_val, _v_theta_unit = config[sec]['v_theta'].split(' ')
    V_T = float(_v_theta_val) * get_conversion_constant(_v_theta_unit)

    _v_radial_val, _v_radial_unit = config[sec]['v_radial'].split(' ')
    V_R = float(_v_radial_val) * get_conversion_constant(_v_radial_unit)

    _theta_fluid, _theta_fl_unit = config[sec]['theta_fluid'].split(' ')
    tf = float(_theta_fluid) * get_conversion_constant(_theta_fl_unit)

    X, Y = np.meshgrid(np.arange(*ax.get_xlim(), 200), np.arange(*ax.get_ylim(), 200))
    R = np.hypot(X, Y) + 1e-3
    sin = np.sin
    cos = np.cos

    V_X = (V_R/R)*(((s_x*cos(tf)*X)-(s_y*sin(tf)*Y)) - V_T*((s_x*cos(tf)*Y) + (s_y*sin(tf)*X)))
    V_Y = (V_R/R)*(((s_y*cos(tf)*Y)+(s_x*sin(tf)*X)) + V_T*((s_y*cos(tf)*X) - (s_x*sin(tf)*Y)))

    ax.quiver(X, Y, V_X, V_Y, color='grey')

def plot(file):
    read_header(file)
    X, Y, THETA, TIME = read_data(file)
    x0, y0 = X[0], Y[0]

    ax = plt.gca()

    ax.annotate('Start', (x0, y0), [x0-200, y0-200])

    _set_boundaries(ax)
    _set_title(ax)
    _set_axes(ax)
    _set_ticks(ax)
    _plot_goals(ax)
    _add_beta_gamma(ax)
    _add_current(ax)

    ax.plot(X, Y, color='black')
    #plt.show()
    count = 1
    for f in os.listdir(curdir):
        if f.startswith('trajectory'):
            count += 1
    plt.savefig('trajectory%d.svg' % count, dpi=200, format='svg', bbox_inches='tight', pad_inches=1)




class TrajectoryConfigParser(configparser.ConfigParser):

    UNIT_RE   = re.compile(r"\([a-zA-Z0-9_\^\/]+\){0,1}")
    NUMBER_RE = re.compile(r"-{0,1}\d+(\.\d*)?")

    def _convert_to_quantity(self, value):
        unit = self.UNIT_RE.search(value)
        if unit is not None:
            unit = getattr(ureg, unit.group(0), None)
        values = (match.group(0) for match in self.NUMBER_RE.finditer(value))
        quantities = [ureg.Quantity(float(n), unit).to_base_units().m for n in values]
        if len(quantities) == 1:
            return quantities[0]
        return quantities

    def getquantity(self, section, option, *, raw=False, vars=None,
               fallback=configparser._UNSET, **kwargs):
        return self._get_conv(section, option, self._convert_to_quantity,
                              raw=raw, vars=vars,
                              fallback=fallback, **kwargs)





















class Reader:

    CSVLINE = re.compile(r"(-{0,1}\d+\.{0,1}\d*,{0,1})+")

    CSV_HEADER = re.compile(r"[a-zA-Z\(\)]+")

    def __init__(self, file, **kwds):
        self.config = TrajectoryConfigParser()
        self._file = file

        self.field_properties    = {}
        self.current_properties  = {}
        self.goal_properties     = {}
        self.boundary_conditions = {}

        # A trajectory file is a hybrid file with an ini style of configuration
        # settings at the start, a csv header, and csv style storage of data.
        # The main goal of the Reader object is to separate these various
        # sections so they can be processed individually.

        delimiter = kwds.pop('delimiter', ',')

        CSV_HEADER_RE = re.compile(r"([a-zA-Z]+\([a-zA-Z]+\)\s*%s*\s*)+" % delimiter)

        _config = ''
        with open(file, 'r', buffering=1) as f:
            for linenum, line in enumerate(f, start=1):
                if CSV_HEADER_RE.match(line):
                    header_line = linenum
                    break
                _config += line

        self.config.read_string(_config)
        self.data = np.loadtxt(file, skiprows=header_line, delimiter=delimiter).T

        for section in self.config.sections():
            cache = getattr(self, section.lower().replace(' ', '_'), None)
            if cache is not None:
                for option, value in self.config.items(section):
                    cache[option] = self.config.getquantity(section, option)

        print(self.boundary_conditions)

    @property
    def file(self):
        return self._file


class Properties:
    """Base dataclass for all config properties."""

    def __init__(self, config, section):
        """
        Given a section contained in a configparser object, store all option
        and value pairs as attributes of this class.
        """
        pass





class FieldProperties(Properties):

    REQUIRED = (
        'A_inc', 'B_inc', 'C_inc', 'A_int', 'B_int', 'C_int', 'eta',
        'theta_int', 'lambda'
        )

    OPTIONAL = ('beta_0', 'gamma_0')

    def __init__(self, config):
        self.cache = {}

        for option in self.REQUIRED:
            self.cache[option] = config.getquantity()





class CurrentProperties(Properties):
    pass


class PlotProperties(Properties):
    pass










class Plotter:
    def __init__(self, *files, **kwds):
        time_offset = kwds.pop('time_offset', 0.0)

        for file in files:
            self.file = Reader(file)
            X, Y, THETA, TIME = self.file.data
            self.x0, self.y0, self.theta0, self.time0 = X[0], Y[0], THETA[0], TIME[0]

            self.ax = plt.gca()
            self.ax.plot(X, Y, color='black')

            self.set_bounds()

            plt.show()

    def set_bounds(self, xbounds=None, ybounds=None, auto=False):
        xbounds = (-2743.2, 2743.2) if xbounds is None else xbounds
        ybounds = (-2743.2, 2743.2) if ybounds is None else ybounds

        self.ax.set_xlim(*xbounds, auto=auto)
        self.ax.set_ylim(*ybounds, auto=auto)


if __name__ == '__main__':
    file = os.path.join(os.path.dirname(curdir), 'north_atlantic_signatures', 'data', '2020-03-11', 'Test-1.csv.gz')
    x = Plotter(file)
    #print(x)
