# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, cards
from thb.actions import ttags
from thb.ui.ui_meta.common import G, ui_meta_for

# -- code --
ui_meta = ui_meta_for(cards)


@ui_meta
class MassiveDamageCard:
    # action_stage meta
    image = 'thb-card-question'
    name = '99 Damage'
    description = name

    def is_action_valid(self, g, cl, target_list):
        return (True, 'Massive Damage')
