import math
import random
from time import sleep_ms # type: ignore
import _thread

from engine import (
    DisplayDriver, Game, World, Actor,
    Color, Font, GameImage, Buzzer
)

#* Display driver -- replace with your adapter (SSD1306Driver, ILI9341Driver, FrameBufDriver ...)
from engine.display_drivers.st7789_adapter import ST7789Driver # default driver
from engine import Input

local_in: Input = Input()
sound = Buzzer()

# Game constants
CELL          = 1          # cell size (pixel world)
SCREEN_W      = 310        # display width -- adjust for your display
SCREEN_H      = 230        # display height
PLAYER_SPEED  = 2          # ship speed (px/tick)
BULLET_SPEED  = 4          # player bullet speed
ALIEN_ROWS    = 3          # alien rows
ALIEN_COLS    = 8          # alien columns
ALIEN_W       = 16         # alien sprite width
ALIEN_H       = 10         # alien sprite height
ALIEN_X_GAP   = 4          # horizontal gap
ALIEN_Y_GAP   = 6          # vertical gap
ALIEN_STEP    = 2          # movement step in X
ALIEN_DROP    = 8          # drop on direction change
ALIEN_FIRE_P  = 3          # fire probability (1/N per tick)
ALIEN_SPEED   = 4          # ticks between alien steps (lower = faster)
BUNKER_COUNT  = 3          # number of bunkers
BUNKER_HP     = 8          # bunker hit points

# Colors
C_BG         = Color(0,   0,   0)
C_PLAYER     = Color(0,   220, 50)
C_BULLET     = Color(255, 255, 0)
C_ALIEN_TOP  = Color(200, 100, 255)
C_ALIEN_MID  = Color(100, 200, 255)
C_ALIEN_BOT  = Color(255, 130,  50)
C_ALIEN_BOMB = Color(255,  50,  50)
C_BUNKER     = Color( 50, 180,  50)
C_TEXT       = Color(255, 255, 255)
C_UFO        = Color(255,  50, 100)


# Sprite helpers
def _make_image(w: int, h: int, color: Color, shape: str = "rect") -> GameImage:
    """Create a simple sprite of the given shape."""
    img = GameImage(w, h)
    img.set_color(color)
    if shape == "rect":
        img.fill_rect(0, 0, w, h)
    elif shape == "oval":
        img.fill_oval(0, 0, w, h)
    elif shape == "ship":
        _draw_ship(img, color, w, h)
    elif shape == "alien1":
        _draw_alien1(img, color, w, h)
    elif shape == "alien2":
        _draw_alien2(img, color, w, h)
    elif shape == "alien3":
        _draw_alien3(img, color, w, h)
    return img


