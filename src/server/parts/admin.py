# -*- coding: utf-8 -*-

# -- stdlib --
import logging

# -- third party --
import gevent

# -- own --
from server.endpoint import Client
from server.utils import command


# -- code --
log = logging.getLogger('Admin')


class Admin(object):
    def __init__(self, core):
        self.core = core

        _ = core.events.client_command
        _['admin:stacktrace']        += self._stacktrace
        _['admin:clearzombies']      += self._clearzombies
        _['admin:migrate']           += self._migrate
        _['admin:kick']              += self._kick
        _['admin:kill-game']         += self._kill_game
        _['admin:add']               += self._add
        _['admin:remove']            += self._remove
        _['admin:add-bigbrother']    += self._add_bigbrother
        _['admin:remove-bigbrother'] += self._remove_bigbrother

        self.admins = [2, 109, 351, 3044, 6573, 6584, 9783]

    def _need_admin(f):
        def wrapper(self, ev):
            core = self.core
            c, args = ev
            if core.auth.uid_of(c) not in self.admins:
                return ev

            f(self, ev)
            c.write(['system_msg', [None, '成功的执行了管理命令']])
            return ev

        return wrapper

    @_need_admin
    @command()
    def _kick(self, c: Client, uid: int):
        core = self.core
        u = core.lobby.get_by_uid(uid)
        u and u.close()

    @_need_admin
    @command()
    def _clearzombies(self, c: Client):
        core = self.core
        users = core.lobby.all_users()
        for u in users:
            if u.ready():
                log.info('Clear zombie: %r', u)
                core.events.client_dropped.emit(u)

    @_need_admin
    @command()
    def _migrate(self, c: Client):
        core = self.core

        @gevent.spawn
        def sysmsg():
            while True:
                users = core.lobby.all_users()
                users.write(['system_msg', [None, '游戏已经更新，当前的游戏结束后将会被自动踢出，请更新后重新游戏']])
                gevent.sleep(30)

        @gevent.spawn
        def kick():
            gevent.sleep(30)
            while True:
                users = core.lobby.all_users()
                for u in users:
                    if core.lobby.state_of(u) in ('lobby', 'room', 'ready', 'connected'):
                        u.close()

                gevent.sleep(1)

    @_need_admin
    @command()
    def _stacktrace(self, c: Client):
        core = self.core
        g = core.game.current(c)
        if not g:
            return

        log.info('>>>>> GAME STACKTRACE <<<<<')

        def logtraceback(gr):
            import traceback
            log.info('----- %r -----\n%s', gr, ''.join(traceback.format_stack(gr.gr_frame)))

        logtraceback(g)

        for u in core.room.online_users_of(g):
            u.gr_frame and logtraceback(u)

        log.info('===========================')

    @_need_admin
    @command()
    def _kill_game(self, c: Client, gid: int):
        core = self.core
        g = core.room.get_game(gid)
        if not g: return

        users = core.room.online_users_of(g)
        for u in users:
            core.room.exit_game(u, is_drop=True)

    @_need_admin
    @command()
    def _add(self, c: Client, uid: int):
        self.admins.append(uid)

    @_need_admin
    @command()
    def _remove(self, c: Client, uid: int):
        try:
            self.admins.remove(uid)
        except Exception:
            pass

    @_need_admin
    @command()
    def _add_bigbrother(self, c: Client, uid: int):
        core = self.core
        core.observe.add_bigbrother(uid)

    @_need_admin
    @command()
    def _remove_bigbrother(self, c: Client, uid: int):
        core = self.core
        core.observe.remove_bigbrother(uid)
