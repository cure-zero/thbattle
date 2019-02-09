from game.base import AbstractPlayer, Inputlet, InputTransaction, Game as BaseGame

def user_input(
    players: List[AbstractPlayer],
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
