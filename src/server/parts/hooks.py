# -*- coding: utf-8 -*-

# -- stdlib --
from typing import List
import logging

# -- third party --
# -- own --
from game.base import EventHandler
from server.base import Game
from server.core import Core


# -- code --
log = logging.getLogger('server.parts.hooks')


class ServerEventHooks(EventHandler):
    def __init__(self):
        self.hooks: List[EventHandler] = [
        ]

    def handle(self, evt_type, arg):
        for h in self.hooks:
            arg = h.handle(evt_type, arg)

        return arg


class Hooks(object):
    def __init__(self, core: Core):
        self.core = core
        core.events.game_started += self.handle_game_started

    def handle_game_started(self, g: Game):
        g.event_observer = ServerEventHooks()
        return g
