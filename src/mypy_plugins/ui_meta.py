# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Callable, Optional, cast

# -- third party --
# -- own --
# -- errord --
from mypy.checkmember import bind_self
from mypy.nodes import Decorator, MemberExpr, SYMBOL_FUNCBASE_TYPES, CallExpr, SymbolTableNode, MDEF, Var, TypeInfo
from mypy.plugin import AttributeContext, MethodSigContext, Plugin
from mypy.types import AnyType, CallableType, Instance, Type, TypeOfAny, UnionType
from mypy.plugin import (
    Plugin, FunctionContext, MethodContext, MethodSigContext, AttributeContext, ClassDefContext
)


# -- code --
class UIMetaPlugin(Plugin):

    def get_class_decorator_hook(self, fullname: str
                                 ) -> Optional[Callable[[ClassDefContext], None]]:

        if fullname == 'thb.meta.common.ui_meta':
            return ui_meta_class_deco_hook
            print(fullname)

        return None


def ui_meta_class_deco_hook(ctx: ClassDefContext) -> None:
    if not isinstance(ctx.reason, CallExpr):
        ctx.api.fail('Calling ui_meta without an arg', ctx.reason)
        return

    expr = ctx.reason.args[0]
    assert isinstance(expr, MemberExpr), expr
    ti = expr.node
    if not ti:
        return

    assert isinstance(ti, TypeInfo), ti

    var = Var('ui_meta', Instance(ctx.cls.info, []))
    var.info = ctx.cls.info
    ti.names[var.name()] = SymbolTableNode(MDEF, var)


def plugin(version: str) -> type:
    return UIMetaPlugin
