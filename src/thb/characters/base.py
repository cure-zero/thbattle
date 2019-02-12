# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Set, TYPE_CHECKING, Tuple, Type, Union

# -- third party --
# -- own --
from game.autoenv import Game
from game.base import Player, EventHandler, GameObject
from thb.meta.typing import CharacterMeta
from utils.misc import partition

# -- typing --
if TYPE_CHECKING:
    from thb.cards.base import CardList, Skill  # noqa: F401


# -- code --
# common, id8, faith, kof, 3v3, testing
# -id8, ...
characters_by_category: Dict[str, Set[Type['Character']]] = defaultdict(set)


class Character(GameObject):
    classes: Dict[str, Type['Character']] = {}

    # ----- Class Variables -----
    ui_meta: CharacterMeta
    eventhandlers: List[Type[EventHandler]] = []
    categories: Iterable[str]
    skills: List[Type['Skill']]
    maxlife: int

    # ----- Instance Variables -----
    dead: bool = False
    life: int
    disabled_skills: Dict[str, Set[Type['Skill']]]
    tags: Dict[str, Any]
    cards: 'CardList'
    showncards: 'CardList'
    equips: 'CardList'
    fatetell: 'CardList'
    special: 'CardList'
    showncardlists: List['CardList']

    def __init__(self, player: Player):
        self.player = player
        self.disabled_skills = defaultdict(set)

        self.cards          = CardList(self, 'cards')       # Cards in hand
        self.showncards     = CardList(self, 'showncards')  # Cards which are shown to the others, treated as 'Cards in hand'
        self.equips         = CardList(self, 'equips')      # Equipments
        self.fatetell       = CardList(self, 'fatetell')    # Cards in the Fatetell Zone
        self.special        = CardList(self, 'special')     # used on special purpose
        self.showncardlists = [self.showncards, self.fatetell]
        self.tags           = defaultdict(int)

    def get_skills(self, skill: Type['Skill']):
        return [s for s in self.skills if issubclass(s, skill)]

    def has_skill(self, skill: Type['Skill']):
        if self.dead:
            return False

        if any(issubclass(skill, s) for l in self.disabled_skills.values() for s in l):
            return False

        return self.get_skills(skill)

    def disable_skill(self, skill: Type['Skill'], reason: str):
        self.disabled_skills[reason].add(skill)

    def reenable_skill(self, reason: str):
        self.disabled_skills.pop(reason, '')

    def __repr__(self) -> str:
        return '<Char: {}>'.format(self.__class__.__name__)


Entity = Union[Player, Character]


def register_character_to(*cats):
    sets = [characters_by_category[c] for c in set(cats)]

    def register(cls: Type[Character]):
        Character.classes[cls.__name__] = cls

        for s in sets:
            s.add(cls)

        cls.categories = cats
        return cls

    return register


def get_characters(*categories):
    cats: Set[str] = set(categories)
    chars: Set[Type[Character]] = set()
    pos, neg = partition(lambda c: not c.startswith('-'), cats)
    chars.update(*[characters_by_category[c] for c in pos])
    chars.difference_update(*[characters_by_category['-' + c] for c in pos])
    chars.difference_update(*[characters_by_category[c.strip('-')] for c in neg])
    return list(sorted(chars, key=lambda i: i.__name__))


def mixin_character(g: Game, player: Entity, char_cls: Type[Character]) -> Tuple[Character, Optional[Type[Character]]]:
    player.index = g.get_playerid(player)

    old = None
    if isinstance(player, Character):
        old = player.__class__
        player = player.player

    new = char_cls(player)
    new.skills = list(char_cls.skills)
    new.maxlife = char_cls.maxlife
    new.life = char_cls.maxlife
    new.dead = False
    return new, old
