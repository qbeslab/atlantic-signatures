"""
Python configuration file that contains all the data structures necessary to
generate a plot or plots with the formatting of the paper:
    
 A bioinspired navigation strategy that uses magnetic signatures Q1 to navigate
 without GPS in a linearized northern Atlantic ocean: a simulation study

"""

import os.path

from matplotlib.colors import ListedColormap
import numpy as np
from pint import UnitRegistry
ureg = UnitRegistry()

__all__ = ['beta_kwargs', 'gamma_kwargs',
           'xboundary_kwargs', 'yboundary_kwargs']


curdir = os.path.dirname(os.path.abspath(__file__))

beta_colormap  = ListedColormap(
    np.loadtxt(os.path.join(curdir, 'beta_colors.csv'),  delimiter=','))

gamma_colormap = ListedColormap(
    np.loadtxt(os.path.join(curdir, 'gamma_colors.csv'), delimiter=','))

beta_kwargs = {}
beta_kwargs['cmap'] = beta_colormap
beta_kwargs['linestyles'] = 'dashed'

gamma_kwargs = {}
gamma_kwargs['cmap'] = gamma_colormap

xboundary_kwargs = {}
xboundary_kwargs['xmin'] = -2.7432
xboundary_kwargs['xmax'] = 2.7432

yboundary_kwargs = {}
yboundary_kwargs['ymin'] = -2.7432
yboundary_kwargs['ymax'] = 2.7432

title_kwargs = {}

# The title of the plot. The special value: None defaults to the below format
# which is based on the date of the test and the test number from that day:
# Roomba Trajectory ("date" - TestX) which for example could be:
# Roomba Trajectory (2020/03/11 - Test3)
title_kwargs['label'] = None

title_kwargs['fontdict'] = {}
title_kwargs['fontdict']['fontsize'] = 16
title_kwargs['fontdict']['fontweight'] = 100
title_kwargs['fontdict']['color'] = 'black'


xaxis_kwargs = {}
xaxis_kwargs['xlabel'] = 'X (meters)'
xaxis_kwargs['fontsize'] = 12

yaxis_kwargs = {}
yaxis_kwargs['ylabel'] = 'Y (meters)'
yaxis_kwargs['fontsize'] = 12

nticks = 7
xticks_kwargs = {}
xticks_kwargs['ticks'] = np.linspace(xboundary_kwargs['xmin'], xboundary_kwargs['xmax'], nticks)

yticks_kwargs = {}
yticks_kwargs['ticks'] = np.linspace(yboundary_kwargs['ymin'], yboundary_kwargs['ymax'], nticks)


goal_marker_kwargs = {}
goal_marker_kwargs['color'] = 'blue'
goal_marker_kwargs['marker'] = 'o'
goal_marker_kwargs['markersize'] = 10
goal_marker_kwargs['markeredgecolor'] = 'black'
goal_marker_kwargs['alpha'] = 0.5
goal_marker_kwargs['linewidth'] = 1


# -----------------------------------------------------------------------------

REQUIRED_CONFIG_SECTIONS = (
    'Field Properties',
    'Current Properties',
    'Goal Properties', 
    'Boundary Conditions',
    'Create Properties'
    )

CONFIG_OPTIONS = {
    ('Field Properties', 'a_inc'): ('float', None),
    ('Field Properties', 'b_inc'): ('float', None),
    ('Field Properties', 'c_inc'): ('float', None),
    ('Field Properties', 'a_int'): ('float', None),
    ('Field Properties', 'b_int'): ('float', None),
    ('Field Properties', 'c_int'): ('float', None),
    ('Field Properties', 'beta_0'): ('quantity', [0.0, 0.0, 0.0] * ureg.meter),
    ('Field Properties', 'gamma_0'): ('quantity', [0.0, 0.0, 0.0] * ureg.meter),
    ('Field Properties', 'eta'): ('float', None),
    ('Field Properties', 'theta_int'): ('quantity', 10 * ureg.degree),
    ('Field Properties', 'lambda'): ('quantity', 5 * ureg.degree),
    ('Current Properties', 'v_theta'): ('quantity', None),
    ('Current Properties', 'v_radial'): ('quantity', None),
    ('Current Properties', 'current_source_position'): ('quantity', [0.0, 0.0] * ureg.meter),
    ('Current Properties', 'theta_fluid'): ('quantity', 5 * ureg.degree),
    ('Current Properties', 's_x'): ('float', 2.0),
    ('Current Properties', 's_y'): ('float', 1.0),
    ('Boundary Conditions', 'xmin'): ('quantity', -2.7432 * ureg.meter),
    ('Boundary Conditions', 'xmax'): ('quantity', 2.7432 * ureg.meter),
    ('Boundary Conditions', 'ymin'): ('quantity', -2.7432 * ureg.meter),
    ('Boundary Conditions', 'ymax'): ('quantity', 2.7432 * ureg.meter),
    ('Create Properties', 'linear_velocity'): ('quantity', 100 * ureg.meter_per_second),
    ('Create Properties', 'r_multi'): ('quantity', 0.1 * ureg.meter),
    ('Create Properties', 'r_goal'): ('quantity', 0.5 * ureg.meter),
    }


























if __name__ == '__main__':
    # Test plot with random data to visualize formatting
    import matplotlib.pyplot as plt
    
    X = [0.0, 1.0, 2.0, -1.0]
    Y = [-1.0, 0.5, 1.2, 0.9]
    
    Goals = [(0.7, -0.8), (1.7, 1.1), (-0.2, 0.8)]
    
    fig, ax = plt.subplots()
    ax.plot(X, Y, color='black')
    
    for num, goal in enumerate(Goals):
        ax.annotate('Marker %d' % num, goal)
        ax.plot(*goal, color='blue', marker='o', markeredgecolor='black', markersize=14, alpha=0.5)
        #ax.plot(*goal, 'grey', marker="$%s$" % u"\u2690", markersize=20)
        #ax.plot(*goal, 'ko')

    ax.set_xlim(**xboundary_kwargs)
    ax.set_ylim(**yboundary_kwargs)
    
    title_kwargs['label'] = 'Roomba Trajectory Test'
    ax.set_title(**title_kwargs)
    
    ax.set_xlabel(**xaxis_kwargs)
    ax.set_ylabel(**yaxis_kwargs)
    
    ax.set_xticks(**xticks_kwargs)
    ax.set_yticks(**yticks_kwargs)
    
    print(fig.dpi*fig.get_size_inches())
    fig.tight_layout()
    
    plt.show()
    
    












