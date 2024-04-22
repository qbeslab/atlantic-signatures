


from configparser import _UNSET, ConfigParser, NoOptionError, NoSectionError
import re

from north_atlantic_signatures.units import ureg


class InvalidConfigFormatError(Exception):
    """Raised when a config file has an invalid format."""


class TrajectoryParser(ConfigParser):

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
            
        unit = self._UNIT_RE.search(value)
        if unit not in ureg:
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
        


        
        
        
        
        
        
        
        
        
        
        