# -*- coding: utf-8 -*-


# -- stdlib --
import logging

# -- third party --

# -- own --

# -- code --
log = logging.getLogger('server.parts.stats')


class Stats(object):
    def __init__(self, core):
        self.core = core
