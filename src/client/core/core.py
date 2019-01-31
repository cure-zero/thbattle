# -*- coding: utf-8 -*-

# -- stdlib --

# -- third party --
# -- own --
from . import parts
from .base import Game
from utils.events import EventHub


# -- code --
class Options(object):
    def __init__(self, options):
        self.no_update        = options.get('no_update', False)
        self.show_hidden_mode = options.get('show_hidden_mode', False)
        self.freeplay         = options.get('freeplay', False)
        self.disables         = options.get('disables', [])       # disabled core components, will assign a None value


class Events(object):
    def __init__(self):
        # ev = (core: Core)
        self.core_initialized = EventHub([Core])

        # Fires when server send some command
        # ev = (cmd: str, arg: object)
        self.server_command = EventHub([str, object])

        # Server connected
        self.server_connected = EventHub(None)

        # Server timed-out or actively rejects
        self.server_refused = EventHub(None)

        # Server dropped
        self.server_dropped = EventHub(None)

        # Server & client version mismatch
        self.version_mismatch = EventHub(None)

        # Update error'd
        # ev = (up: GitUpdator, rst: Exception)
        self.update_error.emit([object, Exception])

        # Update in progress
        # ev = (up: GitUpdator, stat: <SomeComplexObjectFromPyGit>)
        self.update_progress.emit([object, object])

        # Joined a game
        self.game_joined = EventHub(Game)

        # Left a game
        self.game_left = EventHub(Game)

        # Left a game
        # ev = (g: Game, users: [server.core.view.User(u), ...])
        self.room_users = EventHub([Game, [dict, ...]])

        # Server side game started, and client core has finished preparing the game,
        # ready to launch
        self.game_prepared = EventHub(Game)

        # Game is up and running
        # ev = (g: Game)
        self.game_started = EventHub(Game)

        # ev = (g: Game)
        self.game_crashed = EventHub(Game)

        # Client game finished,
        # Server will send `game_end` soon if everything goes right
        self.client_game_finished = EventHub(Game)

        # ev = (g: Game)
        self.game_ended = EventHub(Game)

        # ev = (success: bool, reason: str)
        self.auth = EventHub([bool, str])


class Core(object):
    def __init__(self, **options):
        self.options = Options(options)

        self.events = Events()

        disables = self.options.disables
        self.server   = parts.server.Server(self) if 'server' not in disables else None
        self.auth     = parts.auth.Auth(self) if 'auth' not in disables else None
        self.game     = parts.game.Game(self) if 'game' not in disables else None
        self.replay   = parts.replay.Replay(self) if 'replay' not in disables else None
        self.request  = parts.request.Request(self) if 'request' not in disables else None
        self.update   = parts.update.Update(self) if 'update' not in disables else None
        self.warpgate = parts.warpgate.Warpgate(self) if 'warpgate' not in disables else None

        self.events.core_initialized.emit(self)
