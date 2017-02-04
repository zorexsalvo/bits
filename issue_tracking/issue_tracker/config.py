from __future__ import unicode_literals
import os
from six.moves.configparser import SafeConfigParser
from os import path
from . import settings

def get_config_path(filename):
    return path.join(os.getcwd(), "issue_tracker", "config", filename)


def config_for_environment(environment):
    env_filename = "%s.ini" % environment
    env_path = get_config_path(env_filename)

    config = read_config(env_path)
    return config


def read_config(config_file):
    config = SafeConfigParser()
    config.read(config_file)

    return config

environment = settings.DEFAULT_ENVIRONMENT

sys_config = config_for_environment(environment)

__all__ = [ sys_config, environment ]
