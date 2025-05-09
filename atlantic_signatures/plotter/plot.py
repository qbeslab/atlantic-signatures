"""
Python configuration file that contains all the data structures necessary to
generate a plot or plots with the formatting of the paper:

 A bioinspired navigation strategy that uses magnetic signatures Q1 to navigate
 without GPS in a linearized northern Atlantic ocean: a simulation study

"""
import os
import sys

from matplotlib.animation import FuncAnimation
from matplotlib.patches   import Circle
import matplotlib.pyplot as plt
import numpy as np

from atlantic_signatures.plotter import colors
from atlantic_signatures.calculate import Current, Field
from atlantic_signatures.config_loader import Loader, config_to_dict
from atlantic_signatures.navigator import Navigator, FinalGoalReached

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



class Plot:
    def __init__(self, config_file, csv_file, **kwargs):
        self.cache = config_to_dict(Loader().read_config_file(config_file))
        a = np.loadtxt(csv_file, skiprows=1, delimiter=',', unpack=True)
        X, Y, THETA, TIME = a
        self.X, self.Y, self.THETA, self.T = X, Y, THETA, TIME
        self.data = (X, Y, TIME)
        self.t0 = TIME[0]

        xboundary_kwargs['xmin'] = self.cache['Boundary Conditions']['x_min'] / 1000  # convert mm to m
        xboundary_kwargs['xmax'] = self.cache['Boundary Conditions']['x_max'] / 1000  # convert mm to m
        yboundary_kwargs['ymin'] = self.cache['Boundary Conditions']['y_min'] / 1000  # convert mm to m
        yboundary_kwargs['ymax'] = self.cache['Boundary Conditions']['y_max'] / 1000  # convert mm to m

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

        # goal_marker_kwargs['markersize'] = self.native_units_to_pts() * self.cache['Create Properties']['r_goal'].m
        r_goal_kwargs['radius'] = self.cache['Create Properties']['r_goal'] / 1000  # convert mm to m
        r_multi_kwargs['radius'] = self.cache['Create Properties']['r_multi'] / 1000  # convert mm to m

        """
        for goalnum, goal in enumerate(self.cache['Goal Properties'].values()):
           self.ax.plot(*goal.m, color=r_goal_colors[goalnum % len(r_goal_colors)], **goal_marker_kwargs)
           self.ax.add_artist(Circle(goal.m, **r_multi_kwargs))
        """

        _goals = self.cache['Goal Properties'].copy()
        _circuits = _goals.pop('circuits', 1)  # default circuits given here
        _goals = _goals.values()
        for goal, parulacolor in zip(_goals, colors.PARULA_COLORMAP.get_spaced_colors(len(_goals))):
            #self.ax.plot(*goal.m, color=parulacolor, **goal_marker_kwargs)
            goal = np.array(goal) / 1000  # convert mm to m
            self.ax.add_artist(Circle(goal, facecolor=parulacolor, **r_goal_kwargs))
            self.ax.add_artist(Circle(goal, **r_multi_kwargs))

        self.navigator = Navigator.from_cache(self.cache)

        self.add_current()
        self.add_beta_gamma()

        self.plot_data()

    def native_units_to_pts(self):
        """
        Return the number of points (fontsize) that scales the axis dimensions
        of the trajectory plot to the physical size of the plot.
        """
        xmin, xmax = self.ax.get_xlim()

        # scale is the number of pixels per base plot unit (typically meters)
        scale = self.ax.get_window_extent().width / (xmax - xmin)
        return scale // 2

    def add_current(self):
        """
        Plot the ocean current as a quiver plot
        """

        X, Y = np.meshgrid(np.linspace(*self.ax.get_xlim(), 20), np.linspace(*self.ax.get_ylim(), 20))

        current = Current.from_cache(self.cache)
        V_X, V_Y = current.calculate(X, Y)

        self.ax.quiver(X, Y, V_X, V_Y, color='grey')

    def add_beta_gamma(self):
        """
        Plot the magnetic field as a contour plot
        """

        X, Y = np.meshgrid(np.linspace(*self.ax.get_xlim(), 5), np.linspace(*self.ax.get_ylim(), 5))

        field = Field.from_cache(self.cache)
        beta, gamma = field.calculate(X, Y)

        Cb = self.ax.contour(X, Y, beta, **beta_kwargs)
        Cg = self.ax.contour(X, Y, gamma, **gamma_kwargs)

    def plot_data(self):
        # create a line plot for the trajectory
        x = self.X / 1000  # convert mm to m
        y = self.Y / 1000  # convert mm to m
        self.line, = self.ax.plot(x, y, color='black', linewidth=2, solid_capstyle='round')

    def save(self, fname, *args, **kwargs):
        self.fig.savefig(fname, *args, **kwargs)



