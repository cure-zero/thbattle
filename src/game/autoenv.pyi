from game.base import Player, Inputlet, InputTransaction, Game as BaseGame
from typing import List, Optional, Sequence

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
