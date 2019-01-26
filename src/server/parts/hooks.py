# -*- coding: utf-8 -*-


# -- stdlib --
import logging

# -- third party --

# -- own --
from game.autoenv import EventHandler

# -- code --
log = logging.getLogger('server.actors.hooks')


class ServerEventHooks(EventHandler):
    def __init__(self):
        self.hooks = [
        ]

    def handle(self, evt_type, arg):
        for h in self.hooks:
            arg = h.handle(evt_type, arg)

        return arg


class Hooks(object):
    def __init__(self, core):
        self.core = core
        core.events.game_started += self.handle_game_started

    def handle_game_started(self, g):
        g.event_observer = ServerEventHooks()
        return g
