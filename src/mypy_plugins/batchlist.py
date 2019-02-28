# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Callable, Optional, cast

# -- third party --
from mypy.nodes import MemberExpr
from mypy.plugin import AttributeContext, MethodSigContext, Plugin
from mypy.types import AnyType, CallableType, Instance, Type, TypeOfAny, UnionType

# -- own --

# -- code --


class BatchListPlugin(Plugin):

    def get_method_signature_hook(self, fullname: str
                                  ) -> Optional[Callable[[MethodSigContext], CallableType]]:
        if fullname == 'utils.misc.BatchList.__call__':
            return batchlist_method_signature_hook

        return None

    def get_attribute_hook(self, fullname: str
                           ) -> Optional[Callable[[AttributeContext], Type]]:
        if fullname.startswith('utils.misc.BatchList'):
            return batchlist_attribute_hook

        return None


def batchlist_attribute_hook(ctx: AttributeContext) -> Type:
    if isinstance(ctx.type, UnionType):
        for i in ctx.type.items:
            if isinstance(i, Instance) and i.type.fullname() == 'utils.misc.BatchList':
                instance = i
                break

    elif isinstance(ctx.type, Instance):
        instance = ctx.type

    else:
        assert False, 'WTF?!'

    typeinfo = instance.type

    expr = ctx.context
    assert isinstance(expr, MemberExpr), expr

    field = expr.name

    if field in typeinfo.names:
        t = typeinfo.names[field].type
        assert t
        return t

    typeparam = instance.args[0]
    if not isinstance(typeparam, Instance):
        ctx.api.fail('BatchList[{}] not supported by checker'.format(typeparam), expr)
        return Instance(typeinfo, [AnyType(TypeOfAny.from_error)])

    names = cast(Instance, typeparam).type.names

    if field not in names:
        ctx.api.fail(
            'BatchList item {} has no attribute "{}"'.format(
                instance.args[0], field,
            ), expr
        )
        return Instance(typeinfo, [AnyType(TypeOfAny.from_error)])

    t = names[field].type
    assert t
    return Instance(typeinfo, [t])


def batchlist_method_signature_hook(ctx: MethodSigContext) -> CallableType:
    instance = cast(Instance, ctx.type)
    typeinfo = instance.type

    expr = ctx.context

    c = instance.args[0]
    if isinstance(c, CallableType):
        return c.copy_modified(
            ret_type=Instance(typeinfo, [c.ret_type])
        )
    else:
        ctx.api.fail("BatchList item {} is not callable".format(instance.args[0]), expr)
        return ctx.default_signature


def plugin(version: str) -> type:
    return BatchListPlugin
