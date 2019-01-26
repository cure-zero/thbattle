# -*- coding: utf-8 -*-


# -- stdlib --
import zlib

# -- third party --
import msgpack

# -- own --


# -- code --
class Replay(object):
    def __init__(self, core):
        self.core = core

    def dumps(self, g):
        core = self.core
        me_uid = core.auth.uid()
        users = core.game.users_of(g)
        pos = [uv['uid'] for uv in users].index(me_uid)

        rep = {
            'version': 1,
            'cliver': core.update.current_version(),
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

    def loads(self, s):
        s = msgpack.unpackb(zlib.decompress(s), encoding='utf-8')
        return s

    def save(self, g, filename):
        with open(filename, 'wb') as f:
            f.write(self.dumps(g))

    def start_replay(self, rep):
        core = self.core
        g = core.game.create_game(
            rep['gid'],
            rep['mode'],
            rep['name'],
            rep['users'],
            rep['params'],
            rep['items'],
        )
        core.game.prepare_game(g)
        core.game.gamedata_of(g).feed_archive(rep['data'])
        core.events.game_prepared.emit(g)
