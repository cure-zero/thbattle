# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Callable, Sequence, TypeVar, cast, Any
import functools
import logging

# -- third party --
# -- own --
from server.endpoint import Client


# -- code --
log = logging.getLogger("server.utils")
T = TypeVar('T', bound=Callable)


def for_state(*states: Sequence[str]) -> Callable[[T], T]:
    def decorate(f: T) -> T:
        @functools.wraps(f)
        def wrapper(self: Any, u: Client, *args: Any) -> Any:
            core = self.core
            if core.lobby.state_of(u) not in states:
                log.debug('Command %s is for state %s, called in %s', f.__name__, states, core.lobby.state_of(u))
            else:
                return f(u, *args)

        return cast(T, wrapper)

    return decorate
