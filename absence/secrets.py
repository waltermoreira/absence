import os
import ConfigParser

FILE = 'secrets'

class ConfigParserWithDefaults(ConfigParser.ConfigParser):

    def get(self, *args, **kwargs):
        try:
            return ConfigParser.ConfigParser.get(self, *args, **kwargs)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return None
            
def read(directory):
    try:
        os.makedirs(os.path.expanduser(directory))
    except OSError:
        pass
    c = ConfigParserWithDefaults()
    if not c.read(os.path.expanduser(os.path.join(directory, FILE))):
        raise IOError('cannot find config file: secrets')
    return c
