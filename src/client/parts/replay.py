# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Any, Dict, List, TYPE_CHECKING
import zlib

# -- third party --
from mypy_extensions import TypedDict
import msgpack

# -- own --
from client.base import Game
import wire

# -- typing --
if TYPE_CHECKING:
    from client.core import Core  # noqa: F401


# -- code --
class ReplayFile(TypedDict):
    version: int
    cliver: str
    mode: str
    name: str
    params: Dict[str, Any]
    items: Dict[int, List[str]]
    users: List[wire.model.User]
    index: int
    data: Any  # FIXME
    gid: int


class Replay(object):
    def __init__(self, core: 'Core'):
        self.core = core

    def dumps(self, g: Game) -> bytes:
        core = self.core
        me_uid = core.auth.uid
        users = core.game.users_of(g)
        pos = [uv['uid'] for uv in users].index(me_uid)

        rep: ReplayFile = {
            'version': 1,
            'cliver': core.warpgate.current_git_version(),
            'mode': g.__class__.__name__,
            'name': core.game.name_of(g),
            'params': core.game.params_of(g),
            'items': core.game.items_of(g),
            'users': users,
            'index': pos,
            'data': core.game.gamedata_of(g).archive(),
            'gid': core.game.gid_of(g),
        }

        return zlib.compress(msgpack.packb(rep, use_bin_type=True))

    def loads(self, s: bytes) -> ReplayFile:
        s = msgpack.unpackb(zlib.decompress(s), encoding='utf-8')
        return s

    def start_replay(self, rep: ReplayFile) -> None:
        core = self.core
        g = core.game.create_game(
            rep['gid'],
            rep['mode'],
            rep['name'],
            rep['users'],
            rep['params'],
            rep['items'],
        )
        core.game.gamedata_of(g).feed_archive(rep['data'])
        core.events.game_started.emit(g)
