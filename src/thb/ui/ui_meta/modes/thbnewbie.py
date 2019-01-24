# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from thb import thbnewbie
from thb.ui.ui_meta.common import gen_metafunc


# -- code --
__metaclass__ = gen_metafunc(thbnewbie)


class THBattleNewbie:
    name = '琪露诺的完美THB教室'
    logo = 'thb-modelogo-newbie'
    params_disp = {}
    description = (
        '|R游戏人数|r：1人+1NPC\n'
        '\n'
        '|G游戏目标|r：让琪露诺带你飞\n'
        '\n'
        '|G胜利条件|r：完整的完成教学，不掉线\n'
        '\n'
    ).strip()

    def ui_class():
        from thb.ui.view import THBattleNewbieUI
        return THBattleNewbieUI

    T = thbnewbie.Identity.TYPE
    identity_table = {
        T.HIDDEN:  '？',
    }

    identity_color = {
        T.HIDDEN:  'blue',
    }

    IdentityType = T
    del T
