# -*- coding: utf-8 -*-

# update-url: points to git repo
# server has version, and a branch name(eg 'production', 'testing').
# client always tracks corresponding branch.
#
# replay: saves current commit sha1 as version.
# when playing, switch to that version.

# -- stdlib --
from threading import RLock
import logging

# -- third party --
from gevent.hub import get_hub
import gevent

# -- own --

# -- code --
log = logging.getLogger('client.core.parts.update')


class GitUpdator(object):
    def __init__(self, core, base, url=None):
        self.base = base
        self.core = core

        import pygit2
        self.repo = pygit2.Repository(self.base)
        url and self.set_update_url(url)

    @property
    def remote(self):
        for remote in self.repo.remotes:
            if remote.name == 'origin':
                return remote

        raise AttributeError

    def set_update_url(self, url):
        remote = self.remote
        self.repo.remotes.set_url(remote.name, url)

    def update(self):
        core = self.core
        hub = get_hub()
        noti = hub.loop.async()
        lock = RLock()
        stats = []

        def progress(s):
            with lock:
                stats.append(s)
                noti.send()

        remote = self.remote
        remote.transfer_progress = progress

        def do_fetch():
            try:
                return remote.fetch()
            except Exception as e:
                return e

        fetch = hub.threadpool.spawn(do_fetch)
        noti_w = gevent.spawn(lambda: hub.wait(noti))

        try:
            while True:
                for r in gevent.iwait([noti_w, fetch]):
                    break

                if r is fetch:
                    rst = r.get()
                    if isinstance(rst, Exception):
                        core.events.update_error.emit((self, rst))

                    return

                v = None
                with lock:
                    if stats:
                        v = stats[-1]

                    stats[:] = []

                if v:
                    core.events.update_progress.emit((self, v))
        finally:
            noti_w.kill()

    def switch(self, version):
        import pygit2
        repo = self.repo
        try:
            desired = repo.revparse_single(version)
        except KeyError:
            return False

        repo.reset(desired.id, pygit2.GIT_RESET_HARD)
        return True

    def is_version_match(self, version):
        repo = self.repo
        try:
            current = repo.revparse_single('HEAD')
            desired = repo.revparse_single(version)
            return current.id == desired.id
        except KeyError:
            return False

    def get_current_version(self):
        current = self.repo.revparse_single('HEAD')
        return current.id.hex

    def is_version_present(self, version):
        try:
            self.repo.revparse_single(version)
            return True
        except KeyError:
            return False


class Update(object):
    def __init__(self, core):
        self.core = core

    def get_updator(self, name, base, src):
        core = self.core
        return GitUpdator(core, name, base, src)

    def resolve_update_url(self, server_name):
        from gevent.pool import Group

        group = Group()

        def local():
            import dns.resolver
            return dns.resolver.query(server_name, 'TXT').response

        def recursive():
            import dns.resolver
            from settings import NAME_SERVER
            ns = dns.resolver.query(NAME_SERVER, 'NS').response.answer[0]
            ns = ns.items[0].target.to_text()

            import socket
            ns = socket.gethostbyname(ns)

            import dns.message
            import dns.query
            q = dns.message.make_query(server_name, 'TXT')

            return dns.query.udp(q, ns)

        def public(ns):
            def _public():
                import dns.message
                import dns.query
                q = dns.message.make_query(server_name, 'TXT')
                return dns.query.udp(q, ns)

            return _public

        workers = [group.apply_async(i) for i in [
            local,
            recursive,
            public('119.29.29.29'),
            public('223.5.5.5'),
            public('114.114.114.114'),
            public('1.1.1.1'),
            public('8.8.8.8'),
        ]]

        for result in gevent.iwait(workers, 10):
            if result.successful():
                result = result.value
                break

            else:
                log.exception(result.exception)

        else:
            group.kill()
            return False

        group.kill()
        result = result.answer[0]
        url = result.items[0].strings[0]
        return url
