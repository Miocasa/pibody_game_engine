from .space_invaders import run_space_invaders
from .pong import run_pong
from engine import iotest
from game import run_game

def empty_func(*args):
    pass

class GameInfo:
    def __init__(
        self,
        name: str = "Not named",
        call_func = empty_func,
        save_file: str = "", #TODO! save system implemented in engine
    ):
        self.name      = name
        self.call_func = call_func
        self.save_file = save_file


GamesInfoList: list[GameInfo] = [
    GameInfo(
        name      = "Space Invaders",
        call_func = run_space_invaders,
        save_file = ""
    ),
    GameInfo(
        name      = "Ping Pong",
        call_func = run_pong,
        save_file = ""
    ),
    GameInfo(
        name      = "Test In/Out",
        call_func = iotest.run, #! iotest.run will return error: TypeError: 'module' object isn't callable
        save_file = ""
    ),
    GameInfo(
        name      = "Test stability",
        call_func = run_game,
        save_file = ""
    ),
    GameInfo(
        name      = "Test empty game",
        call_func = empty_func,
        save_file = ""
    ),
]