# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
from collections import defaultdict
from typing import TYPE_CHECKING, Tuple, Optional
import logging

# -- third party --
# -- own --
from server.base import Game
from server.endpoint import Client
from server.utils import command
from utils.events import EventHub
import wire

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Invite')


class Invite(object):
    def __init__(self, core: 'Core'):
        self.core = core

        core.events.game_created += self.handle_game_created
        core.events.game_left += self.handle_game_left
        core.events.game_successive_create += self.handle_game_successive_create

        D = core.events.client_command
        D[wire.Invite] += self._invite
        D[wire.Kick] += self._kick

        D[wire.JoinRoom].subscribe(self._room_join_invite_limit, -3)

    def handle_game_created(self, g: Game) -> Game:
        g._[self] = {
            'invited': set(),  # { uid1, uid2, ... }
            'banned': defaultdict(set),  # { banned_id: {uid1, ...}, ...}
        }
        return g

    def handle_game_successive_create(self, ev: Tuple[Game, Game]) -> Tuple[Game, Game]:
        old, g = ev
        g._[self] = old._[self]
        return ev

    def handle_game_left(self, ev: Tuple[Game, Client]) -> Tuple[Game, Client]:
        g, c = ev
        core = self.core

        for bl in g._[self]['banned'].values():
            bl.discard(core.auth.uid_of(c))

        return ev

    # ----- Commands -----
    @command()
    def _room_join_invite_limit(self, u: Client, ev: wire.JoinRoom) -> Optional[EventHub.StopPropagation]:
        core = self.core
        g = core.room.get(ev.gid)
        if not g:
            return None

        flags = core.room.flags_of(g)
        uid = core.auth.uid_of(u)

        banned = g._[self]['banned']
        invited = g._[self]['invited']

        # banned
        if len(banned[uid]) >= max(g.n_persons // 2, 1):
            u.write(wire.Error('banned'))
            return EventHub.STOP_PROPAGATION

        # invite
        if flags.get('invite') and uid not in invited:
            u.write(wire.Error('not_invited'))
            return EventHub.STOP_PROPAGATION

        return None

    @command('room', 'ready')
    def _invite(self, u: Client, ev: wire.Invite) -> None:
        core = self.core

        other = core.lobby.get(ev.uid)

        if not (other and core.lobby.state_of(other) in ('lobby', 'ob')):
            return

        g = core.game.current(u)
        g._[self]['invited'].add(other)

        other.write(wire.InviteRequest(
            uid=core.auth.uid_of(u),
            name=core.auth.name_of(u),
            gid=core.room.gid_of(g),
            type=g.__class__.__name__,
        ))

    @command('room', 'ready')
    def _kick(self, c: Client, ev: wire.Kick) -> None:
        core = self.core
        other = core.lobby.get(ev.uid)
        if not other:
            return

        g = core.game.current(c)
        g2 = core.game.current(other)
        if g is not g2:
            return

        if core.lobby.state_of(other) not in ('room', 'ready'):
            return

        bl = g._[self]['banned'][other]
        bl.add(c)

        for u in core.room.online_users_of(g):
            u.write(wire.KickRequest(
                uid=core.auth.uid_of(c),
                victim=core.auth.uid_of(other),
                votes=len(bl),
            ))

        if len(bl) >= len(core.room.users_of(g)) // 2:
            g._[self]['invited'].discard(other)
            core.room.exit_game(other)

    # ----- Methods -----
    def add_invited(self, g: Game, u: Client) -> None:
        g._[self]['invited'].add(u)
