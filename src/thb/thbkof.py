# -*- coding: utf-8 -*-

# -- stdlib --
from enum import Enum
from itertools import cycle
from typing import Dict, List
import logging

# -- third party --
# -- own --
from game.autoenv import user_input
from game.base import Player, BootstrapAction, EventHandler, InputTransaction
from game.base import InterruptActionFlow, list_shuffle, GameEnded
from thb.actions import DistributeCards, PlayerDeath, PlayerTurn, RevealRole
from thb.cards.base import Deck
from thb.cards.definition import kof_card_definition
from thb.common import CharChoice, PlayerRole, build_choices_shared, roll
from thb.inputlets import ChooseGirlInputlet
from thb.mode import THBattle
from utils.misc import BatchList
from thb.item import GameItem
from typing import Any


# -- code --
log = logging.getLogger('THBattleKOF')


class DeathHandler(EventHandler):
    interested = ['action_apply']

    game: 'THBattleKOF'

    def handle(self, evt_type: str, act: PlayerDeath):
        if evt_type != 'action_apply': return act
        if not isinstance(act, PlayerDeath): return act
        tgt = act.target
        p = tgt.player

        g = self.game
        pl = g.players.player

        if len(g.chosen[p]) <= 2:  # 5(total chosen) - 3(available characters) = 2
            pl.remove(p)
            raise GameEnded(pl)

        if pl[0].dropped:
            reveal_type(pl[0])
            raise GameEnded([pl[1]])

        if pl[1].dropped:
            raise GameEnded([pl[0]])

        return act


class KOFCharacterSwitchHandler(EventHandler):
    interested = ['action_after', 'action_before', 'action_stage_action']
    game: 'THBattleKOF'

    def handle(self, evt_type, act):
        cond = evt_type in ('action_before', 'action_after')
        cond = cond and isinstance(act, PlayerTurn)
        cond = cond or evt_type == 'action_stage_action'
        cond and self.do_switch_dead()
        return act

    def do_switch_dead(self):
        g = self.game

        for p in [p for p in g.players if p.dead and p.choices]:
            new = self.switch(p)
            g.process_action(DistributeCards(new, 4))
            g.emit_event('character_debut', (p, new))

    def switch(self, p):
        g = self.game
        mapping = {p: p.choices}

        with InputTransaction('ChooseGirl', [p], mapping=mapping) as trans:
            rst = user_input([p], ChooseGirlInputlet(g, mapping), timeout=30, trans=trans)
            rst = rst or p.choices[0]

        p = g.next_character(p, rst)
        p.choices.remove(rst)
        return p


class THBKOFRole(Enum):
    HIDDEN  = 0
    HAKUREI = 1
    MORIYA  = 2


class THBattleKOFBootstrap(BootstrapAction):
    game: 'THBattleKOF'

    def __init__(self, params: Dict[str, Any],
                       items: Dict[Player, List[GameItem]],
                       players: BatchList[Player]):
        self.source = self.target = None
        self.params = params
        self.items = items
        self.players = players

    def apply_action(self) -> bool:
        g = self.game

        g.deck = Deck(g, kof_card_definition)
        pl = self.players
        A, B = pl
        g.roles = {
            A: PlayerRole[THBKOFRole](),
            B: PlayerRole[THBKOFRole](),
        }
        g.roles[A].set(THBKOFRole.HAKUREI)
        g.roles[B].set(THBKOFRole.MORIYA)

        # choose girls -->
        from thb.characters import get_characters
        chars = get_characters('common', 'kof')

        A, B = roll(g, pl, self.items)
        order = [A, B, B, A, A, B, B, A, A, B]

        choices, imperial_choices = build_choices_shared(
            g, pl, self.items,
            candidates=chars, spec={'num': 10, 'akaris': 4},
        )

        g.chosen = {A: [], B: []}

        with InputTransaction('ChooseGirl', pl, mapping=choices) as trans:
            for p, c in imperial_choices.items():
                c.chosen = p
                g.chosen[p].append(c)
                trans.notify('girl_chosen', (p, c))
                order.remove(p)

            for p in order:
                c = user_input([p], ChooseGirlInputlet(g, {p: choices}), 10, 'single', trans)
                # c = c or next(choices[p], lambda c: not c.chosen, None)
                c = c or next(c for c in choices if not c.chosen)

                c.chosen = p
                g.chosen[p].append(c)

                trans.notify('girl_chosen', (p, c))

        # reveal akaris for themselves
        for p in [A, B]:
            for c in g.chosen[p]:
                c.akari = False
                p.reveal(c)
                del c.chosen

        list_shuffle(g, g.chosen[A], A)
        list_shuffle(g, g.chosen[B], B)

        with InputTransaction('ChooseGirl', pl, mapping=g.chosen) as trans:
            ilet = ChooseGirlInputlet(g, g.chosen)
            ilet.with_post_process(lambda p, rst: trans.notify('girl_chosen', (p, rst)) or rst)
            rst = user_input([A, B], ilet, type='all', trans=trans)

        def s(p):
            c = rst[p] or g.chosen[p][0]
            g.chosen[p].remove(c)
            p.tags['remaining'] = 2
            p = g.next_character(p, c)
            return p

        A, B = s(A), s(B)

        order = [1, 0] if A is g.players[0] else [0, 1]

        for p in [A, B]:
            g.process_action(RevealRole(p, g.players))

        g.emit_event('game_begin', g)

        g.process_action(DistributeCards(A, amount=4))
        g.process_action(DistributeCards(B, amount=3))

        for i in order:
            g.emit_event('character_debut', (None, g.players[i]))

        for i, idx in enumerate(cycle(order)):
            p = g.players[idx]
            if i >= 6000: break
            if p.dead:
                handler = g.dispatcher.find_by_cls(KOFCharacterSwitchHandler)
                assert handler, 'WTF?!'
                handler.do_switch_dead()
                p = g.players[idx]  # player changed

            assert not p.dead

            try:
                g.emit_event('player_turn', p)
                g.process_action(PlayerTurn(p))
            except InterruptActionFlow:
                pass


class THBattleKOF(THBattle):
    n_persons  = 2
    game_ehs = [
        DeathHandler,
        KOFCharacterSwitchHandler,
    ]
    bootstrap  = THBattleKOFBootstrap

    chosen: Dict[Player, List[CharChoice]]

    def get_opponent(g, p):
        a, b = g.players
        if p is a:
            return b
        elif p is b:
            return a
        else:
            raise Exception('WTF?!')

    def can_leave(g, p):
        return False

    def next_character(g, p, choice):
        g.players.reveal(choice)
        cls = choice.char_cls

        # mix char class with player -->
        new, old_cls = mixin_character(g, p, cls)
        g.decorate(new)
        g.players.replace(p, new)

        g.refresh_dispatcher()

        g.emit_event('switch_character', (p, new))

        return new
