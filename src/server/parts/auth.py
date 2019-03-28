# -*- coding: utf-8 -*-

# -- stdlib --
from typing import TYPE_CHECKING, Tuple, Sequence
import logging

# -- third party --
# -- own --
from server.endpoint import Client
from server.utils import command
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

    @command('connected')
    def _auth(self, u: Client, m: wiremsg.Auth) -> None:
        core = self.core
        token = m.token

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
            u.write(wiremsg.AuthError('invalid_credentials'))
            return

        rst = rst['player']

        if not rst['user']['isActive']:
            u.write(wiremsg.AuthError('not_available'))
        else:
            uid = int(rst['id'])
            u.write(wiremsg.AuthSuccess(uid))
            u._[self] = {
                'uid': uid,
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

    def set_auth(self, u: Client, uid: int = 1, name: str = 'Foo', kedama: bool = False, permissions: Sequence[str] = []) -> None:
        u._[self] = {
            'uid': uid,
            'name': name,
            'kedama': kedama,
            'permissions': set(permissions),
        }
