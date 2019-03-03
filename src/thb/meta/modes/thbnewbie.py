# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb.meta.typing import ModeMeta
from thb import thbnewbie
from thb.meta.common import ui_meta_for


# -- code --
ui_meta = ui_meta_for(thbnewbie)


@ui_meta
class THBattleNewbie(ModeMeta):
    name = '琪露诺的完美THB教室'
    logo = 'thb-modelogo-newbie'
    description = (
        '|R游戏人数|r：1人+1NPC\n'
        '\n'
        '|G游戏目标|r：让琪露诺带你飞\n'
        '\n'
        '|G胜利条件|r：完整的完成教学，不掉线\n'
        '\n'
    ).strip()

    T = thbnewbie.Identity.TYPE
    identity_table = {
        T.HIDDEN:  '？',
        T.HAKUREI: '博丽',
        T.BAKA:    '马鹿',
    }

    identity_color = {
        T.HIDDEN:  'blue',
    }

    IdentityType = T
    del T
