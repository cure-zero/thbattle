# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Any, Optional, Sequence

# -- third party --
# -- own --
from game.base import Game as BaseGame, InputTransaction, Inputlet


# -- code --
def user_input(
    players: Sequence[Any],
    inputlet: Inputlet,
    timeout: int=25,
    type: str='single',
    trans: Optional[InputTransaction]=None,
):
    ...

class Game(BaseGame):
    ...


def init(place: str):
    ...
