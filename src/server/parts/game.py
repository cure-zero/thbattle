# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
from typing import List, Type, Dict, Any, cast
import logging
import random

# -- third party --
# -- own --
from game.base import Player, GameData
from server.base import Game as ServerGame, NPCPlayer, HumanPlayer
from server.core import Core
from server.endpoint import Client
from server.utils import command
from utils.misc import BatchList
from wire import msg as wiremsg


# -- code --
log = logging.getLogger('Game')


class Game(object):
    def __init__(self, core: Core):
        self.core = core

        core.events.game_started += self.handle_game_started
        core.events.game_ended += self.handle_game_ended
        core.events.game_joined += self.handle_game_joined
        core.events.game_left += self.handle_game_left
        core.events.game_successive_create += self.handle_game_successive_create
        core.events.user_state_transition += self.handle_user_state_transition
        core.events.client_pivot += self.handle_client_pivot

        _ = core.events.client_command
        _['game:set-param'] += self._set_param
        _['game:data'] += self._gamedata

    def handle_user_state_transition(self, ev):
        u, f, t = ev
        if t == 'lobby':
            u._[self] = {
                'game': None,
                'params': {},
            }
        return ev

    def handle_client_pivot(self, u):
        core = self.core
        if core.lobby.state_of(u) == 'game':
            g = u._[self]['game']
            assert g
            assert u in g.players.client

            u.write(['game_joined',  core.view.Game(g)])
            u.write(['game_started', core.view.GameDetail(g)])

            self.replay(u, u)

        return u

    def handle_game_started(self, g):
        self.setup_game(g)

        core = self.core
        users = core.room.users_of(g)
        for u in users:
            u.write(['game_started', core.view.GameDetail(g)])

        return g

    def handle_game_ended(self, g):
        core = self.core
        users = core.room.online_users_of(g)
        for u in users:
            u.write(['game_ended', core.room.gid_of(g)])

    def handle_game_joined(self, ev):
        g, c = ev
        core = self.core
        if core.room.is_started(g):
            g._[self]['data'][c].revive()
            g._[self]['fleed'][c] = False

        c._[self]['game'] = g

        return ev

    def handle_game_left(self, ev):
        g, c = ev
        core = self.core
        if core.room.is_started(g):
            g._[self]['data'][c].die()
            g._[self]['fleed'][c] = bool(g.can_leave(self._find_player(c)))

        c._[self]['game'] = None

        return ev

    def handle_game_successive_create(self, ev):
        old, g = ev
        core = self.core

        params = old._[self]['params']
        g._[self]['params'] = params
        gid = core.room.gid_of(g)
        core.room.online_users_of(old).write(['game_params', [gid, params]])

        return ev

    # ----- Commands -----
    @command('room')
    def _set_param(self, u: Client, key: str, value: object):
        core = self.core

        if core.lobby.state_of(u) != 'room':
            return

        g = core.game.current(u)
        users = core.room.online_users_of(g)

        cls = g.__class__
        if key not in cls.params_def:
            log.error('Invalid option "%s"', key)
            return

        if value not in cls.params_def[key]:
            log.error('Invalid value "%s" for key "%s"', value, key)
            return

        if g._[self]['params'][key] == value:
            return

        g._[self]['params'][key] = value

        gid = core.room.gid_of(g)

        for u in users:
            if core.lobby.state_of(u) == 'ready':
                core.room.cancel_ready(u)

            u.write(['set_game_param', [u, key, value]])
            u.write(['game_params', [gid, g._[self]['params']]])

    @command('game')
    def _gamedata(self, u: Client, gid: int, serial: int, tag: str, data: object):
        core = self.core
        g = u._[self]['game']
        if gid != core.room.gid_of(g):
            return

        pkt = g._[self]['data'][u].feed_recv(serial, tag, data)
        core.events.game_data_recv.emit((g, u, pkt))

    # ----- Public Methods -----
    def create_game(self, cls: Type[ServerGame]) -> ServerGame:
        core = self.core
        g = cls(core)

        seed = random.getrandbits(63)
        g.random = random.Random(seed)

        g._[self] = {
            'params': {k: v[0] for k, v in cls.params_def.items()},
            'fleed': defaultdict(bool),
            'aborted': False,
            'crashed': False,
            'rngseed': seed,
            'data': {},
        }

        return g

    def replay(self, c: Client, to: Client) -> None:
        # XXX compress
        g = c._[self]['game']
        pkts = g._[self]['data'][c].get_sent()
        if not pkts:
            return

        to.write(['game:live-at', pkts[-1].serial])
        for p in pkts:
            to.write(['game:data', [p.id, p.tag, p.data]])

    # ----- Public Methods -----
    def mark_crashed(self, g: ServerGame) -> None:
        g._[self]['crashed'] = True

    def is_crashed(self, g: ServerGame) -> bool:
        return g._[self]['crashed']

    def abort(self, g: ServerGame) -> None:
        core = self.core
        g._[self]['aborted'] = True
        core.events.game_aborted.emit(g)

    def is_aborted(self, g: ServerGame) -> bool:
        return g._[self]['aborted']

    def setup_game(self, g: ServerGame) -> None:
        core = self.core
        users = core.room.users_of(g)

        g._[self]['data'] = {
            core.auth.uid_of(u): GameData()
            for u in users
        }

    def build_players(self, g: ServerGame, users: List[Client]) -> BatchList[Player]:
        pl: BatchList[Player] = BatchList([HumanPlayer(g, u) for u in users])
        pl[:0] = [NPCPlayer(g, i.name, i.input_handler) for i in g.npc_players]

        return pl

    def is_fleed(self, g: ServerGame, u: Client) -> bool:
        return g._[self]['fleed'][u]

    def get_gamedata_archive(self, g: ServerGame) -> List[dict]:
        return [
            g._[self]['data'][i].archive()
            for i in g._[self]['users']
        ]

    def write(self, g: ServerGame, u: Client, tag: str, data: object) -> None:
        core = self.core
        assert u._[self]['game'] is g
        pkt = g._[self]['data'][u].feed_send(tag, data)
        gid = core.room.gid_of(g)
        u.write(wiremsg.GameData(gid=gid, serial=pkt.serial, tag=pkt.tag, data=pkt.data))
        core.events.game_data_send.emit((g, u, pkt))

    def current(self, u: Client) -> ServerGame:
        return u._[self]['game']

    def params_of(self, g: ServerGame) -> Dict[str, Any]:
        return g._[self]['params']

    def winners_of(self, g: ServerGame) -> List[Client]:
        return [p.client for p in cast(List[HumanPlayer], g.winners)]

    def rngseed_of(self, g: ServerGame) -> int:
        return g._[self]['rngseed']
