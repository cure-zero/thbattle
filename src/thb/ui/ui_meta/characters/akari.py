# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid, ui_meta_for


# -- code --
ui_meta = ui_meta_for(characters.akari)


@ui_meta
class AkariSkill:
    # Skill
    name = '阿卡林'
    description = '消失在画面里的能力。在开局之前没有人知道这是谁。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta
class Akari:
    # Character
    name        = '随机角色'
    title       = '会是谁呢'

    port_image  = 'thb-portrait-akari'
