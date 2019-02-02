# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from graphene.types import generic as ghg
from graphene_django.types import DjangoObjectType
import graphene as gh

# -- own --
from . import models


# -- code --
class Game(DjangoObjectType):
    class Meta:
        model = models.Game

    flags = ghg.GenericScalar(description='游戏选项', required=True)


class GameReward(DjangoObjectType):
    class Meta:
        model = models.GameReward


class GameArchive(DjangoObjectType):
    class Meta:
        model = models.GameArchive
        exclude_fields = ['replay']

    replay = gh.String(description='Replay 数据（Base64）')



# ---------------------------
class GameQuery(gh.ObjectType):
    game = gh.Field(
        Game,
        id=gh.Int(description="势力ID"),
        name=gh.String(description='势力名称'),
        description='获取势力',
    )
    '''
    guilds = gh.List(
        gh.NonNull(Game),
        keyword=gh.String(required=True, description='关键词'),
        description='查找势力',
    )

    @staticmethod
    def resolve_guild(root, info, id=None, name=None):
        if id is not None:
            return models.Game.objects.get(id=id)
        elif name is not None:
            return models.Game.objects.get(name=name)

    @staticmethod
    def resolve_guilds(root, info, keyword):
        return models.Game.objects.filter(name__contains=keyword)
'''


class GameOps(gh.ObjectType):
    archive = gh.Field(
        Game,
    )
    '''
    reward = gh.Field(
        Game,
        name=gh.String(required=True, description="势力名称"),
        slogan=gh.String(required=True, description="势力口号"),
        totem=gh.String(description="势力图腾（图片URL）"),
        description="",
    )

    transfer = gh.Boolean(
        guildId=gh.Int(required=True, description="势力ID"),
        to=gh.Int(required=True, description="接收人用户ID"),
        description="转让势力",
    )

    join = gh.Boolean(
        guildId=gh.Int(required=True, description="势力ID"),
        description="申请加入势力",
    )

    approve = gh.Boolean(
        playerId=gh.Int(required=True, description="玩家ID"),
        description="批准加入势力",
    )

    kick = gh.Boolean(
        playerId=gh.Int(required=True, description="玩家ID"),
        description="踢出势力",
    )

    quit = gh.Boolean(
        description="退出势力",
    )

    update = gh.Field(
        Game,
        slogan=gh.String(description="口号"),
        totem=gh.String(description="图腾（URL）"),
        description="更新势力信息",
    )
    '''
