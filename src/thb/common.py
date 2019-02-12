# -*- coding: utf-8 -*-

# -- stdlib --
from collections import OrderedDict, defaultdict
from enum import Enum
from itertools import cycle
from typing import Any, Dict, Iterable, List, Type
import logging
import random

# -- third party --
# -- own --
from game.autoenv import Game
from game.base import Player, GameViralContext, get_seed_for, sync_primitive
from thb.characters.base import Character
from thb.item import GameItem
from thb.mode import THBattle
from utils.misc import BatchList, partition
import settings


# -- code --
log = logging.getLogger('thb.common')


class CharChoice(GameViralContext):
    chosen = False
    akari = False

    def __init__(self, char_cls=None, akari=False):
        self.set(char_cls, akari)

    def __data__(self):
        return self.char_cls.__name__ if not self.akari else 'Akari'

    def sync(self, data):
        from thb.characters.base import Character
        self.set(Character.classes[data], False)

    def conceal(self):
        self.char_cls = None
        self.chosen = False
        self.akari = False

    def set(self, char_cls, akari=False):
        self.char_cls = char_cls

        if akari:
            self.akari = True
            if self.game.CLIENT:
                from thb import characters
                self.char_cls = characters.akari.Akari

    def __repr__(self):
        return '<Choice: {}{}>'.format(
            'None' if not self.char_cls else self.char_cls.__name__,
            '[Akari]' if self.akari else '',
        )


class PlayerIdentity(GameViralContext):
    game: THBattle

    def __init__(self, e: Type[Enum]):
        self._idtype = e
        self._value = e(0)

    def __data__(self) -> Any:
        return self._value.value

    def __str__(self) -> str:
        return self._value.name

    def sync(self, data) -> None:
        self._value = self._idtype(data)

    '''
    def is_type(self, t: Enum) -> bool:
        g = self.game
        pl = g.players
        return sync_primitive(self.value == t, pl)
    '''

    def set_value(self, t: int) -> None:
        if Game.SERVER:
            self._value = self._idtype(t)

    def get_value(self) -> Enum:
        return self._value

    value = property(get_value, set_value)


def roll(g: THBattle, pl: List[Player], items: Dict[Player, List[GameItem]]) -> BatchList[Player]:
    from thb.item import European
    roll = list(range(len(pl)))
    g.random.shuffle(roll)
    for i, p in enumerate(pl):
        if European.is_european(g, items, p):
            g.emit_event('european', p)
            roll.remove(i)
            roll.insert(0, i)
            break

    roll = sync_primitive(roll, pl)
    roll = BatchList(pl[i] for i in roll)
    g.emit_event('game_roll', roll)
    return roll


def build_choices(g, items, candidates, players, num, akaris, shared):
    from thb.item import ImperialChoice

    # ----- testing -----
    all_characters = Character.classes
    testing_lst: Iterable[str] = settings.TESTING_CHARACTERS
    testing = list(all_characters[i] for i in testing_lst)
    candidates, _ = partition(lambda c: c not in testing, candidates)

    if g.SERVER:
        candidates = list(candidates)
        g.random.shuffle(candidates)
    else:
        candidates = [None] * len(candidates)

    if shared:
        entities = ['shared']
        num = [num]
        akaris = [akaris]
    else:
        entities = players

    assert len(num) == len(akaris) == len(entities), 'Uneven configuration'
    assert sum(num) <= len(candidates) + len(testing), 'Insufficient choices'

    result: Dict[Any, List[CharChoice]] = defaultdict(list)

    entities_for_testing = entities[:]

    candidates = list(candidates)
    seed = get_seed_for(g, g.players)
    shuffler = random.Random(seed)
    shuffler.shuffle(entities_for_testing)

    for e, cls in zip(cycle(entities_for_testing), testing):
        result[e].append(CharChoice(cls))

    # ----- imperial (force chosen by ImperialChoice) -----
    imperial = ImperialChoice.get_chosen(items, players)
    imperial = [(p, CharChoice(cls)) for p, cls in imperial]

    for p, c in imperial:
        result['shared' if shared else p].append(c)

    # ----- normal -----
    for e, n in zip(entities, num):
        for _ in range(len(result[e]), n):
            result[e].append(CharChoice(candidates.pop()))

    # ----- akaris -----
    if g.SERVER:
        rest = candidates
    else:
        rest = [None] * len(candidates)

    g.random.shuffle(rest)

    for e, n in zip(entities, akaris):
        for i in range(-n, 0):
            result[e][i].set(rest.pop(), True)

    # ----- compose final result, reveal, and return -----
    if shared:
        result = OrderedDict([(p, result['shared']) for p in players])
    else:
        result = OrderedDict([(p, result[p]) for p in players])

    for p, l in result.items():
        p.reveal(l)

    return result, imperial
