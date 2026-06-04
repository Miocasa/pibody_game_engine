from machine import Pin, SoftI2C    # type: ignore
from neopixel import NeoPixel       # type: ignore
from engine import st7789, Input, DisplayDriver
from engine.Buzzer import Buzzer
from time import sleep
import time
import math


PIN_BUZZER   = 12
PIN_NEOPIXEL = 13
NEOPIXEL_N   = 4

CUBE_CX,   CUBE_CY,   CUBE_SZ = 70,  120, 48
BUBBLE_CX, BUBBLE_CY, BUBBLE_R = 195, 120, 42



class GyroCalibrator:
    _SAMPLES   = 5
    _DELAY_MS  = 200
    _COUNTDOWN = 3

    _COL_OVERLAY = st7789.BLACK
    _COL_TITLE   = st7789.YELLOW
    _COL_OK      = st7789.GREEN
    _COL_ERR     = st7789.RED
    _COL_INFO    = st7789.BLUE

    _OX, _OY, _OW, _OH = 10, 70, 220, 110

    def __init__(self, drv, inp: Input):
        self._drv = drv
        self._inp = inp

    def run(self):
        drv = self._drv
        inp = self._inp

        
        for sec in range(self._COUNTDOWN, 0, -1):
            self._draw_overlay(
                'CALIBRATION',
                'Place device flat',
                'Starting in  ' + str(sec) + ' ...',
                self._COL_INFO,
            )
            deadline = time.ticks_add(time.ticks_ms(), 1000)
            while time.ticks_diff(deadline, time.ticks_ms()) > 0:
                pass

        sums = [0.0] * 6
        for i in range(self._SAMPLES):
            self._draw_overlay(
                'CALIBRATION',
                'Measuring... ' + str(i + 1) + '/' + str(self._SAMPLES),
                '',
                self._COL_TITLE,
            )
            gx, gy, gz = inp.read_gyro_raw()
            ax, ay, az = inp.read_accel_raw()
            sums[0] += gx;  sums[1] += gy;  sums[2] += gz
            sums[3] += ax;  sums[4] += ay;  sums[5] += az
            deadline = time.ticks_add(time.ticks_ms(), self._DELAY_MS)
            while time.ticks_diff(deadline, time.ticks_ms()) > 0:
                pass

        n = self._SAMPLES
        off = [round(s / n, 4) for s in sums]

        off[5] = round(off[5] - 1.0, 4)

        print('=== GYRO CALIBRATION RESULT ===')
        print('  GX offset:', off[0])
        print('  GY offset:', off[1])
        print('  GZ offset:', off[2])
        print('  AX offset:', off[3])
        print('  AY offset:', off[4])
        print('  AZ offset:', off[5], '(gravity removed)')
        print('================================')


        ok = inp.set_calibration(*off)

        msg2 = 'Saved to gyro_offset.json' if ok else 'Save FAILED (check fs)'
        col  = self._COL_OK if ok else self._COL_ERR
        self._draw_overlay('DONE!', 'Offsets applied.', msg2, col)
        sleep(2)
        drv.fill(drv.BLACK)

    def _draw_overlay(self, title, line1, line2, col):
        drv = self._drv
        ox, oy, ow, oh = self._OX, self._OY, self._OW, self._OH
        drv.fill_rect(ox, oy, ow, oh, self._COL_OVERLAY)
        drv.draw_round_rectangle(ox, oy, ow, oh, 8, col)
        tw, _ = drv.get_text_size(title)
        drv.print(title, ox + (ow - tw) // 2, oy + 10, col)
        drv.print(line1, ox + 8, oy + 34, drv.WHITE)
        drv.print(line2, ox + 8, oy + 54, drv.WHITE)

class FpsLimiter:
    def __init__(self, fps):
        self._period_ms = int(1000 / fps)
        self._prev_ms   = time.ticks_ms() - self._period_ms 

    def ready(self):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._prev_ms) >= self._period_ms:
            self._prev_ms = now
            return True
        return False

