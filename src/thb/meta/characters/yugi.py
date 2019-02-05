# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta_for, passive_clickable, passive_is_action_valid

# -- code --
ui_meta = ui_meta_for(characters.yugi)


@ui_meta
class Yugi:
    # Character
    name        = '星熊勇仪'
    title       = '人所谈论的怪力乱神'
    illustrator = '渚FUN'
    cv          = '北斗夜'

    port_image        = 'thb-portrait-yugi'
    figure_image      = 'thb-figure-yugi'
    miss_sound_effect = 'thb-cv-yugi_miss'


@ui_meta
class YugiKOF:
    # Character
    name        = '星熊勇仪'
    title       = '人所谈论的怪力乱神'
    illustrator = '渚FUN'
    cv          = '北斗夜'

    port_image        = 'thb-portrait-yugi'
    figure_image      = 'thb-figure-yugi'
    miss_sound_effect = 'thb-cv-yugi_miss'

    notes = '|RKOF修正角色|r'


@ui_meta
class Assault:
    # Skill
    name = '强袭'
    description = '|B锁定技|r，你与其他角色计算距离时始终-1。'

    no_display = False
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta
class AssaultAttack:
    name = '强袭'

    def sound_effect(self, act):
        return 'thb-cv-yugi_assaultkof'


@ui_meta
class AssaultKOFHandler:
    choose_option_prompt = '你要发动【强袭】吗？'
    choose_option_buttons = (('发动', True), ('不发动', False))


@ui_meta
class AssaultKOF:
    # Skill
    name = '强袭'
    description = '|B登场技|r，你登场时可以视为使用了一张|G弹幕|r。'

    no_display = False
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta
class FreakingPower:
    # Skill
    name = '怪力'
    description = '每当你使用|G弹幕|r指定了其他角色时，你可以进行一次判定，若结果为红，则此|G弹幕|r不能被响应；若结果为黑，则此|G弹幕|r造成伤害后，你弃置其一张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta
class FreakingPowerAction:
    fatetell_display_name = '怪力'

    def effect_string_before(self, act):
        return '|G【%s】|r稍微认真了一下，弹幕以惊人的速度冲向|G【%s】|r' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-yugi_fp'


@ui_meta
class FreakingPowerHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【怪力】吗？'
