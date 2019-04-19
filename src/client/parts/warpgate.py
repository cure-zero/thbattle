# -*- coding: utf-8 -*-

# -- stdlib --
import typing
from typing import TYPE_CHECKING, Any, Callable, Tuple, List
from typing_extensions import Literal
import logging
from mypy_extensions import TypedDict
import utils.log

import random
import sys

# -- third party --
from gevent.event import Event
import gevent
import gevent.hub

# -- own --
from game.base import EventHandler
from client.base import Game
import settings

# -- typing --
if TYPE_CHECKING:
    from client.core import Core  # noqa: F401


# -- code --
class GameEvent(TypedDict):
    t: Literal['g']
    g: Game
    evt: str
    arg: Any


class InputEvent(TypedDict):
    t: Literal['i']
    g: Game
    arg: Any
    done: Callable


class SystemEvent(TypedDict):
    t: Literal['s']
    evt: str
    arg: Tuple


class UnityUIEventHook(EventHandler):
    game: Game

    def __init__(self, g: Game):
        EventHandler.__init__(self, g)
        self.game = g
        self.live = False

    def evt_user_input(self, arg: Any) -> None:
        evt = Event()
        g = self.game
        core = g.core
        core.warpgate.feed_ev({'t': 'i', 'g': g, 'arg': arg, 'done': evt.set})
        evt.wait()

    def handle(self, evt: str, arg: Any) -> Any:
        if not self.live and evt not in ('game_begin', 'switch_character', 'reseat'):
            return arg

        g = self.game
        core = g.core

        if evt == 'user_input':
            self.evt_user_input(arg)
        else:
            core.warpgate.feed_ev({'t': 'g', 'g': g, 'evt': evt, 'arg': arg})

        if random.random() < 0.01:
            gevent.sleep(0.005)

        return arg

    def set_live(self) -> None:
        self.live = True
        core = self.game.core
        core.warpgate.feed_ev({'t': 'g', 'g': self.game, 'evt': 'game_live', 'arg': None})


sys.argv = []



class ExecutiveWrapper(object):
    def connect_server(self, host, port):
        from UnityEngine import Debug
        Debug.Log(repr((host, port)))

        @gevent.spawn
        def do():
            Q = self.warpgate.queue_system_event
            Q('connect', self.executive.connect_server((host, port), Q))

    def start_replay(self, rep):
        self.executive.start_replay(rep, self.warpgate.queue_system_event)

    def ignite(self, g):
        g.event_observer = UnityUIEventHook(self.warpgate, g)

        @gevent.spawn
        def start():
            gevent.sleep(0.3)
            svr = g.me.server
            if svr.gamedata_piled():
                g.start()
                svr.wait_till_live()
                gevent.sleep(0.1)
                svr.wait_till_live()
                g.event_observer.set_live()
            else:
                g.event_observer.set_live()
                g.start()


class Warpgate(object):
    def __init__(self, core: 'Core'):
        self.core = core
        self.events: List[Any] = []
        core.events.core_initialized += self.init_warpgate

    def init_warpgate(self, core: 'Core') -> 'Core':
        from UnityEngine import Debug

        Debug.Log("core.warpgate: Initializing logging")
        utils.log.init_unity(logging.ERROR, settings.SENTRY_DSN, settings.VERSION)
        utils.log.patch_gevent_hub_print_exception()

        Debug.Log("core.warpgate: Before gevent")
        from gevent import monkey
        monkey.patch_socket()
        monkey.patch_os()
        monkey.patch_select()
        Debug.Log("core.warpgate: After gevent")

        from game import autoenv
        autoenv.init('Client')

        return core

    @typing.overload
    def feed_ev(self, ev: GameEvent) -> None: ...

    @typing.overload
    def feed_ev(self, ev: InputEvent) -> None: ...

    @typing.overload
    def feed_ev(self, ev: SystemEvent) -> None: ...

    def feed_ev(self, ev: Any) -> None:
        self.events.append(ev)

    def get_events(self) -> List[Any]:
        l = self.events
        self.events = []
        return l
