# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
from enum import IntEnum
from itertools import cycle
from typing import Any, Dict, List
import logging
import random

# -- third party --
# -- own --
from game.autoenv import Game, user_input
from game.base import Player, BootstrapAction, EventHandler, GameEnded, GameItem
from game.base import InputTransaction, InterruptActionFlow, get_seed_for
from thb.actions import DrawCards, PlayerDeath, PlayerTurn, RevealIdentity
from thb.cards.base import CardList, Deck
from thb.characters.base import Character, mixin_character
from thb.common import PlayerRole, build_choices, roll
from thb.inputlets import ChooseGirlInputlet
from utils.misc import BatchList


# -- code --
log = logging.getLogger('THBattle')


class DeathHandler(EventHandler):
    interested = ['action_apply']

    def handle(self, evt_type, act: PlayerDeath):
        if evt_type != 'action_apply': return act
        if not isinstance(act, PlayerDeath): return act

        g = self.game

        # see if game ended
        force1, force2 = g.forces
        tgt = act.target
        dead = lambda p: p.dead or p.dropped or p is tgt

        if all(dead(p) for p in force1):
            raise GameEnded(force2[:])

        if all(dead(p) for p in force2):
            raise GameEnded(force1[:])

        return act


class Identity(PlayerRole):
    class TYPE(IntEnum):
        HIDDEN  = 0
        HAKUREI = 1
        MORIYA  = 2


class THBattleBootstrap(BootstrapAction):
    def __init__(self, params: Dict[str, Any],
                       items: Dict[Player, List[GameItem]],
                       players: List[Player]):
        self.source = self.target = None
        self.params = params
        self.items = items

    def apply_action(self):
        g = self.game
        params = self.params

        g.deck = Deck(g)

        if params['random_seat']:
            seed = get_seed_for(g, g.players)
            random.Random(seed).shuffle(g.players)
            g.emit_event('reseat', (FROM, TO))

        for i, p in enumerate(g.players):
            p.identity = Identity()
            p.identity.type = (Identity.TYPE.HAKUREI, Identity.TYPE.MORIYA)[i % 2]

        g.forces = forces = BatchList([BatchList(), BatchList()])
        for i, p in enumerate(g.players):
            f = i % 2
            p.force = f
            forces[f].append(p)

        pl = g.players
        for p in pl:
            g.process_action(RevealIdentity(p, pl))

        from . import characters
        chars = characters.get_characters('common', '3v3')
        choices, imperial_choices = build_choices(
            g, self.items,
            candidates=chars, players=g.players,
            num=16, akaris=4, shared=True,
        )

        roll_rst = roll(g, self.items)
        first = roll_rst[0]
        first_index = g.players.index(first)

        order_list   = (0, 5, 3, 4, 2, 1)
        n = len(order_list)
        order = [g.players[(first_index + i) % n] for i in order_list]

        akaris = []
        with InputTransaction('ChooseGirl', g.players, mapping=choices) as trans:
            chosen = set()

            for p, c in imperial_choices:
                chosen.add(p)
                c.chosen = p
                g.set_character(p, c.char_cls)
                trans.notify('girl_chosen', (p, c))

            for p in order:
                if p in chosen:
                    continue

                c = user_input([p], ChooseGirlInputlet(g, choices), timeout=30, trans=trans)
                c = c or [_c for _c in reversed(choices[p]) if not _c.chosen][0]
                c.chosen = p

                if c.akari:
                    c.akari = False
                    akaris.append((p, c))
                else:
                    g.set_character(p, c.char_cls)

                trans.notify('girl_chosen', (p, c))

        # reveal akaris
        if akaris:
            g.players.reveal([i[1] for i in akaris])

            for p, c in akaris:
                g.set_character(p, c.char_cls)

        # -------
        for p in g.players:
            log.info(
                '>> Player: %s:%s %s',
                p.__class__.__name__,
                Identity.TYPE.rlookup(p.identity.type),
                p.account.username,
            )
        # -------

        first = g.players[first_index]

        g.emit_event('game_begin', g)

        for p in g.players:
            g.process_action(DrawCards(p, amount=3 if p is first else 4))

        pl = g.players.rotate_to(first)

        for i, p in enumerate(cycle(pl)):
            if i >= 6000: break
            if not p.dead:
                g.emit_event('player_turn', p)
                try:
                    g.process_action(PlayerTurn(p))
                except InterruptActionFlow:
                    pass

        return True


class THBattle3v3(Game):
    n_persons    = 6
    game_ehs     = [DeathHandler]
    bootstrap    = THBattleBootstrap
    params_def   = {
        'random_seat': (False, True),
    }

    def can_leave(self, p):
        return getattr(p, 'dead', False)

    def set_character(g, p, cls):
        # mix char class with player -->
        new, old_cls = mixin_character(g, p, cls)
        g.decorate(new)
        g.players.replace(p, new)
        g.forces[0].replace(p, new)
        g.forces[1].replace(p, new)
        assert not old_cls
        g.refresh_dispatcher()
        g.emit_event('switch_character', (p, new))
        return new
