# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from thb import thbdebug
from thb.ui.ui_meta.common import ui_meta_for, meta_property


# -- code --
ui_meta = ui_meta_for(thbdebug)


@ui_meta
class DebugUseCard:
    # Skill
    name = '转化'
    params_ui = 'UIDebugUseCardSelection'

    @meta_property
    def image(self, c):
        return c.treat_as.ui_meta.image

    @meta_property
    def image_small(self, c):
        return c.treat_as.ui_meta.image_small

    @meta_property
    def tag_anim(self, c):
        return c.treat_as.ui_meta.tag_anim

    description = 'DEBUG'

    def clickable(self, game):
        return True

    def is_action_valid(self, g, cl, target_list):
        skill = cl[0]
        try:
            skill.treat_as.ui_meta
        except:
            return False, 'Dummy'

        return skill.treat_as.ui_meta.is_action_valid(g, [skill], target_list)

    def is_complete(self, g, cl):
        return True, 'XXX'


@ui_meta
class DebugDecMaxLife:
    # Skill
    name = '减上限'

    def clickable(self, g):
        return True

    def is_action_valid(self, g, cl, target_list):
        acards = cl[0].associated_cards
        if len(acards):
            return (False, '请不要选择牌！')

        return (True, 'XXX')
