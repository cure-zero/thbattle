# -*- coding: utf-8 -*-

# -- stdlib --
from typing import List, Type

# -- third party --
# -- own --
from game.base import EventHandler
from thb.cards.classes import Skill, t_None
from thb.characters.base import Character, register_character_to


# -- code --
class AkariSkill(Skill):
    associated_action = None
    skill_category: List[str] = []
    target = t_None


@register_character_to('special')
class Akari(Character):
    # dummy player for hidden choices
    skills = [AkariSkill]
    eventhandlers: List[Type[EventHandler]] = []
    maxlife = 0
