# -*- coding: utf-8 -*-

# -- stdlib --
from typing import TYPE_CHECKING, Optional
import logging

# -- third party --
# -- own --
from server.endpoint import Client
from server.utils import command
from utils.events import EventHub
from wire import msg as wiremsg

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('server.parts.kedama')


class Kedama(object):
    def __init__(self, core: 'Core'):
        self.core = core
        D = core.events.client_command
        D[wiremsg.CreateRoom].subscribe(self._room_create_limit, -5)
        D[wiremsg.JoinRoom].subscribe(self._room_join_limit, -5)
        D[wiremsg.Invite].subscribe(self._invite_limit, -5)

    # ----- Commands -----
    @command()
    def _room_create_limit(self, u: Client, ev: wiremsg.CreateRoom) -> Optional[EventHub.StopPropagation]:
        core = self.core
        from thb import modes_kedama
        if core.auth.is_kedama(u) and ev.mode not in modes_kedama:
            u.write(wiremsg.Error('kedama_limitation'))
            return EventHub.STOP_PROPAGATION

        return None

    @command()
    def _room_join_limit(self, u: Client, ev: wiremsg.JoinRoom) -> Optional[EventHub.StopPropagation]:
        core = self.core
        g = core.room.get(ev.gid)
        if not g:
            return None

        from thb import modes_kedama
        if core.auth.is_kedama(u) and g.__class__.__name__ not in modes_kedama:
            u.write(wiremsg.Error('kedama_limitation'))
            return EventHub.STOP_PROPAGATION

        return None

    @command()
    def _invite_limit(self, c: Client, ev: wiremsg.Invite) -> Optional[EventHub.StopPropagation]:
        core = self.core
        uid = core.auth.uid_of(c)
        if uid <= 0:
            c.write(wiremsg.Error('kedama_limitation'))
            return EventHub.STOP_PROPAGATION

        return None
