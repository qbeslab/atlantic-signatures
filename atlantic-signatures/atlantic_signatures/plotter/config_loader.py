"""
Loads configuration files (INI format) that contain all metadata associated to
trajectory data and stores that metadata in a dict structure stored in the
Loader instance.
"""
from collections import UserDict
import configparser
from configparser import _UNSET, NoOptionError, NoSectionError
import fnmatch
import glob
import os
import os.path
import re
import string
import zipfile

import numpy as np
from pint import UnitRegistry
ureg = UnitRegistry()

UNIT_RE   = re.compile(r"\([a-zA-Z0-9_\^\/]+\){0,1}")
NUMBER_RE = re.compile(r"-{0,1}\d+(\.\d*)?")


class ConfigError(BaseException):
    pass


class InvalidConfigFormatError(ConfigError):
    pass


class MissingDataFileError(ConfigError):
    """
    Raised when a config file does not have a corresponding data file and thus
    has no real purpose.
    """

    def __init__(self, path, datafile):
        message = ("The config file: '%s' is missing its linked data file: "
                   "'%s'" % (path, datafile)
                   )
        super(MissingDataFileError, self).__init__(message)


class MissingConfigFileError(ConfigError):
    """Raised when a given config file cannot be found."""

    def __init__(self, dirname, configfile):
        message = ("The config file: '%s' cannot be found in the given "
                   "directory: '%s'" % (configfile, dirname)
                   )
        super(MissingConfigFileError, self).__init__(message)

        

BUILTINS = {}
BUILTINS['north_atlantic_signatures'] = os.path.join('north_atlantic_signatures', 'data.zip')

CONFIG_SIGNATURE = '*.cfg'

def find_builtin_configs(builtin):
    """
    Given a builtin module name, recursively search for all config files
    that match the signature within the builtin modules data.zip archive.
    """
    try:
        path = BUILTINS[builtin]
        assert os.path.exists(path)
    except:
        raise ValueError("The builtin name: '%s' does not exist" % builtin) from None

    if os.path.isdir(path):
        files = glob.glob(os.path.join(path, CONFIG_SIGNATURE), recursive=True)
    
    if path.endswith('.zip'):
        with zipfile.ZipFile(path) as ziparchive:
            files = fnmatch.filter(ziparchive.namelist(), CONFIG_SIGNATURE)
    
    return files


def get_data_file(config_file, *, config_file_path=None, extension='.csv'):
    base = os.path.splitext(config_file)[0]
    if config_file_path is not None:
        base = os.path.join(config_file_path, base)
    return base + extension


def load_data_file(file):
    return np.loadtxt(file, skiprows=1, delimiter=',', unpack=True)
    
def load_zipped_data_file(file, zip_path):
    with zipfile.ZipFile(zip_path) as zipdir:
        with zipdir.open(file) as file:
            data = np.loadtxt(file, skiprows=1, delimiter=',', unpack=True)
    return data


class MetadataConfigParser(configparser.ConfigParser):

    UNIT_RE   = re.compile(r"\([a-zA-Z0-9_\^\/]+\){0,1}")
    NUMBER_RE = re.compile(r"-{0,1}\d+(\.\d*)?")


    def _convert_to_quantity(self, value):
        unit = self.UNIT_RE.search(value)
        if unit is not None:
            unit = getattr(ureg, unit.group(0), None)
        values = (match.group(0) for match in self.NUMBER_RE.finditer(value))
        #quantities = [ureg.Quantity(float(n), unit).to_base_units() for n in values]
        quantities = ureg.Quantity([float(n) for n in values], unit).to_base_units()
        if len(quantities) == 1:
            return quantities[0]
        return quantities

    def getquantity(self, section, option, *, raw=False, vars=None,
               fallback=configparser._UNSET, **kwargs):
        return self._get_conv(section, option, self._convert_to_quantity,
                              raw=raw, vars=vars,
                              fallback=fallback, **kwargs)
    

    