class AnimatedPlot(Plot):
    def __init__(self, config_file, csv_file, **kwargs):
        self.n = kwargs.pop('n', 5)
        self.t_multi = kwargs.pop('t_multi', 1)
        self.robot_radius = 0.17  # iRobot Create2 is 34 cm in diameter
        super().__init__(config_file, csv_file, **kwargs)

    def plot_data(self):
        # create an empty line plot for the trajectory (data to be updated later)
        self.line, = self.ax.plot([], [], color='black', linewidth=2, solid_capstyle='round')

        # create a circle to highlight the currently active goal (position to be updated)
        self.active_goal = Circle((0, 0), radius=r_goal_kwargs['radius'], facecolor='none', edgecolor='r', linewidth=2)
        self.ax.add_artist(self.active_goal)

        # create a cross showing the currently active magnetic signature (position to be updated)
        self.active_magnetic_signature = self.ax.scatter([], [], marker='+', color='r')

        # create a circle for the robot itself (position to be updated)
        self.robot = Circle((0, 0), radius=self.robot_radius, facecolor='none', edgecolor='k')
        self.ax.add_artist(self.robot)

        # create an arrow for the net velocity (position to be updated)
        self.net_velocity = self.ax.annotate('', xytext=(0, 0), xy=(0.5, 0.5), arrowprops=dict(color='black', width=1, headwidth=4, headlength=4))

        # create an arrow for the ocean velocity (position to be updated)
        self.ocean_velocity = self.ax.annotate('', xytext=(0, 0), xy=(0.5, 0.5), arrowprops=dict(color='blue', width=1, headwidth=4, headlength=4))

        # create an arrow for the agent velocity (position to be updated)
        self.agent_velocity = self.ax.annotate('', xytext=(0, 0), xy=(0.5, 0.5), arrowprops=dict(color='green', width=1, headwidth=4, headlength=4))

        # create an arrow for the robot's heading (position to be updated)
        self.heading = self.ax.annotate('', xytext=(0, 0), xy=(self.robot_radius, self.robot_radius), arrowprops=dict(color='red', width=1, headwidth=4, headlength=4))

        # create the animation
        frames = np.arange(0, len(self.T), self.n)  # animate every nth data point
        frames = np.unique(np.append(frames, len(self.T)-1))  # guarantee the final data point is included
        self._last_i = -1
        self.anim = FuncAnimation(self.fig, self.update_animation, frames=frames)

    def update_animation(self, i):
        t = self.T[i]
        x = self.X[i] / 1000  # convert mm to m
        y = self.Y[i] / 1000  # convert mm to m

        delay = int(1000*(t-self.t0)/self.t_multi)
        if delay < 0:
            delay = 0
        self.anim.event_source.interval = delay
        self.t0 = t

        # update the current goal and/or current circuit
        for j in range(self._last_i+1, i+1):
            try:
                class HiddenPrints:
                    def __enter__(self):
                        self._original_stdout = sys.stdout
                        sys.stdout = open(os.devnull, 'w')
                    def __exit__(self, exc_type, exc_val, exc_tb):
                        sys.stdout.close()
                        sys.stdout = self._original_stdout
                with HiddenPrints():
                    self.navigator.check_reached_goal(self.X[j], self.Y[j])  # keep units in mm for Navigator
            except FinalGoalReached:
                pass
        self._last_i = i

        dx_net, dy_net = self.navigator.net_velocity(self.X[i], self.Y[i])  # keep units in mm for Navigator
        dx_current, dy_current = self.navigator._current_calculator.calculate(self.X[i], self.Y[i])  # keep units in mm for Navigator
        dx_agent, dy_agent = dx_net - dx_current, dy_net - dy_current

        # update the trajectory
        self.line.set_data(self.X[:i+1] / 1000, self.Y[:i+1] / 1000)  # convert mm to m

        # update the active goal
        self.active_goal.set_center((self.navigator._x_goal / 1000, self.navigator._y_goal / 1000))  # convert mm to m

        # update the active magnetic signature
        mag_sig_x, mag_sig_y = self.navigator._field_calculator.inverse(self.navigator._beta_goal, self.navigator._gamma_goal)
        self.active_magnetic_signature.set_offsets((mag_sig_x / 1000, mag_sig_y / 1000))  # convert mm to m

        # update the robot
        self.robot.set_center((x, y))

        # update the robot's heading
        self.heading.set_x(x)
        self.heading.set_y(y)
        self.heading.xy = (x + self.robot_radius * np.cos(self.THETA[i]), y + self.robot_radius * np.sin(self.THETA[i]))

        vector_shrink_factor = 150

        # update the net velocity vector (units of mm/s divided by shrink factor)
        self.net_velocity.set_x(x)
        self.net_velocity.set_y(y)
        self.net_velocity.xy = (x + dx_net / vector_shrink_factor, y + dy_net / vector_shrink_factor)

        # update the ocean velocity vector (units of mm/s divided by shrink factor)
        self.ocean_velocity.set_x(x)
        self.ocean_velocity.set_y(y)
        self.ocean_velocity.xy = (x + dx_current / vector_shrink_factor, y + dy_current / vector_shrink_factor)

        # update the agent velocity vector (units of mm/s divided by shrink factor)
        self.agent_velocity.set_x(x)
        self.agent_velocity.set_y(y)
        self.agent_velocity.xy = (x + dx_agent / vector_shrink_factor, y + dy_agent / vector_shrink_factor)

        # report the circuit number for multi-circuit only
        if self.navigator._circuits > 1:
            self.ax.set_title(f'Circuit {self.navigator._current_circuit_number} of {self.navigator._circuits}')

    def save(self, fname, *args, **kwargs):
        self.anim.save(fname, *args, **kwargs)











