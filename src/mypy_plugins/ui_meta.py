# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Callable, Optional, cast

# -- third party --
# -- own --
# -- errord --
from mypy.checkmember import bind_self
from mypy.nodes import Decorator, MemberExpr, SYMBOL_FUNCBASE_TYPES
from mypy.plugin import AttributeContext, MethodSigContext, Plugin
from mypy.types import AnyType, CallableType, Instance, Type, TypeOfAny, UnionType
from mypy.plugin import (
    Plugin, FunctionContext, MethodContext, MethodSigContext, AttributeContext, ClassDefContext
)


# -- code --
class UIMetaPlugin(Plugin):

    def get_class_decorator_hook(self, fullname: str
                                 ) -> Optional[Callable[[ClassDefContext], None]]:
        from mypy.plugins import attrs
        from mypy.plugins import dataclasses

        if 'ui_meta' in fullname:
            print(fullname)

        return None


def ui_meta_class_deco_hook(ctx: ClassDefContext) -> None:
    pass


def plugin(version: str) -> type:
    return UIMetaPlugin
