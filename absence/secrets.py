import os
import ConfigParser

DIRECTORY = '~/.absence'
FILE = 'secrets'

class ConfigParserWithDefaults(ConfigParser.ConfigParser):

    def get(self, *args, **kwargs):
        try:
            ConfigParser.ConfigParser.get(self, *args, **kwargs)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return None
            
def read():
    try:
        os.makedirs(os.path.expanduser(DIRECTORY))
    except OSError:
        pass
    c = ConfigParserWithDefaults()
    c.read(os.path.expanduser(os.path.join(DIRECTORY, FILE)))
    return c
