# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Dict, Type

# -- third party --
# -- own --
from game.base import Game
from thb.thb2v2 import THBattle2v2
from thb.thbfaith import THBattleFaith
from thb.thbidentity import THBattleIdentity
from thb.thbkof import THBattleKOF
from thb.thbnewbie import THBattleNewbie


# -- code --
import thb.item  # noqa, init it

modes: Dict[str, Type[Game]] = {}
modelst = [
    THBattleKOF,
    THBattleIdentity,
    THBattleFaith,
    THBattle2v2,
    THBattleNewbie,
]

for g in modelst:
    modes[g.__name__] = g

del modelst, g

modes_kedama = {
    'THBattleNewbie',
    'THBattleKOF',
}
