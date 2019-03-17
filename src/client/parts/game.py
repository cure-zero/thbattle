# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Dict, List, Sequence
import logging

# -- third party --
import gevent

# -- own --
from client.base import ForcedKill, Game as ClientGame, Someone, Theone
from client.core import Core
from game.base import Player, GameData
from utils.events import EventHub
from utils.misc import BatchList


# -- code --
log = logging.getLogger('client.parts.Game')
STOP = EventHub.STOP_PROPAGATION


class Game(object):
    def __init__(self, core: Core):
        self.core = core
        core.events.server_command += self.handle_server_command

        self.games: Dict[int, ClientGame] = {}

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

    def _room_users(self, args):
        core = self.core
        gid, pl = args

        g = self.games.get(gid)
        if not g:
            return

        g._[self]['users'] = pl
        core.events.room_users.emit((g, pl))

    def _game_started(self, gv: dict):
        core = self.core
        core.events.game_started.emit(g)

    def _observe_started(self, gv: dict):
        g = self.games[gv['gid']]
        g._[self]['observe'] = True
        return self._game_started(gv)

    def handle_game_joined(self, gv: dict):
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

    def handle_game_left(self, gid: int):
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
    def is_observe(self, g: ClientGame) -> bool:
        return g._[self]['observe']

    def create_game(self, gid: int, mode: str, name: str, users: List[dict], params: dict, items: dict) -> ClientGame:
        from thb import modes
        g: ClientGame = modes[mode]()  # type: ignore

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

    def build_players(self, g: ClientGame, uvl: Sequence[dict]) -> BatchList[Player]:
        core = self.core

        me_uid = core.auth.uid

        assert me_uid in [uv['id'] for uv in uvl]

        me = Theone(g, me_uid, core.auth.name)

        pl: BatchList[Player] = BatchList([
            me if uv['uid'] == me_uid else Someone(g, uv['uid'], uv['name'])
            for uv in uvl
        ])

        pl[:0] = [Someone(g, i.name, i.input_handler) for i in g.npc_players]

        return pl

    def start_game(self, g: ClientGame) -> None:
        core = self.core
        gr = gevent.spawn(g.run)
        g._[self]['greenlet'] = gr

        @gr.link_exception
        def crash(gr):
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
