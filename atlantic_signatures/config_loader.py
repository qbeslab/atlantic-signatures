"""
Loads config files for plotting and serialization methods
"""


from configparser import _UNSET, ConfigParser, NoOptionError, NoSectionError
import json
import re

from atlantic_signatures.units import ureg


class InvalidConfigFormatError(Exception):
    """Raised when a config file has an invalid format."""


class QuantityConfigParser(ConfigParser):

    _UNIT_RE   = re.compile(r"\([a-zA-Z0-9_\^\/]+\){0,1}")
    _NUMBER_RE = re.compile(r"(-{0,1}\d+)(\.\d*)?")

    def getquantity(self, section, option, *, raw=False, vars=None, fallback=_UNSET,
                    units=_UNSET, size=_UNSET):
        """
        Return a pint.Quantity (a number/number array bound to a unit) from a
        given section-option pair.
        """

        try:
            # First we get the raw string as returned from the ConfigParser.get
            # method and then evaluate instead of deferring to the _get_conv
            # method that the various other getter methods use.
            value = self.get(section, option, raw=raw, vars=vars, fallback=fallback)

        except (NoSectionError, NoOptionError):
            if fallback is _UNSET:
                raise
            elif isinstance(fallback, (int, float)) and units is not _UNSET:
                # Special fallback case where both a numeric fallback and a
                # default unit were provided.
                return ureg.Quantity(fallback, units)
            else:
                return fallback

        unit_match = self._UNIT_RE.search(value)
        unit = unit_match.group(0) if unit_match is not None else None

        if unit is None or unit not in ureg:
            # If the returned unit is invalid or there is no unit, resort to
            # the default unit provided in the "units" keyword-argument and
            # finally the quantity is set as "dimensionless" as a last resort
            unit = 'dimensionless' if units is _UNSET else units

        # Retain the type of the magnitude with the below code. If a option is
        # "45 millimeters" its magnitude will be 45 and not 45.0.
        magnitudes = []
        for num, decimal in self._NUMBER_RE.findall(value):
            if not decimal:
                magnitudes.append(int(num))
            else:
                magnitudes.append(float(num + decimal))

        if size is not _UNSET:
            if len(magnitudes) != size:
                raise InvalidConfigFormatError(
                        "The section-option pair: '%s:%s' should have a size: "
                        "%d" %(section, option, size)
                        )

        if len(magnitudes) == 1:
            # If only one number, turn back into a scalar quantity
            magnitudes = magnitudes[0]

        return ureg.Quantity(magnitudes, unit)


REQUIRED_CONFIG_SECTIONS = (
    'Field Properties',
    'Current Properties',
    'Goal Properties',
    'Boundary Conditions',
    'Create Properties'
    )

# (section, option): (type ID, default value, default unit string)
CONFIG_OPTIONS = {
    ('Field Properties', 'a_inc'): ('<float>', None, None),
    ('Field Properties', 'b_inc'): ('<float>', None, None),
    ('Field Properties', 'c_inc'): ('<float>', None, None),
    ('Field Properties', 'a_int'): ('<float>', None, None),
    ('Field Properties', 'b_int'): ('<float>', None, None),
    ('Field Properties', 'c_int'): ('<float>', None, None),
    ('Field Properties', 'beta_0'): ('<quantity>', [0.0, 0.0, 0.0] * ureg.meter, 'meter'),
    ('Field Properties', 'gamma_0'): ('<quantity>', [0.0, 0.0, 0.0] * ureg.meter, 'meter'),
    ('Field Properties', 'eta'): ('<float>', None, None),
    ('Field Properties', 'theta_int'): ('<quantity>', 10 * ureg.degree, 'degree'),
    ('Field Properties', 'lambda'): ('<quantity>', 5 * ureg.degree, 'degree'),
    ('Current Properties', 'v_theta'): ('<quantity>', None, 'm/s'),
    ('Current Properties', 'v_radial'): ('<quantity>', None, 'm/s'),
    ('Current Properties', 'current_source_position'): ('<quantity>', [0.0, 0.0] * ureg.meter, 'meter'),
    ('Current Properties', 'theta_fluid'): ('<quantity>', 5 * ureg.degree, 'degree'),
    ('Current Properties', 's_x'): ('<float>', 2.0, None),
    ('Current Properties', 's_y'): ('<float>', 1.0, None),
    ('Boundary Conditions', 'x_min'): ('<quantity>', -2.7432 * ureg.meter, 'meter'),
    ('Boundary Conditions', 'x_max'): ('<quantity>', 2.7432 * ureg.meter, 'meter'),
    ('Boundary Conditions', 'y_min'): ('<quantity>', -2.7432 * ureg.meter, 'meter'),
    ('Boundary Conditions', 'y_max'): ('<quantity>', 2.7432 * ureg.meter, 'meter'),
    ('Create Properties', 'linear_velocity'): ('<quantity>', 0.1 * ureg.meters_per_second, 'mm/s'),
    ('Create Properties', 'agent_time_step'): ('<quantity>', 1.0 * ureg.sec, 'second'),
    ('Create Properties', 'angle_cutoff'): ('<quantity>', 1 * ureg.degree, 'degree'),
    ('Create Properties', 'multimodal_method'): ('<string>', 'direct', None),
    ('Create Properties', 'r_multi'): ('<quantity>', 0.1 * ureg.meter, 'meter'),
    ('Create Properties', 'r_goal'): ('<quantity>', 0.5 * ureg.meter, 'meter'),
    }



class Loader:

    _VAR_RE = re.compile(r"(?P<var>\w+)\s*\((?P<unit>[a-zA-Z0-9_\^\/]+)\)")

    def __init__(self, *args, **kwargs):
        self._DELIM  = kwargs.get('delimiter', ',')
        self._SEP_RE = re.compile(r"\s*%s\s*" % self._DELIM)

    def read_data_file(self, file):
        """
        Given an opened data file object *file* this function will return a
        numpy array of the data inside that file.
        """

        import numpy as np

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
        config = QuantityConfigParser(allow_no_value=True)
        config.read(file)
        return config



def config_to_dict(parser_object):

    id_map = {
        '<int>': parser_object.getint,
        '<float>': parser_object.getfloat,
        '<bool>': parser_object.getboolean,
        '<quantity>': parser_object.getquantity,
        '<string>': parser_object.get
        }

    cache = {}
    for section in REQUIRED_CONFIG_SECTIONS:
        cache[section] = {}
        for option in parser_object.options(section):
            id, default, unit = CONFIG_OPTIONS.get((section, option), ('<string>', None, None))
            kwargs = {}

            if default is not None:
                kwargs['fallback'] = default

            if section == 'Goal Properties':
                id, unit = '<quantity>', 'meters'

            if id == '<quantity>' and unit is not None:
                kwargs['units'] = unit
                q = id_map[id](section, option, **kwargs).to_base_units().m
                cache[section][option] = q if isinstance(q, (int, float)) else list(q)
                continue

            cache[section][option] = id_map[id](section, option, **kwargs)

    return cache


def config_to_json(parser_object):
    return json.dumps(config_to_dict(parser_object))
