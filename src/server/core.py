# -*- coding: utf-8 -*-


# -- stdlib --
from collections import defaultdict

# -- third party --
# -- own --
from . import parts
from .base import Game
from .endpoint import Client
from game.base import Packet
from utils.events import EventHub


# -- code --
class Options(object):
    def __init__(self, options):
        self.node         = options.get('node', 'localhost')  # Current node name
        self.backend      = options.get('backend', '')        # Backend URI
        self.interconnect = options.get('interconnect', '')   # URI of chat server
        self.archive_path = options.get('archive_path', '')   # file:// URI of dir for storing game archives
        self.disables     = options.get('disables', [])       # disabled core components, will assign a None value


class Events(object):
    def __init__(self):
        # ev = (core: Core)
        self.core_initialized = EventHub([Core])

        # Fires when user state changes,
        # ev = (c: Client, from: str, to: str)
        self.user_state_transition = EventHub([Client, str, str])

        # Client connected
        self.client_connected = EventHub(Client)

        # Client dropped(connection lost)
        self.client_dropped = EventHub(Client)

        # Client logged in when previous login still online, or still in active game
        # ev = c: Client  # old client obj with new connection `pivot_to`ed to it
        self.client_pivot = EventHub(Client)

        # Client send some command
        # ev = (c: Client, args: (...))
        self.client_command = defaultdict(lambda: EventHub([Client, []]))

        # Game is created
        # ev = g: Game
        self.game_created = EventHub(Game)

        # Received client game data
        # ev = (g: Game, u: Client, pkt: Packet)
        self.game_data_recv = EventHub([Game, Client, Packet])

        # Fires after old game ended and new game created.
        # Actors should copy settings from old to new
        # ev = (old: Game, g: Game)
        self.game_successive_create = EventHub([Game, Game])

        # All the things are ready, waiting UI to prepare and ignite
        # ev = (g: Game)
        self.game_prepared = EventHub(Game)

        # Game started running
        # ev = (g: Game)
        self.game_started = EventHub(Game)

        # Client joined a game
        # ev = (g: Game, c: Client)
        self.game_joined = EventHub([Game, Client])

        # Client left a game
        # ev = (g: Game, c: Client)
        self.game_left = EventHub([Game, Client])

        # Game was ended, successfully or not.
        # ev = (g: Game)
        self.game_ended = EventHub(Game)

        # Game ended in half way.
        # This fires before GAME_ENDED
        # ev = (g: Game)
        self.game_killed = EventHub(Game)


class Core(object):
    def __init__(self, **options):
        self.options = Options(options)

        self.events = Events()

        disables = self.options.disables
        self.auth    = parts.auth.Auth(self) if 'auth' not in disables else None
        self.lobby   = parts.lobby.Lobby(self) if 'lobby' not in disables else None
        self.room    = parts.room.Room(self) if 'room' not in disables else None
        self.game    = parts.game.Game(self) if 'game' not in disables else None
        self.observe = parts.observe.Observe(self) if 'observe' not in disables else None
        self.invite  = parts.invite.Invite(self) if 'invite' not in disables else None
        self.items   = parts.items.Items(self) if 'items' not in disables else None
        self.reward  = parts.reward.Reward(self) if 'reward' not in disables else None
        self.match   = parts.match.Match(self) if 'match' not in disables else None
        self.admin   = parts.admin.Admin(self) if 'admin' not in disables else None
        self.kedama  = parts.kedama.Kedama(self) if 'kedama' not in disables else None
        self.archive = parts.archive.Archive(self) if 'archive' not in disables else None
        self.hooks   = parts.hooks.Hooks(self) if 'hooks' not in disables else None
        self.connect = parts.connect.Connect(self) if 'connect' not in disables else None
        self.backend = parts.backend.Backend(self) if 'backend' not in disables else None
        self.log     = parts.log.Log(self) if 'log' not in disables else None
        self.stats   = parts.stats.Stats(self) if 'stats' not in disables else None
        self.view    = parts.view.View(self) if 'view' not in disables else None

        self.events.core_initialized.emit(self)
