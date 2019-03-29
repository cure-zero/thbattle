# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Any, TYPE_CHECKING, Optional, cast
from urllib.parse import urlparse
import logging
import socket

# -- third party --
import gevent
from gevent import Greenlet

# -- own --
from endpoint import Endpoint
from utils.events import EventHub
import wire

# -- typing --
if TYPE_CHECKING:
    from client.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('client.core.parts.Server')
STOP = EventHub.STOP_PROPAGATION


class Server(object):
    def __init__(self, core: 'Core'):
        self.core = core
        core.events.server_command += self.handle_server_command

        self.server_name = 'Unknown'

        self.state = 'initial'

        self._ep: Optional[Endpoint] = None
        self._recv_gr: Optional[Greenlet] = None
        self._beater_gr: Optional[Greenlet] = None

    def handle_server_command(self, ev: wire.Message) -> Any:
        greet = wire.cast(wire.Greeting, ev)
        if greet:
            from settings import VERSION

            core = self.core

            if greet.version != VERSION:
                self.disconnect()
                core.events.version_mismatch.emit(None)
            else:
                self.server_name = greet.node
                core.events.server_connected.emit(None)

            return STOP

        ping = wire.cast(wire.Ping, ev)
        if ping:
            self.write(wire.Pong())
            return STOP

        return ev

    # ----- Public Methods -----
    def connect(self, uri: str) -> None:
        core = self.core

        uri = urlparse(uri)
        assert uri.scheme == 'tcp'

        if not self.state == 'initial':
            return

        try:
            self.state = 'connecting'
            addr = uri.hostname, uri.port
            s = socket.create_connection(addr)
            self._ep = Endpoint(s, addr)
            self._recv_gr = gevent.spawn(self._recv)
            self._beater_gr = gevent.spawn(self._beat)
            self.state = 'connected'
        except Exception:
            self.state = 'initial'
            log.exception('Error connecting server')
            core.events.server_refused.emit(None)

    def disconnect(self) -> None:
        if self.state != 'connected':
            return

        self.state = 'dying'
        ep, recv, beater = self._ep, self._recv_gr, self._beater_gr
        self._ep = None
        self._recv_gr = None
        self._beater_gr = None
        ep and ep.close()
        recv and recv.kill()
        beater and beater.kill()
        self.state = 'initial'

    def write(self, v: wire.ClientToServer) -> None:
        ep = self._ep
        ep and ep.write(cast(wire.Message, v).encode())

    def raw_write(self, v: bytes) -> None:
        ep = self._ep
        ep and ep.raw_write(v)

    # ----- Methods -----
    def _recv(self) -> None:
        me = gevent.getcurrent()
        me.link_exception(self._dropped)
        core = self.core
        ev = core.events.server_command
        while self._ep:
            v = self._ep.read()
            ev.emit(v)

    def _dropped(self) -> None:
        core = self.core
        core.events.server_dropped.emit(None)

    def _beat(self) -> None:
        while self._ep:
            self._ep.write(['heartbeat', ()])
            gevent.sleep(10)
