from machine import Pin, SoftI2C
from neopixel import NeoPixel
from engine import st7789, Input, DisplayDriver
from engine.Buzzer import Buzzer
from time import sleep
import math


PIN_BUZZER   = 12
PIN_NEOPIXEL = 13
NEOPIXEL_N   = 4

SPHERE_CX, SPHERE_CY, SPHERE_R = 60,  110, 48
BUBBLE_CX, BUBBLE_CY, BUBBLE_R = 185, 110, 40


class Sphere3D:

    LAT_LINES = 5
    LON_LINES = 6
    SEGMENTS  = 20

    COL_X    = 0xF800
    COL_Y    = 0x07E0
    COL_Z    = 0x001F
    COL_GRID = 0x39E7

    def __init__(self, drv, cx, cy, r):
        self._drv:DisplayDriver = drv
        self.cx                 = cx
        self.cy                 = cy
        self.r                  = r
        self._rx                = 0.0
        self._ry                = 0.0
        self._rz                = 0.0
        self._prev_pts          = None  # cached point lists from last draw

    def update_rotation(self, gx, gy, gz, dt=0.016):
        scale     = math.pi / 180.0 * dt
        self._rx += gx * scale
        self._ry += gy * scale
        self._rz += gz * scale

    def _rot(self, x, y, z):
        cx, sx = math.cos(self._rx), math.sin(self._rx)
        y, z   = y * cx - z * sx,   y * sx + z * cx
        cy, sy = math.cos(self._ry), math.sin(self._ry)
        x, z   = x * cy + z * sy,  -x * sy + z * cy
        cz, sz = math.cos(self._rz), math.sin(self._rz)
        x, y   = x * cz - y * sz,   x * sz + y * cz
        return x, y, z

    def _project(self, x, y, z):
        fov = 280.0
        dz  = fov / (fov + z * self.r * 0.8 + fov)
        sx  = int(self.cx + x * self.r * dz)
        sy  = int(self.cy + y * self.r * dz)
        return sx, sy, z

    def _build_points(self):
        pi  = math.pi
        seg = self.SEGMENTS
        strips = []

        for i in range(self.LAT_LINES):
            lat     = -pi / 2 + pi * (i + 1) / (self.LAT_LINES + 1)
            cos_lat = math.cos(lat)
            sin_lat = math.sin(lat)
            strip   = []
            for j in range(seg + 1):
                lon        = 2 * pi * j / seg
                x0         = math.cos(lon) * cos_lat
                y0         = sin_lat
                z0         = math.sin(lon) * cos_lat
                xr, yr, zr = self._rot(x0, y0, z0)
                px, py, pz = self._project(xr, yr, zr)
                strip.append((px, py, pz > -0.2))
            strips.append(strip)

        for i in range(self.LON_LINES):
            lon   = 2 * pi * i / self.LON_LINES
            strip = []
            for j in range(seg + 1):
                lat        = -pi / 2 + pi * j / seg
                x0         = math.cos(lon) * math.cos(lat)
                y0         = math.sin(lat)
                z0         = math.sin(lon) * math.cos(lat)
                xr, yr, zr = self._rot(x0, y0, z0)
                px, py, pz = self._project(xr, yr, zr)
                strip.append((px, py, pz > -0.2))
            strips.append(strip)

        # axis endpoints
        axes_pts = []
        for ax, ay, az in [(1,0,0),(0,1,0),(0,0,1)]:
            xr, yr, zr = self._rot(ax * 0.85, ay * 0.85, az * 0.85)
            tx, ty, _  = self._project(xr, yr, zr)
            axes_pts.append((tx, ty))

        return strips, axes_pts

    def _draw_strips(self, strips, axes_pts, color):
        drv = self._drv
        for strip in strips:
            prev = None
            for px, py, visible in strip:
                if prev and visible:
                    drv.line(prev[0], prev[1], px, py, color)
                prev = (px, py)

        labels = ['X', 'Y', 'Z']
        cols   = [self.COL_X, self.COL_Y, self.COL_Z]
        for i, (tx, ty) in enumerate(axes_pts):
            drv.line(self.cx, self.cy, tx, ty, color)
            drv.print(labels[i], tx, ty - 8, color)

    def draw(self):
        drv              = self._drv
        new_strips, new_axes = self._build_points()

        # erase previous frame by redrawing in BLACK
        if self._prev_pts is not None:
            prev_strips, prev_axes = self._prev_pts
            self._draw_strips(prev_strips, prev_axes, drv.BLACK)

        if self._prev_pts is None:
            r = self.r
            drv.draw_round_rectangle(self.cx - r, self.cy - r, r*2, r*2, r, drv.WHITE)

        self._draw_strips(new_strips, new_axes, self.COL_GRID)

        labels = ['X', 'Y', 'Z']
        cols   = [self.COL_X, self.COL_Y, self.COL_Z]
        for i, (tx, ty) in enumerate(new_axes):
            drv.line(self.cx, self.cy, tx, ty, cols[i])
            drv.print(labels[i], tx, ty - 8, cols[i])

        self._prev_pts = (new_strips, new_axes)

    def invalidate(self):
        self._prev_pts = None


