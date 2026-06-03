import math
import random
from time import sleep_ms # type: ignore
from engine import (
    DisplayDriver, Color, GameImage,
    Game, World, Actor, Input, st7789,
)
from engine.Buzzer import Buzzer
CELL = 1
FPS_DELAY = 16

PADDLE_W = 6
PADDLE_H = 30
BALL_SIZE = 4

WINNING_SCORE = 7

# === AI ===
ai_speed = 1.9          #! 2.0 or more makes beating AI imposible
dead_zone = 10          # can be decreased to make ai harder, #! don't increase 
reaction_chance = 0.75

C_BG      = 0x0000
C_WHITE   = 0xFFFF
C_GREEN   = 0x07E0
C_RED     = 0xF800
C_YELLOW  = 0xFFE0
C_CYAN    = 0x07FF
C_DIVIDER = 0x2104

DIGITS = [
    [0b111, 0b101, 0b101, 0b101, 0b111],
    [0b010, 0b110, 0b010, 0b010, 0b111],
    [0b111, 0b001, 0b111, 0b100, 0b111],
    [0b111, 0b001, 0b111, 0b001, 0b111],
    [0b101, 0b101, 0b111, 0b001, 0b001],
    [0b111, 0b100, 0b111, 0b001, 0b111],
    [0b111, 0b100, 0b111, 0b101, 0b111],
    [0b111, 0b001, 0b001, 0b001, 0b001],
    [0b111, 0b101, 0b111, 0b101, 0b111],
    [0b111, 0b101, 0b111, 0b001, 0b111],
]

def draw_digit(drv, digit, x, y, scale=3, color=C_WHITE):
    rows = DIGITS[digit % 10]
    for row_i, bits in enumerate(rows):
        for col_i in range(3):
            c = color if (bits & (1 << (2 - col_i))) else C_BG
            drv.fill_rect(x + col_i * scale, y + row_i * scale, scale, scale, c)

def draw_number(drv, n, x, y, scale=3, color=C_WHITE):
    dw = 3 * scale + 2
    for ch in str(n):
        draw_digit(drv, int(ch), x, y, scale, color)
        x += dw


class Paddle(Actor):
    def __init__(self, w, h, color):
        super().__init__()
        self._pw    = w
        self._ph    = h
        self._color = color
        img = GameImage(w, h)
        hi = (color >> 8) & 0xFF
        lo = color & 0xFF
        for i in range(w * h):
            img._buf[i * 2]     = hi
            img._buf[i * 2 + 1] = lo
        self.set_image(img)

    def move_to(self, y, world_h):
        ny = max(0, min(world_h - self._ph, y))
        self.set_location(self._x, ny)


