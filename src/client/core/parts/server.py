# -*- coding: utf-8 -*-


# -- stdlib --
from urllib.parse import urlparse
import logging
import socket

# -- third party --
import gevent

# -- own --
from endpoint import Endpoint
from utils.events import EventHub


# -- code --
log = logging.getLogger('client.core.parts.Server')
STOP = EventHub.STOP_PROPAGATION


class Server(object):
    def __init__(self, core):
        self.core = core
        core.events.server_command += self.handle_server_command

        self.server_name = 'Unknown'

        self.state = 'initial'
        self._ep = None
        self._recv_gr = None
        self._beater_gr = None

    def handle_server_command(self, ev):
        cmd, arg = ev

        if cmd == 'thbattle_greeting':
            from settings import VERSION

            core = self.core
            try:
                name, ver = arg
            except ValueError:
                name, ver = 'UNKNOWN', 'UNKNOWN'

            if ver != VERSION:
                self.disconnect()
                core.events.version_mismatch.emit(None)
            else:
                self.server_name = name
                core.events.server_connected.emit(None)

            return STOP

        elif cmd == 'ping':
            self._ep.write(['pong', ()])
            return STOP

        return ev

    # ----- Public Methods -----
    def connect(self, uri):
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

    def disconnect(self):
        if self.state != 'connected':
            return

        self.state = 'dying'
        ep = self._ep
        self._ep = None
        ep.close()
        self._recv_gr and self._recv_gr.kill()
        self._beater_gr and self._beater_gr.kill()
        self.state = 'initial'

    # ----- Methods -----
    def _recv(self):
        me = gevent.getcurrent()
        me.link_exception(self._dropped)
        core = self.core
        ev = core.events.server_command
        while True:
            v = self._ep.read()
            ev.emit(v)

    def _dropped(self):
        core = self.core
        core.events.server_dropped.emit(None)

    def _beat(self):
        while self._ep:
            self._ep.write(['heartbeat', ()])
            gevent.sleep(10)
