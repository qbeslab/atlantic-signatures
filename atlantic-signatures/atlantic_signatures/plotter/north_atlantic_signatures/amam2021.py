
from copy import deepcopy
import itertools

import numpy as np
from   matplotlib.collections import PatchCollection
from   matplotlib.patches import Circle
import matplotlib.pyplot as plt



PARULA_COLORMAP = np.loadtxt('parula_colors.csv', delimiter=',')

def get_evenly_spaced_parula_colors(ncolors):
    for color in itertools.islice(PARULA_COLORMAP, 0, 256, 256 // ncolors):
        yield color


class GenerateGoals:

    r_goal_defaults, r_multi_defaults = {}, {}

    r_goal_defaults['edgecolors'] = 'black'
    r_goal_defaults['alpha']     = 0.5
    r_goal_defaults['linewidth'] = 1

    r_multi_defaults['edgecolors'] = 'black'
    r_multi_defaults['linestyle'] = '--'
    r_multi_defaults['facecolors'] = (0, 0, 0, 0.0125)

    def __init__(self, ax, positions, r_goal, r_multi, *, r_goal_kwds={}, r_multi_kwds={}):
        self.r_goal_kwds = deepcopy(self.r_goal_defaults)
        self.r_goal_kwds.update(r_goal_kwds)

        self.r_multi_kwds = deepcopy(self.r_multi_defaults)
        self.r_multi_kwds.update(r_multi_kwds)

        r_goal_patches, r_multi_patches = [], []
        for position in positions:
            r_goal_patches.append(Circle(position,  radius=r_goal))
            r_multi_patches.append(Circle(position, radius=r_multi))

        ax.add_collection(PatchCollection(r_goal_patches,  **self.r_goal_kwds))
        ax.add_collection(PatchCollection(r_multi_patches, **self.r_multi_kwds))



if __name__ == '__main__':
    bounds    = (-3, 3)
    r_goal    = 0.5
    r_multi   = 0.1
    positions = np.random.uniform(*bounds, (8, 2))


    fig = plt.figure(figsize=(4.8, 4.8))
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlim(*bounds)
    ax.set_ylim(*bounds)

    r_goal_colors = list(get_evenly_spaced_parula_colors(8))

    GenerateGoals(ax, positions, r_goal, r_multi, r_goal_kwds={'facecolors': r_goal_colors})


    plt.show()
