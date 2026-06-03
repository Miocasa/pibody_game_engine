import math
import random
from micropython import const # type: ignore
from time import sleep_ms     # type: ignore

from engine import (
    DisplayDriver, Color, GameImage,
    Game, World, Actor,
    st7789, Input,
)


class GameWorld(World):
    def __init__(self, width, height, input_handler):
        super().__init__(width, height, cell_size=1, input=input_handler, bounded=True)
        
        self._score = 0
        self._player = Player(20, 20, Color.RED)
        self.add_object(self._player, 30, 30)

    def act(self):
        pass

    def draw_ui(self):
        drv = Game._display
        if drv is None:
            return

        
        (tw, th) = const(drv.get_text_size("Score: "))
        (sw, _) = const(drv.get_text_size(f"{self._score}"))
        drv.fill_rect(8 + tw, 2, sw, th, drv.BLACK)
        drv.print(f"Score: {self._score}", 8, 6, drv.YELLOW, font=drv.FONT_MEDIUM)
        

class Player(Actor):
    def __init__(self, width: int, height: int, color: Color):
        super().__init__()

        img = GameImage(width, height)
        img.set_color(color)
        img.fill_rect(0, 0, width, height)
        
        img.set_color(Color.WHITE)
        img.draw_rect(0, 0, width, height)
        
        self.set_image(img)

    def act(self):
        wrld = self.get_world()
        if wrld.input.is_B():
            Game._running = False
            return
        if wrld.input.is_A():
            self.set_rotation(25)
            self.move_with_rotation(-20)
        speed = 4
        x = self._x
        y = self._y

        if wrld.input.is_left():  x -= speed
        if wrld.input.is_right(): x += speed
        if wrld.input.is_up():    y -= speed
        if wrld.input.is_down():  y += speed

        x = max(0, min(wrld.get_width() - self.get_width(), x))
        y = max(0, min(wrld.get_height() - self.get_height(), y))

        self.set_location(x, y)
        pass


def run_game(display = None, input = None):
    if input == None:
        input = Input()
    if display == None:
        display = st7789()
    

    world = GameWorld(display.width, display.height, input)

    Game._running = True
    Game.init(display, world, sound=None, fps=40, ui_fps=10)
    Game.start()

    Game.run()


if __name__ == "__main__":
    run_game(st7789(), Input())