# -*- coding: utf-8 -*-


# -- stdlib --
import logging

# -- third party --
import requests


# -- own --
# -- code --
log = logging.getLogger('Backend')


class BackendError(Exception):
    __slots__ = ('message', 'errors')

    def __init__(self, errors):
        self.errors = errors
        self.message = ', '.join(
            '%s: %s' % ('.'.join(e['path']), e['message'])
            for e in errors
        )

    def __repr__(self):
        return 'BackendError(%s)' % repr(self.message)


class Backend(object):
    def __init__(self, core):
        self.core = core

        self._client = requests.Session()

    # ----- Public Method -----
    def query_raw(self, ql, **vars):
        cli = self._client
        core = self.core
        resp = cli.post(core.options.backend, json={'query': ql, 'variables': vars})
        rst = resp.json()
        return rst

    def query(self, ql, **vars):
        rst = self.query_raw(ql, **vars)
        if 'errors' in rst:
            raise BackendError(rst['errors'])

        return rst['data']
