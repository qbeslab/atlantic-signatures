"""
Python configuration file that contains all the data structures necessary to
generate a plot or plots with the formatting of the paper:
    
 A bioinspired navigation strategy that uses magnetic signatures Q1 to navigate
 without GPS in a linearized northern Atlantic ocean: a simulation study

"""

import itertools
import math
from operator import attrgetter, itemgetter

from matplotlib.animation import FuncAnimation
from matplotlib.patches   import Circle
import matplotlib.pyplot as plt
import numpy as np


from atlantic_signatures.plotter.config_loader import ConfigLoader, load_zipped_data_file, get_data_file, ureg
from atlantic_signatures.plotter import defaults, colors

#plt.rcParams['animation.ffmpeg_path'] = os.path.join(os.expan)



__all__ = ['beta_kwargs', 'gamma_kwargs',
           'xboundary_kwargs', 'yboundary_kwargs']




beta_kwargs = {}
beta_kwargs['cmap'] = colors.BETA_COLORMAP.cmap
beta_kwargs['linestyles'] = 'dashed'

gamma_kwargs = {}
gamma_kwargs['cmap'] = colors.GAMMA_COLORMAP.cmap

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

xticks_kwargs = {}
xticks_kwargs['ticks'] = [-2.4, 0.0, 2.4]

yticks_kwargs = {}
yticks_kwargs['ticks'] = [-2.4, 0.0, 2.4]


goal_marker_kwargs = {}
#goal_marker_kwargs['color'] = 'blue'
goal_marker_kwargs['marker'] = 'o'
goal_marker_kwargs['markersize'] = 10
goal_marker_kwargs['markeredgecolor'] = 'black'
goal_marker_kwargs['alpha'] = 0.5
goal_marker_kwargs['linewidth'] = 1


r_goal_kwargs = {}


# RGB color map for the 8 goals defined in the
# atlantic_signatures/legend_code.m file which can be found on outlook.
r_goal_colors = [
    (0,     0.447,  0.741),
    (0.85,  0.325,  0.098),
    (0.929, 0.694,  0.125),
    (0.494, 0.184,  0.556),
    (0.466, 0.674,  0.188),
    (0.301, 0.745,  0.933),
    (0.635, 0.078,  0.184),
    (0,     0,      0)
    ]

"""
PARULA_COLORMAP = np.loadtxt('parula_colors.csv', delimiter=',')

def get_evenly_spaced_parula_colors(ncolors):
    for color in itertools.islice(PARULA_COLORMAP, 0, 256, 256 // ncolors):
        yield color

"""


# The r_multi circle is NOT treated as a marker object due to the extremely
# limited shape + border support for marker objects and even a circle with a
# dashed ring is beyond its reach. There is a not so appealing hack where if
# you set your marker to: u"$\u25CC$" which is the unicode dashed circle.
# However, we avoid using this by leveraging the matplotlib.patches module
# which allows artistic control over a variety of common shapes. Below are the
# keyword arguments provided to an instance of matplotlib.patches.Circle and
# are subsequently added to the plot with the add_artist method.
r_multi_kwargs = {}
r_multi_kwargs['radius'] = 0.1
r_multi_kwargs['edgecolor'] = 'black'
r_multi_kwargs['linestyle'] = '--'
r_multi_kwargs['facecolor'] = (0, 0, 0, 0.0125)

r_goal_kwargs['radius'] = 0.5
r_goal_kwargs['edgecolor'] = 'black'
r_goal_kwargs['alpha'] = 0.5
r_goal_kwargs['linewidth'] = 1



