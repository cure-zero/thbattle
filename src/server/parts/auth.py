# -*- coding: utf-8 -*-

# -- stdlib --
from typing import TYPE_CHECKING, Tuple
import logging

# -- third party --
# -- own --
from server.endpoint import Client
from server.utils import for_state
from wire import msg as wiremsg

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Auth')


class Auth(object):
    def __init__(self, core: 'Core'):
        self.core = core
        self._kedama_uid = -10032

        core.events.user_state_transition += self.handle_user_state_transition
        D = core.events.client_command
        D[wiremsg.Auth] += self._auth

    def handle_user_state_transition(self, ev: Tuple[Client, str, str]) -> Tuple[Client, str, str]:
        u, f, t = ev

        if (f, t) == ('initial', 'connected'):
            from settings import VERSION
            core = self.core
            u.write(wiremsg.Greeting(node=core.options.node, version=VERSION))
            u._[self] = {
                'uid': 0,
                'name': '',
                'kedama': False,
                'permissions': set(),
            }

        return ev

    # ----- Command -----
    @for_state('connected')
    def _auth(self, ev: Tuple[Client, wiremsg.Auth]) -> Tuple[Client, wiremsg.Auth]:
        core = self.core
        u, auth = ev
        token = auth.token

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
            u.write(['auth:error', {'error': 'invalid_credential'}])
            return

        rst = rst['player']

        if not rst['user']['isActive']:
            u.write(['auth:error', {'error': 'not_available'}])
        else:
            u.write(['auth:result', {'uid': rst['id'], 'name': rst['name']}])
            u._[self] = {
                'uid': int(rst['id']),
                'name': rst['name'],
                'kedama': False,
                'permissions': set(
                    [i['codename'] for i in rst['user']['userPermissions']] +
                    [i['codename'] for i in rst['user']['groups']['permissions']]
                ),
            }
            core.lobby.state_of(u).transit('authed')

    # ----- Public Methods -----
    def uid_of(self, u: Client) -> int:
        return u._[self]['uid']

    def name_of(self, u: Client) -> str:
        return u._[self]['name']

    def is_kedama(self, u: Client) -> bool:
        return u._[self]['kedama']

    def set_auth(self, u: Client, uid=1, name='Foo', kedama=False, permissions=[]) -> None:
        u._[self] = {
            'uid': uid,
            'name': name,
            'kedama': kedama,
            'permissions': set(permissions),
        }
