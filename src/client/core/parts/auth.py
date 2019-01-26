# -*- coding: utf-8 -*-


# -- stdlib --
# -- third party --
# -- own --
from utils.events import EventHub


# -- code --
class Auth(object):
    def __init__(self, core):
        self.core = core
        core.events.server_command += self.handle_server_command

        self.uid = 0
        self.name = ''

    def handle_server_command(self, ev):
        cmd, arg = ev
        if cmd == 'auth:result':
            core = self.core
            self.uid = arg['uid']
            self.name = arg['name']
            core.events.auth.emit((True, arg))
            return EventHub.STOP_PROPAGATION

        elif cmd == 'auth:error':
            core.events.auth.emit((False, arg))
            return EventHub.STOP_PROPAGATION

        return ev

    # ----- Public Methods -----
    def login(self, token):
        core = self.core
        core.server.write(['auth', token])
