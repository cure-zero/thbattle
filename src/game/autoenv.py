# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Callable

# -- third party --
# -- own --
from game.base import Game as BaseGame


# -- code --
class Game(BaseGame):
    pass


U: Callable


def user_input(*a, **k):
    return U(*a, **k)  # noqa


def init(place, custom=None):
    if custom:
        locals().update(custom)
    elif place == 'Server':
        from server.base import Game as G, user_input as U
    elif place == 'Client':
        from client.base import Game as G, user_input as U  # noqa
    else:
        raise Exception('Where am I?')

    Game.__bases__ = (G,)
    globals().update(locals())
