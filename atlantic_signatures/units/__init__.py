"""
The :mod:`atlantic_signatures.units` module implements a rudimentary unit system
for the purpose of plotting trajectories of the Roomba. Since the Roomba's state
vector is fully described as (x, y, theta, time) there is only a need for units
of length, time, and angles in our unit system.

The file *units.txt* defines a system known as 'RoombaUnits' with its base
units:

* [length] = meters
* [angle]  = radians
* [time]   = seconds

If units.txt is missing the default system (SI) will be resorted to.
"""

import os.path

from pint import UnitRegistry as _UnitRegistry


__all__ = ['ureg']


_unitfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'units.txt')

if os.path.isfile(_unitfile):
    ureg = _UnitRegistry(_unitfile)  #: an instance of :class:`pint.UnitRegistry` defined by units.txt
else:
    ureg = _UnitRegistry()
