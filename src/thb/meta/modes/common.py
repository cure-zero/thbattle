# -*- coding: utf-8 -*-

# -- stdlib --
from enum import Enum
from typing import Dict, List, Tuple, Type

# -- third party --
from mypy_extensions import TypedDict

# -- own --


# -- code --
class ParamDisplayItem(TypedDict):
    desc: str
    options: List[Tuple[str, object]]


class ModeMeta:
    name: str
    logo: str
    description: str
    params_disp: Dict[str, ParamDisplayItem] = {}
    identities: Type[Enum]
