# -*- coding: utf-8 -*-

# -- stdlib --
from collections import OrderedDict
from typing import Dict, Type

# -- third party --
# -- own --
from game.base import Game
from thb.thb2v2 import THBattle2v2
from thb.thb3v3 import THBattle
from thb.thbfaith import THBattleFaith
from thb.thbidentity import THBattleIdentity
from thb.thbkof import THBattleKOF
from thb.thbnewbie import THBattleNewbie


# -- code --
import thb.item  # noqa, init it

modes: Dict[str, Type[Game]] = OrderedDict()
modelst = [
    THBattle,
    THBattleKOF,
    THBattleIdentity,
    THBattleFaith,
    THBattle2v2,
    THBattleNewbie,
]

for g in modelst:
    modes[g.__name__] = g

del modelst, g, OrderedDict

modes_kedama = {
    'THBattleNewbie',
    'THBattleKOF',
}
