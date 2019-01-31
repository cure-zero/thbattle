# -*- coding: utf-8 -*-


# -- stdlib --
# -- third party --
# -- own --
from thb import thbkof
from thb.ui.ui_meta.common import ui_meta_for


# -- code --
ui_meta = ui_meta_for(thbkof)


@ui_meta
class THBattleKOF:
    name = 'KOF模式'
    logo = 'thb-modelogo-kof'
    description = (
        '|R游戏人数|r：2人\n'
        '\n'
        '|R选将模式|r：选将按照1-2-2-2-2-1来选择。\n'
        '\n'
        '|R游戏过程|r：选好角色后，将会翻开第一个角色进行对决，其他角色为隐藏。当有一方角色被击坠后，需弃置所有的牌（手牌、装备牌、判定区的牌），然后选择下一个出场的角色，并摸4张牌。\n'
        '\n'
        '|R胜利条件|r：当其中一方3名角色被击坠时，判对方胜出'
    )

    params_disp = {
    }

    def ui_class(self):
        from thb.ui.view import THBattleKOFUI
        return THBattleKOFUI

    T = thbkof.Identity.TYPE
    identity_table = {
        T.HIDDEN:  '？',
        T.HAKUREI: '博丽',
        T.MORIYA:  '守矢'
    }

    identity_color = {
        T.HIDDEN:  'blue',
        T.HAKUREI: 'blue',
        T.MORIYA:  'orange'
    }

    IdentityType = T
    del T
