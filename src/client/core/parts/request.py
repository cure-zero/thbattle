# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Optional, Union, Any
import functools

# -- third party --
# -- own --


# -- code --
def request(cmd):
    def decorate(f):
        @functools.wraps(f)
        def wrapper(self, *args):
            core = self.core
            core.server.write([cmd, args])

        wrapper.__name__ = f.__name__
        return wrapper
    return decorate


class Room(object):
    def __init__(self, core):
        self.core = core

    @request('room:create')
    def create(self, mode: str, name: str, flags: dict) -> None:
        pass

    @request('room:join')
    def join(self, gid: int, slot: Optional[int]) -> None:
        pass

    @request('room:leave')
    def leave(self) -> None:
        pass

    @request('room:users')
    def users(self, gid: int) -> None:
        pass

    @request('room:get-ready')
    def get_ready(self) -> None:
        pass

    @request('room:cancel-ready')
    def cancel_ready(self) -> None:
        pass

    @request('room:change-location')
    def change_location(self, loc: int) -> None:
        pass


class Observe(object):
    def __init__(self, core):
        self.core = core

    @request('ob:observe')
    def observe(self, uid: int) -> None:
        pass

    @request('ob:grant')
    def grant(self, uid: int, grant: bool) -> None:
        pass

    @request('ob:kick')
    def kick(self, uid: int) -> None:
        pass

    @request('ob:leave')
    def leave(self) -> None:
        pass


class Invite(object):
    def __init__(self, core):
        self.core = core

    @request('invite:invite')
    def invite(self, uid: int) -> None:
        pass

    @request('invite:kick')
    def kick(self, uid: int) -> None:
        pass


class Game(object):
    def __init__(self, core):
        self.core = core

    @request('game:set-param')
    def set_param(self, key: str, value: Union[int, str, bool]) -> None:
        pass

    @request('game:data')
    def data(self, gid: int, serial: int, tag: str, data: Any) -> None:
        pass


class Item(object):
    def __init__(self, core):
        self.core = core

    @request('item:use')
    def use(self, sku: str) -> None:
        pass


class Request(object):
    def __init__(self, core):
        self.core = core

        self.room   = Room(core)
        self.ob     = Observe(core)
        self.invite = Invite(core)
        self.game   = Game(core)
        self.item   = Item(core)
