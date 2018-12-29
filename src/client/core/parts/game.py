# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
import functools
import logging

# -- third party --
import gevent

# -- own --
from client.core.base import ForcedKill, Someone, Theone
from game.base import GameData
from utils.events import EventHub
from utils.misc import BatchList


# -- code --
log = logging.getLogger('client.core.parts.Game')
STOP = EventHub.STOP_PROPAGATION


class Game(object):
    def __init__(self, core):
        self.core = core
        core.events.server_command += self.handle_server_command

        self.games = {}

        self._dispatch = {
            'room_users': self._room_users,
            'game_started': self._game_started,
            'game_joined': self._game_joined,
            'observe_started': self._observe_started,
            'game_left': self._game_left,
            'game_ended': self._game_ended,
        }

    def handle_server_command(self, ev):
        cmd, args = ev
        f = self._dispatch.get(cmd)
        if f:
            f(args)
            return STOP
        return ev

    def handle_room_users(self, args):
        core = self.core
        gid, pl = args

        g = self.games.get(gid)
        if not g:
            return

        g._[self]['users'] = pl
        core.events.room_users.emit((g, pl))

    def handle_game_started(self, g):
        core = self.core
        self.prepare_game(g)
        core.events.game_prepared.emit(g)

    def handle_observe_started(self, gv):
        g = self.games[gv['gid']]
        g._[self]['observe'] = True
        return self.handle_game_started(gv)

    def handle_game_joined(self, gv):
        gid = gv['gid']
        g = self.create_game(
            gid,
            gv['type'],
            gv['name'],
            gv['users'],
            gv['params'],
            gv['items'],
        )
        self.games[gid] = g
        core = self.core
        core.events.game_joined.emit(g)

    def handle_game_left(self, gid):
        g = self.games.get(gid)
        if not g:
            return

        self.kill_game(g)

        core = self.core
        core.events.game_left.emit(g)

    def handle_game_ended(self, gid):
        g = self.games.get(gid)
        if not g:
            return

        log.info('=======GAME ENDED=======')
        core = self.core
        core.events.game_ended.emit(g)

    # ----- Public Methods -----
    def is_observe(self, g):
        return g._[self]['observe']

    def create_game(self, gid, mode, name, users, params, items):
        from thb import modes
        g = modes[mode]()

        g._[self] = {
            'gid':     gid,
            'name':    name,
            'users':   users,
            'params':  params,
            'items':   items,
            'data':    GameData(),
            'observe': False,
        }
        return g

    def prepare_game(self, g):
        core = self.core

        me_uid = core.auth.uid()

        uvl = g._[self]['users']
        assert me_uid in [uv['id'] for uv in uvl]

        me = Theone(g, me_uid, core.auth.name())
        pl = [
            me if uv['uid'] == me_uid else Someone(g, uv['uid'], uv['name'])
            for uv in uvl
        ]

        g.me = me
        g.players = BatchList(pl)

    def start_game(self, g):
        core = self.core
        gr = gevent.spawn(g.run)
        g._[self]['greenlet'] = gr

        @gr.link_exception
        def crash(gr):
            core.events.game_crashed.emit(g)

        log.info('----- GAME STARTED: %d -----' % g._[self]['gid'])

    def kill_game(self, g):
        g._[self]['greenlet'].kill(ForcedKill)

    def gid_of(self, g):
        return g._[self]['gid']

    def name_of(self, g):
        return g._[self]['name']

    def gamedata_of(self, g):
        return g._[self]['data']

    def items_of(self, g):
        return g._[self]['items']

    def params_of(self, g):
        return g._[self]['params']

    def users_of(self, g):
        return g._[self]['users']
