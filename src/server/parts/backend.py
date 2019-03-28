# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Any, Dict, List, TYPE_CHECKING
import logging

# -- third party --
import requests

# -- own --
# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Backend')


class BackendError(Exception):
    __slots__ = ('message', 'errors')

    def __init__(self, errors: List[Dict[str, Any]]):
        self.errors = errors
        self.message = ', '.join(
            '%s: %s' % ('.'.join(e['path']), e['message'])
            for e in errors
        )

    def __repr__(self) -> str:
        return 'BackendError(%s)' % repr(self.message)


class Backend(object):
    def __init__(self, core: 'Core'):
        self.core = core
        self._client = requests.Session()

    # ----- Public Method -----
    def query_raw(self, ql: str, **vars: Dict[str, Any]) -> dict:
        cli = self._client
        core = self.core
        resp = cli.post(core.options.backend, json={'query': ql, 'variables': vars})
        rst = resp.json()
        return rst

    def query(self, ql: str, **vars: Any) -> Dict[str, Any]:
        rst = self.query_raw(ql, **vars)
        if 'errors' in rst:
            raise BackendError(rst['errors'])

        return rst['data']
