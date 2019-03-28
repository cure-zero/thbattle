# -*- coding: utf-8 -*-

# -- stdlib --
from typing import TYPE_CHECKING
import logging

# -- third party --
# -- own --
# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('server.parts.stats')


class Stats(object):
    def __init__(self, core: 'Core'):
        self.core = core
