import os
import ConfigParser

DIRECTORY = '~/.absence'
FILE = 'secrets'

def read():
    try:
        os.makedirs(os.path.expanduser(DIRECTORY))
    except OSError:
        pass
    c = ConfigParser.ConfigParser()
    c.read(os.path.expanduser(os.path.join(DIRECTORY, FILE)))
    return c
