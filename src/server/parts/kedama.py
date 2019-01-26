# -*- coding: utf-8 -*-


# -- stdlib --
import logging

# -- third party --
# -- own --
from server.utils import command
from utils.events import EventHub


# -- code --
log = logging.getLogger('server.parts.kedama')


class Kedama(object):
    def __init__(self, core):
        self.core = core
        _ = core.events.client_command
        _['room:create'].subscribe(self._room_create_limit, -5)
        _['room:join'].subscribe(self._room_join_limit, -5)

    # ----- Commands -----
    @command(None, [str, str, dict])
    def _room_create_limit(self, c, gametype, name, flags):
        core = self.core
        from thb import modes_kedama
        if core.auth.is_kedama(c) and gametype not in modes_kedama:
            c.write(['error', 'kedama_limitation'])
            return EventHub.STOP_PROPAGATION

    @command(None, [int, int])
    def _room_join_limit(self, c, gid, slot):
        core = self.core
        g = core.room.get_game_by_id(gid)
        if not g:
            return

        from thb import modes_kedama
        if core.auth.is_kedama(c) and g.__class__.__name__ not in modes_kedama:
            c.write(['error', 'kedama_limitation'])
            return EventHub.STOP_PROPAGATION

    @command(None, [int])
    def _invite(self, c, uid):
        core = self.core
        uid = core.auth.uid_of(c)
        if uid <= 0:
            c.write(['error', 'kedama_limitation'])
            return EventHub.STOP_PROPAGATION
