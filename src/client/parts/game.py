# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Any, Dict, List, Sequence
import logging

# -- third party --
import gevent
from gevent import Greenlet

# -- own --
from client.base import ForcedKill, Game as ClientGame, Someone, Theone
from client.core import Core
from game.base import GameData, Player
from utils.events import EventHub
from utils.misc import BatchList
import wire


# -- code --
log = logging.getLogger('client.parts.Game')
STOP = EventHub.STOP_PROPAGATION


class Game(object):
    def __init__(self, core: Core):
        self.core = core
        self.games: Dict[int, ClientGame] = {}

        D = core.events.server_command
        D[wire.RoomUsers]      += self._room_users
        D[wire.GameStarted]    += self._game_started
        D[wire.GameJoined]     += self._game_joined
        D[wire.ObserveStarted] += self._observe_started
        D[wire.GameLeft]       += self._game_left
        D[wire.GameEnded]      += self._game_ended

    def _room_users(self, ev: wire.RoomUsers) -> wire.RoomUsers:
        core = self.core

        g = self.games.get(ev.gid)
        if not g:
            return ev

        g._[self]['users'] = ev.users
        core.events.room_users.emit((g, ev.users))

        return ev

    def _game_started(self, ev: wire.GameStarted) -> wire.GameStarted:
        core = self.core
        gv = ev.game
        g = self.games[gv['gid']]
        core.events.game_started.emit(g)
        return ev

    def _observe_started(self, ev: wire.ObserveStarted) -> wire.ObserveStarted:
        gv = ev.game
        g = self.games[gv['gid']]
        g._[self]['observe'] = True
        core = self.core
        core.events.game_started.emit(g)
        return ev

    def _game_joined(self, ev: wire.GameJoined) -> wire.GameJoined:
        gv = ev.game
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
        return ev

    def _game_left(self, ev: wire.GameLeft) -> wire.GameLeft:
        g = self.games.get(ev.gid)
        if not g:
            return ev

        self.kill_game(g)

        core = self.core
        core.events.game_left.emit(g)

        return ev

    def _game_ended(self, ev: wire.GameEnded) -> wire.GameEnded:
        g = self.games.get(ev.gid)
        if not g:
            return ev

        log.info('=======GAME ENDED=======')
        core = self.core
        core.events.game_ended.emit(g)

        return ev

    # ----- Public Methods -----
    def is_observe(self, g: ClientGame) -> bool:
        return g._[self]['observe']

    def create_game(self, gid: int, mode: str, name: str, users: List[wire.model.User], params: Dict[str, Any], items: Dict[int, List[str]]) -> ClientGame:
        from thb import modes
        g = modes[mode]()
        assert isinstance(g, ClientGame)

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

    def write(self, g: ClientGame, tag: str, data: object) -> None:
        core = self.core
        pkt = g._[self]['data'].feed_send(tag, data)
        gid = g._[self]['gid']
        core.server.write(wire.GameData(
            gid=gid,
            serial=pkt.serial,
            tag=pkt.tag,
            data=pkt.data,
        ))
        # core.events.game_data_send.emit((g, pkt))

    def build_players(self, g: ClientGame, uvl: Sequence[wire.model.User]) -> BatchList[Player]:
        core = self.core
        me_uid = core.auth.uid
        assert me_uid in [uv['uid'] for uv in uvl]

        me = Theone(g, me_uid)

        pl = BatchList[Player]([
            me if uv['uid'] == me_uid else Someone(g, uv['uid'])
            for uv in uvl
        ])
        pl[:0] = [Someone(g, 0) for i, npc in enumerate(g.npc_players)]

        return pl

    def start_game(self, g: ClientGame) -> None:
        core = self.core
        gr = gevent.spawn(g.run)
        g._[self]['greenlet'] = gr

        @gr.link_exception
        def crash(gr: Greenlet) -> None:
            core.events.game_crashed.emit(g)

        log.info('----- GAME STARTED: %d -----' % g._[self]['gid'])

    def kill_game(self, g: ClientGame) -> None:
        g._[self]['greenlet'].kill(ForcedKill)

    def gid_of(self, g: ClientGame) -> int:
        return g._[self]['gid']

    def name_of(self, g: ClientGame) -> str:
        return g._[self]['name']

    def gamedata_of(self, g: ClientGame) -> GameData:
        return g._[self]['data']

    def items_of(self, g: ClientGame) -> None:
        return g._[self]['items']

    def params_of(self, g: ClientGame) -> dict:
        return g._[self]['params']

    def users_of(self, g: ClientGame) -> List[wire.model.User]:
        return g._[self]['users']
