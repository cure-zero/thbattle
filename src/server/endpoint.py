# -*- coding: utf-8 -*-

# -- stdlib --
from typing import TYPE_CHECKING, cast, Optional
import logging

# -- third party --
from gevent import getcurrent, Greenlet
import gevent

# -- own --
from endpoint import Endpoint, EndpointDied
from utils.misc import log_failure
from wire import msg as wiremsg

# -- typing --
if TYPE_CHECKING:
    from server.core import Core


# -- code --
log = logging.getLogger('server.core.endpoint')


class Pivot(Exception):
    pass


class Client(object):
    __slots__ = ('_ep', '_gr', '_core', '_')

    def __init__(self, core: Core, ep: Optional[Endpoint]):
        self._ep: Optional[Endpoint] = ep
        self._gr: Optional[Greenlet] = None
        self._core = core

        self._: dict = {}

    def _before_serve(self) -> None:
        core = self._core
        self._gr = getcurrent()
        core.events.client_connected.emit(self)

    @log_failure(log)
    def _serve(self) -> None:
        core = self._core
        tbl = core.events.client_command

        while True:
            if not self._ep:
                break

            try:
                for msg in self._ep.messages(timeout=90):
                    tbl[msg.op].emit(msg)

            except EndpointDied:
                break

            except Pivot:
                continue

            except Exception:
                log.exception("Error occurred when handling client command")

        core.events.client_dropped.emit(self)

    def serve(self) -> None:
        self._before_serve()
        self._serve()

    def close(self) -> None:
        self._ep and self._ep.close()
        self._ep = None
        self._gr and self._gr.kill(EndpointDied)
        self._gr = None

    def is_dead(self) -> bool:
        return not self._gr or self._gr.ready()

    def pivot_to(self, other) -> None:
        if not self._ep:
            raise Exception("self._ep is not valid!")

        other._ep = self._ep
        self._ep = None
        self._gr.kill()  # this skips client_dropped event

        if other._ep:
            other._gr.kill(Pivot)
        else:
            other._gr = gevent.spawn(other._serve)

    def __repr__(self):
        return '%s:%s:%s' % (
            self.__class__.__name__,
            'FIXME', 'FIXME'
        )

    def get_greenlet(self) -> Optional[Greenlet]:
        return self._gr

    def write(self, v: wiremsg.ServerToClient) -> None:
        ep = self._ep
        data = cast(wiremsg.Message, v).encode()
        if ep: ep.write(data)

    def raw_write(self, v: bytes) -> None:
        ep = self._ep
        if ep: ep.raw_write(v)
