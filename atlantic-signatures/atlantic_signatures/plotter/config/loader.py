"""
mycreate_plotter.config.loader module does major heavy lifting for interpreting
configuration data that is attached to a test run.
"""
import os
import os.path
import re
import sys
import zipfile

import numpy as np

from north_atlantic_signatures.units import ureg
from north_atlantic_signatures.plotter.config import TrajectoryParser


class ConfigLoader:
    """Loads a config file(s) into a configparser instance."""

    _VALID_EXTENSIONS = ('.cfg', '.txt', '.conf', '.ini', '.cnf', '.cn')

    _PARSER_ARGS = {
        'defaults': None,
        }


    def __init__(self, *files):
        pass



class Loader:
    """Base Loader class for opening data+config files."""

    _VAR_RE = re.compile(r"(?P<var>\w+)\s*\((?P<unit>[a-zA-Z0-9_\^\/]+)\)")

    def __init__(self, locale=None, **kwargs):
        self._DELIM = kwargs.pop('delim', ',')
        self._SEP_RE = re.compile(r"\s*%s\s*" % self._DELIM)

        #self.TEST_RE = re.compile(self.get_signature(testnums, extensions))


    def load_data_file(self, file):
        """
        Given an opened data file object *file* this function will return a
        numpy array of the data inside that file.
        """

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

    def load_config_file(self, file):
        """

        """
        config = TrajectoryParser(allow_no_value=True)
        config.read(file)
        return config


    def pool_locales(self):
        """
        Return all locales (A locale is a directory or zip archive that may
        contain test data) as a single iterable.

        If a path(s) is provided as a command line argument this pool will be
        modified to include those path(s).
        """
        locales = set()

        # The order of pooling is:
        #
        # 1.) Command-line provided paths
        # 2.) Paths saved in the "DATA_LOCALES" environment variable (if it exists)
        # 3.) The current working directory
        # 4.) Suspected locales below the current working directory

        if 'DATA_LOCALES' in os.environ:
            if os.name == 'posix':
                locales.update(os.environ['DATA_LOCALES'].split(':'))
            elif os.name == 'nt':
                locales.update(os.environ['DATA_LOCALES'].split(';'))

        locales.update(self._get_locales_from_dir(os.getcwd()))

        return locales


    def _get_locales_from_dir(self, dir):
        """Return all locales below the directory *dir*."""
        paths = set()
        for path in os.listdir(dir):
            fullpath = os.path.join(dir, path)

            if os.path.isfile(fullpath):
                if self.TEST_RE.match(path) is not None:
                    # If test files are in dir
                    paths.add(dir)
                elif path == 'data.zip':
                    paths.add(fullpath)

            if os.path.isdir(fullpath) and path == 'data':
                paths.add(fullpath)

        return paths


    def find_tests(self, *dirs):
        """
        Given a list of directories *dirs* return all files that CAN be test
        data.
        """

        tests = []

        if not dirs:
            cwd = os.getcwd()
            print('No directory was provided. Default to the current working '
                  'directory: %s' % cwd)
            dirs = [cwd]

        for dir in dirs:
            for file in os.listdir(dir):
                if self.TEST_RE.match(file) is not None:
                    tests.append(os.path.join(dir, file))

        print('%d test files were found' % len(tests))

        return tests

    @staticmethod
    def get_signature(testnums=[], extensions=[]):
        """
        Given a list of test numbers and/or extensions, return a regex pattern
        string that can be used with a suitable re function to find files that
        match that pattern.
        """
        base = r"Test-(%s)\.(%s)"
        exts = '|'.join(ext for ext in extensions) if extensions else '.+'
        nums = '|'.join(str(num) for num in testnums) if testnums else '\d+'
        return base % (nums, exts)


    @classmethod
    def loader_from_builtin(cls, name, *args, **kwargs):
        """
        Alternative constructor to __init__ that loads builtin data from the
        module *name* and any modules below it.
        """
        locales = set()
        for root, dirs, _ in os.walk(sys.modules['mycreate_plotter'].__path__[0]):
            for dir in dirs:
                if dir == name:
                    path = os.path.join(root, dir, 'data.zip')
                    if os.path.isfile(path):
                        locales.add(path)
        return cls(locales, *args, **kwargs)

    @classmethod
    def load_direct(cls, configfile, datafile, **kwargs):
        kwargs['configfile'] = configfile
        kwargs['datafile']   = datafile
        return cls(**kwargs)




class CachedLoader(Loader):
    """Load data that is builtin to the mycreate_plotter package.

    ** If a hypothetical module ``mycreate_plotter.example`` has data that is
    ** to be cached and loaded then it must contain a zip archive titled
    ** data.zip.
    ** Within data.zip, directories are named after the test date in YYYY-MM-DD
    ** format, and each run within a directory must have two files:
    ** Test-X.csv (The test data) and Test-X.cfg (Configuration for that run).

    data.zip/
        2020-03-01/
            Test-1.csv
            demo.cfg
        2020-04-01/
            Test-1.csv
            demo.cfg
            Test-2.csv
            Test-2.cfg

    The file Test-X.csv is loaded into a numpy array while the configuration
    file is handled by the configparser module. It is up to the user/module for
    how that confugration data is evaluated.
    """

    def __init__(self, testdates=None, testnums=None, signatures=None, **kwargs):
        _DEFAULT_DIR = os.path.join(os.getcwd(), 'data.zip')
        self._zipdir = zipfile.ZipFile(kwargs.get('zipfile', _DEFAULT_DIR))

        self._delim  = kwargs.pop('delimiter', ',')

        self._SEP_RE = re.compile(r"\s*%s\s*" % self._delim)
        self._VAR_RE = re.compile(r"(?P<var>\w+)\s*\((?P<unit>[a-zA-Z0-9_\^\/]+)\)")




    def _load_data_file(self, file, **kwargs):
        _kwargs = dict(skiprows=1, delimiter=self._delim)  #unpack=True
        _kwargs.update(kwargs)

        with self.zipdir.open(file) as f:
            header_dict = self._process_header_string(f.readline())
            _kwargs['dtype'] = [(var, float) for var in header_dict]

            # Try fast load first with np.loadtxt which assumes there is no
            # missing data within the file
            try:
                data = np.loadtxt(f, **_kwargs)
            except:

                # np.genfromtxt is significantly slower than np.loadtxt and
                # thus it is used only as a last resort
                _kwargs['skip_header'] = _kwargs.pop('skiprows')
                data = np.genfromtxt(f, **_kwargs)

        return header_dict, data

    def _process_header_string(self, header_string):
        """
        Pre-process the header string into a dict with each key-value pair as
        the variable name mapped to its unit.
        """
        retdict = {}
        for chunk in self._SEP_RE.split(header_string):
            var, unit = self._VAR_RE.match(chunk).groupdict().values()
            if unit not in ureg:
                unit = ''
            retdict[var] = ureg.Unit(unit)
        return retdict



    @property
    def zipdir(self):
        return self._zipdir