class BubbleLevel:

    COL_RING   = 0x39E7
    COL_BUBBLE = 0x07FF
    COL_CENTER = 0xFFFF
    COL_Z_POS  = 0x07E0
    COL_Z_NEG  = 0xF800
    COL_CROSS  = 0x39E7

    def __init__(self, drv, cx, cy, r):
        self._drv      = drv
        self.cx        = cx
        self.cy        = cy
        self.r         = r
        self._prev_bx  = None
        self._prev_by  = None
        self._prev_filled   = None
        self._prev_z_pos    = None
        self._static_drawn  = False

    def _draw_static(self):
        drv      = self._drv
        cx, cy, r = self.cx, self.cy, self.r

        drv.hline(cx - r, cy,     r * 2, self.COL_CROSS)
        drv.vline(cx,     cy - r, r * 2, self.COL_CROSS)
        drv.draw_round_rectangle(cx - r,    cy - r,    r*2, r*2, r,    drv.WHITE)
        drv.draw_round_rectangle(cx - r//2, cy - r//2, r,   r,   r//2, self.COL_RING)

        bx0 = cx + r + 6
        by0 = cy - r
        bh  = r * 2
        bw  = 10
        drv.rect(bx0, by0, bw, bh, drv.WHITE)
        drv.hline(bx0 - 2, cy, bw + 4, drv.WHITE)
        drv.print('Z', bx0, by0 - 12, drv.WHITE)

    def draw(self, ax, ay, az, max_g=2.0):
        drv       = self._drv
        cx, cy, r = self.cx, self.cy, self.r

        # static parts drawn once
        if not self._static_drawn:
            self._draw_static()
            self._static_drawn = True

        # --- bubble ---
        bx = int(cx - ax / max_g * (r - 8))
        by = int(cy - ay / max_g * (r - 8))
        dx, dy = bx - cx, by - cy
        dist   = math.sqrt(dx * dx + dy * dy)
        lim    = r - 8
        if dist > lim:
            bx = int(cx + dx / dist * lim)
            by = int(cy + dy / dist * lim)

        if bx != self._prev_bx or by != self._prev_by:
            # erase old bubble
            if self._prev_bx is not None:
                drv.fill_round_rectangle(
                    self._prev_bx - 8, self._prev_by - 8, 17, 17, 8, drv.BLACK)
                drv.hline(cx - r, cy, r * 2, self.COL_CROSS)
                drv.vline(cx, cy - r, r * 2, self.COL_CROSS)
                drv.fill_round_rectangle(cx - 3, cy - 3, 6, 6, 3, self.COL_CENTER)
            drv.fill_round_rectangle(bx - 7, by - 7, 14, 14, 7, self.COL_BUBBLE)
            drv.draw_round_rectangle(bx - 8, by - 8, 16, 16, 8, drv.WHITE)
            drv.fill_round_rectangle(cx - 3, cy - 3, 6,  6,  3, self.COL_CENTER)

            self._prev_bx = bx
            self._prev_by = by

        bx0        = cx + r + 6
        bh         = r * 2
        bw         = 10
        az_clamped = max(-max_g, min(max_g, az))
        filled     = int(abs(az_clamped) / max_g * (bh // 2))
        z_pos      = az_clamped >= 0

        if filled != self._prev_filled or z_pos != self._prev_z_pos:
            # erase bar interior
            drv.fill_rect(bx0 + 1, cy - bh // 2, bw - 2, bh // 2, drv.BLACK)
            drv.fill_rect(bx0 + 1, cy,            bw - 2, bh // 2, drv.BLACK)

            col = self.COL_Z_POS if z_pos else self.COL_Z_NEG
            if z_pos:
                drv.fill_rect(bx0 + 1, cy - filled, bw - 2, filled, col)
            else:
                drv.fill_rect(bx0 + 1, cy,          bw - 2, filled, col)

            # restore midline
            drv.hline(bx0 - 2, cy, bw + 4, drv.WHITE)

            self._prev_filled = filled
            self._prev_z_pos  = z_pos

    def invalidate(self):
        self._static_drawn = False
        self._prev_bx      = None
        self._prev_by      = None
        self._prev_filled  = None
        self._prev_z_pos   = None


class GyroValues:
    _LABELS = ['GX:', 'GY:', 'GZ:', 'AX:', 'AY:', 'AZ:']
    _COLS   = [0x07FF, 0x07FF, 0x07FF, 0x07E0, 0x07E0, 0x07E0]  # CYAN x3, GREEN x3
    _YS     = [24, 40, 56, 96, 112, 128]
    _TX     = 240

    def __init__(self, drv):
        self._drv    = drv
        self._prev   = [None] * 6
        self._drawn  = False

    def draw(self, gx, gy, gz, ax, ay, az):
        drv    = self._drv
        values = [gx, gy, gz, ax, ay, az]

        if not self._drawn:
            drv.print('GYRO',   self._TX, 8,   drv.WHITE)
            drv.print('ACCEL',  self._TX, 80,  drv.WHITE)
            drv.print('[A+B]>', self._TX, 160, drv.YELLOW)
            self._drawn = True

        fw, _ = drv.get_text_size('X')   # single char width
        max_chars = 10                    # enough for label + value

        for i, val in enumerate(values):
            if val != self._prev[i]:
                y   = self._YS[i]
                col = self._COLS[i]
                # erase previous value area
                drv.fill_rect(self._TX, y, fw * max_chars, 16, drv.BLACK)
                drv.print(self._LABELS[i] + str(val), self._TX, y, col)
                self._prev[i] = val

    def invalidate(self):
        self._drawn = False
        self._prev  = [None] * 6


class ButtonState:
    _FIELDS = ('left', 'right', 'up', 'down', 'a', 'b')

    def __init__(self, left=False, right=False, up=False,
                down=False, a=False, b=False):
        self.left  = left
        self.right = right
        self.up    = up
        self.down  = down
        self.a     = a
        self.b     = b

    def diff(self, other):
        changed = []
        for name in self._FIELDS:
            if getattr(self, name) != getattr(other, name):
                changed.append(name)
        return changed


class GamepadUI:
    DPAD_X   = 15
    DPAD_Y   = 50
    DPAD_W   = 40
    DPAD_H   = 40
    DPAD_OFF = 2
    DPAD_R   = 10

    AB_X   = 200
    AB_Y   = 120
    AB_W   = 44
    AB_H   = 44
    AB_OFF = 5
    AB_R   = 22

    def __init__(self, drv, inp):
        self._drv  = drv
        self._inp  = inp
        self._prev = None

    def update(self):
        state = self._read()
        if self._prev is None:
            self._draw_cross()
            for name in ButtonState._FIELDS:
                self._draw_btn(name, getattr(state, name))
        else:
            for name in state.diff(self._prev):
                self._draw_btn(name, getattr(state, name))
        self._prev = state

    def invalidate(self):
        self._prev = None

    def _read(self):
        i = self._inp
        return ButtonState(
            left  = i.is_left(),
            right = i.is_right(),
            up    = i.is_up(),
            down  = i.is_down(),
            a     = i.is_A(),
            b     = i.is_B(),
        )

    def _geometry(self, name):
        dx, dy = self.DPAD_X, self.DPAD_Y
        dw, dh = self.DPAD_W, self.DPAD_H
        sx, sy = dw + self.DPAD_OFF, dh + self.DPAD_OFF
        dr     = self.DPAD_R
        ax, ay = self.AB_X, self.AB_Y
        aw, ah = self.AB_W, self.AB_H
        ar     = self.AB_R
        table  = {
            'up':    (dx + sx,               dy,              dw, dh, dr, '^'),
            'left':  (dx,                    dy + sy,         dw, dh, dr, '<'),
            'right': (dx + sx * 2,           dy + sy,         dw, dh, dr, '>'),
            'down':  (dx + sx,               dy + sy * 2,     dw, dh, dr, 'v'),
            'a':     (ax,                    ay,              aw, ah, ar, 'A'),
            'b':     (ax + aw + self.AB_OFF, ay - ah - self.AB_OFF, aw, ah, ar, 'B'),
        }
        if name not in table:
            raise ValueError('Unknown button: ' + name)
        return table[name]

    def _draw_btn(self, name, pressed):
        drv = self._drv
        x, y, w, h, r, label = self._geometry(name)
        if pressed:
            drv.fill_round_rectangle(x, y, w, h, r, drv.WHITE)
            txt_color = drv.BLACK
        else:
            drv.fill_round_rectangle(x, y, w, h, r, drv.BLACK)
            drv.draw_round_rectangle(x, y, w, h, r, drv.WHITE)
            txt_color = drv.WHITE
        tw, th = drv.get_text_size(label)
        drv.print(label, x + (w - tw) // 2, y + (h - th) // 2,
                txt_color, bg=drv.WHITE if pressed else drv.BLACK)

    def _draw_cross(self):
        drv = self._drv
        dx  = self.DPAD_X + (self.DPAD_W + self.DPAD_OFF)
        dy  = self.DPAD_Y + (self.DPAD_H + self.DPAD_OFF)
        drv.fill_round_rectangle(dx, dy, self.DPAD_W, self.DPAD_H, self.DPAD_R, drv.BLACK)
        drv.draw_round_rectangle(dx, dy, self.DPAD_W, self.DPAD_H, self.DPAD_R, drv.WHITE)


class IOTest:
    _STATES_N = 4

    def __init__(self):
        self.drv    = st7789()
        self.input  = Input()
        self.buzzer = Buzzer(Pin(PIN_BUZZER))
        self.led    = NeoPixel(Pin(PIN_NEOPIXEL), NEOPIXEL_N)
        self._sphere  = Sphere3D(self.drv,    SPHERE_CX, SPHERE_CY, SPHERE_R)
        self._bubble  = BubbleLevel(self.drv, BUBBLE_CX, BUBBLE_CY, BUBBLE_R)
        self._values  = GyroValues(self.drv)
        self._ui      = GamepadUI(self.drv, self.input)
        self._st      = 0
        self._ab_lock = self.input.is_A() and self.input.is_B()
        self._running = True
    def run(self):
        if __name__ == '__main__':
            self.drv.fill(self.drv.BLACK)
            self.drv.draw_logo()
            sleep(2)
        self.drv.fill(self.drv.BLACK)

        while self._running:
            if self._st == 0:
                self._test_buttons()
            elif self._st == 1:
                self._test_gyro()
            elif self._st == 2:
                self._test_buzzer()
            elif self._st == 3:
                self._test_led()
            self._handle_next()
            sleep(0.016)

    def _handle_next(self):
        pressed = self.input.is_A() and self.input.is_B()
        if pressed and not self._ab_lock:
            self._st = (self._st + 1) % self._STATES_N
            self.drv.fill(self.drv.BLACK)
            self._ui.invalidate()
            self._sphere.invalidate()
            self._bubble.invalidate()
            self._values.invalidate()
        self._ab_lock = pressed
        quit = self.input.is_up() and self.input.is_B()
        if quit:
            self._running = False
        return

    def _test_buttons(self):
        self._ui.update()

    def _test_gyro(self):
        gx, gy, gz = self.input.read_gyro()
        ax, ay, az = self.input.read_accel()

        self._sphere.update_rotation(gx, gy, gz)
        self._sphere.draw()
        self._bubble.draw(ax, ay, az)
        self._values.draw(gx, gy, gz, ax, ay, az)

    def _test_buzzer(self):
        inp = self.input
        if   inp.is_up():    self.buzzer.play_note('A4', duration=0.05)
        elif inp.is_down():  self.buzzer.play_note('C4', duration=0.05)
        elif inp.is_left():  self.buzzer.play_note('E4', duration=0.05)
        elif inp.is_right(): self.buzzer.play_note('G4', duration=0.05)
        elif inp.is_A():     self.buzzer.beep()
        elif inp.is_B():     self.buzzer.boop()


    
    

    def _test_led(self):
        inp = self.input
        if   inp.is_up():    c = (0,   0,   255)
        elif inp.is_down():  c = (255, 0,   0)
        elif inp.is_left():  c = (0,   255, 0)
        elif inp.is_right(): c = (255, 255, 0)
        elif inp.is_A():     c = (255, 0,   255)
        elif inp.is_B():     c = (0,   0,   0)
        else:                c = None
        if c is not None:
            for i in range(NEOPIXEL_N):
                self.led[i] = c
            self.led.write()


if __name__ == '__main__':
    IOTest().run()