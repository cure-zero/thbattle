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

        if core.game.is_crashed(g):
            return g

        if core.game.is_aborted(g):
            return g

        rewards = []

        users = core.room.users_of(g)
        fleed = [u for u in users if core.game.is_fleed(g, u)]
        rewards.extend([{
            'playerId': core.auth.uid_of(u),
            'type': 'game',
            'amount': 1,
        } for u in users])

        rewards.extend([{
            'playerId': core.auth.uid_of(u),
            'type': 'drop',
            'amount': 1,
        } for u in fleed])

        good = list(set(users) - set(fleed))
        winners_good = list(set(core.game.winners_of(g)) - set(fleed))
        bonus = len(users) * 5 / len(winners_good) if winners_good else 0

        rewards.extend([{
            'playerId': core.auth.uid_of(u),
            'type': 'jiecao',
            'amount': 2 + bonus if u in winners_good else 2,
        } for u in good])

        core.backend.query('''
            mutation AddReward($gid: Int!, $rewards: [GameRewardInput!]!) {
              game {
                addReward(gameId: $gid, rewards: $rewards) {
                  id
                }
              }
            }
        ''', gid=core.room.gid_of(g), rewards=rewards)

        return g