def _draw_ship(img: GameImage, c: Color, w: int, h: int):
    """Triangle ship sprite."""
    img.set_color(c)
    # hull
    img.fill_rect(w // 4, h // 2, w // 2, h // 2)
    # nose (pyramid)
    for row in range(h // 2):
        left  = w // 2 - row - 1
        right = w // 2 + row + 1
        img.draw_line(left, h // 2 - row, right, h // 2 - row)
    # gun (1px)
    img.set_color(c)
    img.fill_rect(w // 2 - 1, 0, 2, h // 4)


def _draw_alien1(img: GameImage, c: Color, w: int, h: int):
    """Top-row alien: crab."""
    img.set_color(c)
    img.fill_rect(2, 2, w - 4, h - 4)
    # antennae
    img.fill_rect(0, 0, 2, 3)
    img.fill_rect(w - 2, 0, 2, 3)
    # legs
    img.fill_rect(0, h - 4, 3, 4)
    img.fill_rect(w - 3, h - 4, 3, 4)
    # eyes
    img.set_color(Color.WHITE)
    img.fill_rect(3, 3, 2, 2)
    img.fill_rect(w - 5, 3, 2, 2)


def _draw_alien2(img: GameImage, c: Color, w: int, h: int):
    """Mid-row alien: jellyfish."""
    img.set_color(c)
    img.fill_oval(1, 1, w - 2, h - 4)
    # tentacles
    for i in range(4):
        img.fill_rect(2 + i * ((w - 4) // 3), h - 4, 2, 4)


def _draw_alien3(img: GameImage, c: Color, w: int, h: int):
    """Bottom-row alien: spider."""
    img.set_color(c)
    img.fill_rect(1, h // 4, w - 2, h // 2)
    # legs
    for i in range(3):
        x = 0 + i * (w // 3)
        img.draw_line(x, 0, w // 2, h // 4)
        img.draw_line(x, h, w // 2, h * 3 // 4)


# Actors
class Player(Actor):
    SHIP_W = 20
    SHIP_H = 12

    def __init__(self):
        super().__init__()
        img = _make_image(self.SHIP_W, self.SHIP_H, C_PLAYER, "ship")
        self.set_image(img)
        self._cooldown  = 0
        self._fire_lock = False   # button debounce

    def act(self):
        world:World = self.get_world()
        x = self.get_x()
        # movement
        if local_in.is_left():
            x = max(self.SHIP_W // 2, x - PLAYER_SPEED)
        if local_in.is_right():
            x = min(SCREEN_W - self.SHIP_W // 2, x + PLAYER_SPEED)
        self.set_location(x, self.get_y())
        # fire
        fire_now = local_in.is_A()
        if fire_now and not self._fire_lock and self._cooldown == 0:
            world.add_object(PlayerBullet(), int(x + Player.SHIP_W / 2), self.get_y() - self.SHIP_H // 2)
            self._cooldown  = 15
            self._fire_lock = True
        if not fire_now:
            self._fire_lock = False
        if self._cooldown > 0:
            self._cooldown -= 1


class PlayerBullet(Actor):
    def __init__(self):
        super().__init__()
        img = GameImage(2, 8)
        img.set_color(C_BULLET)
        img.fill_rect(0, 0, 2, 8)
        self.set_image(img)

    def act(self):
        if self.get_world() is None:
            return
        y = self.get_y() - BULLET_SPEED
        if y < 0:
            self.get_world().remove_object(self)
            return
        self.set_location(self.get_x(), y)

        world = self.get_world()

        hit = self.get_one_intersecting_object(Alien)
        if hit:
            world.remove_object(self)
            world.score_kill(hit)
            world.remove_object(hit)
            world.play_alien_hit()
            return

        hit = self.get_one_intersecting_object(Bunker)
        if hit:
            world.remove_object(self)
            hit.damage()
            return

        hit = self.get_one_intersecting_object(UFO)
        if hit:
            world.remove_object(self)
            world.score_ufo()
            world.remove_object(hit)
            world.play_ufo_hit()
            return

class AlienBomb(Actor):
    BOMB_SPEED = 3

    def __init__(self):
        super().__init__()
        img = GameImage(3, 8)
        img.set_color(C_ALIEN_BOMB)
        img.fill_rect(0, 0, 3, 8)
        self.set_image(img)

    def act(self):
        y = self.get_y() + self.BOMB_SPEED
        if y > SCREEN_H:
            self.get_world().remove_object(self)
            return
        self.set_location(self.get_x(), y)

        hit = self.get_one_intersecting_object(Player)
        if hit:
            self.get_world().player_hit()
            self.get_world().remove_object(self)
            return

        hit = self.get_one_intersecting_object(Bunker)
        if hit:
            self.get_world().remove_object(self)
            hit.damage()


class Alien(Actor):
    def __init__(self, row: int, col: int):
        super().__init__()
        self.row = row
        self.col = col
        if row == 0:
            shape, color = "alien1", C_ALIEN_TOP
        elif row == 1:
            shape, color = "alien2", C_ALIEN_MID
        else:
            shape, color = "alien3", C_ALIEN_BOT
        self.set_image(_make_image(ALIEN_W, ALIEN_H, color, shape))

    def act(self):
        pass   # movement controlled by World via AlienFleet


class UFO(Actor):
    UFO_W = 24
    UFO_H = 10
    SPEED = 1

    def __init__(self, direction: int = 1):
        super().__init__()
        self._dir = direction
        img = GameImage(self.UFO_W, self.UFO_H)
        img.set_color(C_UFO)
        img.fill_oval(0, 2, self.UFO_W, self.UFO_H - 4)
        img.set_color(Color.WHITE)
        img.fill_rect(self.UFO_W // 2 - 4, 0, 8, 4)
        self.set_image(img)

    def act(self):
        x = self.get_x() + self._dir * self.SPEED
        if x < 0 or x > SCREEN_W:
            self.get_world().remove_object(self)
            return
        self.set_location(x, self.get_y())


class Bunker(Actor):
    W = 20
    H = 10

    def __init__(self):
        super().__init__()
        self._hp = BUNKER_HP
        self._rebuild()

    def _rebuild(self):
        ratio = self._hp / BUNKER_HP
        r = int(C_BUNKER.r * ratio)
        g = int(C_BUNKER.g * ratio)
        b = int(C_BUNKER.b * ratio)
        img = GameImage(self.W, self.H)
        img.set_color(Color(r, g, b))
        img.fill_rect(0, 0, self.W, self.H)
        self.set_image(img)

    def damage(self):
        self._hp -= 1
        if self._hp <= 0:
            self.get_world().remove_object(self)
        else:
            self._rebuild()


# Game Over / Win overlay
class MessageActor(Actor):
    """Text message rendered on top of the scene."""
    W = 100
    H = 30

    def __init__(self, lines: list, color: Color = C_TEXT):
        super().__init__()
        img = GameImage(self.W, self.H)
        img.set_color(Color(0, 0, 0))
        img.fill_rect(0, 0, self.W, self.H)
        # text is rendered via DisplayDriver.text(), not draw_string
        self.set_image(img)
        self._lines  = lines
        self._color  = color

    def act(self):
        if local_in.is_A():
            drv = self.get_world().get_display()
            if drv:
                drv.fill(drv.BLACK)
            from engine.GameEngine import Game
            Game.set_world(SpaceInvadersWorld(sound=sound))

# World
class SpaceInvadersWorld(World):
    def __init__(self, sound=None):
        super().__init__(SCREEN_W, SCREEN_H, CELL, bounded=False)
        self.set_background(C_BG)
        
        self._sound:Buzzer = sound # type: ignore
        self._score = 0
        self._lives = 3
        self._over = False
        self._won = False
        self._ticks = 0
        self._ufo_timer = 0
        self._alien_dir = 1
        self._alien_move_tick = 0
        self._aliens_speed = ALIEN_SPEED
        
        self._btn_b_lock = False
        self.playing_sound = False
        self._fleet: list[Alien] = []
        start_x = 20
        start_y = 20
        for row in range(ALIEN_ROWS):
            for col in range(ALIEN_COLS):
                a = Alien(row, col)
                px = start_x + col * (ALIEN_W + ALIEN_X_GAP) + ALIEN_W // 2
                py = start_y + row * (ALIEN_H + ALIEN_Y_GAP) + ALIEN_H // 2
                self.add_object(a, px, py)
                self._fleet.append(a)

        bunker_y = SCREEN_H - 30
        spacing = SCREEN_W // (BUNKER_COUNT + 1)
        for i in range(BUNKER_COUNT):
            b = Bunker()
            self.add_object(b, spacing * (i + 1), bunker_y)

        self._player = Player()
        self.add_object(self._player, SCREEN_W // 2, SCREEN_H - 14)

        self.set_paint_order(MessageActor, Player, PlayerBullet,
                            AlienBomb, UFO, Alien, Bunker)

    # ====================== Sound ======================
    def _alien_hit(self):
        self.playing_sound = True
        self._sound.make_sound(1200, 0.7, 0.04)
        sleep_ms(20)
        self._sound.make_sound(800, 0.5, 0.06)
        self.playing_sound = False
        
    def play_alien_hit(self):
        if self._sound and not self.playing_sound:
            _thread.start_new_thread(
                self._alien_hit,
                ()
            )

    def play_ufo_hit(self):
        if self._sound and not self.playing_sound:
            _thread.start_new_thread(
                self._sound.play_melody,
                (["C6", "E6", "G6"], 0.08)
            )

    def _player_hit(self): # wraper
        self.playing_sound = True
        self._sound.make_sound(200, 0.9, 0.15)
        sleep_ms(50)
        self._sound.make_sound(150, 0.8, 0.2)
        self.playing_sound = False

    def play_player_hit(self):
        if self._sound and not self.playing_sound:
            _thread.start_new_thread(
                self._player_hit,
                ()
            )

    def play_melody(self, melody, tempo = 0.3):
        self.playing_sound = True
        self._sound.play_melody(melody, tempo)
        self.playing_sound = False

    def play_win_melody(self):
        if self._sound and not self.playing_sound:
            
            _thread.start_new_thread(
                self.play_melody, 
                (["C5","E5","G5","C6","E6","G6"], 0.12)
            )

    def play_lose_melody(self):
        if self._sound and not self.playing_sound:
            _thread.start_new_thread(
                self.play_melody,
                (["A4", "F4", "D4", "A3"], 0.25)
            )



    # ====================== main logic ======================
    def score_kill(self, alien: Alien):
        pts = (ALIEN_ROWS - alien.row) * 10
        self._score += pts
        self._fleet = [a for a in self._fleet if a is not alien]
        self._aliens_speed = max(1, ALIEN_SPEED - (ALIEN_ROWS*ALIEN_COLS - len(self._fleet)) // 4)
        self._draw_hud()
        if not self._fleet:
            self._win()

    def score_ufo(self):
        self._score += 100
        self._draw_hud()

    def player_hit(self):
        self._lives -= 1
        self._draw_hud()
        self.play_player_hit()
        if self._lives <= 0:
            self._game_over()


    # Main world loop
    def act(self):
        if self._over or self._won:
            return
        
        # close game any time using B button
        if local_in.is_B():
            if not self._btn_b_lock:
                self._btn_b_lock = True
                drv = Game._display
                if drv:
                    drv.fill(drv.BLACK)
                    drv.show()
                Game._running = False
                return
        else:
            self._btn_b_lock = False
    
    
        self._ticks += 1
        self._move_fleet()
        self._alien_fire()
        self._ufo_logic()
        # redraw HUD every 30 ticks to save cycles
        if self._ticks % 30 == 0:
            self._draw_hud()

    # Fleet movement
    def _move_fleet(self):
        self._alien_move_tick += 1
        if self._alien_move_tick < self._aliens_speed:
            return
        self._alien_move_tick = 0
        if not self._fleet:
            return
        xs    = [a.get_x() for a in self._fleet]
        min_x = min(xs)
        max_x = max(xs)
        drop  = False
        if self._alien_dir == 1 and max_x + ALIEN_W // 2 + ALIEN_STEP >= SCREEN_W:
            drop = True
        elif self._alien_dir == -1 and min_x - ALIEN_W // 2 - ALIEN_STEP <= 0:
            drop = True
        if drop:
            self._alien_dir = -self._alien_dir
            for a in self._fleet:
                a.set_location(a.get_x(), a.get_y() + ALIEN_DROP)
                # reached bottom -- game over
                if a.get_y() >= SCREEN_H - 40:
                    self._game_over()
                    return
        else:
            for a in self._fleet:
                a.set_location(a.get_x() + self._alien_dir * ALIEN_STEP, a.get_y())

    # Alien bombing
    def _alien_fire(self):
        if not self._fleet:
            return
        if random.randint(0, ALIEN_FIRE_P * len(self._fleet)) == 0:
            shooter = random.choice(self._fleet)
            self.add_object(AlienBomb(), shooter.get_x(), shooter.get_y() + ALIEN_H)

    # UFO logic
    def _ufo_logic(self):
        self._ufo_timer += 1
        if self._ufo_timer > 500 and random.randint(0, 200) == 0:
            self._ufo_timer = 0
            direction = random.choice([-1, 1])
            ufo = UFO(direction)
            start_x = 0 if direction == 1 else SCREEN_W
            self.add_object(ufo, start_x, 8)

    # HUD
    def _draw_hud(self):
        drv = Game._display
        if drv is None:
            return
        drv.fill_rect(0, 0, SCREEN_W, 10, C_BG.pack())
        score_txt = "SCR:{} LV:{}".format(self._score, self._lives)
        drv.print(score_txt, 2, 1, C_TEXT.pack(), 1)

    # End game
    def _game_over(self):
        self._over = True
        self.play_lose_melody()
        self._show_message(["GAME OVER", "Score: {}".format(self._score), "A/B restart"])

    def _win(self):
        self._won = True
        self.play_win_melody()
        self._show_message(["YOU WIN!", "Score: {}".format(self._score), "A/B restart"])

    def _show_message(self, lines: list):
        drv = Game._display
        if drv is None:
            return
        bx = SCREEN_W // 2 - 55
        by = SCREEN_H // 2 - 18
        drv.fill_rect(bx, by, 110, 36, Color(20, 20, 60).pack())
        drv.rect(bx, by, 110, 36, C_TEXT.pack())
        for i, line in enumerate(lines):
            drv.print(line, bx + 4, by + 3 + i * 11, C_TEXT.pack(), 1)
        drv.show()
        msg = MessageActor(lines)
        self.add_object(msg, SCREEN_W // 2, SCREEN_H // 2)
        
def run_space_invaders(display=None, input=None):
    if display is None:
        display = ST7789Driver(rotation=1)
    if input is None:
        local_in = input
    

    world = SpaceInvadersWorld(sound=sound)
    Game.init(display, world, sound=sound)
    # Game.set_speed(60)

    Game._running = True
    while Game._running:
        if Game._world:
            Game._world.act()
            for actor in list(Game._world._actors):
                actor.act()
            Game._world._render()
        sleep_ms(16)

if __name__ == "__main__":
    run_space_invaders()