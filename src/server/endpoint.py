# -*- coding: utf-8 -*-


# -- stdlib --
import logging

# -- third party --
from gevent import Timeout, getcurrent
import gevent

# -- own --
from endpoint import EndpointDied
from utils.misc import log_failure


# -- code --
log = logging.getLogger('server.core.endpoint')


class Pivot(Exception):
    pass


class Client(object):
    __slots__ = ('_ep', '_gr', '_core', '_')

    def __init__(self, core, ep):
        self._ep = ep
        self._core = core

        self._ = {}

    def _before_serve(self):
        core = self._core
        self._gr = getcurrent()
        core.events.client_connected.emit(self)

    @log_failure(log)
    def _serve(self):
        core = self._core

        while True:
            try:
                hasdata = False
                with Timeout(90, False):
                    cmd, args = self._ep.read()
                    hasdata = True

                if not hasdata:
                    # client should send heartbeat periodically
                    self.close()
                    break

                if cmd == 'heartbeat':
                    continue

                if not isinstance(cmd, str):
                    continue

                tbl = core.events.client_command
                if cmd not in tbl:
                    continue
                tbl[cmd].emit((self, args))

            except EndpointDied:
                break

            except Pivot:
                continue

            except Exception:
                log.exception("Error occurred when handling client command")

        core.events.client_dropped.emit(self)

    def serve(self):
        self._before_serve()
        self._serve()

    def close(self):
        self._ep and self._ep.close()
        self._ep = None
        self._gr and self._gr.kill(EndpointDied)
        self._gr = None

    def pivot_to(self, other):
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

    def write(self, d):
        ep = self._ep
        ep and ep.write(d)

    def raw_write(self, d):
        ep = self._ep
        ep and ep.raw_write(d)
