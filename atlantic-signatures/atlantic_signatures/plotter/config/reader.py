"""
The mycreate_plotter.config.reader module defines the class: Reader which
handles translating information from trajectory config and data files.
"""

import re

import numpy as np

from mycreate_plotter.config import TrajectoryParser, ureg
from mycreate_plotter.config.loader import Loader




class Reader:
    
    _VAR_RE = re.compile(r"(?P<var>\w+)\s*\((?P<unit>[a-zA-Z0-9_\^\/]+)\)")
    
    def __init__(self, *args, **kwargs):
        self._DELIM  = kwargs.get('delimiter', ',')
        self._SEP_RE = re.compile(r"\s*%s\s*" % self._DELIM)

    def read_data_file(self, file):
        """
        Given an opened data file object *file* this function will return a
        numpy array of the data inside that file.
        """
        
        # Before the file is loaded into a numpy array we process the first
        # row of the file which is supposed to be the header

        var_dict = {}
        for chunk in self._SEP_RE.split(file.readline()):
            var, unit = self._VAR_RE.match(chunk).groupdict().values()
            if unit not in ureg:
                unit = ''
            var_dict[var] = ureg.Unit(unit)
            
        kwargs = dict(skiprows=1, delimiter=self.DELIM, dtype=[(var, float) for var in var_dict])

        try:
            # Try fast load first with np.loadtxt which assumes there is no
            # missing data within the file
            data = np.loadtxt(file, **kwargs)
        except:
            # np.genfromtxt is significantly slower than np.loadtxt and
            # thus it is used only as a last resort
            kwargs['skip_header'] = kwargs.pop('skiprows')
            data = np.genfromtxt(file, **kwargs)
            
        return var_dict, data

    def read_config_file(self, file):
        """
        Load a given config file into a TrajectoryParser (special configparser)
        instance and return that instance. How each section/option is read is
        left up to the caller.
        """
        config = TrajectoryParser(allow_no_value=True)
        config.read(file)
        return config

    

    
    
    
x = Reader().read_config_file('Test-1.cfg')
print(x.getquantity('Current Properties', 'v_theta'))
    
    
    
    
    
    
    
    
    
    
    