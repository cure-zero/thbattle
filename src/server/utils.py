# -*- coding: utf-8 -*-

# -- stdlib --
import functools
import logging

# -- third party --
# -- own --
from server.endpoint import Client
from utils.events import EventHub


# -- code --
log = logging.getLogger("server.utils")


def command(*for_state):
    def decorate(f):
        a = f.__annotations__
        assert a['u'] is Client

        varnames = f.__code__.co_varnames
        assert varnames[:2] == ('self', 'u')
        argstype = [a[n] for n in varnames[2:]]

        @functools.wraps(f)
        def wrapper(self, ev):
            core = self.core
            u, args = ev

            if for_state and core.lobby.state_of(u) not in for_state:
                log.debug('Command %s is for state %s, called in %s', f.__name__, for_state, core.lobby.state_of(u))
                return

            if not (len(argstype) == len(args) and all(isinstance(v, t) for t, v in zip(argstype, args))):
                log.debug('Command %s with wrong args, expecting %r, actual %r', f.__name__, argstype, args)
                return

            rst = f(u, *args)

            if rst is EventHub.STOP_PROPAGATION:
                return rst
            else:
                return ev

        wrapper.__name__ = f.__name__
        return wrapper

    return decorate