class AnimatedPlot:
    def __init__(self, file, **kwargs):
        path = kwargs.setdefault('path', BUILTIN_DATA_DIR)
        self.t_multi = kwargs.pop('t_multi', 1)
        config = ConfigLoader(file, **kwargs)
        #X, Y, THETA, TIME = 
        a = load_zipped_data_file(get_data_file(file), zip_path=path)
        print(a)
        X, Y, THETA, TIME = a
        X *= 0.001
        Y *= 0.001
        self.X, self.Y, self.T = X, Y, TIME
        self.data = (X, Y, TIME)
        self.t0 = TIME[0]
        

        id_map = {
            '<int>': config.getint,
            '<float>': config.getfloat,
            '<bool>': config.getboolean,
            '<quantity>': config.getquantity,
            '<string>': config.get
            }

        self.cache = {}
        for section in defaults.REQUIRED_CONFIG_SECTIONS:
            self.cache[section] = {}
            for option in config.options(section):
                id, default, unit = defaults.CONFIG_OPTIONS.get((section, option), ('<string>', None, None))
                kwargs = {}
                
                if default is not None:
                    kwargs['fallback'] = default
                
                if id == '<quantity>' and unit is not None:
                    kwargs['default_units'] = unit
                    
                if section == 'Goal Properties':
                    id = '<quantity>'

                self.cache[section][option] = id_map[id](section, option, **kwargs)


        self.fig = plt.figure(figsize=(5.5, 5.5))
        self.ax = self.fig.add_subplot(1, 1, 1)

        self.ax.set_xlim(**xboundary_kwargs)
        self.ax.set_ylim(**yboundary_kwargs)
        self.ax.set_xlabel(**xaxis_kwargs)
        self.ax.set_ylabel(**yaxis_kwargs)
        self.ax.set_xticks(**xticks_kwargs)
        self.ax.set_yticks(**yticks_kwargs)
        
        #bbox = self.ax.get_window_extent().transformed(self.fig.dpi_scale_trans.inverted())
        #print(self.ax.get_window_extent().inverse_transformed(plt.gca().transData))
        #print(self.ax.get_window_extent().x1 - self.ax.get_window_extent().x0)

        goal_marker_kwargs['markersize'] = self.native_units_to_pts() * self.cache['Create Properties']['r_goal'].m
        print(goal_marker_kwargs['markersize'])
        r_multi_kwargs['radius'] = self.cache['Create Properties']['r_multi'].m

        """
        for goalnum, goal in enumerate(self.cache['Goal Properties'].values()):
           self.ax.plot(*goal.m, color=r_goal_colors[goalnum % len(r_goal_colors)], **goal_marker_kwargs)
           self.ax.add_artist(Circle(goal.m, **r_multi_kwargs))
        """
           
        _goals = self.cache['Goal Properties'].values()
        for goal, parulacolor in zip(_goals, colors.PARULA_COLORMAP.get_spaced_colors(len(_goals))):
            #self.ax.plot(*goal.m, color=parulacolor, **goal_marker_kwargs)
            self.ax.add_artist(Circle(goal.m, facecolor=parulacolor, **r_goal_kwargs))
            self.ax.add_artist(Circle(goal.m, **r_multi_kwargs))
           
        self.add_current()
        self.add_beta_gamma()
        

        
        self.start_animation()
        
        #self.ax.plot(X, Y, color='black')
        # plt.show()
        
    def add_current(self):
        sec = 'Current Properties'
    
        s_x = self.cache[sec]['s_x']
        s_y = self.cache[sec]['s_y']
        v_t = self.cache[sec]['v_theta'].m
        v_r = self.cache[sec]['v_radial'].m
        t_f = self.cache[sec]['theta_fluid'].to_base_units().m


        X, Y = np.meshgrid(np.linspace(*self.ax.get_xlim(), 20), np.linspace(*self.ax.get_ylim(), 20))
        R = np.hypot(X, Y) + 1e-3

        a, b = (s_x/R)*(v_r*X - v_t*Y), (s_y/R)*(v_r*Y + v_t*X)
        V_X, V_Y = a*math.cos(t_f) - b*math.sin(t_f), a*math.sin(t_f) + b*math.cos(t_f)

        self.ax.quiver(X, Y, V_X, V_Y, color='grey')
        
    def add_beta_gamma(self):
        sec = 'Field Properties'
        getter = itemgetter('a_inc', 'b_inc', 'c_inc', 'a_int', 'b_int', 'c_int', 'eta')
        a_inc, b_inc, c_inc, a_int, b_int, c_int, eta = getter(self.cache[sec])

        d_beta  = sum(i*j for i, j in zip(self.cache[sec]['beta_0'].m, (a_inc, b_inc, c_inc)))
        d_gamma = sum(i*j for i, j in zip(self.cache[sec]['gamma_0'].m, (a_int, b_int, c_int)))
        
        t_int = self.cache[sec]['theta_int'].to_base_units().m
        t_inc = -1 * (math.pi/2 - t_int - self.cache[sec]['lambda'].to_base_units().m)
        
        X, Y = np.meshgrid(np.linspace(*self.ax.get_xlim(), 5), np.linspace(*self.ax.get_ylim(), 5))

        beta  = (eta/c_inc) * (d_beta  - a_inc*(X*math.cos(t_inc) + Y*math.sin(t_inc)) - b_inc*(Y*math.cos(t_inc) - X*math.sin(t_inc)))
        gamma = (eta/c_int) * (d_gamma - a_int*(X*math.cos(t_int) + Y*math.sin(t_int)) - b_int*(Y*math.cos(t_int) - X*math.sin(t_int)))
    
        Cb = self.ax.contour(X, Y, beta, **beta_kwargs)
        Cg = self.ax.contour(X, Y, gamma, **gamma_kwargs)
    
    def gen_func(self):
        multi = int(self.t_multi)
        for i, t in enumerate(itertools.islice(self.T, 0, len(self.T), multi)):
            yield i*multi, t

    def start_animation(self):
        self.line, = self.ax.plot([], [], color='black', linewidth=2, solid_capstyle='round')
        #self.anim = FuncAnimation(self.fig, self.update_animation, self.gen_func, interval=self.t0)
        self.anim = FuncAnimation(self.fig, self.update_animation_mk2, 
                                  frames=np.arange(0, len(self.T), 10))
        
    def update_animation(self, data):
        i, t = data

        delay = int(1000*(t-self.t0)/self.t_multi)
        if delay < 0:
            delay = 0
        self.anim.event_source.interval = delay
        self.t0 = t

        self.line.set_data(self.X[:i], self.Y[:i])
        return self.line,
    
    def update_animation_mk2(self, i):
        t = self.T[i]
        
        delay = int(1000*(t-self.t0)/self.t_multi)
        if delay < 0:
            delay = 0
        self.anim.event_source.interval = delay
        self.t0 = t
        
        self.line.set_data(self.X[:i], self.Y[:i])
        return self.line,
        
    
    def native_units_to_pts(self):
        """
        Return the number of points (fontsize) that scales the axis dimensions
        of the trajectory plot to the physical size of the plot.
        """
        xmin, xmax = self.ax.get_xlim()

        # scale is the number of pixels per base plot unit (typically meters) 
        scale = self.ax.get_window_extent().width / (xmax - xmin)
        return scale // 2
    
    def save(self, fname, *args, **kwargs):
        self.anim.save(fname, *args, **kwargs)











if __name__ == '__main__':
    import zipfile
    import os.path
    BUILTIN_DATA_DIR = 'data.zip'

    testnum = 9
    date = '2020-03-04'
    plt.rcParams['animation.ffmpeg_path'] = os.path.join(os.path.expanduser('~'), 'ffmpeg-4.4-essentials_build', 'bin', 'ffmpeg')
    vid_file = 'Test'

    with zipfile.ZipFile(BUILTIN_DATA_DIR) as zipdir:
        for cfgfile in zipdir.namelist():
            if cfgfile.startswith(date) and cfgfile.endswith('.cfg') and os.path.basename(cfgfile).startswith('Test-%d' % testnum):
                x = AnimatedPlot(cfgfile, t_multi=10)
                x.save('Test-%d.gif' % testnum, fps=10)
                break













