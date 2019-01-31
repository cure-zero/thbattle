# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.base import Action, ActionShootdown, EventHandler, EventHandlerGroup, Game as BaseGame, GameEnded  # noqa
from game.base import GameError, GameException, GameItem, GameObject, InputTransaction  # noqa
from game.base import InterruptActionFlow, NPC, get_seed_for, list_shuffle, sync_primitive  # noqa


# -- code --
class Game(BaseGame):
    pass


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