if __name__ == '__main__':

    import argparse
    import glob
    import re
    from pathlib import Path
    import tempfile
    import os.path

    parser = argparse.ArgumentParser(description='Generate plots of an experiment')
    parser.add_argument('file', nargs='+', help='The input file to plot, created by an experiment (multiple files and/or wildcards allowed)')
    parser.add_argument(
        '--type', '-t',
        dest='plot_type',
        default='all',
        choices=['all', 'static', 'animated'],
        help='The type of plot to generate (default: all)',
    )
    args = parser.parse_args()

    files = []
    for file in args.file:
        files += glob.glob(file)

    for file in files:
        file = Path(file)
        print(f'Reading "{file}"')

        with (open(file, 'r', buffering=1) as input_file,
              tempfile.TemporaryFile(mode='w', delete_on_close=False) as config_file,
              tempfile.TemporaryFile(mode='w', delete_on_close=False) as csv_file):

            # walk through the input file to where the CSV content starts,
            # copying what comes before into a temporary config file, and what
            # comes after into a temporary CSV file
            CSV_HEADER_RE = re.compile(r'([a-zA-Z]+\s\([a-zA-Z]+\)\s*,*\s*)+')
            csv_header_found = False
            for line in input_file:
                if not csv_header_found:
                    csv_header_found = (CSV_HEADER_RE.match(line) is not None)
                if not csv_header_found:
                    config_file.write(line)
                else:
                    csv_file.write(line)

            # close the temp files so that they can be read by AnimatedPlot
            config_file.close()
            csv_file.close()

            if args.plot_type in ['all', 'static']:
                print(f'Plotting "{file}"')
                fig = Plot(config_file.name, csv_file.name)
                out_file = str(file.parent / (file.stem + '.png'))
                fig.save(out_file)
                print(f'Saved "{out_file}"')

            if args.plot_type in ['all', 'animated']:
                print(f'Animating "{file}"')
                anim = AnimatedPlot(config_file.name, csv_file.name, t_multi=10)
                out_file = str(file.parent / (file.stem + '.gif'))
                anim.save(out_file, fps=10)
                print(f'Saved "{out_file}"')

        print()
