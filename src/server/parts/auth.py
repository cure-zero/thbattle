# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
import logging

# -- third party --
# -- own --
from server.utils import command


# -- code --
log = logging.getLogger('Auth')


class Auth(object):
    def __init__(self, core):
        self.core = core
        self._kedama_uid = -10032

        core.events.user_state_transition += self.handle_user_state_transition
        core.events.client_command['auth'] += self._auth

    def handle_user_state_transition(self, ev):
        c, f, t = ev

        if (f, t) == ('initial', 'connected'):
            from settings import VERSION
            core = self.core
            c.write(['thbattle_greeting', (core.options.node, VERSION)])
            c._[self] = {
                'uid': 0,
                'name': '',
                'kedama': False,
                'permissions': set(),
            }

        return ev

    # ----- Command -----
    @command(['connected'], [str])
    def _auth(self, c, token):
        core = self.core
        rst = core.backend.query('''
            query($token: String) {
                player(token: $token) {
                    id
                    user {
                        isActive
                        userPermissions {
                            codename
                        }
                        groups {
                            permissions {
                                codename
                            }
                        }
                    }
                    name
                }
            }
        ''', token=token)

        if not rst or rst['player']:
            c.write(['auth:error', {'error': 'invalid_credential'}])
            return

        rst = rst['player']

        if not rst['user']['isActive']:
            c.write(['auth:error', {'error': 'not_available'}])
        else:
            c.write(['auth:result', {'uid': rst['id'], 'name': rst['name']}])
            c._[self] = {
                'uid': int(rst['id']),
                'name': rst['name'],
                'kedama': False,
                'permissions': set(
                    [i['codename'] for i in rst['user']['userPermissions']] +
                    [i['codename'] for i in rst['user']['groups']['permissions']]
                ),
            }
            core.lobby.state_of(c).transit('authed')

    # ----- Public Methods -----
    def uid_of(self, c):
        return c._[self]['uid']

    def name_of(self, c):
        return c._[self]['name']

    def is_kedama(self, c):
        return c._[self]['kedama']

    # ----- Auxiliary Methods -----
    def set_auth(self, c, uid=1, name='Foo', kedama=False, permissions=[]):
        '''
        Used by tests
        '''
        core = self.core
        assert core.lobby.state_of(c) == 'connected'
        c._[self] = {
            'uid': uid,
            'name': name,
            'kedama': kedama,
            'permissions': set(permissions),
        }
        core.lobby.state_of(c).transit('authed')
