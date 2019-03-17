from mypy_extensions import TypedDict
from typing import List, Dict, Any


class User(TypedDict):
    uid: int
    name: str
    state: str


class Game(TypedDict):
    gid: int
    type: str
    name: str
    started: bool
    online: int


class GameDetail(Game):
    users: List[User]
    params: Dict[str, Any]
    items: Dict[int, List[str]]
