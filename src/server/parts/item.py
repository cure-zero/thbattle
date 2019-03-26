# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
from typing import Dict, List, TYPE_CHECKING, Tuple
import logging

# -- third party --
# -- own --
from game.base import GameItem
from server.base import Game
from server.endpoint import Client
from server.utils import command
from utils.misc import BusinessException
from wire import msg as wiremsg

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('server.parts.item')


class Item(object):
    def __init__(self, core: 'Core'):
        self.core = core
        core.events.game_created += self.handle_game_created
        core.events.game_started += self.handle_game_started
        _ = core.events.client_command
        _['item:use'] += self._use_item

    def handle_game_started(self, g: Game) -> Game:
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

    def handle_game_created(self, g: Game) -> Game:
        g._[self] = {
            'items': defaultdict(list),
        }
        return g

    def handle_game_left(self, ev: Tuple[Game, Client]) -> Tuple[Game, Client]:
        g, u = ev
        core = self.core
        if not core.room.is_started(g) and not g.ended:
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
            uid = core.auth.uid_of(u)
            g._[self]['items'][uid].append(i)
            u.write(wiremsg.Info('use_item_success'))
        except BusinessException as e:
            uid = core.auth.uid_of(u)
            log.exception('User %s failed to use item %s', uid, sku)
            u.write(wiremsg.Error(e.snake_case))

    # ----- Methods ------
    # ----- Public Methods -----
    def items_of(self, g: Game) -> Dict[int, List[GameItem]]:
        return g._[self]['items']

    def item_skus_of(self, g: Game) -> Dict[int, List[str]]:
        return {k: [i.sku for i in v] for k, v in self.items_of(g).items()}
