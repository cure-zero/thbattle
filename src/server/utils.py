# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
import functools
import logging

# -- third party --
# -- own --
from utils.events import EventHub


# -- code --
log = logging.getLogger("server.utils")


def command(for_state, argstype):
    def decorate(f):
        @functools.wraps(f)
        def wrapper(self, ev):
            core = self.core
            c, args = ev

            if for_state and core.lobby.state_of(c) not in for_state:
                log.debug('Command %s is for state %s, called in %s', f.__name__, for_state, core.lobby.state_of(c))
                return

            if not (len(argstype) == len(args) and all(isinstance(v, t) for t, v in zip(argstype, args))):
                log.debug('Command %s with wrong args, expecting %r, actual %r', f.__name__, argstype, args)
                return

            rst = f(c, *args)

            if rst is EventHub.STOP_PROPAGATION:
                return rst
            else:
                return ev

        wrapper.__name__ = f.__name__
        return wrapper

    return decorate
