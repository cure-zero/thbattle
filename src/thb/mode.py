# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
from typing import List, Type

# -- third party --
# -- own --
from game.autoenv import Game
from game.base import EventDispatcher, EventHandler
from thb.cards.base import CardList, Deck
from thb.characters.base import Character
from utils.misc import BatchList


# -- code --
class THBEventDispatcher(EventDispatcher):
    game: 'THBattle'

    def populate_handlers(self) -> List[EventHandler]:
        from thb.actions import COMMON_EVENT_HANDLERS
        g = self.game
        ehclasses = list(COMMON_EVENT_HANDLERS) + list(g.game_ehs)
        for c in g.players:
            ehclasses.extend(c.eventhandlers)

        return EventHandler.make_list(g, ehclasses)


class THBattle(Game):
    game: 'THBattle'
    game_ehs: List[Type[EventHandler]]
    deck: Deck
    players: BatchList[Character]

    dispatcher_cls = THBEventDispatcher

    def decorate(g, p: Character):
        p.cards          = CardList(p, 'cards')       # Cards in hand
        p.showncards     = CardList(p, 'showncards')  # Cards which are shown to the others, treated as 'Cards in hand'
        p.equips         = CardList(p, 'equips')      # Equipments
        p.fatetell       = CardList(p, 'fatetell')    # Cards in the Fatetell Zone
        p.special        = CardList(p, 'special')     # used on special purpose
        p.showncardlists = [p.showncards, p.fatetell]
        p.tags           = defaultdict(int)
