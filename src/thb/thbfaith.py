# -*- coding: utf-8 -*-

# -- stdlib --
from enum import Enum
from itertools import cycle
import logging
from typing import Any
import random

# -- third party --
# -- own --
from game.autoenv import user_input
from game.base import BootstrapAction, EventHandler, InputTransaction, InterruptActionFlow
from game.base import get_seed_for
from thb.actions import DistributeCards, MigrateCardsTransaction, PlayerDeath, PlayerTurn
from thb.actions import RevealIdentity, migrate_cards
from thb.cards.base import Deck
from thb.characters.base import Character, mixin_character
from thb.common import CharChoice, PlayerIdentity, build_choices, roll
from thb.inputlets import ChooseGirlInputlet, ChooseOptionInputlet, SortCharacterInputlet
from thb.mode import THBattle
from utils.misc import BatchList


# -- code --
log = logging.getLogger('THBattle')


class DeathHandler(EventHandler):
    interested = ['action_after', 'action_apply']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerDeath):
            g = self.game

            tgt = act.target
            force = tgt.tags['force']
            if len(force.pool) <= 1:
                forces = g.forces[:]
                forces.remove(force)
                g.winners = forces[0][:]
                g.game_end()

        elif evt_type == 'action_after' and isinstance(act, PlayerDeath):
            g = self.game

            tgt = act.target
            pool = tgt.tags['force'].pool
            assert pool

            mapping = {tgt: pool}
            with InputTransaction('ChooseGirl', [tgt], mapping=mapping) as trans:
                c = user_input([tgt], ChooseGirlInputlet(g, mapping), timeout=30, trans=trans)
                c = c or [_c for _c in pool if not _c.chosen][0]
                c.chosen = tgt
                pool.remove(c)
                trans.notify('girl_chosen', (tgt, c))

            tgt = g.switch_character(tgt, c)

            c = getattr(g, 'current_player', None)

            g.process_action(DistributeCards(tgt, 4))

            if user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                g.process_action(RedrawCards(tgt, tgt))

        return act


class RedrawCards(DistributeCards):
    def apply_action(self):
        tgt = self.target
        g = self.game

        with MigrateCardsTransaction(self) as trans:
            g.players.reveal(list(tgt.cards))
            migrate_cards(tgt.cards, g.deck.droppedcards, trans=trans)
            cards = g.deck.getcards(4)
            tgt.reveal(cards)
            migrate_cards(cards, tgt.cards, trans=trans)

        return True


class Identity(PlayerIdentity):
    class TYPE(Enum):
        HIDDEN  = 0
        HAKUREI = 1
        MORIYA  = 2


class THBattleFaithBootstrap(BootstrapAction):
    game: 'THBattleFaith'

    def __init__(self, params, items):
        self.source = self.target = None
        self.params = params
        self.items = items

    def apply_action(self) -> bool:
        g = self.game
        params = self.params

        g.deck = Deck(g)

        H, M = Identity.TYPE.HAKUREI, Identity.TYPE.MORIYA
        if params['random_seat']:
            # reseat
            seed = get_seed_for(g, g.players)
            random.Random(seed).shuffle(g.players)
            g.emit_event('reseat', (FROM, TO))

            L = [[H, H, M, M, H, M], [H, M, H, M, H, M]]
            rnd = random.Random(get_seed_for(g, g.players))
            L = rnd.choice(L) * 2
            s = rnd.randrange(0, 6)
            idlist = L[s:s+6]
            del L, s, rnd
        else:
            idlist = [H, M, H, M, H, M]

        del H, M

        for p, identity in zip(g.players, idlist):
            p.identity = Identity()
            p.identity.type = identity
            g.process_action(RevealIdentity(p, g.players))

        hakureis      = BatchList()
        moriyas       = BatchList()
        hakureis.pool = []
        moriyas.pool  = []

        for p in g.players:
            if p.identity.type == Identity.TYPE.HAKUREI:
                hakureis.append(p)
                p.force = hakureis
            elif p.identity.type == Identity.TYPE.MORIYA:
                moriyas.append(p)
                p.force = moriyas

        g.forces = BatchList([hakureis, moriyas])

        roll_rst = roll(g, self.items)
        first = roll_rst[0]

        # choose girls -->
        from . import characters
        chars = characters.get_characters('common', 'faith')

        choices, _ = build_choices(
            g, self.items,
            candidates=chars, players=g.players,
            num=[4] * 6, akaris=[1] * 6,
            shared=False,
        )

        rst = user_input(g.players, SortCharacterInputlet(g, choices, 2), timeout=30, type='all')

        for p in g.players:
            a, b = [choices[p][i] for i in rst[p][:2]]
            b.chosen = None
            p.force.reveal(b)
            g.switch_character(p, a)
            p.force.pool.append(b)

        for p in g.players:
            if p.player is first:
                first = p
                break

        pl = g.players
        first_index = pl.index(first)
        order = BatchList(range(len(pl))).rotate_to(first_index)

        for p in pl:
            g.process_action(RevealIdentity(p, pl))

        g.emit_event('game_begin', g)

        for p in pl:
            g.process_action(DistributeCards(p, amount=4))

        pl = g.players.rotate_to(first)
        rst = user_input(pl[1:], ChooseOptionInputlet(DeathHandler(g), (False, True)), type='all')

        for p in pl[1:]:
            rst.get(p) and g.process_action(RedrawCards(p, p))

        pl = g.players
        for i, idx in enumerate(cycle(order)):
            if i >= 6000: break
            p = pl[idx]
            if p.dead: continue

            g.emit_event('player_turn', p)
            try:
                g.process_action(PlayerTurn(p))
            except InterruptActionFlow:
                pass

        return True


class THBattleFaith(THBattle):
    n_persons  = 6
    game_ehs   = [DeathHandler]
    bootstrap  = THBattleFaithBootstrap
    params_def = {
        'random_seat': (True, False),
    }

    def can_leave(g: 'THBattleFaith', p: Any):
        return False

    def switch_character(g, p: Character, choice: CharChoice):
        choice.akari = False

        g.players.reveal(choice)
        cls = choice.char_cls

        log.info('>> NewCharacter: %s %s', Identity.TYPE(p.identity.type).name, cls.__name__)

        # mix char class with player -->
        old = p
        p, oldcls = mixin_character(p, cls)
        g.decorate(p)
        g.players.replace(old, p)
        g.forces[0].replace(old, p)
        g.forces[1].replace(old, p)

        g.refresh_dispatcher()
        g.emit_event('switch_character', (old, p))

        return p

    def get_remaining_characters(g):
        try:
            hakurei, moriya = g.forces
        except Exception:
            return -1, -1

        h, m = len(hakurei.pool) - 1, len(moriya.pool) - 1
        if h < 0 or m < 0:
            return -1, -1

        return h, m
