# -*- coding: utf-8 -*-

# -- stdlib --
import logging

# -- third party --
# -- own --
from server.base import Game
from server.endpoint import Client


# -- code --
log = logging.getLogger('server.parts.view')


class View(object):
    def __init__(self, core):
        self.core = core

    def User(self, u: Client):
        core = self.core

        return {
            'uid': core.auth.uid_of(u),
            'name': core.auth.name_of(u),
            'state': str(core.lobby.state_of(u)),
        }

    def Game(self, g: Game):
        core = self.core

        return {
            'gid':      core.room.gid_of(g),
            'type':     g.__class__.__name__,
            'name':     core.room.name_of(g),
            'started':  bool(g.greenlet),
            'online':   len(core.room.online_users_of(g)),
        }

    def GameDetail(self, g: Game):
        core = self.core

        rst = {
            'users':  [self.User(u) for u in core.room.users_of(g)],
            'params': core.game.params_of(g),
            'items':  core.item.items_of(g),
        }
        rst.update(self.Game(g))
        return rst

    def Player(self, p: Client):
        return self.User(p.client)
