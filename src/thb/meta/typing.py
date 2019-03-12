# -*- coding: utf-8 -*-

# -- stdlib --
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple, Type

# -- third party --
from mypy_extensions import TypedDict
from typing_extensions import Protocol

# -- own --
from thb.cards.base import Card
from thb.characters.base import Character
from thb.mode import THBAction, THBattle


# -- code --
class ParamDisplayItem(TypedDict):
    desc: str
    options: List[Tuple[str, object]]


class ModeMeta(Protocol):
    name: str
    logo: str
    description: str
    params_disp: Dict[str, ParamDisplayItem]
    roles: Type[Enum]


class CharacterMeta(Protocol):
    name: str
    title: str
    designer: str
    illustrator: str
    cv: str
    port_image: str
    figure_image: str
    miss_sound_effect: str


class PhysicalCardMeta(Protocol):
    name: str
    image: str
    description: str


class ActionMeta(Protocol):
    def is_action_valid(self, g: THBattle, cl: Sequence[Card], tl: Sequence[Character]) -> Tuple[bool, str]:
        ...

    def sound_effect(self, act: THBAction) -> Optional[str]:
        ...
