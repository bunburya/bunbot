"""This module contains classes for ensuring compatibility across multiple
minor versions of Python 3."""

from configparser import ConfigParser as ConfigParser_pre32, ParsingError
from optparse import OptionParser

### ConfigParser

class _Section:

    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
    
    def __getitem__(self, option):
        return self.parent.get(self.name, option)
    
    def __setitem__(self, option, value):
        self.parent.set(self.name, option, str(value))
    
    def __contains__(self, option):
        return self.parent.has_option(self.name, option)

    def get(self, option, default=None):
        if self.parent.has_option(self.name, option):
            return self[option]
        else:
            return default

    def getint(self, option):
        return self.parent.getint(self.name, option)

    def getboolean(self, option):
        return self.parent.getboolean(self.name, option)


class ConfigParser(ConfigParser_pre32):
    
    def __getitem__(self, section):
        return _Section(self, section)
    
    def __setitem__(self, section, optdict):
        self.add_section(section)
        for key in optdict:
            self.set(section, key, str(optdict[key]))
    
    def __contains__(self, section):
        return self.has_section(section)

### OptionParser/ArgumentParser

class ArgumentParser(OptionParser):
    
    """A thin wrapper around OptionParser implementing the relevant parts of
    the ArgumentParser API. Designed to ensure compatibility with
    Python 3.0-3.1."""
    
    def add_argument(self, *args, **kwargs):
        return OptionParser.add_option(self, *args, **kwargs)
    
    def parse_args(self, args=None, values=None):
        return OptionParser.parse_args(self, args, values)[0]
