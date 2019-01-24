# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
import logging

# -- third party --
import gevent

# -- own --
from server.utils import command
from utils import BatchList
from utils.events import EventHub


# -- code --
log = logging.getLogger('Match')


class Match(object):
    def __init__(self, core):
        self.core = core

        core.events.user_state_transition += self.handle_user_state_transition
        core.events.game_started += self.handle_game_started
        core.events.game_killed += self.handle_game_killed
        core.events.game_ended += self.handle_game_ended
        core.events.game_successive_create += self.handle_game_successive_create

        _ = core.events.client_command
        _['match:setup'] += self._match
        _['room:join'].subscribe(self._room_join_match_limit, -3)

    def handle_user_state_transition(self, ev):
        c, f, t = ev
        return ev

    def handle_game_started(self, g):
        core = self.core
        flags = core.game.flags_of(g)

        if flags.get('match'):
            core.interconnect.speaker(
                '文文', '“%s”开始了！参与玩家：%s' % (
                    self.game_name,
                    '，'.join(self.users.account.username)
                )
            )

        return g

    def handle_game_killed(self, g):
        core = self.core
        if g.greenlet and core.game.flags_of(g).get('match'):
            core.interconnect.speaker(
                '文文', '“%s”意外终止了，比赛结果作废！' % core.room.name_of(g)
            )

        return g

    def handle_game_ended(self, g):
        core = self.core
        if core.game.flags_of(g).get('match'):
            if not g.suicide:
                core.interconnect.speaker(
                    '文文',
                    '“%s”结束了！获胜玩家：%s' % (
                        self.game_name,
                        '，'.join(BatchList(self.game.winners).account.username)
                    )
                )

    def handle_game_successive_create(self, ev):
        old, g = ev
        fields = old._[self]
        g._[self] = fields
        self._start_poll(g, fields['match_uids'])
        return ev

    # ----- Client Commands -----
    @command(None, [str, str, [int]])
    def _match(self, c, name, typ, uids):
        core = self.core
        from thb import modes
        gamecls = modes[typ]
        if len(uids) != gamecls.n_persons:
            c.write(['system_msg', [None, '参赛人数不正确']])
            return

        g = core.room.create_game(gamecls, name, {'match': True})

        g._[self] = {
            'match_uids': uids,
        }
        self._start_poll(g, uids)

    @command(None, [int, int])
    def _room_join_match_limit(self, u, gid, slot):
        core = self.core
        g = core.room.get_game_by_id(gid)
        if not g:
            return

        flags = core.game.flags_of(g)
        uid = core.auth.uid_of(u)

        if flags.get('match'):
            uid = core.auth.uid_of(u)
            if uid not in self.match_users:
                u.write(['error', 'not_invited'])
                return EventHub.STOP_PROPAGATION

    # ----- Methods -----
    def _start_poll(self, g, uids):
        core = self.core
        gid = core.room.gid_of(g)

        gevent.spawn(lambda: [
            gevent.sleep(1),
            core.interconnect.speaker('文文', '“%s”房间已经建立，请相关玩家就位！' % self.game_name),
        ])

        @gevent.spawn
        def pull():
            while core.room.get_by_gid(gid) is g:
                users = core.room.online_users_of(g)
                uids = {core.auth.uid_of(u) for u in users}
                match_uids = set(g._[self]['match_uids'])

                for uid in match_uids - uids:
                    u = core.lobby.get_by_uid(uid)
                    if not u:
                        continue

                    if core.lobby.state_of(u) == 'lobby':
                        core.room.join_game(g, u, None)
                    elif core.lobby.state_of(u) in ('ob', 'ready', 'room'):
                        core.room.exit_game(u)
                        gevent.sleep(1)
                        core.room.join_game(g, u, None)
                    elif core.lobby.state_of(u) == 'game':
                        gevent.spawn(u.write, ['system_msg', [None, '你有比赛房间，请尽快结束游戏参与比赛']])

                    gevent.sleep(0.1)

                gevent.sleep(30)