class Ball(Actor):
    def __init__(self, size):
        super().__init__()
        self._size = size
        self._vx   = 0.0
        self._vy   = 0.0
        img = GameImage(size, size)
        hi = (C_WHITE >> 8) & 0xFF
        lo = C_WHITE & 0xFF
        for i in range(size * size):
            img._buf[i * 2]     = hi
            img._buf[i * 2 + 1] = lo
        self.set_image(img)

    def reset(self, cx, cy, speed=3.0):
        self.set_location(cx - self._size // 2, cy - self._size // 2)
        angle = random.uniform(-30, 30)
        if random.randint(0, 1):
            angle += 180
        rad = math.radians(angle)
        self._vx = speed * math.cos(rad)
        self._vy = speed * math.sin(rad)


class PongWorld(World):
    def __init__(self, width, height, inp, sound=None):
        super().__init__(width, height, CELL, bounded=False)
        self._inp = inp
        self._sound = sound  # Buzzer or SoundDriver
        
        self._score_l = 0
        self._score_r = 0
        self._paused = False
        self._game_over = False
        self._winner = ""
        self._exit = False
        self._frame = 0
        self._speed = 3.0

        self._prev_ball_x = None
        self._prev_ball_y = None
        self._prev_lpaddle_y = None
        self._prev_rpaddle_y = None

        px = 6
        self._lpad_x = px
        self._rpad_x = width - px - PADDLE_W

        self._paddle_l = Paddle(PADDLE_W, PADDLE_H, C_GREEN)
        self._paddle_r = Paddle(PADDLE_W, PADDLE_H, C_CYAN)
        self.add_object(self._paddle_l, self._lpad_x, height // 2 - PADDLE_H // 2)
        self.add_object(self._paddle_r, self._rpad_x, height // 2 - PADDLE_H // 2)

        self._ball = Ball(BALL_SIZE)
        self.add_object(self._ball, 0, 0)
        self._ball.reset(width // 2, height // 2, self._speed)

        self._bg_color = Color.BLACK

        self._a_prev = False
        self._b_prev = False

        self._drawn_score_l = -1
        self._drawn_score_r = -1

    def play_hit_sound(self, strength=1.0):
        """Bounce sound"""
        if self._sound:
            freq = 800 + random.randint(0, 400)
            self._sound.make_sound(freq, 0.6 * strength, 0.03)

    def play_win_melody(self):
        if self._sound:
            self._sound.play_melody(["C5", "E5", "G5", "C6"], tempo=0.15)

    def play_lose_melody(self):
        if self._sound:
            self._sound.play_melody(["A4", "F4", "D4", "A3"], tempo=0.25)

    def act(self):
        inp = self._inp

        # Quit
        b = inp.is_B()
        if b and not self._b_prev:
            self._exit = True
        self._b_prev = b
        if self._exit:
            return

        # Pause / restart
        a = inp.is_A()
        if a and not self._a_prev:
            if self._game_over:
                self._reset_game()
            else:
                self._paused = not self._paused
        self._a_prev = a

        if self._game_over or self._paused:
            return

        self._frame += 1

        # === Player ===
        speed_p = 4
        ly = self._paddle_l.get_y()
        if inp.is_up():
            ly -= speed_p
        if inp.is_down():
            ly += speed_p
        self._paddle_l.move_to(ly, self._height)

        # === AI ===
        ball_cy = self._ball.get_y() + BALL_SIZE // 2
        pad_cy = self._paddle_r.get_y() + PADDLE_H // 2
        
        
        
        

        if random.random() < reaction_chance:
            if ball_cy < pad_cy - dead_zone:
                self._paddle_r.move_to(self._paddle_r.get_y() - ai_speed, self._height)
            elif ball_cy > pad_cy + dead_zone:
                self._paddle_r.move_to(self._paddle_r.get_y() + ai_speed, self._height)

        # Ball move
        bx = self._ball.get_x() + self._ball._vx
        by = self._ball.get_y() + self._ball._vy

        # Bounce from walls
        hit_wall = False
        if by <= 0:
            by = 0
            self._ball._vy = abs(self._ball._vy)
            hit_wall = True
        elif by + BALL_SIZE >= self._height:
            by = self._height - BALL_SIZE
            self._ball._vy = -abs(self._ball._vy)
            hit_wall = True

        if hit_wall:
            self.play_hit_sound(0.7)

        # Collision with rackets
        lx = self._paddle_l.get_x()
        lpy = self._paddle_l.get_y()
        if (bx <= lx + PADDLE_W and bx + BALL_SIZE >= lx and
            by + BALL_SIZE >= lpy and by <= lpy + PADDLE_H and
            self._ball._vx < 0):
            self._ball._vx = abs(self._ball._vx) * 1.08
            self._ball._vy = ((by + BALL_SIZE // 2) - (lpy + PADDLE_H // 2)) * 0.18
            bx = lx + PADDLE_W + 1
            self.play_hit_sound(1.0)

        rx = self._paddle_r.get_x()
        rpy = self._paddle_r.get_y()
        if (bx + BALL_SIZE >= rx and bx <= rx + PADDLE_W and
            by + BALL_SIZE >= rpy and by <= rpy + PADDLE_H and
            self._ball._vx > 0):
            self._ball._vx = -abs(self._ball._vx) * 1.08
            self._ball._vy = ((by + BALL_SIZE // 2) - (rpy + PADDLE_H // 2)) * 0.18
            bx = rx - BALL_SIZE - 1
            self.play_hit_sound(1.0)

        # Speep limits
        max_v = 8.0
        spd = math.sqrt(self._ball._vx ** 2 + self._ball._vy ** 2)
        if spd > max_v:
            self._ball._vx = self._ball._vx / spd * max_v
            self._ball._vy = self._ball._vy / spd * max_v

        self._ball.set_location(int(bx), int(by))

        # Score
        if bx + BALL_SIZE < 0:
            self._score_r += 1
            self._check_win("AI")
            self._ball.reset(self._width // 2, self._height // 2, self._speed)
        elif bx > self._width:
            self._score_l += 1
            self._check_win("You")
            self._ball.reset(self._width // 2, self._height // 2, self._speed)

    def _check_win(self, name):
        if self._score_l >= WINNING_SCORE or self._score_r >= WINNING_SCORE:
            self._game_over = True
            self._winner = name
            if name == "You":
                self.play_win_melody()
            else:
                self.play_lose_melody()

    def _render(self):
        drv = Game._display
        if drv is None:
            return

        # Init background on first frame
        if self._frame == 0 and self._prev_ball_x is None:
            drv.fill(C_BG)
            cx = self._width // 2
            for dy in range(0, self._height, 8):
                drv.fill_rect(cx - 1, dy, 2, 4, C_DIVIDER)
            drv.show()

        cx = self._width // 2

        # Score render
        score_y = 4
        score_scale = 4
        dw = 3 * score_scale + 2

        if self._score_l != self._drawn_score_l:
            draw_number(drv, self._score_l,
                        cx - 30 - dw, score_y, score_scale, C_GREEN)
            self._drawn_score_l = self._score_l

        if self._score_r != self._drawn_score_r:
            draw_number(drv, self._score_r,
                        cx + 14, score_y, score_scale, C_CYAN)
            self._drawn_score_r = self._score_r

        # === Ball ===
        bx = self._ball.get_x()
        by = self._ball.get_y()

        # Forced rounding to int
        bx = int(bx)
        by = int(by)

        if self._prev_ball_x is not None:
            if self._prev_ball_x != bx or self._prev_ball_y != by:
                self._erase_ball(drv, self._prev_ball_x, self._prev_ball_y)
                drv.fill_rect(bx, by, BALL_SIZE, BALL_SIZE, C_WHITE)
        else:
            drv.fill_rect(bx, by, BALL_SIZE, BALL_SIZE, C_WHITE)

        self._prev_ball_x = bx
        self._prev_ball_y = by

        # === Left racket (Player) ===
        ly = int(self._paddle_l.get_y())
        if self._prev_lpaddle_y is None or self._prev_lpaddle_y != ly:
            if self._prev_lpaddle_y is not None:
                drv.fill_rect(self._lpad_x, self._prev_lpaddle_y,
                                PADDLE_W, PADDLE_H, C_BG)
            drv.fill_rect(self._lpad_x, ly, PADDLE_W, PADDLE_H, C_GREEN)
            self._prev_lpaddle_y = ly

        # === Right racket (AI) ===
        ry = int(self._paddle_r.get_y())
        if self._prev_rpaddle_y is None or self._prev_rpaddle_y != ry:
            if self._prev_rpaddle_y is not None:
                drv.fill_rect(self._rpad_x, self._prev_rpaddle_y,
                                PADDLE_W, PADDLE_H, C_BG)
            drv.fill_rect(self._rpad_x, ry, PADDLE_W, PADDLE_H, C_CYAN)
            self._prev_rpaddle_y = ry

        # Message
        if self._paused and not self._game_over:
            msg = "PAUSE"
            tw = len(msg) * 6
            drv.print(msg, self._width // 2 - tw // 2,
                     self._height // 2 - 4, C_YELLOW)

        if self._game_over:
            win_msg = self._winner + " wins!"
            sub_msg = "B=exit A=restart"
            tw1 = len(win_msg) * 6
            tw2 = len(sub_msg) * 6
            hy = self._height // 2
            drv.fill_rect(self._width // 2 - tw1 // 2 - 4,
                            hy - 16, tw1 + 8, 36, C_BG)
            drv.print(win_msg, self._width // 2 - tw1 // 2, hy - 12, C_YELLOW)
            drv.print(sub_msg, self._width // 2 - tw2 // 2, hy + 4, C_WHITE)

        drv.show()

    def _erase_ball(self, drv, bx, by):
        drv.fill_rect(bx, by, BALL_SIZE, BALL_SIZE, C_BG)
        cx = self._width // 2
        if bx <= cx + 1 and bx + BALL_SIZE >= cx - 1:
            for dy in range(0, self._height, 8):
                if dy + 4 > by and dy < by + BALL_SIZE:
                    drv.fill_rect(cx - 1, dy, 2, 4, C_DIVIDER)

    def _reset_game(self):
        self._score_l        = 0
        self._score_r        = 0
        self._game_over      = False
        self._winner         = ""
        self._drawn_score_l  = -1
        self._drawn_score_r  = -1
        self._prev_ball_x    = None
        self._prev_ball_y    = None
        self._prev_lpaddle_y = None
        self._prev_rpaddle_y = None
        drv = Game._display
        if drv:
            drv.fill(C_BG)
            cx = self._width // 2
            for dy in range(0, self._height, 8):
                drv.fill_rect(cx - 1, dy, 2, 4, C_DIVIDER)
            drv.show()
        self._ball.reset(self._width // 2, self._height // 2, self._speed)
        self._paddle_l.move_to(self._height // 2 - PADDLE_H // 2, self._height)
        self._paddle_r.move_to(self._height // 2 - PADDLE_H // 2, self._height)

    def repaint(self):
        pass


def run_pong(display: DisplayDriver = None, input: Input = None): # type: ignore
    if display is None or input is None:
        raise ValueError("display & input requered")

    w = display.width
    h = display.height

    buzzer = Buzzer()
    world = PongWorld(w, h, input, sound=buzzer)

    Game.init(display, world, sound=buzzer)
    Game.start()

    def _raw(pin, active_low):
        v = pin.value()
        return (v == 0) if active_low else (v == 1)

    world._a_prev = _raw(input.PIN_A, input._active_low[input.PIN_A])
    world._b_prev = _raw(input.PIN_B, input._active_low[input.PIN_B])

    while True:
        world.act()
        world._render()

        if world._exit:
            display.fill(C_BG)
            display.show()
            break

        sleep_ms(FPS_DELAY)

if __name__ == "__main__":
    run_pong(st7789(), Input())