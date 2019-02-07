# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import thbdebug
from thb.meta.common import ui_meta_for


# -- code --
ui_meta = ui_meta_for(thbdebug)


@ui_meta
class DebugUseCard:
    # Skill
    name = '转化'
    params_ui = 'UIDebugUseCardSelection'

    @property
    def image(self):
        return self.for_cls.treat_as.ui_meta.image

    @property
    def image_small(self):
        return self.for_cls.treat_as.ui_meta.image_small

    @property
    def tag_anim(self):
        return self.for_cls.treat_as.ui_meta.tag_anim

    description = 'DEBUG'

    def clickable(self, g):
        return True

    def is_action_valid(self, g, cl, tl):
        skill = cl[0]
        try:
            skill.treat_as.ui_meta
        except Exception:
            return False, 'Dummy'

        return skill.treat_as.ui_meta.is_action_valid(g, [skill], tl)

    def is_complete(self, g, cl):
        return True, 'XXX'


@ui_meta
class DebugDecMaxLife:
    # Skill
    name = '减上限'

    def clickable(self, g):
        return True

    def is_action_valid(self, g, cl, tl):
        acards = cl[0].associated_cards
        if len(acards):
            return (False, '请不要选择牌！')

        return (True, 'XXX')