class RotatingCube:
    _VERTS = (
        (-1,-1,-1),( 1,-1,-1),( 1, 1,-1),(-1, 1,-1),
        (-1,-1, 1),( 1,-1, 1),( 1, 1, 1),(-1, 1, 1),
    )
    _EDGES = (
        (0,1),(1,2),(2,3),(3,0),
        (4,5),(5,6),(6,7),(7,4),
        (0,4),(1,5),(2,6),(3,7),
    )
    _AXIS_VERTS = ((1,0,0),(0,1,0),(0,0,1))
    _AXIS_COLS  = (0xF800, 0x07E0, 0x001F)
    _AXIS_LABS  = ('X','Y','Z')
    _COL_EDGE   = 0x4208

    def __init__(self, drv, cx, cy, size):
        self._drv       = drv
        self.cx         = cx
        self.cy         = cy
        self.size       = size
        self._rx        = 0.0
        self._ry        = 0.0
        self._rz        = 0.0
        self._prev_pts  = None
        self._prev_apts = None

    def update_rotation(self, gx, gy, gz, dt=0.016):
        s = math.pi / 180.0 * dt
        self._rx += gx * s
        self._ry += gy * s
        self._rz += gz * s

    def _rotate(self, x, y, z):
        cx_, sx_ = math.cos(self._rx), math.sin(self._rx)
        y, z = y*cx_ - z*sx_, y*sx_ + z*cx_
        cy_, sy_ = math.cos(self._ry), math.sin(self._ry)
        x, z = x*cy_ + z*sy_, -x*sy_ + z*cy_
        cz_, sz_ = math.cos(self._rz), math.sin(self._rz)
        x, y = x*cz_ - y*sz_, x*sz_ + y*cz_
        return x, y, z

    def _proj(self, x, y, z):
        d = 3.5 / (3.5 + z)
        return int(self.cx + x*self.size*d), int(self.cy + y*self.size*d)

    def draw(self):
        drv = self._drv
        cx, cy = self.cx, self.cy

        pts = []
        for vx, vy, vz in self._VERTS:
            rx, ry, rz = self._rotate(vx, vy, vz)
            pts.append(self._proj(rx, ry, rz))

        apts = []
        for ax, ay, az in self._AXIS_VERTS:
            rx, ry, rz = self._rotate(ax, ay, az)
            apts.append(self._proj(rx, ry, rz))

        if self._prev_pts is not None:
            pp = self._prev_pts
            for i, j in self._EDGES:
                drv.line(pp[i][0], pp[i][1], pp[j][0], pp[j][1], drv.BLACK)
            pa = self._prev_apts
            for k in range(3):
                tx, ty = pa[k]
                drv.line(cx, cy, tx, ty, drv.BLACK)
                drv.fill_rect(tx - 4, ty - 11, 10, 12, drv.BLACK)

        for i, j in self._EDGES:
            drv.line(pts[i][0], pts[i][1], pts[j][0], pts[j][1], self._COL_EDGE)

        for k, (tx, ty) in enumerate(apts):
            drv.line(cx, cy, tx, ty, self._AXIS_COLS[k])
            drv.print(self._AXIS_LABS[k], tx - 3, ty - 10, self._AXIS_COLS[k])

        self._prev_pts  = pts
        self._prev_apts = apts

    def invalidate(self):
        self._prev_pts  = None
        self._prev_apts = None


