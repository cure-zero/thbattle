# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
from utils import BatchList

# -- own --

# -- code --


class TestFunctions(object):

    @classmethod
    def setup_class(cls):
        from game import autoenv
        autoenv.init('Server')

    def testImperialChoice(self):
        from thb.thb3v3 import THBattle
        from thb.item import ImperialChoice
        from thb.characters.sp_aya import SpAya

        from .mock import ServerWorld
        w = ServerWorld()
        g = w.fullgame(THBattle)

        p = g.players[0]
        pi = {p: ['imperial-choice:SpAya', 'foo']}
        assert ImperialChoice.get_chosen(pi, g.players) == [(p, SpAya)]

    def testBuildChoices(self):
        import logging
        from thb.common import build_choices
        import random
        from thb.characters.baseclasses import get_characters
        from thb import characters
        from game import autoenv
        # def build_choices(g, items, candidates, players, num, akaris, shared):

        from thb.thb3v3 import THBattle
        from .mock import ServerWorld
        w = ServerWorld()
        g = w.fullgame(THBattle)

        autoenv.Game.getgame = staticmethod(lambda: g)
        chars = get_characters('common', '3v3')
        assert chars

        choices, imperial = build_choices(g, {}, chars, g.players, 10, 3, True)
        assert len(choices.items()) == len(g.players)
        assert len(set([id(i) for i in choices.values()])) == 1
        assert set(choices.keys()) == set(g.players)
        assert imperial == []

        choices, imperial = build_choices(g, {0: ['imperial-choice:SpAya', 'foo']}, chars, g.players, 10, 3, True)
        assert len(choices.items()) == len(g.players)
        assert len(set([id(i) for i in choices.values()])) == 1
        assert set(choices.keys()) == set(g.players)
        p, c = imperial[0]
        assert (p, c.char_cls) == (g.players[0], characters.sp_aya.SpAya)
        assert c in choices[p]
        del c
        assert sum([c.akari for c in choices[p]]) == 3

        choices, imperial = build_choices(g, {0: ['imperial-choice:SpAya', 'foo']}, chars, g.players, [4] * 8, [1] * 8, False)
        assert len(choices.items()) == len(g.players)
        assert len(set([id(i) for i in choices.values()])) == 8
        assert set(choices.keys()) == set(g.players)
        assert [len(i) for i in choices.values()] == [4] * 8
        assert [len([j for j in i if j.akari]) for i in choices.values()] == [1] * 8

        p, c = imperial[0]
        assert (p, c.char_cls) == (g.players[0], characters.sp_aya.SpAya)
        assert c in choices[p]
