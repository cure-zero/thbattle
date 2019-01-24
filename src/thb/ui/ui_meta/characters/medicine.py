# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.medicine)


class Medicine:
    # Character
    name        = '梅蒂欣'
    title       = '小小的甜蜜毒药'
    illustrator = '和茶'
    cv          = 'VV'

    port_image        = 'thb-portrait-medicine'
    figure_image      = 'thb-figure-medicine'
    miss_sound_effect = 'thb-cv-medicine_miss'

    notes = '|RKOF不平衡角色|r'


class Ciguatera:
    # Skill
    name = '神经之毒'
    description = '一名角色准备阶段开始时，你可以弃置一张黑色牌，令其失去1点体力并获得“喝醉”状态。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class CiguateraAction:
    def effect_string_before(act):
        return '|G【%s】|r对|G【%s】|r使用了|G神经之毒|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name
        )

    def sound_effect(act):
        return 'thb-cv-medicine_ciguatera'


class CiguateraHandler:
    def choose_card_text(g, act, cards):
        return act.cond(cards), '弃置一张黑色牌，发动【神经之毒】'


class Melancholy:
    # Skill
    name = '忧郁之毒'
    description = '每当你受到一次有来源的伤害后，你可以展示并获得牌堆顶的一张牌，若此牌不是梅花牌，伤害来源不能使用或打出手牌，直到回合结束。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MelancholyPoison:
    name = '忧郁之毒(效果)'

    def is_complete(g, cl):
        return (False, '忧郁之毒：无法使用或打出手牌直到该回合结束')

    def is_action_valid(g, cl, target_list):
        return (False, '忧郁之毒：无法使用或打出手牌直到该回合结束')


class MelancholyAction:
    def effect_string_before(act):
        return '|G【%s】|r对|G【%s】|r使用了|G忧郁之毒|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name
        )

    def effect_string(act):
        return ('|G【%s】|r陷入了忧郁。' if act.effective
                else '但|G【%s】|r缓了过来。') % act.target.ui_meta.name

    def sound_effect(act):
        return 'thb-cv-medicine_melancholy'


class MelancholyHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '是否发动【忧郁之毒】'


class MelancholyLimit:
    target_independent = True
    shootdown_message = '【忧郁】你不能使用或打出手牌'
