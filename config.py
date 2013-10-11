from os.path import join

from sys import version_info

if version_info.minor < 2:
    from compat import ConfigParser
else:
    from configparser import ConfigParser

def get_config(cfgdir, host):
    parser = ConfigParser()
    cfgfile = join(cfgdir, host)
    parser.read(cfgfile)
    if parser.sections():
        return parser
    else:
        return None


