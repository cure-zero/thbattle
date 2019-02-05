# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
import logging
import sys

# -- third party --
# -- own --
from game.base import GameItem
from server.endpoint import Client
from server.utils import command
from utils.misc import BusinessException


# -- code --
log = logging.getLogger('server.parts.items')


class Items(object):
    def __init__(self, core):
        self.core = core
        core.events.game_created += self.handle_game_created
        core.events.game_started += self.handle_game_started
        _ = core.events.client_command
        _['item:use'] += self._use_item

    def handle_game_started(self, g):
        core = self.core
        final = {}
        for uid, l in g._[self]['items']:
            consumed = []
            for i in l:
                try:
                    rst = core.backend.query('''
                        mutation($id: Int!, $typ: String, $r: String) {
                            item {
                                remove(player: $id, typ: $typ, reason: $r)
                            }
                        }
                    ''', id=uid, typ=i, reason="Use in game %s" % core.room.gid_of(g))

                    if rst['item']['remove']:
                        consumed.append(i)
                except Exception as e:
                    log.exception(e)

            final[uid] = consumed

        g._[self]['items'] = final

        return g

    def handle_game_created(self, g):
        g._[self] = {
            'items': defaultdict(list),  # userid -> ['item:meh', ...]
        }
        return g

    def handle_game_left(self, ev):
        g, u = ev
        core = self.core
        if not g.greenlet and not g.ended:
            g._[self]['items'].pop(core.auth.uid_of(u), None)

        return ev

    # ----- Command -----
    @command('room')
    def _use_item(self, u: Client, sku: str):
        core = self.core
        g = core.game.current(u)
        assert g

        try:
            i = GameItem.from_sku(sku)
            i.should_usable(g, u)
            g._[self]['items'].append(sku)
            u.write(['info', 'use_item_success'])
        except BusinessException as e:
            uid = core.auth.uid_of(u)
            log.info('User %s failed to use item %s', uid, sku, exc_info=sys.exc_info())
            u.write(['error', e.snake_case])

    # ----- Methods ------
