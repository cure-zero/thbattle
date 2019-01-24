# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, limit1_skill_used, my_turn

# -- code --
__metaclass__ = gen_metafunc(characters.marisa)


class Marisa:
    # Character
    name        = '雾雨魔理沙'
    title       = '绝非普通的强盗少女'
    illustrator = '霏茶'
    cv          = '君寻'

    port_image        = 'thb-portrait-marisa'
    figure_image      = 'thb-figure-marisa'
    miss_sound_effect = 'thb-cv-marisa_miss'


class Daze:
    name = '打贼'

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return '|G【%s】|r喊道：“打贼啦！”向|G【%s】|r使用了|G弹幕|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )


class BorrowAction:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要视为对魔理沙使用弹幕吗？'


class Borrow:
    # Skill
    name = '借走'
    description = '出牌阶段限一次，你可以获得其他角色的一张牌，然后该角色可以视为对你使用了一张|G弹幕|r。'

    def clickable(g):
        if limit1_skill_used('borrow_tag'):
            return False

        if not my_turn(): return False

        return True

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        if skill.associated_cards:
            return (False, '请不要选择牌!')

        if len(target_list) != 1:
            return (False, '请选择1名玩家')

        tgt = target_list[0]
        if not (tgt.cards or tgt.showncards or tgt.equips):
            return (False, '目标没有牌可以“借给”你')

        return (True, '我死了以后你们再拿回去好了！')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return '大盗|G【%s】|r又出来“|G借走|r”了|G【%s】|r的牌。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-marisa_borrow'
