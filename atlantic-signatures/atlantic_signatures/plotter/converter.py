# -*- coding: utf-8 -*-
"""
Created on Fri Jun  4 16:01:11 2021

@author: lucsc
"""


import glob
import gzip
import os
import os.path
import zipfile

dates = ['2020-03-%s' % i for i in ('03', '04', '05', '06', '11', '12')]

for date in dates:
    datedir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'north_atlantic_signatures', 'data', date)
    for path in os.listdir(datedir):
        if path.endswith('.csv.gz'):
            n = os.path.join(datedir, path)
            with gzip.open(n, mode='rt') as file:
                with open(os.path.splitext(n)[0] + '.csv', mode='w') as csvfile:
                    csvfile.write(file.read())
