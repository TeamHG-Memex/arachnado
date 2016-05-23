# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
from six.moves.configparser import SafeConfigParser

_ROOT = os.path.abspath(os.path.dirname(__file__))

FILENAMES = [
    os.path.join(_ROOT, 'config', 'defaults.conf'),
    '/etc/arachnado.conf',
    os.path.expanduser('~/.config/arachnado.conf'),
    os.path.expanduser('~/.arachnado.conf'),
]


def load_config(config_files=(), overrides=()):
    cp = SafeConfigParser()
    cp.optionxform = str  # make parsing case-sensitive
    cp.read(FILENAMES + config_files)

    for section, option, value in overrides:
        if value is not None:
            if isinstance(value, bool):
                value = int(value)
            cp.set(section, option, str(value))

    return {
        section: dict(cp.items(section))
        for section in cp.sections()
    }


def ensure_bool(opts, section, name):
    opts[section][name] = bool(int(opts[section][name]))
