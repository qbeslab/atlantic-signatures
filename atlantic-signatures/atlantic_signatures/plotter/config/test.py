# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 15:32:13 2021

@author: lucsc
"""


import os
import os.path
import sys

curdir = os.path.dirname(os.path.abspath(__file__))
config = os.path.join(curdir, 'Test-2.cfg')
data   = os.path.join(curdir, 'Test-1.csv')

print(os.readlink('Test-2.cfg'))
#os.symlink(config, data)
#print(os.getlogin())