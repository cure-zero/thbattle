# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import cards, characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.sakuya)


class Sakuya:
    # Character
    name        = '十六夜咲夜'
    title       = '完全潇洒的PAD长'
    illustrator = '和茶'
    cv          = 'VV'

    port_image        = 'thb-portrait-sakuya'
    figure_image      = 'thb-figure-sakuya'
    miss_sound_effect = 'thb-cv-sakuya_miss'


class Dagger:
    # Skill
    name = '飞刀'
    description = '你可以将一张装备牌当|G弹幕|r使用或打出，以此法使用的|G弹幕|r无距离限制。'

    def clickable(g):
        me = g.me

        if not (me.cards or me.showncards or me.equips): return False

        try:
            act = g.hybrid_stack[-1]
            if act.cond([characters.sakuya.Dagger(me)]):
                return True

        except (IndexError, AttributeError):
            pass

        return False

    def is_complete(g, cl):
        skill = cl[0]
        assert skill.is_card(characters.sakuya.Dagger)
        cl = skill.associated_cards
        if len(cl) != 1 or 'equipment' not in cl[0].category:
            return (False, '请选择一张装备牌！')
        return (True, '快看！灰出去了！')

    def is_action_valid(g, cl, target_list, is_complete=is_complete):
        rst, reason = is_complete(g, cl)
        if not rst:
            return rst, reason
        else:
            return cards.AttackCard.ui_meta.is_action_valid(g, cl, target_list)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        target = act.target
        s = '|G【%s】|r将|G%s|r制成了|G飞刀|r，向|G【%s】|r掷去！' % (
            source.ui_meta.name,
            card.associated_cards[0].ui_meta.name,
            target.ui_meta.name,
        )
        return s

    def sound_effect(act):
        return random.choice([
            'thb-cv-sakuya_dagger1',
            'thb-cv-sakuya_dagger2',
        ])


class LunaDialActionStage:
    def sound_effect(act):
        return 'thb-cv-sakuya_lunadial'


class LunaDial:
    # Skill
    name = '月时计'
    description = '|B锁定技|r，准备阶段开始时，你执行一个额外的出牌阶段。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid
