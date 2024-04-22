# -*- coding: utf-8 -*-
"""
Created on Fri Jun  4 09:44:39 2021

@author: lucsc
"""
import configparser
import gzip
import os
import os.path
import re

date = '2020-03-12'
delimiter = ','

CSV_HEADER_RE = re.compile(r"([a-zA-Z]+\([a-zA-Z]+\)\s*%s*\s*)+" % delimiter)

datadir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', date)

config = configparser.ConfigParser()




for file in os.listdir(datadir):
    if file.endswith('csv'):
        file = os.path.join(datadir, file)
        _config = ''
        with open(file, 'r', buffering=1) as f:
            for linenum, line in enumerate(f, start=1):
                if CSV_HEADER_RE.match(line):
                    header_line = linenum
                    break
                _config += line
        config.read_string(_config)
        with open(os.path.splitext(file)[0] + '.cfg', mode='w') as f:
            config.write(f)
        config.clear()
        
        with open(file, 'rb') as f:
            with gzip.open(file + '.gz', mode='wb') as fg:
                for linenum, line in enumerate(f, start=1):
                    if linenum >= header_line:
                        fg.write(line)

