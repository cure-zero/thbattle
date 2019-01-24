# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.youmu20150620)


class Youmu20150620:
    # Character
    name        = '魂魄妖梦'
    title       = '苍天型半人半灵'
    designer    = '真炎的爆发'

    port_image        = 'thb-portrait-youmu20150620'


class Xianshizhan:
    # Skill
    name = '现世斩'
    description = '结束阶段开始时，你可以重铸1张非基本牌，视为对一名其他角色使用了1张|G弹幕|r'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class XianshizhanAttackCard:
    name = '现世斩'

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return '|G【%s】|r对|G【%s】|r使用了|G现世斩|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )


class XianshizhanHandler:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, '现世斩!')
        else:
            return (False, '现世斩：请选择一张非基本牌（否则不发动）')

    def target(pl):
        if not pl:
            return (False, '现世斩：请选择1名玩家')

        return (True, '现世斩!')


# -------------------------

class Jiongyanjian:
    # Skill
    name = '炯眼剑'
    description = '你可以对自己使用1张武器牌，视为使用或打出了1张|G擦弹|r；|B锁定技|r，当你响应|G弹幕|r后，若你有武器牌，你对使用者造成1点伤害。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class JiongyanjianGrazeAction:
    def effect_string_before(act):
        return '妖梦发动了|G炯眼剑|r'