class InterpolatedMetadataConfigParser(configparser.ConfigParser):
    """
    Child class of ConfigParser that combines interpolation and a custom
    getter method for numbers combined with units (quantities).
    """
    
    UNIT_RE   = re.compile(r"\([a-zA-Z0-9_\^\/]+\){0,1}")
    NUMBER_RE = re.compile(r"-{0,1}\d+(\.\d*)?")
    

    
    def _convert_to_quantity(self, value):
        unit = self.UNIT_RE.search(value)
        if unit is not None:
            unit = getattr(ureg, unit.group(0), None)
        values = (match.group(0) for match in self.NUMBER_RE.finditer(value))
        quantities = [ureg.Quantity(float(n), unit).to_base_units() for n in values]
        if len(quantities) == 1:
            return quantities[0]
        return quantities

    def getquantity(self, section, option, *, raw=False, vars=None,
               fallback=configparser._UNSET, **kwargs):
        return self._get_conv(section, option, self._convert_to_quantity,
                              raw=raw, vars=vars,
                              fallback=fallback, **kwargs)
    
    def get(self, section, option):
        value = super(InterpolatedMetadataConfigParser, self).get(section, option)
        if value.lower() in self.BOOLEAN_STATES:
            return self._convert_to_boolean(value)
        
        unit = self.UNIT_RE.search(value)
        if unit is None:
            unit = getattr(ureg, unit.group(0), None)

        

class ConfigLoader(configparser.ConfigParser):
    def __init__(self, file, **kwargs):
        path = kwargs.pop('path', os.getcwd())
        super(ConfigLoader, self).__init__(**kwargs)


        if not os.path.exists(path):
            raise MissingConfigFileError(path, file)
        
        if path.endswith('.zip'):
            with zipfile.ZipFile(path) as ziparchive:
                with ziparchive.open(file) as zippedfile:
                    self.read_string(zippedfile.read().decode('utf-8'))
        else:
            self.read(os.path.join(path, file))

            
    def read_goal_properties(self, **defaults):
        cache = {}
        if not 'Goal Properties' in self.sections():
            return cache

        for option, valuestr in self.items('Goal Properties'):
            if option.startswith('goal_'):
                unitstr = UNIT_RE.search(valuestr)
                try:
                    unitstr = UNIT_RE.search(valuestr).group(0)
                    assert unitstr in ureg
                except (AttributeError, AssertionError):
                    unitstr = 'meter'
                finally:
                    unit = getattr(ureg, unitstr)
                
                coords = [float(match.group(0)) for match in NUMBER_RE.finditer(valuestr)]
                if len(coords) != 2:
                    raise InvalidConfigFormatError('A goal needs 2 coordinates to be a valid location')
            
                cache[option] = ureg.Quantity(coords, unit)
            else:
                cache[option] = valuestr

        return cache
    
    def getquantity(self, section, option, **kwargs):
        raw      = kwargs.pop('raw', False)
        vars     = kwargs.pop('vars', None)
        fallback = kwargs.pop('fallback', _UNSET)
        
        try:
            value = self.get(section, option, raw=raw, vars=vars, fallback=fallback)
            
            try:
                unit = UNIT_RE.search(value)
                assert unit in ureg
            except (AttributeError, AssertionError):
                unit = kwargs.pop('default_units', 'dimensionless')
            finally:
                unit = getattr(ureg, unit)

            values = [float(match.group(0)) for match in NUMBER_RE.finditer(value)]
            size = kwargs.pop('size', 0)
            if size:
                if len(values) != size:
                    raise InvalidConfigFormatError(
                        "The section-option pair: '%s:%s' should have a size: "
                        "%d" %(section, option, size)
                        )
            return ureg.Quantity(values, unit)
        except (NoSectionError, NoOptionError, InvalidConfigFormatError):
            if fallback is _UNSET:
                raise
            return fallback           
            




                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
  
