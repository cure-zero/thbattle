# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
import logging

# -- third party --
import gevent

# -- own --
from endpoint import Endpoint
from server.utils import command
from utils.events import FSM
from utils.misc import throttle, BatchList


# -- code --
log = logging.getLogger('Lobby')


class Lobby(object):
    def __init__(self, core):
        self.core = core

        core.events.client_connected += self.handle_client_connected
        core.events.user_state_transition += self.handle_user_state_transition
        core.events.game_ended += self.handle_game_ended

        self.users = {}          # all users
        self.dropped_users = {}  # passively dropped users

    def handle_user_state_transition(self, ev):
        c, f, t = ev

        if (f, t) == ('connected', 'authed'):
            self._user_join(c)

        if t == 'dropped':
            if f != 'connected':
                self._user_leave(c)

        ul = [u for u in self.users.values() if u._[self]['state'] == 'lobby']
        self._notify_online_users(ul)

        return ev

    def handle_client_connected(self, c):
        core = self.core
        c._[self] = {
            'state': FSM(
                c,
                [
                    'initial',
                    'connected',
                    'authed',
                    'lobby',
                    'room',
                    'ready',
                    'game',
                    'ob',
                    'dropped',
                ],
                'initial',
                FSM.to_evhub(core.events.user_state_transition),
            )
        }
        c._[self]['state'].transit('connected')
        return c

    def handle_game_ended(self, g):
        core = self.core
        users = core.room.users_of(g)

        for u in users:
            self.dropped_users.pop(core.auth.uid_of(u), 0)

        return g

    # ----- Client Commands -----
    # ----- Public Methods -----
    def state_of(self, c):
        return c._[self]['state']

    def all_users(self):
        return BatchList(self.users.itervalues())


    # ----- Methods -----
    def _user_join(self, u):
        core = self.core
        uid = core.auth.uid_of(u)
        name = core.auth.name_of(u)

        old = None

        if uid in self.users:
            # squeeze the original one out
            log.info('%s[%s] has been squeezed out' % (name, uid))
            old = self.users[uid]

        if uid in self.dropped_users:
            log.info(u'%s[%s] rejoining dropped game' % (name, uid))
            old = self.dropped_users.pop(uid)

            # XXX
            '''
            @gevent.spawn
            def reconnect():
                self.send_account_info(user)
            '''

        if old:
            u.pivot_to(old)
            core.events.client_pivot.emit(old)
        else:
            self.users[uid] = u
            self.state_of(u).transit('lobby')

        log.info(u'User %s joined, online user %d' % (name, len(self.users)))

    def _user_leave(self, u):
        core = self.core
        uid = core.auth.uid_of(u)
        name = core.auth.name_of(u)
        self.users.pop(uid, 0)
        log.info(u'User %s left, online user %d' % (name, len(self.users)))

    @throttle(3)
    def _notify_online_users(self, ul):
        core = self.core

        lst = [core.view.User(u) for u in self.users.values()]

        d = Endpoint.encode([
            ['current_users', lst],
        ], Endpoint.FMT_BULK_COMPRESSED)

        @gevent.spawn
        def do_send():
            for u in ul:
                u.write(d)
