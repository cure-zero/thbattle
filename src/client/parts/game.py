# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Any, Dict, List, Sequence, Union
import logging

# -- third party --
import gevent

# -- own --
from client.base import ForcedKill, Game as ClientGame, Someone, Theone
from client.core import Core
from game.base import GameData, Player
from utils.events import EventHub
from utils.misc import BatchList
from wire import model as wiremodel, msg as wiremsg


# -- code --
log = logging.getLogger('client.parts.Game')
STOP = EventHub.STOP_PROPAGATION


class Game(object):
    def __init__(self, core: Core):
        self.core = core
        core.events.server_command += self.handle_server_command
        self.games: Dict[int, ClientGame] = {}

    def handle_server_command(self, ev: wiremsg.Message) -> Union[wiremsg.Message, EventHub.StopPropagation]:
        if isinstance(ev, wiremsg.RoomUsers):
            self._room_users(ev)
            return STOP
        elif isinstance(ev, wiremsg.GameStarted):
            self._game_started(ev)
            return STOP
        elif isinstance(ev, wiremsg.GameJoined):
            self._game_joined(ev)
            return STOP
        elif isinstance(ev, wiremsg.ObserveStarted):
            self._observe_started(ev)
            return STOP
        elif isinstance(ev, wiremsg.GameLeft):
            self._game_left(ev)
            return STOP
        elif isinstance(ev, wiremsg.GameEnded):
            self._game_ended(ev)
            return STOP

        return ev

    def _room_users(self, ev: wiremsg.RoomUsers) -> None:
        core = self.core

        g = self.games.get(ev.gid)
        if not g:
            return

        g._[self]['users'] = ev.users
        core.events.room_users.emit((g, ev.users))

    def _game_started(self, ev: wiremsg.GameStarted):
        core = self.core
        gv = ev.game
        g = self.games[gv['gid']]
        core.events.game_started.emit(g)

    def _observe_started(self, ev: wiremsg.ObserveStarted):
        gv = ev.game
        g = self.games[gv['gid']]
        g._[self]['observe'] = True
        core = self.core
        core.events.game_started.emit(g)

    def _game_joined(self, ev: wiremsg.GameJoined):
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

    def _game_left(self, ev: wiremsg.GameLeft):
        g = self.games.get(ev.gid)
        if not g:
            return

        self.kill_game(g)

        core = self.core
        core.events.game_left.emit(g)

    def _game_ended(self, ev: wiremsg.GameEnded):
        g = self.games.get(ev.gid)
        if not g:
            return

        log.info('=======GAME ENDED=======')
        core = self.core
        core.events.game_ended.emit(g)

    # ----- Public Methods -----
    def is_observe(self, g: ClientGame) -> bool:
        return g._[self]['observe']

    def create_game(self, gid: int, mode: str, name: str, users: List[wiremodel.User], params: Dict[str, Any], items: Dict[int, List[str]]) -> ClientGame:
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
        core.server.write(wiremsg.GameData(
            gid=gid,
            serial=pkt.serial,
            tag=pkt.tag,
            data=pkt.data,
        ))
        # core.events.game_data_send.emit((g, pkt))

    def build_players(self, g: ClientGame, uvl: Sequence[wiremodel.User]) -> BatchList[Player]:
        core = self.core
        me_uid = core.auth.uid
        assert me_uid in [uv['uid'] for uv in uvl]

        me = Theone(g, me_uid, core.auth.name)

        pl = BatchList[Player]([
            me if uv['uid'] == me_uid else Someone(g, uv['uid'], uv['name'])
            for uv in uvl
        ])
        pl[:0] = [Someone(g, -i, npc.name) for i, npc in enumerate(g.npc_players)]

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

    def users_of(self, g: ClientGame) -> List[wiremodel.User]:
        return g._[self]['users']
