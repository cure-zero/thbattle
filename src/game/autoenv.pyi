from game.base import AbstractPlayer, Inputlet, InputTransaction, Game as BaseGame
from typing import List, Optional

def user_input(
    players: List,
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
