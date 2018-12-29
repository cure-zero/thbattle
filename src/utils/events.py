# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
import sys
import zlib
import logging

# -- third party --
# -- own --


# -- code --
log = logging.getLogger('utils.events')


class EventHub(object):
    __slots__ = ('_subscribers', '_contract')
    STOP_PROPAGATION = object()

    def __init__(self, contract):
        self._subscribers = []
        self._contract = contract

    def subscribe(self, cb, prio):
        self._subscribers.append((prio, cb))
        self._subscribers.sort()
        return self

    def __iadd__(self, cb):
        # deterministic priority
        f = sys._getframe(1)
        s = '{}:{}'.format(f.f_code.co_filename, f.f_lineno)
        prio = zlib.crc32(s) * 1.0 / 0x100000000
        self.subscribe(cb, prio)
        return self

    def emit(self, ev):
        if not self._subscribers:
            log.warning('Emit event when no subscribers present!')
            return

        for prio, cb in self._subscribers:
            ev = cb(ev)
            if ev is self.STOP_PROPAGATION:
                return None
            elif ev is None:
                raise Exception("Returning None in EventHub!")

        return ev


class FSM(object):
    __slots__ = ('_context', '_valid', '_state', '_callback')

    def __init__(self, context, valid, initial, callback):
        if initial not in valid:
            raise Exception('State not in valid choices!')

        self._context  = context
        self._valid    = valid
        self._state    = initial
        self._callback = callback

    def transit(self, state):
        if state not in self._valid:
            raise Exception('Invalid state transition!')

        if state == self._state:
            return

        old, self._state = self._state, state
        self._callback(self._context, old, state)

    def __eq__(self, other):
        return self._state == other

    @staticmethod
    def to_evhub(evhub):
        return lambda ctx, f, t: evhub.emit((ctx, f, t))
