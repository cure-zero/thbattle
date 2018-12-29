# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
from collections import defaultdict
import logging

# -- third party --
import gevent

# -- own --
from server.utils import command
from utils.events import EventHub


# -- code --
log = logging.getLogger('Invite')


class Invite(object):
    def __init__(self, core):
        self.core = core

        core.events.game_created += self.handle_game_created
        core.events.game_left += self.handle_game_left
        core.events.game_successive_create += self.handle_game_successive_create

        _ = core.events.client_command
        _['invite:invite'] += self._invite
        _['invite:kick'] += self._kick

        _['room:join'].subscribe(self._room_join_invite_limit, -3)

    def handle_game_created(self, g):
        g._[self] = {
            'invited': set(),  # { uid1, uid2, ... }
            'banned': defaultdict(set),  # { banned_id: {uid1, ...}, ...}
        }
        return g

    def handle_game_successive_create(self, ev):
        old, g = ev
        g._[self] = old._[self]
        return ev

    @command(None, [int, int])
    def _room_join_invite_limit(self, u, gid, slot):
        core = self.core
        g = core.room.get_game_by_id(gid)
        if not g:
            return

        flags = core.game.flags_of(g)
        uid = core.auth.uid_of(u)

        banned = g._[self]['banned']
        invited = g._[self]['invited']

        # banned
        if len(banned[uid]) >= max(g.n_persons // 2, 1):
            u.write(['error', 'banned'])
            return EventHub.STOP_PROPAGATION

        # invite
        if flags.get('invite') and uid not in invited:
            u.write(['error', 'not_invited'])
            return EventHub.STOP_PROPAGATION

    def handle_game_left(self, ev):
        g, c = ev
        core = self.core

        for bl in g._[self]['banned'].values():
            bl.discard(core.auth.uid_of(c))

        return ev

    # ----- Commands -----
    @command(['room', 'ready'], [int])
    def _invite(self, u, uid):
        core = self.core

        other = core.lobby.get_by_uid(uid)

        if not (other and core.lobby.state_of(other) in ('lobby', 'ob')):
            return

        g = core.game.current(u)
        g._[self]['invited'].add(other)

        other.write(['invite_request', [
            core.auth.uid_of(u),
            core.auth.name_of(u),
            core.room.gid_of(g),
            g.__class__.__name__,
        ]])

    @command(['room', 'ready'], [int])
    def _kick(self, c, uid):
        core = self.core
        other = core.lobby.user_from_uid(uid)
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
            u.write(['kick_request', [c, other, len(bl)]])

        if len(bl) >= len(self.users) // 2:
            g._[self]['invited'].discard(other)
            core.room.exit_game(other)

    # ----- Methods -----
    def add_invited(self, g, u):
        g._[self]['invited'].add(u)
