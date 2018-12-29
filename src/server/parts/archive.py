# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
import logging

# -- third party --
# -- own --
import settings
import gzip
import time
import os
import json

# -- code --
log = logging.getLogger('Archive')


class Archive(object):
    def __init__(self, core):
        self.core = core

        if not core.options.archive_path:
            return

        core.events.game_ended += self.handle_game_ended

    def handle_game_ended(self, g):
        core = self.core
        gid = core.room.gid_of(g)

        data = {
            'version': settings.VERSION,
            'gid': gid,
            'start_time': core.room.start_time_of(g),
            'end_time': int(time.time()),
            'class': g.__class__.__name__,
            'params': core.game.params_of(g),
            'items': core.items.items_of(g),  # XXX {k: list(v) for k, v in self.game_items.items()},
            'rngseed': g.rngseed,
            'players': [{
                'uid': core.auth.uid_of(u),
                'name': core.auth.name_of(u),
            } for u in core.room.users_of(g)],
            'data': core.game.get_game_archive(g),
        }

        fn = os.path.join(core.options.archive_path, '%s-%s.gz' % (core.options.node, gid))

        with gzip.open(fn, 'wb') as f:
            f.write(json.dumps(data))

        return g
