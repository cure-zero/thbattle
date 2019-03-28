# -*- coding: utf-8 -*-

# -- stdlib --
from typing import List, TYPE_CHECKING, Tuple
import logging

# -- third party --
import gevent

# -- own --
from endpoint import Endpoint
from server.base import Game
from server.endpoint import Client
from server.utils import command
from game.base import Packet
from utils.misc import BatchList, throttle
import wire

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Observe')


class Observe(object):
    def __init__(self, core: Core):
        self.core = core

        core.events.user_state_transition += self.handle_ust_observee
        core.events.game_created += self.handle_game_created
        core.events.game_joined += self.handle_game_joined
        core.events.game_data_recv += self.handle_game_data_recv

        _ = core.events.client_command
        _[wire.Observe] += self._observe
        _[wire.GrantObserve] += self._grant
        _[wire.LeaveRoom] += self._leave
        _[wire.KickObserver] += self._kick

        self._bigbrothers: List[int] = []

    def handle_ust_observee(self, ev: Tuple[Client, str, str]) -> Tuple[Client, str, str]:
        c, f, t = ev

        if (f, t) == ('ready', 'game'):
            for u in c._[self]['obs']:
                self._observe_start(u, c)

        elif (f, t) == ('game', 'lobby'):
            for u in c._[self]['obs']:
                self._observe_detach(u)

        if t == 'lobby':
            c._[self] = {
                'obs': BatchList(),  # observers
                'reqs': set(),       # observe requests
                'ob': None,          # observing
            }

        if f in ('room', 'ready', 'game') or \
           t in ('room', 'ready', 'game'):
            core = self.core
            # TODO: order with core.game?
            g = core.game.current(c)
            if g: self._notify(g)

        return ev

    def handle_game_created(self, g: Game) -> Game:
        g._[self] = {
            '_notifier': None
        }
        return g

    def handle_game_joined(self, ev: Tuple[Game, Client]) -> Tuple[Game, Client]:
        g, c = ev
        core = self.core
        for ob in c._[self]['obs']:
            ob.write(wire.GameJoined(core.view.GameDetail(g)))
            core.lobby.state_of(ob).transit('ob')

        return ev

    def handle_game_data_recv(self, ev: Tuple[Game, Client, Packet]) -> Tuple[Game, Client, Packet]:
        core = self.core
        g, u, pkt = ev
        gid = core.room.gid_of(g)

        d = Endpoint.encode(wire.GameData(
            gid=gid, serial=pkt.serial, tag=pkt.tag, data=pkt.data
        ))

        for u in u._[self]['obs']:
            u.raw_write(d)

        return ev

    # ----- Client Commands -----
    @command('lobby')
    def _observe(self, u: Client, ev: wire.Observe) -> None:
        core = self.core

        observee = core.lobby.get(ev.uid)
        if observee is None:
            return

        if core.lobby.state_of(observee) == 'ob':
            observee = observee._[self]['ob']
            assert observee

        if core.lobby.state_of(observee) not in ('game', 'room', 'ready'):
            return

        uid = core.auth.uid_of(u)

        if uid in self._bigbrothers:
            observee.write(wire.SystemMsg(
                '管理员对你使用了强制观战，效果拔群。'
                '强制观战功能仅用来处理纠纷，如果涉及滥用，请向 Proton 投诉。'
            ))
            self._observe_attach(u, observee)
            return

        if uid in observee._[self]['reqs']:
            # request already sent
            return

        observee._[self]['reqs'].add(uid)
        observee.write(wire.ObserveRequest(uid=uid))

    @command('room', 'ready', 'game')
    def _grant(self, c: Client, ev: wire.GrantObserve) -> None:
        if ev.uid not in c._[self]['reqs']:
            return

        core = self.core
        ob = core.lobby.get(ev.uid)

        if ob is None:
            return

        if core.lobby.state_of(ob) != 'lobby':
            return

        if ev.grant:
            self._observe_attach(ob, c)
        else:
            ob.write(wire.Error('observe_refused'))

    @command('room', 'ready', 'game')
    def _kick(self, c: Client, ev: wire.KickObserver) -> None:
        core = self.core
        ob = core.lobby.get(ev.uid)
        if not ob:
            return

        g = core.game.current(c)
        for u in core.room.online_users_of(g):
            if ob in u._[self]['obs']:
                break
        else:
            return

        assert core.lobby.state_of(u) == 'ob'

        self._observe_detach(u)
        return

        # TODO
        '''
        bl = self.ob_banlist[other]
        bl.add(c)

        s = Client.encode(['ob_kick_request', [user, other, len(bl)]])
        for cl in self.users:
            cl.raw_write(s)
            cl.observers and cl.observers.raw_write(s)

        return len(bl) >= len(self.users) // 2

        self.exit_game(other)
        '''

    @command('ob')
    def _leave(self, u: Client, ev: wire.LeaveRoom) -> None:
        self._observe_detach(u)

    # ----- Public Methods -----
    def add_bigbrother(self, uid: int) -> None:
        self._bigbrothers.append(uid)

    def remove_bigbrother(self, uid: int) -> None:
        try:
            self._bigbrothers.remove(uid)
        except Exception:
            pass

    # ----- Methods -----
    def _observe_start(self, ob: Client, observee: Client) -> None:
        core = self.core
        uid = core.auth.uid_of(observee)
        g = core.game.current(observee)
        assert g

        ob.write(wire.ObserveStarted(core.view.GameDetail(g), observee=uid))
        core.lobby.state_of(ob).transit('ob')

    def _observe_end(self, ob: Client, observee: Client) -> None:
        core = self.core
        g = core.game.current(observee)
        gid = core.room.gid_of(g)
        ob.write(wire.GameEnded(gid))
        core.lobby.state_of(ob).transit('ob')

    def _observe_attach(self, ob: Client, observee: Client) -> None:
        core = self.core

        g = core.game.current(observee)
        users = core.room.online_users_of(g)

        assert observee in users
        assert core.lobby.state_of(ob) == 'lobby'
        assert core.lobby.state_of(observee) in ('room', 'ready', 'game')

        log.info("observe attach")

        observee._[self]['obs'].add(ob)
        ob._[self]['ob'] = observee
        core.lobby.state_of(ob).transit('ob')

        ob.write(wire.GameJoined(core.view.GameDetail(g)))

        @gevent.spawn
        def notify_observer() -> None:
            d = Endpoint.encode(wire.ObserverEnter(
                observer=core.auth.uid_of(ob),
                observee=core.auth.uid_of(observee),
            ))

            for u in users:
                u.raw_write(d)
                u._[self]['obs'].raw_write(d)

        if core.room.is_started(g):
            self._observe_start(ob, observee)
            core.game.replay(observee, to=ob)

    def _observe_detach(self, ob: Client) -> None:
        core = self.core
        assert core.lobby.state_of(ob) == 'ob'

        observee = ob._[self]['ob']
        ob._[self]['ob'] = None
        observee._[self]['obs'].remove(ob)

        # TODO add these back
        # try:
        #     del self.ob_banlist[user]
        # except KeyError:
        #     pass

        core.lobby.state_of(ob).transit('lobby')
        g = core.game.current(observee)
        gid = core.room.gid_of(g)
        ob.write(wire.GameLeft(gid))

        @gevent.spawn
        def notify_observer_leave() -> None:
            g = core.game.current(observee)
            ul = core.room.online_users_of(g)

            d = Endpoint.encode(wire.ObserverLeave(
                observer=core.auth.uid_of(ob),
                observee=core.auth.uid_of(observee),
            ))

            for u in ul:
                u.raw_write(d)
                u._[self]['obs'].raw_write(d)

    def _notify(self, g: Game) -> None:
        notifier = g._[self]['_notifier']
        core = self.core

        if notifier:
            notifier()
            return

        @throttle(0.5)
        def _notifier() -> None:
            pl = core.room.users_of(g)
            obs: List[Client] = []
            for u in pl:
                obs.extend(u._[self]['obs'])

            gevent.spawn(core.room.send_room_users, g, obs)

        g._[self]['_notifier'] = _notifier

        _notifier()
