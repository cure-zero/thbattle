# -*- coding: utf-8 -*-

# -- stdlib --
from collections import deque
from typing import Callable, Dict
import logging
import random
import re

# -- third party --
from gevent.event import Event
from gevent.queue import Queue
import gevent

# -- own --
from endpoint import Endpoint, EndpointDied
from server.base import Player
from server.core import Core
from server.endpoint import Client
from utils import hook


# -- code --
log = logging.getLogger('mock')


class MockEndpoint(object):

    def __init__(self):
        self.send = []
        self.recv = Queue(100)

    def raw_write(self, s):
        self.send.append(Endpoint.decode(s))

    def write(self, p, format=Endpoint.FMT_PACKED):
        Endpoint.encode(p, format)
        self.send.append(p)

    def read(self):
        if not self.recv:
            return EndpointDied

        return self.recv.get()

    def close(self):
        r = self.recv
        self.recv = None
        r.put(EndpointDied)


class MockBackend(object):
    MOCKED: Dict[str, Callable] = {}

    def __init__(self, core):
        self.core = core

    def query(self, q, **vars):
        q = self._strip(q)
        if q not in self.MOCKED:
            raise Exception("Can't mock query %s" % q)

        return self.MOCKED[q](vars)

    def _strip(self, q):
        q = q.strip()
        q = re.sub(r'[\r\n]', q, '')
        q = re.sub(r' +', q, ' ')
        return q

    def _reg(f, strip=_strip, MOCKED=MOCKED):
        q = strip(None, f.__doc__)
        MOCKED[q] = f
        return f

    @_reg
    def gameId(self):
        '''
        query { gameId }
        '''
        return {'gameId': random.randint(0, 1000000)}


class ServerWorld(object):
    def __init__(self):
        self.core = Core(disables=[
            'archive', 'connect', 'stats', 'backend'
        ])
        self.core.backend = MockBackend(self.core)

    def client(self):
        ep = MockEndpoint()
        core = self.core
        cli = Client(core, ep)
        gevent.spawn(cli.serve)
        gevent.sleep(0.01)
        return cli

    def fullgame(self, cls=None, flags={}):
        if not cls:
            from thb.thb2v2 import THBattle2v2 as cls

        base = random.randint(1, 1000000)
        core = self.core
        g = core.room.create_game(cls, 'Game-%s' % base, flags)

        for i in range(g.n_persons):
            u = self.client()
            assert core.lobby.state_of(u) == 'connected'
            core.auth.set_auth(u, base + i, 'UID%d' % (base + i))
            core.lobby.state_of(u).transit('authed')
            core.room.join_game(g, u, i)

        core.game.setup_game(g)
        return g

    def start_game(self, g):
        core = self.core
        for u in core.room.users_of(g):
            s = core.lobby.state_of(u)
            s == 'room' and s.transit('ready')

        gevent.sleep(0.01)


def hook_game(g):
    @hook(g)
    def pause(*a):
        pass

    g.synctag = 0
