# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
from enum import IntEnum
from itertools import cycle
import logging

# -- third party --
# -- own --
from game.autoenv import Game, user_input
from game.base import EventHandler, InputTransaction, InterruptActionFlow, list_shuffle
from thb.actions import DistributeCards, GenericAction, PlayerDeath, PlayerTurn, RevealIdentity
from thb.cards.base import Deck
from thb.characters.base import mixin_character
from thb.common import PlayerIdentity, build_choices, roll
from thb.inputlets import ChooseGirlInputlet


# -- code --
log = logging.getLogger('THBattleKOF')


class DeathHandler(EventHandler):
    interested = ['action_apply']

    def handle(self, evt_type, act):
        if evt_type != 'action_apply': return act
        if not isinstance(act, PlayerDeath): return act
        tgt = act.target

        g = self.game

        if tgt.remaining[0] <= 0:
            pl = g.players[:]
            pl.remove(tgt)
            g.winners = pl
            g.game_end()

        tgt.remaining[0] -= 1

        pl = g.players
        if pl[0].dropped:
            g.winners = [pl[1]]
            g.game_end()

        if pl[1].dropped:
            g.winners = [pl[0]]
            g.game_end()

        return act


class KOFCharacterSwitchHandler(EventHandler):
    interested = ['action_after', 'action_before', 'action_stage_action']

    def __init__(self, g):
        EventHandler.__init__(self, g)
        g.switch_handler = self

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


class Identity(PlayerIdentity):
    class TYPE(IntEnum):
        HIDDEN  = 0
        HAKUREI = 1
        MORIYA  = 2


class THBattleKOFBootstrap(GenericAction):
    def __init__(self, params, items):
        self.source = self.target = None
        self.params = params
        self.items = items

    def apply_action(self):
        g = self.game

        g.deck = Deck(g, cards.kof_card_definition)
        g.current_player = None

        for i, p in enumerate(g.players):
            p.identity = Identity()
            p.identity.type = (Identity.TYPE.HAKUREI, Identity.TYPE.MORIYA)[i % 2]

        # choose girls -->
        from thb.characters import get_characters
        chars = get_characters('common', 'kof')

        A, B = roll(g, self.items)
        order = [A, B, B, A, A, B, B, A, A, B]

        choices, imperial_choices = build_choices(
            g, self.items,
            candidates=chars, players=[A, B],
            num=10, akaris=4, shared=True,
        )

        chosen = {A: [], B: []}

        with InputTransaction('ChooseGirl', g.players, mapping=choices) as trans:
            for p, c in imperial_choices:
                c.chosen = p
                chosen[p].append(c)
                trans.notify('girl_chosen', (p, c))
                order.remove(p)

            for p in order:
                c = user_input([p], ChooseGirlInputlet(g, choices), 10, 'single', trans)
                c = c or next(choices[p], lambda c: not c.chosen, None)

                c.chosen = p
                chosen[p].append(c)

                trans.notify('girl_chosen', (p, c))

        # reveal akaris for themselves
        for p in [A, B]:
            for c in chosen[p]:
                c.akari = False
                p.reveal(c)
                del c.chosen

        list_shuffle(g, chosen[A], A)
        list_shuffle(g, chosen[B], B)

        with InputTransaction('ChooseGirl', g.players, mapping=chosen) as trans:
            ilet = ChooseGirlInputlet(g, chosen)
            ilet.with_post_process(lambda p, rst: trans.notify('girl_chosen', (p, rst)) or rst)
            rst = user_input([A, B], ilet, type='all', trans=trans)

        def s(p):
            c = rst[p] or chosen[p][0]
            chosen[p].remove(c)
            p.choices = chosen[p]
            p.remaining = [2]
            p = g.next_character(p, c)
            return p

        A, B = s(A), s(B)

        order = [1, 0] if A is g.players[0] else [0, 1]

        for p in [A, B]:
            g.process_action(RevealIdentity(p, g.players))

        g.emit_event('game_begin', g)

        g.process_action(DistributeCards(A, amount=4))
        g.process_action(DistributeCards(B, amount=3))

        for i in order:
            g.emit_event('character_debut', (None, g.players[i]))

        for i, idx in enumerate(cycle(order)):
            p = g.players[idx]
            if i >= 6000: break
            if p.dead:
                g.switch_handler.do_switch_dead()
                p = g.players[idx]  # player changed

            assert not p.dead

            try:
                g.emit_event('player_turn', p)
                g.process_action(PlayerTurn(p))
            except InterruptActionFlow:
                pass


class THBattleKOF(Game):
    n_persons  = 2
    game_ehs = [
        DeathHandler,
        KOFCharacterSwitchHandler,
    ]
    bootstrap  = THBattleKOFBootstrap

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
        new, old_cls = mixin_character(p, cls)
        g.decorate(new)
        g.players.replace(p, new)

        g.refresh_dispatcher()

        g.emit_event('switch_character', (p, new))

        return new
