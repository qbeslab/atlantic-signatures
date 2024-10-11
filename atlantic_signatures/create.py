"""

Limited API for controlling the iRobot Create2
==============================================

Only the subset of commands related to driving and vital functionality are
implemented.


"""

from enum import IntEnum
import struct
import time

import serial
from serial.tools.list_ports import comports



class OPCODES(IntEnum):
    START        = 0x80
    RESET        = 0x07
    STOP         = 0xad
    SAFE         = 0x83
    FULL         = 0x84
    DRIVE        = 0x89
    DRIVE_DIRECT = 0x91

    def __bytes__(self) -> bytes:
        return bytes([self.value])


def list_ports():
    """List all serial ports that are opened."""
    return [port.device for port in comports()]

def find_port():
    """Returns a "best guess" port that the Create is connected to."""
    for port in comports():
        if port.manufacturer == 'FTDI' or port.vid == 0x403:
            if port.pid in (0x6001, 0x6015):
                return port.device



class Create:
    """
    Create movement and base functionality commands
    """

    _SPECIAL_TURN_RADII = {
        'straight': 32767,
        'rotate_cw': -1,
        'rotate_ccw': 1
        }

    _COMMAND_DELAY = 0.015  # Number of seconds between commands

    # Speeds below ~28.5 mm/s are not actualized and the Create should remain
    # stationary or move extremely slowly. Thus while 0 mm/s is technically the
    # slowest the Create can go, any value below 28.5 (29) mm/s is considered
    # equivalent to 0 mm/s and the "isDriving" property will return False.
    _MIN_MOVING_SPEED = 28.5

    _SHAFT_LENGTH   = 235.0  # The Create's wheels are 235 mm apart
    _WHEEL_DIAMETER = 72.0  # The Create's wheels have a diameter of 72 mm

    def __init__(self, port=None):
        if port is None:
            port = find_port()
        self._serial = serial.Serial(port=port, baudrate=115200)
        self._serial_startup()

    def _serial_send(self, fmt, *v):
        self._serial.write(struct.pack(fmt, *v))
        time.sleep(self._COMMAND_DELAY)

    def _start(self):
        self._serial_send('B', OPCODES.START)

    def _reset(self):
        self._serial_send('B', OPCODES.RESET)

    def _stop(self):
        self._serial_send('B', OPCODES.STOP)

    def _safe(self):
        self._serial_send('B', OPCODES.SAFE)

    def _full(self):
        self._serial_send('B', OPCODES.FULL)

    def _drive(self, v, r='straight'):
        if r in self._SPECIAL_TURN_RADII:
            r = self._SPECIAL_TURN_RADII[r]
        else:
            r = self._bound(r, 0, 2000)

        v = self._bound(v, 0, 500)
        self._serial_send('>B2h', OPCODES.DRIVE, v, r)
        self._is_driving = v > self._MIN_MOVING_SPEED

    def _drive_direct(self, vl, vr):
        vl, vr = self._bound(vl, 0, 500), self._bound(vr, 0, 500)

        self._serial_send('>B2h', OPCODES.DRIVE_DIRECT, vr, vl)
        self._is_driving = (abs(vl + vr) / 2 > self._MIN_MOVING_SPEED or
                            abs(vr - vl) > self._MIN_MOVING_SPEED)

    def _serial_startup(self, mode='full'):
        if not self._serial.is_open:
            self._serial.open()

        self._start()
        self._safe() if mode == 'safe' else self._full()
        time.sleep(2)

    def close(self):
        self._serial.close()

    @staticmethod
    def _bound(q, minq, maxq):
        qsgn = -1 if q < 0 else 1
        return qsgn * min(max(minq, abs(round(q))), maxq)

    @property
    def is_driving(self):
        return self._is_driving
