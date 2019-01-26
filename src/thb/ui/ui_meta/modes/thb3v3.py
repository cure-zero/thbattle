# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from thb import thb3v3
from thb.ui.ui_meta.common import ui_meta_for


# -- code --
ui_meta = ui_meta_for(thb3v3)


@ui_meta
class THBattle:
    name = '3v3模式'
    logo = 'thb-modelogo-3v3'
    description = (
        '|R游戏人数|r：6人\n'
        '\n'
        '阵营分为|!B博丽|r和|!O守矢|r，每个阵营3名玩家，交错入座。\n'
        '由ROLL点最高的人开始，按照顺时针1-2-2-1的方式选将。\n'
        '选将完成由ROLL点最高的玩家开始行动。\n'
        'ROLL点最高的玩家开局摸3张牌，其余玩家开局摸4张牌。\n'
        '\n'
        '|R胜利条件|r：击坠所有对方阵营玩家。'
    )
    params_disp = {
        'random_seat': {
            'desc': '随机座位阵营',
            'options': [
                ('固定', False),
                ('随机', True),
            ],
        },
    }

    def ui_class(self):
        from thb.ui.view import THBattleUI
        return THBattleUI

    T = thb3v3.Identity.TYPE
    identity_table = {
        T.HIDDEN: '？',
        T.HAKUREI: '博丽',
        T.MORIYA: '守矢'
    }

    identity_color = {
        T.HIDDEN: 'blue',
        T.HAKUREI: 'blue',
        T.MORIYA: 'orange'
    }

    IdentityType = T
    del T
