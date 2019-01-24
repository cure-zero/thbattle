# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, meta_property, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.kaguya)


class Kaguya:
    # Character
    name        = '蓬莱山辉夜'
    title       = '永远的公主殿下'
    illustrator = '噗呼噗呼@星の妄想乡'
    cv          = 'shourei小N'

    port_image        = 'thb-portrait-kaguya'
    figure_image      = 'thb-figure-kaguya'
    miss_sound_effect = 'thb-cv-kaguya_miss'


class Dilemma:
    # Skill
    name = '难题'
    description = '每当一名角色令你回复1点体力后，你可以令其摸一张牌；每当你受到一次伤害后，你可以令伤害来源选择一项：|B|R>> |r交给你一张方块牌，|B|R>> |r失去1点体力。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DilemmaDamageAction:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, '交出一张方片牌')
        else:
            return (False, '请选择交出一张方片牌（否则失去一点体力）')

    def effect_string_before(act):
        return '|G【%s】|r对|G【%s】|r发动了|G难题|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name
        )

    def effect_string(act):
        if act.peer_action == 'card':
            return '|G【%s】|r给了|G【%s】|r一张牌。' % (
                act.target.ui_meta.name,
                act.source.ui_meta.name
            )
        # elif act.peer_action == 'life':
        #     <handled by LifeLost>

    def sound_effect(act):
        return random.choice([
            'thb-cv-kaguya_dilemma1',
            'thb-cv-kaguya_dilemma2',
        ])


class DilemmaHealAction:
    def effect_string(act):
        return '|G【%s】|r发动了|G难题|r，|G【%s】|r摸了一张牌。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return random.choice([
            'thb-cv-kaguya_dilemma1',
            'thb-cv-kaguya_dilemma2',
        ])


class DilemmaHandler:
    # choose_option meta
    choose_option_buttons = (('发动', True), ('不发动', False))

    def choose_option_prompt(act):
        _type = {
            'positive': '正面效果',
            'negative': '负面效果'
        }.get(act.dilemma_type, 'WTF?!')
        return '你要发动【难题】吗（%s）？' % _type


class ImperishableNight:
    # Skill
    name = '永夜'
    description = '你的回合外，每当其他角色使用的红色基本牌置入弃牌堆时，你可以将一张红色基本牌或装备牌当|G封魔阵|r对其使用。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid

    @meta_property
    def image(c):
        return c.associated_cards[0].ui_meta.image

    tag_anim = lambda c: 'thb-tag-sealarray'

    def effect_string(act):
        return '|G【%s】|r对|G【%s】|r使用了|G永夜|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name
        )

    def sound_effect(act):
        return 'thb-cv-kaguya_inight'


class ImperishableNightHandler:
    # choose_option meta
    choose_option_buttons = (('发动', True), ('不发动', False))

    def choose_option_prompt(act):
        prompt = '你要发动【永夜】吗（对%s）？'
        return prompt % act.target.ui_meta.name

    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, '陷入永夜吧！')
        else:
            return (False, '请选择一张红色的基本牌或装备牌')
