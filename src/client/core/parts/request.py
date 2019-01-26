# -*- coding: utf-8 -*-


# -- stdlib --
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
    def create(self, mode, name, flags):
        pass

    @request('room:join')
    def join(self, gid, slot):
        pass

    @request('room:leave')
    def leave(self):
        pass

    @request('room:users')
    def users(self, gid):
        pass

    @request('room:get-ready')
    def get_ready(self):
        pass

    @request('room:cancel-ready')
    def cancel_ready(self):
        pass

    @request('room:change-location')
    def change_location(self, loc):
        pass


class Observe(object):
    def __init__(self, core):
        self.core = core

    @request('ob:observe')
    def observe(self, uid):
        pass

    @request('ob:grant')
    def grant(self, uid, grant):
        pass

    @request('ob:kick')
    def kick(self, uid):
        pass

    @request('ob:leave')
    def leave(self, ob):
        pass


class Invite(object):
    def __init__(self, core):
        self.core = core

    @request('invite:invite')
    def invite(self, uid):
        pass

    @request('invite:kick')
    def kick(self, uid):
        pass


class Game(object):
    def __init__(self, core):
        self.core = core

    @request('game:set-param')
    def set_param(self, key, value):
        pass

    @request('game:data')
    def data(self, gid, serial, tag, data):
        pass


class Item(object):
    def __init__(self, core):
        self.core = core

    @request('item:use')
    def use(self, sku):
        pass


class Request(object):
    def __init__(self, core):
        self.core = core

        self.room   = Room(core)
        self.ob     = Observe(core)
        self.invite = Invite(core)
        self.game   = Game(core)
        self.item   = Item(core)
