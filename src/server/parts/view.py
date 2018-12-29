# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import logging

# -- third party --

# -- own --

# -- code --
log = logging.getLogger('server.parts.view')


class View(object):
    def __init__(self, core):
        self.core = core

    def User(self, u):
        core = self.core

        return {
            'uid': core.auth.uid_of(u),
            'name': core.auth.name_of(u),
            'state': str(core.lobby.state_of(u)),
        }

    def Game(self, g):
        core = self.core

        return {
            'gid':      core.room.gid_of(g),
            'type':     g.__class__.__name__,
            'name':     core.room.name_of(g),
            'started':  bool(g.greenlet),
            'online':   len(core.room.online_users_of(g)),
        }

    def GameDetail(self, g):
        core = self.core

        rst = {
            'users':  [self.User(u) for u in core.room.users_of(g)],
            'params': core.game.params_of(g),
            'items':  core.item.items_of(g),
        }
        rst.update(self.Game(g))
        return rst

    def Player(self, p):
        return self.User(p.client)
