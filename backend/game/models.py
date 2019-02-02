# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from django.db import models
from django.contrib.postgres import fields as pg

# -- own --
from player.models import Player


_ = lambda s: {'help_text': s, 'verbose_name': s}


# -- code --
class Game(models.Model):

    class Meta:
        verbose_name        = '完结的游戏'
        verbose_name_plural = '完结的游戏'

    gid         = models.IntegerField(primary_key=True, **_('游戏ID'))
    name        = models.CharField(max_length=100, **_('游戏名称'))
    type        = models.CharField(max_length=20, **_('游戏类型'))
    flags       = pg.JSONField(**_('游戏选项'))
    players     = models.ManyToManyField(Player, related_name='+', **_('玩家列表'))
    winners     = models.ManyToManyField(Player, related_name='+', **_('胜利玩家'))
    duration    = models.PositiveIntegerField(**_('持续时间'))
    finished_at = models.DateTimeField(auto_now_add=True, **_('结束时刻'))

    def __str__(self):
        return f'[{self.gid}]self.name'


class GameReward(models.Model):

    class Meta:
        verbose_name        = '游戏奖励'
        verbose_name_plural = '游戏奖励'

    id     = models.AutoField(primary_key=True)
    game   = models.ForeignKey(Game, **_('游戏'), related_name='rewards', on_delete=models.CASCADE)
    player = models.ForeignKey(Player,  **_('玩家'), on_delete=models.CASCADE)
    type   = models.CharField(**_('奖励类型'), max_length=20)
    amount = models.PositiveIntegerField(**_('数量'))

    def __str__(self):
        return f'{self.player.name}[{self.type}:{self.amount}]'


class GameArchive(models.Model):

    class Meta:
        verbose_name        = '游戏存档'
        verbose_name_plural = '游戏存档'

    game = models.OneToOneField(Game,
        **_('游戏'),
        primary_key=True,
        related_name='archive',
        on_delete=models.CASCADE,
    )
    replay = models.BinaryField(**_('Replay 数据'))

    def __str__(self):
        return self.game.name
