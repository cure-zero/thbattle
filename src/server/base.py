# -*- coding: utf-8 -*-

# -- stdlib --
from collections import OrderedDict
from copy import copy
from typing import Any, Callable
import logging

# -- third party --
from gevent import Greenlet, getcurrent, iwait
from gevent.pool import Group as GreenletGroup
import gevent

# -- own --
from .endpoint import Client
from endpoint import EndpointDied
from game.base import AbstractPlayer, GameEnded, GameViralContext, InputTransaction, Inputlet
from game.base import TimeLimitExceeded
from server.core import Core
from utils.misc import log_failure
from utils.stats import stats
import game.base


# -- code --
log = logging.getLogger('Game_Server')


class InputWaiter(Greenlet, GameViralContext):
    def __init__(self, player, tag):
        Greenlet.__init__(self)
        self.player = player
        self.tag = tag

    def _run(self):
        p, t = self.player, self.tag
        try:
            # should be [tag, <Data for Inputlet.parse>]
            # tag likes 'I?:ChooseOption:2345'
            tag, rst = p.client.gexpect(t)
            return rst
        except EndpointDied:
            return None

    def __repr__(self):
        return '<InputWaiter: p = %s, tag = %s>' % (self.player, self.tag)


class InputWaiterGroup(GreenletGroup):
    greenlet_class = InputWaiter


def user_input(players, inputlet, timeout=25, type='single', trans=None):
    '''
    Type can be 'single', 'all' or 'any'
    '''

    if not trans:
        with InputTransaction(inputlet.tag(), players) as trans:
            return user_input(players, inputlet, timeout, type, trans)

    assert players
    assert type in ('single', 'all', 'any')
    assert not type == 'single' or len(players) == 1

    timeout = max(0, timeout)

    g = trans.game

    inputlet.timeout = timeout
    players = list(players)

    t = {'single': '', 'all': '&', 'any': '|'}[type]
    tag = 'I{0}:{1}:'.format(t, inputlet.tag())

    ilets = {p: copy(inputlet) for p in players}
    for p in players:
        ilets[p].actor = p

    results = {p: None for p in players}
    synctags = {p: g.get_synctag() for p in players}

    orig_players = players[:]
    waiters = InputWaiterGroup()

    try:
        inputany_player = None

        for p in players:
            if p.is_npc:
                ilet = ilets[p]
                p.handle_user_input(trans, ilet)
                waiters.add(gevent.spawn(lambda v: v, ilet.data()))
            else:
                t = tag + str(synctags[p])
                waiters.spawn(p, t)

        for p in players:
            g.emit_event('user_input_start', (trans, ilets[p]))

        bottom_halves = []

        def flush():
            core = g.core
            for t, data, trans, my, rst in bottom_halves:
                for u in g.players.client:
                    core.game.write(g, u, t, data)

                g.emit_event('user_input_finish', (trans, my, rst))

            bottom_halves[:] = []

        for w in iwait(waiters, timeout=timeout + 5):
            try:
                rst = w.get()
                p, data = w.player, rst
            except Exception:
                p, data = w.player, None

            my = ilets[p]

            try:
                rst = my.parse(data)
            except Exception:
                log.error('user_input: exception in .process()', exc_info=1)
                # ----- FOR DEBUG -----
                if g.IS_DEBUG:
                    raise
                # ----- END FOR DEBUG -----
                rst = None

            rst = my.post_process(p, rst)

            bottom_halves.append((
                'R{}{}'.format(tag, synctags[p]), data, trans, my, rst
            ))

            players.remove(p)
            results[p] = rst

            if type != 'any':
                flush()

            if type == 'any' and rst is not None:
                inputany_player = p
                break

    except TimeLimitExceeded:
        pass

    finally:
        waiters.kill()

    # flush bottom halves
    flush()

    # timed-out players
    for p in players:
        my = ilets[p]
        rst = my.parse(None)
        rst = my.post_process(p, rst)
        results[p] = rst
        g.emit_event('user_input_finish', (trans, my, rst))
        core = g.core
        t = 'R{}{}'.format(tag, synctags[p])
        for u in g.players.client:
            core.game.write(g, u, t, None)

    if type == 'single':
        return results[orig_players[0]]

    elif type == 'any':
        if not inputany_player:
            return None, None

        return inputany_player, results[inputany_player]

    elif type == 'all':
        return OrderedDict([(p, results[p]) for p in orig_players])

    assert False, 'WTF?!'


class Game(game.base.Game):
    suicide = False
    '''
    The Game class, all game mode derives from this.
    Provides fundamental behaviors.

    Instance variables:
        players: list(Players)
        event_handlers: list(EventHandler)

        and all game related vars, eg. tags used by [EventHandler]s and [Action]s
    '''

    CLIENT_SIDE = False
    SERVER_SIDE = True

    core: Core

    def __init__(self, core: Core):
        game.base.Game.__init__(self)
        self.core = core
        self.greenlet = None

    @log_failure(log)
    def run(g):
        g.synctag = 0
        gr = getcurrent()
        g.greenlet = gr
        gr.game = g

        core = g.core

        core.events.game_started.emit(g)

        params = core.game.params_of(g)
        items = core.item.items_of(g)
        m = {core.auth.uid_of(p.client) for p in g.players}
        items = {m[k]: v for k, v in items.items()}

        try:
            g.process_action(g.bootstrap(params, items))
        except GameEnded:
            pass
        except Exception:
            core.game.mark_crashed(g)
            raise
        finally:
            core.events.game_ended.emit(g)

        assert g.ended

        # XXX stats
        stats(*g.get_stats())

    @staticmethod
    def getgame():
        return getcurrent().game

    def __repr__(self):
        try:
            gid = str(self.gameid)
        except Exception:
            gid = 'X'

        return '%s:%s' % (self.__class__.__name__, gid)

    def get_synctag(self):
        if self.suicide:
            self.greenlet.kill()
            return

        self.synctag += 1
        return self.synctag

    def pause(self, time):
        gevent.sleep(time)


class Player(AbstractPlayer):
    is_npc  = False

    def __init__(self, g: Game, client: Client):
        self.game = g
        self.client = client

    def reveal(self, obj_list):
        g = self.game
        core = g.core
        st = g.get_synctag()
        core.game.write(g, self.client, 'Sync:%d' % st, obj_list)  # XXX encode?


class NPCPlayer(AbstractPlayer):
    is_npc  = True

    def __init__(self, g: Game, name: str, handler: Callable[[InputTransaction, Inputlet], Any]):
        self.game = g
        self.name = name
        self.handle_user_input = handler

    def reveal(self, obj_list):
        self.game.get_synctag()
