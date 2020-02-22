# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Callable, Dict
import logging

# -- third party --
from gevent.event import AsyncResult, Event
from gevent.greenlet import Greenlet
from gevent.pool import Pool

# -- own --

# -- code --
log = logging.getLogger('core')


class Core(object):
    core_type = ''
    _auto_id = 0

    runner: CoreRunner

    def __init__(self, **options: Dict[str, Any]):
        self._auto_id = Core._auto_id
        Core._auto_id += 1

        self._result = AsyncResult()
        self.tasks: Dict[str, Callable[[], None]] = {}
        self.options = options

    def __repr__(self) -> str:
        return f'Core[{self.core_type}{self._auto_id}]'

    @property
    def result(self):
        return self._result

    def crash(self, e):
        self._result.set_exception(e)

    def initialize(self, options: Dict[str, Any]) -> None:
        raise Exception('Abstract')


class CoreCrashed(Exception):
    pass


class CoreRunner(object):
    def __init__(self, core: Core, paranoid: bool = False):
        self.core = core
        self.pool = Pool()
        self.ready = Event()
        self.tasks: Dict[str, Greenlet] = {}

        self._paranoid = paranoid

    def run(self) -> Any:
        core = self.core

        core.runner = self
        core.initialize(core.options)

        try:
            for k, f in core.tasks.items():
                log.debug('Spawning task [%s] for core %s', k, core)
                gr = self.pool.spawn(f)
                gr.gr_name = k
                self.tasks[k] = gr

            self.ready.set()
            try:
                return core.result.get()
            except BaseException as e:
                raise CoreCrashed(f'{core} crashed') from e
        finally:
            self.shutdown()

    def spawn(self, fn, *args, **kw):
        core = self.core
        gr = self.pool.spawn(fn, *args, **kw)
        if self._paranoid:
            gr.link_exception(lambda gr: core.crash(gr.exception))
        return gr

    def start(self, gr):
        core = self.core
        self.pool.start(gr)
        if self._paranoid:
            gr.link_exception(lambda gr: core.crash(gr.exception))
        return gr

    def shutdown(self) -> None:
        self.pool.kill()
