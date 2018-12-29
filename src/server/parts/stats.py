# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import logging

# -- third party --

# -- own --

# -- code --
log = logging.getLogger('server.actors.stats')


class Stats(object):
    def __init__(self, core):
        self.core = core
        core.events.game_started += self.handle_game_started

    def handle_game_started(self, g):
        stats({'event': 'start_game', 'attributes': {'gametype': manager.gamecls.__name__}})
        return g
