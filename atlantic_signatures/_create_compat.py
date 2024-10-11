

import serial
from serial.tools.list_ports import comports


def all_serial_ports():
    """Returns the complete list of serial ports connected to the host."""
    return [port.device for port in comports()]


def port_to_create():
    """Returns a "best guess" port that the Create is connected to."""

    for port in comports():
        if port.manufacturer == 'FTDI' or port.vid == 1027:
            if port.pid in (24577, 24597):
                return port


class Create:
    """An object representing an extremely limited iRobot Create2 in terms of
    functionality.
    """

    def __init__(self, port=None):
        if port is None:
            port = port_to_create()

        self._si = serial.Serial(port=port, baudrate=115200)

    def start(self):
        self._si.write(b'')
