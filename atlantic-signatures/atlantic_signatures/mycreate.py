from __future__ import print_function

import socket
import select

import serial


CONTROL_PORTS = (10000, 10001, 10002)

class _CreateBase:
    def __init__(self):
        self._step_length = 100
    
    def drive_straight(self):
        pass

class Create(_CreateBase):
    def __init__(self):
        self._interface = serial.serial()
    
    def drive_straight(self):
        pass
    
class CreateController(_CreateBase):
    def __init__(self, rpi_ip):
        self._interface = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._interface.settimeout(10)
        
        for port in CONTROL_PORTS:
            try:
                self._interface.connect((rpi_ip, port))
                break
            except:
                print('Failed to connect to the Raspberry pi at address %s '
                      'and port %d' % (rpi_ip, port))
        else:
            raise ConnectionError('Could not connect to the Raspberry pi at '
                                  '%s' % rpi_ip)
                

