# -*- coding: utf-8 -*-


# -- stdlib --
import logging

# -- third party --
# -- own --
# -- code --
log = logging.getLogger('Reward')


class Reward(object):
    def __init__(self, core):
        self.core = core

        core.events.game_ended += self.handle_game_ended

    def handle_game_ended(self, g):
        core = self.core
        all_dropped = not bool(core.room.users_of(g))

        # XXX bonus
        if not all_dropped:
            bonus = manager.get_bonus()

            for u, l in bonus.items():
                # XXX
                u.account.add_credit(l)

        return g

    def get_bonus(self, g):
        # XXX
        # self is GameManager
        return []

        assert self.get_online_users()

        t = time.time()
        g = self.game
        percent = min(1.0, (t - self.start_time) / 1200)
        import math
        rate = math.sin(math.pi / 2 * percent)
        winners = g.winners
        bonus = g.n_persons * 5 / len(winners) if winners else 0

        rst = {}

        for p in g.players:
            u = p.client
            rst[u] = []

            if isinstance(u, NPCClient):
                continue

            rst[u].append(('games', 1))
            if p.dropped or p.fleed:
                if not options.no_counting_flee:
                    rst[u].append(('drops', 1))
            else:
                s = 5 + bonus if p in winners else 5
                rst[u].append(('jiecao', int(s * rate * options.credit_multiplier)))

        return rst

    # XXX: tag user if he's fleed
    '''
            can_leave = g.can_leave(p)

            if can_leave:
                user.write(['game_left', None])
                p.set_fleed(False)
            else:
                p.set_dropped()
                user.write(['fleed', None])
'''