class BubbleLevel:
    _COL_RING   = 0x39E7
    _COL_BUBBLE = 0x07FF
    _COL_CENTER = 0xFFFF
    _COL_Z_POS  = 0x07E0
    _COL_Z_NEG  = 0xF800
    _COL_CROSS  = 0x39E7

    def __init__(self, drv, cx, cy, r):
        self._drv     = drv
        self.cx       = cx
        self.cy       = cy
        self.r        = r
        self._prev_bx = None
        self._prev_by = None
        self._prev_filled  = None
        self._prev_z_pos   = None
        self._static_drawn = False

    def _draw_static(self):
        drv = self._drv
        cx, cy, r = self.cx, self.cy, self.r
        drv.hline(cx - r, cy,     r*2, self._COL_CROSS)
        drv.vline(cx,     cy - r, r*2, self._COL_CROSS)
        drv.draw_round_rectangle(cx - r,    cy - r,    r*2, r*2, r,    drv.WHITE)
        drv.draw_round_rectangle(cx - r//2, cy - r//2, r,   r,   r//2, self._COL_RING)
        bx0 = cx + r + 6
        by0 = cy - r
        bh  = r*2
        bw  = 10
        drv.rect(bx0, by0, bw, bh, drv.WHITE)
        drv.hline(bx0 - 2, cy, bw + 4, drv.WHITE)
        drv.print('Z', bx0, by0 - 12, drv.WHITE)

    def draw(self, ax, ay, az, max_g=2.0):
        drv = self._drv
        cx, cy, r = self.cx, self.cy, self.r

        if not self._static_drawn:
            self._draw_static()
            self._static_drawn = True

        bx = int(cx - ax / max_g * (r - 8))
        by = int(cy - ay / max_g * (r - 8))
        dx, dy = bx - cx, by - cy
        dist = math.sqrt(dx*dx + dy*dy)
        lim  = r - 8
        if dist > lim:
            bx = int(cx + dx / dist * lim)
            by = int(cy + dy / dist * lim)

        if bx != self._prev_bx or by != self._prev_by:
            if self._prev_bx is not None:
                drv.fill_round_rectangle(self._prev_bx-8, self._prev_by-8, 17, 17, 8, drv.BLACK)
                drv.hline(cx - r, cy, r*2, self._COL_CROSS)
                drv.vline(cx, cy - r, r*2, self._COL_CROSS)
                drv.fill_round_rectangle(cx-3, cy-3, 6, 6, 3, self._COL_CENTER)
            drv.fill_round_rectangle(bx-7, by-7, 14, 14, 7, self._COL_BUBBLE)
            drv.draw_round_rectangle(bx-8, by-8, 16, 16, 8, drv.WHITE)
            drv.fill_round_rectangle(cx-3, cy-3, 6, 6, 3, self._COL_CENTER)
            self._prev_bx = bx
            self._prev_by = by

        bx0  = cx + r + 6
        bh   = r*2
        bw   = 10
        az_c = max(-max_g, min(max_g, az))
        filled = int(abs(az_c) / max_g * (bh // 2))
        z_pos  = az_c >= 0

        if filled != self._prev_filled or z_pos != self._prev_z_pos:
            drv.fill_rect(bx0+1, cy - bh//2, bw-2, bh//2, drv.BLACK)
            drv.fill_rect(bx0+1, cy,          bw-2, bh//2, drv.BLACK)
            col = self._COL_Z_POS if z_pos else self._COL_Z_NEG
            if z_pos:
                drv.fill_rect(bx0+1, cy - filled, bw-2, filled, col)
            else:
                drv.fill_rect(bx0+1, cy,           bw-2, filled, col)
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
    _LABELS = ('GX:','GY:','GZ:','AX:','AY:','AZ:')
    _COLS   = (0x07FF,0x07FF,0x07FF,0x07E0,0x07E0,0x07E0)
    _YS     = (24,40,56,96,112,128)
    _TX     = 148 + 50 + 40 + 18

    def __init__(self, drv):
        self._drv   = drv
        self._prev  = [None]*6
        self._drawn = False

    def draw(self, gx, gy, gz, ax, ay, az):
        drv    = self._drv
        values = (gx, gy, gz, ax, ay, az)
        if not self._drawn:
            drv.print('GYRO',        self._TX, 8,   drv.WHITE)
            drv.print('ACCEL',       self._TX, 80,  drv.WHITE)
            drv.print('[A+B]>',      self._TX, 160, drv.YELLOW)
            drv.print('[A+Dn]CALIB', self._TX, 176, 0x4208)
            self._drawn = True
        fw, _ = drv.get_text_size('X')
        for i, val in enumerate(values):
            if val != self._prev[i]:
                y = self._YS[i]
                drv.fill_rect(self._TX, y, fw*12, 14, drv.BLACK)
                drv.print(self._LABELS[i] + str(round(val, 2)), self._TX, y, self._COLS[i])
                self._prev[i] = val

    def invalidate(self):
        self._drawn = False
        self._prev  = [None]*6


class BuzzerUI:
    _NOTES   = ('C','D','E','F','G','A','B')
    _KEY_W   = 28
    _KEY_H   = 58
    _KEY_GAP = 3
    _KEYS_X  = 13
    _KEYS_Y  = 72
    _COL_DIM = 0x4208

    def __init__(self, drv, buzzer):
        self._drv     = drv
        self._buzzer  = buzzer
        self._note_i  = 4
        self._oct     = 4
        self._drawn   = False
        self._p_note  = -1
        self._p_oct   = -1
        self._nav_cnt = 0
        self._a_prev  = False
        self._b_prev  = False

    def invalidate(self):
        self._drawn  = False
        self._p_note = -1
        self._p_oct  = -1

    def _note_freq(self):
        base = {'C':261.63,'D':293.66,'E':329.63,
                'F':349.23,'G':392.00,'A':440.00,'B':493.88}
        return base[self._NOTES[self._note_i]] * (2 ** (self._oct - 4))

    def update(self, inp):
        if not self._drawn:
            self._draw_static()

        left  = inp.is_left()
        right = inp.is_right()
        up    = inp.is_up()
        down  = inp.is_down()
        nav   = left or right or up or down

        if nav:
            self._nav_cnt += 1
            fire = self._nav_cnt == 1 or (self._nav_cnt > 14 and self._nav_cnt % 4 == 0)
        else:
            self._nav_cnt = 0
            fire = False

        ni = self._note_i
        oc = self._oct
        if fire:
            if   left:  ni = (ni - 1) % 7
            elif right: ni = (ni + 1) % 7
            elif up:    oc = min(7, oc + 1)
            elif down:  oc = max(2, oc - 1)
        self._note_i = ni
        self._oct    = oc

        a = inp.is_A()
        if a != self._a_prev:
            if a:
                self._buzzer.freq(int(self._note_freq()))
                self._buzzer.on()
            else:
                self._buzzer.off()
        self._a_prev = a

        b = inp.is_B()
        if b and not self._b_prev:
            self._buzzer.off()
            self._buzzer.boop()
        self._b_prev = b


        if ni != self._p_note:
            if self._p_note >= 0:
                self._draw_key(self._p_note, selected=False)
            self._draw_key(ni, selected=True)

        if ni != self._p_note or oc != self._p_oct:
            self._draw_info()

        self._p_note = ni
        self._p_oct  = oc

    def _draw_static(self):
        drv = self._drv
        drv.print('BUZZER TEST', 68, 6, drv.WHITE)
        drv.hline(0, 18, 240, 0x39E7)
        drv.print('<>  note',         8, 148, self._COL_DIM)
        drv.print('^v  octave',       8, 163, self._COL_DIM)
        drv.print('A   hold to play', 8, 178, self._COL_DIM)
        drv.print('B   boop',         8, 193, self._COL_DIM)

        for i in range(len(self._NOTES)):
            self._draw_key(i, selected=(i == self._note_i))
        self._drawn = True

    def _draw_key(self, idx, selected):
        drv  = self._drv
        name = self._NOTES[idx]
        x    = self._KEYS_X + idx * (self._KEY_W + self._KEY_GAP)
        y    = self._KEYS_Y
        if selected:
            drv.fill_round_rectangle(x, y, self._KEY_W, self._KEY_H, 5, drv.WHITE)
            drv.print(name, x + 9, y + self._KEY_H - 15, drv.BLACK)
        else:
            drv.fill_round_rectangle(x, y, self._KEY_W, self._KEY_H, 5, drv.BLACK)
            drv.draw_round_rectangle(x, y, self._KEY_W, self._KEY_H, 5, 0x39E7)
            drv.print(name, x + 9, y + self._KEY_H - 15, 0x39E7)

    def _draw_info(self):
        drv = self._drv
        drv.fill_rect(0, 22, 240, 46, drv.BLACK)
        note_str = self._NOTES[self._note_i] + str(self._oct)
        freq_str = str(int(self._note_freq())) + ' Hz'
        drv.print('NOTE', 8,   28, 0x39E7)
        drv.print(note_str,  52,  28, drv.YELLOW)
        drv.print('OCT',  120, 28, 0x39E7)
        drv.print(str(self._oct), 160, 28, drv.CYAN)
        drv.print(freq_str, 8, 48, self._COL_DIM)


class LedUI:
    _PALETTE = (
        ('RED',     (255,   0,   0), 0xF800),
        ('GREEN',   (  0, 255,   0), 0x07E0),
        ('BLUE',    (  0,   0, 255), 0x001F),
        ('WHITE',   (255, 255, 255), 0xFFFF),
        ('YELLOW',  (255, 255,   0), 0xFFE0),
        ('CYAN',    (  0, 255, 255), 0x07FF),
        ('MAGENTA', (255,   0, 255), 0xF81F),
        ('ORANGE',  (255, 128,   0), 0xFC00),
        ('OFF',     (  0,   0,   0), 0x0000),
    )
    _LED_CX   = (30, 80, 130, 180)
    _LED_CY   = 80
    _LED_R    = 20
    _SW_X     = 8
    _SW_Y     = 120
    _SW_W     = 24
    _SW_H     = 24
    _SW_GAP   = 2

    def __init__(self, drv, led, n):
        self._drv        = drv
        self._led        = led
        self._n          = n
        self._sel_led    = 0
        self._sel_col    = 0
        self._drawn      = False
        self._p_led      = -1
        self._p_col      = -1
        self._nav_cnt    = 0
        self._a_prev     = False
        self._b_prev     = False
        self._led_cols   = [8] * n  # index into _PALETTE (8 = OFF)

    def invalidate(self):
        self._drawn  = False
        self._p_led  = -1
        self._p_col  = -1

    def update(self, inp):
        if not self._drawn:
            self._draw_static()
            for i in range(self._n):
                self._draw_led(i)
            for i in range(len(self._PALETTE)):
                self._draw_swatch(i)
            self._draw_info()

        left  = inp.is_left()
        right = inp.is_right()
        up    = inp.is_up()
        down  = inp.is_down()
        nav   = left or right or up or down

        if nav:
            self._nav_cnt += 1
            fire = self._nav_cnt == 1 or (self._nav_cnt > 14 and self._nav_cnt % 4 == 0)
        else:
            self._nav_cnt = 0
            fire = False

        sl = self._sel_led
        sc = self._sel_col
        if fire:
            if   left:  sl = (sl - 1) % self._n
            elif right: sl = (sl + 1) % self._n
            elif up:    sc = (sc - 1) % len(self._PALETTE)
            elif down:  sc = (sc + 1) % len(self._PALETTE)
        self._sel_led = sl
        self._sel_col = sc

        a = inp.is_A()
        if a and not self._a_prev:
            self._led_cols[sl] = sc
            self._led[sl]      = self._PALETTE[sc][1]
            self._led.write()
            self._draw_led(sl)
        self._a_prev = a

        b = inp.is_B()
        if b and not self._b_prev:
            for i in range(self._n):
                self._led_cols[i] = sc
                self._led[i]      = self._PALETTE[sc][1]
            self._led.write()
            for i in range(self._n):
                self._draw_led(i)
        self._b_prev = b

        # перерисовываем только то что изменилось
        if sl != self._p_led:
            if self._p_led >= 0:
                self._draw_led(self._p_led)
            self._draw_led(sl)

        if sc != self._p_col:
            if self._p_col >= 0:
                self._draw_swatch(self._p_col)
            self._draw_swatch(sc)

        if sl != self._p_led or sc != self._p_col:
            self._draw_info()

        self._p_led = sl
        self._p_col = sc

    def _draw_static(self):
        drv = self._drv
        drv.print('LED TEST', 84, 6, drv.WHITE)
        drv.hline(0, 18, 240, 0x39E7)
        drv.print('<>  LED',          8, 160, 0x4208)
        drv.print('^v  color',         8, 175, 0x4208)
        drv.print('A   set LED',       8, 190, 0x4208)
        drv.print('B   set all LEDs',  8, 205, 0x4208)
        self._drawn = True

    def _draw_led(self, idx):
        drv  = self._drv
        cx   = self._LED_CX[idx]
        cy   = self._LED_CY
        r    = self._LED_R
        sel  = (idx == self._sel_led)
        ci   = self._led_cols[idx]
        col  = self._PALETTE[ci][2]

        drv.fill_rect(cx - r - 4, cy - r - 4, (r + 4)*2, (r + 4)*2, drv.BLACK)

        ring_col = drv.WHITE if sel else 0x39E7
        if col:
            drv.fill_round_rectangle(cx-r+2, cy-r+2, r*2-4, r*2-4, r-2, col)
        drv.draw_round_rectangle(cx-r, cy-r, r*2, r*2, r, ring_col)
        if sel:
            drv.draw_round_rectangle(cx-r-2, cy-r-2, r*2+4, r*2+4, r+2, ring_col)

        tw, th = drv.get_text_size(str(idx+1))
        drv.print(str(idx+1), cx - tw//2, cy + r + 4, drv.WHITE)

    def _draw_swatch(self, idx):
        drv       = self._drv
        col565    = self._PALETTE[idx][2]
        sel       = (idx == self._sel_col)
        x         = self._SW_X + idx * (self._SW_W + self._SW_GAP)
        y         = self._SW_Y

        drv.fill_rect(x - 2, y - 2, self._SW_W + 4, self._SW_H + 4, drv.BLACK)

        fill = col565 if col565 else 0x1082
        drv.fill_rect(x, y, self._SW_W, self._SW_H, fill)
        if sel:
            drv.draw_round_rectangle(x-2, y-2, self._SW_W+4, self._SW_H+4, 3, drv.WHITE)
        else:
            drv.rect(x, y, self._SW_W, self._SW_H, 0x39E7)

    def _draw_info(self):
        drv    = self._drv
        drv.fill_rect(0, 148, 240, 10, drv.BLACK)
        name   = self._PALETTE[self._sel_col][0]
        col565 = self._PALETTE[self._sel_col][2]
        led_str = 'LED ' + str(self._sel_led + 1)
        drv.print(led_str + '  ' + name, 8, 148, col565 if col565 else drv.WHITE)


class ButtonState:
    _FIELDS = ('left','right','up','down','a','b')

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
    AB_X     = 200
    AB_Y     = 120
    AB_W     = 44
    AB_H     = 44
    AB_OFF   = 5
    AB_R     = 22

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
        table  = {
            'up':    (dx + sx,               dy,                      dw,dh,dr,'^'),
            'left':  (dx,                    dy + sy,                 dw,dh,dr,'<'),
            'right': (dx + sx*2,             dy + sy,                 dw,dh,dr,'>'),
            'down':  (dx + sx,               dy + sy*2,               dw,dh,dr,'v'),
            'a':     (ax,                    ay,                      aw,ah,dr,'A'),
            'b':     (ax + aw + self.AB_OFF, ay - ah - self.AB_OFF,   aw,ah,dr,'B'),
        }
        if name not in table:
            raise ValueError('Unknown button: ' + name)
        return table[name]

    def _draw_btn(self, name, pressed):
        drv = self._drv
        x, y, w, h, r, label = self._geometry(name)
        if pressed:
            drv.fill_round_rectangle(x, y, w, h, r, drv.WHITE)
            tc = drv.BLACK
        else:
            drv.fill_round_rectangle(x, y, w, h, r, drv.BLACK)
            drv.draw_round_rectangle(x, y, w, h, r, drv.WHITE)
            tc = drv.WHITE
        tw, th = drv.get_text_size(label)
        drv.print(label, x+(w-tw)//2, y+(h-th)//2, tc,
                bg=drv.WHITE if pressed else drv.BLACK)

    def _draw_cross(self):
        drv = self._drv
        dx  = self.DPAD_X + (self.DPAD_W + self.DPAD_OFF)
        dy  = self.DPAD_Y + (self.DPAD_H + self.DPAD_OFF)
        drv.fill_round_rectangle(dx, dy, self.DPAD_W, self.DPAD_H, self.DPAD_R, drv.BLACK)
        drv.draw_round_rectangle(dx, dy, self.DPAD_W, self.DPAD_H, self.DPAD_R, drv.WHITE)


class IOTest:
    _STATES_N = 4

    # FPS for gamepad, gyro, buzzer, led
    _FPS = (60, 30, 30, 30)

    def __init__(self):
        self.drv     = st7789()
        self.input   = Input()
        self.buzzer  = Buzzer(Pin(PIN_BUZZER))
        self.led     = NeoPixel(Pin(PIN_NEOPIXEL), NEOPIXEL_N)
        self._cube   = RotatingCube(self.drv, CUBE_CX,   CUBE_CY,   CUBE_SZ)
        self._bubble = BubbleLevel(self.drv,  BUBBLE_CX, BUBBLE_CY, BUBBLE_R)
        self._values = GyroValues(self.drv)
        self._ui     = GamepadUI(self.drv, self.input)
        self._buz_ui = BuzzerUI(self.drv, self.buzzer)
        self._led_ui = LedUI(self.drv, self.led, NEOPIXEL_N)
        self._calib      = GyroCalibrator(self.drv, self.input)
        self._st         = 0
        self._ab_lock    = self.input.is_A() and self.input.is_B()
        self._calib_lock = False
        self._running = True
        self._fps_limiters = [FpsLimiter(fps) for fps in self._FPS]

    def run(self):
        if __name__ == '__main__':
            self.drv.fill(self.drv.BLACK)
            self.drv.draw_logo()
            sleep(2)
        self.drv.fill(self.drv.BLACK)

        while self._running:
            self._handle_next()

            if self._fps_limiters[self._st].ready():
                if self._st == 0:
                    self._ui.update()
                elif self._st == 1:
                    self._test_gyro()
                elif self._st == 2:
                    self._buz_ui.update(self.input)
                elif self._st == 3:
                    self._led_ui.update(self.input)

    def _handle_next(self):
        pressed = self.input.is_A() and self.input.is_B()
        if pressed and not self._ab_lock:
            self._st = (self._st + 1) % self._STATES_N
            self.drv.fill(self.drv.BLACK)
            self._ui.invalidate()
            self._cube.invalidate()
            self._bubble.invalidate()
            self._values.invalidate()
            self._buz_ui.invalidate()
            self._led_ui.invalidate()

            self._fps_limiters[self._st] = FpsLimiter(self._FPS[self._st])
        self._ab_lock = pressed
        if self.input.is_up() and self.input.is_B():
            self._running = False

    def _test_gyro(self):
        inp = self.input

        calib_pressed = inp.is_A() and inp.is_down()
        if calib_pressed and not self._calib_lock:
            self._calib_lock = True
            self._calib.run()

            self._cube.invalidate()
            self._bubble.invalidate()
            self._values.invalidate()
            return
        if not calib_pressed:
            self._calib_lock = False

        gx, gy, gz = inp.read_gyro()
        ax, ay, az = inp.read_accel()
        gx = round(gx, 2);  gy = round(gy, 2);  gz = round(gz, 2)
        ax = round(ax, 2);  ay = round(ay, 2);  az = round(az, 2)

        self._cube.update_rotation(gx, gy, gz)
        self._cube.draw()
        self._bubble.draw(ax, ay, az)
        self._values.draw(gx, gy, gz, ax, ay, az)


if __name__ == '__main__':
    IOTest().run()