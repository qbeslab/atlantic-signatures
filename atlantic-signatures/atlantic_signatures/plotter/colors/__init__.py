"""
mycreate_plotter.colors module contains color maps and factory functions for
generating colors as found in the various papers/posters/presentations of
the QBES lab.
"""
import os.path

from matplotlib.colors import ListedColormap
import numpy as np


COLOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


class _ColorMap:
    def __init__(self, cmap):
        self.cmap = cmap

    def get_spaced_colors(self, ncolors):
        """Return *ncolors* evenly spaced colors from the colormap."""
        N = self.cmap.N
        return self.cmap(np.arange(0, N, N // ncolors))

    def get_start_colors(self, ncolors):
        """Return the first *ncolors* colors in the colormap."""
        return self.cmap(np.arange(0, ncolors, 1))

    def get_final_colors(self, ncolors):
        """Return the last *ncolors* colors in the colormap."""
        N = self.cmap.N
        return self.cmap(np.arange(N-ncolors-1, N, 1))

    @classmethod
    def load_from_file(cls, file):
        """
        Loads the RGB data stored in a color file stored in this module's "data"
        directory into a numpy array.
        """
        colordata = np.loadtxt(os.path.join(COLOR_DIR, file), delimiter=',')
        return cls(ListedColormap(colordata))

    @classmethod
    def load_from_builtin(cls, name='viridis', lut=None):
        """
        Loads the name of a builtin color map and construct a _ColorMap
        instance from the color map that was returned from the
        matplotlib.cm.get_cmap function.
        """
        from matplotlib import cm
        return cls(cm.get_cmap(name, lut))


BETA_COLORMAP   = _ColorMap.load_from_file('beta_colors.csv')
GAMMA_COLORMAP  = _ColorMap.load_from_file('gamma_colors.csv')
PARULA_COLORMAP = _ColorMap.load_from_file('parula_colors.csv')
