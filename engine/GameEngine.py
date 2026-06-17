import math
import random
from engine import Input
import time 
from micropython import const # type: ignore
class DisplayDriver:
    """
    Hardware Abstraction Layer for the display.
    All methods are stubs - fill them in for your display.

    Subclass responsibilities:
        - Override colour constants if your display uses a different encoding
            (e.g. monochrome: BLACK=0, WHITE=1).
        - Override font constants with actual font modules.
        - Implement every method marked  # === DISPLAY IMPL ===.
        - draw_polygon / draw_logo / all *_bar / draw_circle helpers have
            complete generic implementations here and normally do not need
            to be overridden.
    """

    # -- Colour constants (RGB565 defaults; override for monochrome etc.) ----
    BLACK   = 0x0000
    WHITE   = 0xFFFF
    RED     = 0xF800
    GREEN   = 0x07E0
    BLUE    = 0x001F
    CYAN    = 0x07FF
    MAGENTA = 0xF81F
    YELLOW  = 0xFFE0

    # -- Font constants (override in subclass with real font modules) ---------
    FONT_SMALL  = None
    FONT_MEDIUM = None
    FONT_BOLD   = None


    def __init__(self, width: int, height: int):
        self.width     = width
        self.height    = height
        self._rotation = 0
        self._font     = None



    def init(self):
        """Initialise / reset the display."""
        # === DISPLAY IMPL ===

    def show(self):
        """Flush framebuffer to screen (no-op for displays without a buffer)."""
        # === DISPLAY IMPL ===

    def fill(self, color: int):
        """Fill the entire screen with color."""
        # === DISPLAY IMPL ===

    def pixel(self, x: int, y: int, color: int):
        """Draw a single pixel."""
        # === DISPLAY IMPL ===

    def get_pixel(self, x: int, y: int) -> int:
        """Return the packed colour at (x, y)."""
        # === DISPLAY IMPL ===
        return 0

    # -- Lines & basic shapes -------------------------------------------------

    def hline(self, x: int, y: int, w: int, color: int):
        """Horizontal line."""
        for i in range(w):
            self.pixel(x + i, y, color)

    def vline(self, x: int, y: int, h: int, color: int):
        """Vertical line."""
        for i in range(h):
            self.pixel(x, y + i, color)

    def line(self, x1: int, y1: int, x2: int, y2: int, color: int):
        """Bresenham line."""
        dx = abs(x2 - x1); dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            self.pixel(x1, y1, color)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy; x1 += sx
            if e2 < dx:
                err += dx; y1 += sy

    def rect(self, x: int, y: int, w: int, h: int, color: int):
        """Rectangle outline."""
        self.hline(x,         y,         w, color)
        self.hline(x,         y + h - 1, w, color)
        self.vline(x,         y,         h, color)
        self.vline(x + w - 1, y,         h, color)

    def fill_rect(self, x: int, y: int, w: int, h: int, color: int):
        """Filled rectangle."""
        for row in range(h):
            self.hline(x, y + row, w, color)

    def ellipse(self, x: int, y: int, rx: int, ry: int,
                color: int, fill: bool = False):
        """Ellipse (Bresenham algorithm)."""
        if rx == 0 or ry == 0:
            return
        x0, y0 = x, y
        dx, dy = 0, ry
        rx2, ry2 = rx * rx, ry * ry
        err = ry2 - (2 * ry - 1) * rx2
        while dy >= 0:
            if fill:
                self.hline(x0 - dx, y0 + dy, 2 * dx + 1, color)
                self.hline(x0 - dx, y0 - dy, 2 * dx + 1, color)
            else:
                self.pixel(x0 + dx, y0 + dy, color)
                self.pixel(x0 - dx, y0 + dy, color)
                self.pixel(x0 + dx, y0 - dy, color)
                self.pixel(x0 - dx, y0 - dy, color)
            e2 = 2 * err
            if e2 < (2 * dx + 1) * ry2:
                dx += 1; err += (2 * dx + 1) * ry2
            if e2 > -(2 * dy - 1) * rx2:
                dy -= 1; err -= (2 * dy - 1) * rx2

    def polygon(self, xs, ys, n: int, color: int, fill: bool = False):
        """Polygon. xs, ys - sequences of at least n vertex coordinates."""
        if fill:
            min_y = min(ys[:n]); max_y = max(ys[:n])
            for scan_y in range(min_y, max_y + 1):
                nodes = []
                j = n - 1
                for i in range(n):
                    if (ys[i] < scan_y <= ys[j]) or (ys[j] < scan_y <= ys[i]):
                        if ys[j] != ys[i]:
                            nx = xs[i] + (scan_y - ys[i]) * (xs[j] - xs[i]) // (ys[j] - ys[i])
                            nodes.append(nx)
                    j = i
                nodes.sort()
                for k in range(0, len(nodes) - 1, 2):
                    self.hline(nodes[k], scan_y,
                                nodes[k + 1] - nodes[k] + 1, color)
        else:
            for i in range(n):
                j = (i + 1) % n
                self.line(xs[i], ys[i], xs[j], ys[j], color)

    def print(self, string: str, x: int, y: int, color: int,
            size: int = 1, bg: int = 0, font=None):
        """Draw text."""
        # === DISPLAY IMPL ===

    def get_text_size(self, text: str, font=None):
        """Return (width, height) in pixels. Override in subclass."""
        # === DISPLAY IMPL ===
        return 0, 0

    def draw_image(self, img, x: int, y: int):
        """Draw a GameImage pixel by pixel."""
        for row in range(img.height):
            for col in range(img.width):
                c = img._get_pixel(col, row)
                if c is not None:
                    self.pixel(x + col, y + row, c)

    # -- Configuration --------------------------------------------------------

    def set_rotation(self, rotation: int):
        """Change orientation (0-3)."""
        self._rotation = rotation % 4

    def set_font(self, font):
        """Set default font for text()."""
        self._font = font

    # -- Colour helpers -------------------------------------------------------

    def color(self, r: int, g: int, b: int) -> int:
        """Pack RGB (0-255) -> RGB565."""
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

    def color565(self, r: int, g: int, b: int) -> int:
        """Alias for color()."""
        return self.color(r, g, b)

    def color_from(self, color) -> int:
        """Convert engine Color -> packed int."""
        return color.pack_rgb565()

    # -- Circles & arcs -------------------------------------------------------

    def draw_circle(self, color: int, cx: int, cy: int, r: int,
                    width: int = 1, start_angle: int = 0, end_angle: int = 360):
        """Arc or full circle. Angles in degrees, 0 = 3 o'clock, clockwise."""
        for dr in range(r, r + width):
            for deg in range(start_angle, end_angle):
                rad = math.pi / 180 * deg
                self.pixel(round(cx + dr * math.cos(rad)),
                           round(cy + dr * math.sin(rad)), color)

    def _draw_quarter_circle(self, cx: int, cy: int, r: int,
                            color: int, quadrant: int):
        """One quadrant for rounded corners. 0=BR, 1=BL, 2=TL, 3=TR."""
        start = quadrant * 90
        for deg in range(start, start + 90):
            rad = math.pi / 180 * deg
            self.pixel(round(cx + r * math.cos(rad)),
                       round(cy + r * math.sin(rad)), color)

    # -- Rounded rectangles ---------------------------------------------------

    def draw_round_rectangle(self, x: int, y: int, w: int, h: int,
                            r: int, color: int, width: int = 1):
        """Rectangle outline with rounded corners."""
        r = max(1, min(r, min(w, h) // 2))
        for s in range(max(1, width)):
            xi, yi = x + s, y + s
            wi, hi = w - 2 * s, h - 2 * s
            ri = r - s
            self.hline(xi + ri,          yi,          wi - 2 * ri, color)
            self.hline(xi + ri,          yi + hi - 1, wi - 2 * ri, color)
            self.vline(xi,               yi + ri,     hi - 2 * ri, color)
            self.vline(xi + wi - 1,      yi + ri,     hi - 2 * ri, color)
            self._draw_quarter_circle(xi + ri,          yi + ri,          ri, color, 2)
            self._draw_quarter_circle(xi + wi - ri - 1, yi + ri,          ri, color, 3)
            self._draw_quarter_circle(xi + ri,          yi + hi - ri - 1, ri, color, 1)
            self._draw_quarter_circle(xi + wi - ri - 1, yi + hi - ri - 1, ri, color, 0)

    def fill_round_rectangle(self, x: int, y: int, w: int, h: int,
                            r: int, color: int):
        """Filled rectangle with rounded corners."""
        r = max(1, min(r, min(w, h) // 2))
        self.fill_rect(x + r,     y,     w - 2 * r, h,         color)
        self.fill_rect(x,         y + r, r,         h - 2 * r, color)
        self.fill_rect(x + w - r, y + r, r,         h - 2 * r, color)
        for i in range(r):
            dx = int(math.sqrt(r * r - (r - i - 1) * (r - i - 1)))
            self.hline(x + r - dx,    y + i,         dx, color)
            self.hline(x + w - r,     y + i,         dx, color)
            self.hline(x + r - dx,    y + h - i - 1, dx, color)
            self.hline(x + w - r,     y + h - i - 1, dx, color)

    # -- Progress indicators --------------------------------------------------

    def linear_bar(self, x: int, y: int, length: int,
                    oat, min_value: float, max_value: float,
                    nt = 5, border: bool = False,
                    t = None, border_color: int = None,
                    d_color: int = None):
        """Horizontal linear progress bar."""
        if color            is None: color            = self.GREEN
        if border_color     is None: border_color     = self.WHITE
        if background_color is None: background_color = self.BLACK

        even = 1 - height % 2
        n    = (height - 1 - even) // 2

        if border:
            self.rect(x - 1, y - n - 1, length + 3, height + 2, border_color)
            line_color = background_color
        else:
            for i in range(2):
                self.vline(x - 1 - i,          y - n, height, border_color)
                self.vline(x + length + 1 + i,  y - n, height, border_color)
            line_color = border_color

        ratio  = min(max(value - min_value, 0), max_value - min_value) \
                / (max_value - min_value)
        filled = math.floor(length * ratio)

        for i in range(height):
            self.line(x, y - n + i, x + filled, y - n + i, color)
        for i in range(n):
            self.line(x + filled, y - 1 - i,        x + length - 1, y - 1 - i,        background_color)
            self.line(x + filled, y + 1 + even + i,  x + length - 1, y + 1 + even + i, background_color)
        self.line(x + filled, y,        x + length, y,        line_color)
        self.line(x + filled, y + even, x + length, y + even, line_color)

    def circular_bar(self, cx: int, cy: int, r: int,
                    value: float, min_value: float, max_value: float,
                    width: int = 2, color: int = None,
                    background_color: int = None):
        """Circular progress indicator."""
        if color            is None: color            = self.GREEN
        if background_color is None: background_color = self.WHITE

        angle = int(
            min(max(value - min_value, 0), max_value - min_value)
            / (max_value - min_value) * 360
        )
        self.draw_circle(background_color, cx, cy, r, width, angle - 90, 270)
        self.draw_circle(color,            cx, cy, r, width, -90,        angle - 90)

    # -- Polygon with bumped midpoints ----------------------------------------

    def draw_polygon(self, center_x: int, center_y: int, r: float, n: int,
                    bump: float = 1.0, angle_offset: float = None,
                    color: int = None, fill: bool = False):
        """
        Regular n-gon with optional bumped midpoints.
        bump < 1.0 - concave sides
        bump = 1.0 - straight sides
        bump > 1.0 - convex sides
        """
        if color is None:
            color = self.WHITE

        angle_step = 360.0 / n
        if angle_offset is None:
            angle_offset = angle_step / 2.0 if n % 2 == 0 else 90.0

        xs = []; ys = []
        angle = 0.0
        for _ in range(n):
            a0 = math.pi / 180.0 * (angle - angle_offset)
            vx = center_x + r * math.cos(a0)
            vy = center_y + r * math.sin(a0)
            angle_next = angle + angle_step
            a1 = math.pi / 180.0 * (angle_next - angle_offset)
            nx = center_x + r * math.cos(a1)
            ny = center_y + r * math.sin(a1)
            mid_x = (vx + nx) / 2.0
            mid_y = (vy + ny) / 2.0
            bx = center_x + (mid_x - center_x) * bump
            by = center_y + (mid_y - center_y) * bump
            xs.append(round(vx)); ys.append(round(vy))
            xs.append(round(bx)); ys.append(round(by))
            angle = angle_next

        self.polygon(xs, ys, len(xs), color, fill)

    # -- Logo -----------------------------------------------------------------

    def draw_logo(self, x: int = 120, y: int = 100, r: int = 80):
        """
        Draw the Artisan Education logo.
        Portrait  (rotation % 2 == 0): icon at top, text below.
        Landscape (rotation % 2 == 1): icon left, text right.
        URL always bottom-right.
        """
        self.fill(self.WHITE)
        first_str  = "Artisan"
        second_str = "Education"
        link_str   = "artisan.education"

        if self._rotation % 2 == 0:
            self.draw_polygon(x, y, r,       8, bump=0.7, fill=True,  color=self.BLACK)
            self.draw_polygon(x, y, r * 0.7, 4, bump=0.3, fill=True,  color=self.WHITE, angle_offset=0)
            tw1, th1 = self.get_text_size(first_str,  font=self.FONT_BOLD)
            tw2, th2 = self.get_text_size(second_str, font=self.FONT_BOLD)
            if th1 == 0: th1 = 32
            if th2 == 0: th2 = 32
            text_y = y + r + 8
            self.print(first_str,  x - tw1 // 2, text_y,
                        color=self.BLACK, bg=self.WHITE, font=self.FONT_BOLD)
            self.print(second_str, x - tw2 // 2, text_y + th1 + 4,
                        color=self.BLACK, bg=self.WHITE, font=self.FONT_BOLD)
        else:
            icon_r = min(r, self.height // 2 - 8)
            icon_x = icon_r + 16
            icon_y = self.height // 2
            self.draw_polygon(icon_x, icon_y, icon_r,       8, bump=0.7, fill=True,  color=self.BLACK)
            self.draw_polygon(icon_x, icon_y, icon_r * 0.7, 4, bump=0.3, fill=True,  color=self.WHITE, angle_offset=0)
            tw1, th1 = self.get_text_size(first_str,  font=self.FONT_BOLD)
            tw2, th2 = self.get_text_size(second_str, font=self.FONT_BOLD)
            if th1 == 0: th1 = 32
            if th2 == 0: th2 = 32
            block_h = th1 + 8 + th2
            text_x  = icon_x + icon_r + 20
            text_y  = icon_y - block_h // 2
            self.print(first_str,  text_x, text_y,
                        color=self.BLACK, bg=self.WHITE, font=self.FONT_BOLD)
            self.print(second_str, text_x, text_y + th1 + 8,
                        color=self.BLACK, bg=self.WHITE, font=self.FONT_BOLD)

        tw, th = self.get_text_size(link_str)
        if th == 0: th = 16
        self.print(link_str, self.width - tw, self.height - th,
                    color=self.BLACK, bg=self.WHITE)



#  SoundDriver - HAL for sound 
class SoundDriver:
    """
    Usage:
        Game.init(display, world, sound=Buzzer(12))
        # or later:
        Game.set_sound(Buzzer(12))
    """

    def volume(self, volume=None):
        # === SOUND IMPL ===
        pass

    def make_sound(self, freq, volume, duration):
        # === SOUND IMPL ===
        pass

    def beep(self):
        # === SOUND IMPL ===
        pass

    def boop(self):
        # === SOUND IMPL ===
        pass

    def on(self):
        # === SOUND IMPL ===
        pass

    def off(self):
        # === SOUND IMPL ===
        pass

    def note_to_freq(self, note: str):
        # === SOUND IMPL ===
        pass

    def play_note(self, note: str, volume=None, duration=0.5):
        # === SOUND IMPL ===
        pass

    def play_melody(self, melody, tempo=0.3):
        # === SOUND IMPL ===
        pass

class Color:
    """RGB color (r, g, b)."""
    WHITE      = None
    LIGHT_GRAY = None
    GRAY       = None
    DARK_GRAY  = None
    BLACK      = None
    RED        = None
    PINK       = None
    ORANGE     = None
    YELLOW     = None
    GREEN      = None
    MAGENTA    = None
    CYAN       = None
    BLUE       = None

    def __init__(self, r: int, g: int, b: int, a: int = 255):
        self.r = max(0, min(255, r))
        self.g = max(0, min(255, g))
        self.b = max(0, min(255, b))
        self.a = max(0, min(255, a))

    def pack_rgb565(self) -> int:
        return ((self.r & 0xF8) << 8) | ((self.g & 0xFC) << 3) | (self.b >> 3)

    def pack_rgb888(self) -> int:
        return (self.r << 16) | (self.g << 8) | self.b

    def pack(self) -> int:
        return self.pack_rgb565()

    @staticmethod
    def from_rgb565(value: int) -> "Color":
        r = (value >> 8) & 0xF8
        g = (value >> 3) & 0xFC
        b = (value << 3) & 0xF8
        return Color(r, g, b)

    def get_red(self) -> int:   return self.r
    def get_green(self) -> int: return self.g
    def get_blue(self) -> int:  return self.b
    def get_alpha(self) -> int: return self.a

    def brighter(self) -> "Color":
        factor = 0.7
        return Color(min(255, int(self.r / factor)),
                    min(255, int(self.g / factor)),
                    min(255, int(self.b / factor)), self.a)

    def darker(self) -> "Color":
        factor = 0.7
        return Color(int(self.r * factor), int(self.g * factor),
                     int(self.b * factor), self.a)

    def __eq__(self, other):
        if not isinstance(other, Color): return False
        return (self.r == other.r and self.g == other.g and
                self.b == other.b and self.a == other.a)

    def __repr__(self):
        return "Color(r={}, g={}, b={}, a={})".format(
            self.r, self.g, self.b, self.a)


Color.WHITE      = Color(255, 255, 255)
Color.LIGHT_GRAY = Color(192, 192, 192)
Color.GRAY       = Color(128, 128, 128)
Color.DARK_GRAY  = Color(64,  64,  64)
Color.BLACK      = Color(0,   0,   0)
Color.RED        = Color(255, 0,   0)
Color.PINK       = Color(255, 175, 175)
Color.ORANGE     = Color(255, 200, 0)
Color.YELLOW     = Color(255, 255, 0)
Color.GREEN      = Color(0,   255, 0)
Color.MAGENTA    = Color(255, 0,   255)
Color.CYAN       = Color(0,   255, 255)
Color.BLUE       = Color(0,   0,   255)


# =============================================================================
#  Font
# =============================================================================

class Font:
    def __init__(self, name_or_bold=None, bold=False, italic=False, size=12):
        if isinstance(name_or_bold, bool):
            self._bold = name_or_bold; self._italic = bold
            self._size = italic if isinstance(italic, int) else size
            self._name = "sans-serif"
        elif isinstance(name_or_bold, int):
            self._size = name_or_bold; self._bold = False
            self._italic = False; self._name = "sans-serif"
        elif isinstance(name_or_bold, str):
            self._name = name_or_bold
            if isinstance(bold, int):
                self._size = bold; self._bold = False; self._italic = False
            else:
                self._bold = bold; self._italic = italic; self._size = size
        else:
            self._name = "sans-serif"; self._bold = bold
            self._italic = italic; self._size = size

    def get_name(self) -> str:   return self._name
    def get_size(self) -> int:   return self._size
    def is_bold(self) -> bool:   return self._bold
    def is_italic(self) -> bool: return self._italic
    def is_plain(self) -> bool:  return not self._bold and not self._italic

    def derive_font(self, size: float) -> "Font":
        return Font(self._name, self._bold, self._italic, int(size))

    def __eq__(self, other):
        if not isinstance(other, Font): return False
        return (self._name == other._name and self._size == other._size and
                self._bold == other._bold and self._italic == other._italic)

    def __repr__(self):
        return "Font(name={}, size={}, bold={}, italic={})".format(
            self._name, self._size, self._bold, self._italic)


#  GameImage - offscreen canvas

class GameImage:
    _BYTES_PER_PIXEL = 2

    def __init__(self, width_or_src=None, height=None):
        if isinstance(width_or_src, int) and isinstance(height, int):
            self.width  = width_or_src
            self.height = height
            self._buf   = bytearray(self.width * self.height * self._BYTES_PER_PIXEL)
        elif isinstance(width_or_src, GameImage):
            self.width  = width_or_src.width
            self.height = width_or_src.height
            self._buf   = bytearray(width_or_src._buf)
        elif isinstance(width_or_src, str):
            self.width, self.height = self._load_file(width_or_src)
        else:
            self.width = 1; self.height = 1
            self._buf = bytearray(self._BYTES_PER_PIXEL)
        self._color        = Color.BLACK
        self._font         = Font(12)
        self._transparency = 255

    def _load_file(self, filename: str):
        # === DISPLAY IMPL: add BMP/PNG parser ===
        self._buf = bytearray(2)
        return 1, 1

    def _idx(self, x: int, y: int) -> int:
        return (y * self.width + x) * self._BYTES_PER_PIXEL

    def _get_pixel(self, x: int, y: int) -> int:
        i = self._idx(x, y)
        return (self._buf[i] << 8) | self._buf[i + 1]

    def _set_pixel(self, x: int, y: int, color565: int):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = self._idx(x, y)
            self._buf[i]     = (color565 >> 8) & 0xFF
            self._buf[i + 1] = color565 & 0xFF

    def get_width(self) -> int:  return self.width
    def get_height(self) -> int: return self.height
    def get_color(self) -> Color:        return self._color
    def set_color(self, color: Color):   self._color = color
    def get_font(self) -> Font:          return self._font
    def set_font(self, font: Font):      self._font = font
    def get_transparency(self) -> int:   return self._transparency
    def set_transparency(self, t: int):  self._transparency = max(0, min(255, t))

    def set_color_at(self, x: int, y: int, color: Color):
        self._set_pixel(x, y, color.pack())

    def clear(self):
        for i in range(len(self._buf)): self._buf[i] = 0

    def fill(self):
        c = self._color.pack()
        for y in range(self.height):
            for x in range(self.width):
                self._set_pixel(x, y, c)

    def fill_rect(self, x: int, y: int, w: int, h: int):
        c = self._color.pack()
        for row in range(h):
            for col in range(w):
                self._set_pixel(x + col, y + row, c)

    def draw_rect(self, x: int, y: int, w: int, h: int):
        c = self._color.pack()
        for col in range(w):
            self._set_pixel(x + col, y, c)
            self._set_pixel(x + col, y + h - 1, c)
        for row in range(h):
            self._set_pixel(x, y + row, c)
            self._set_pixel(x + w - 1, y + row, c)

    def draw_line(self, x1: int, y1: int, x2: int, y2: int):
        c = self._color.pack()
        dx = abs(x2 - x1); dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1; sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            self._set_pixel(x1, y1, c)
            if x1 == x2 and y1 == y2: break
            e2 = 2 * err
            if e2 > -dy: err -= dy; x1 += sx
            if e2 < dx:  err += dx; y1 += sy

    def fill_oval(self, x: int, y: int, w: int, h: int):
        c = self._color.pack()
        cx = x + w // 2; cy = y + h // 2
        rx = w // 2;     ry = h // 2
        if rx == 0 or ry == 0: return
        for py in range(-ry, ry + 1):
            dx2 = rx * rx * (1 - (py * py) / (ry * ry))
            if dx2 < 0: dx2 = 0
            for px in range(-int(math.sqrt(dx2)), int(math.sqrt(dx2)) + 1):
                self._set_pixel(cx + px, cy + py, c)

    def draw_oval(self, x: int, y: int, w: int, h: int):
        c = self._color.pack()
        cx = x + w // 2; cy = y + h // 2
        rx = w // 2;     ry = h // 2
        if rx == 0 or ry == 0: return
        dx, dy_val = 0, ry
        rx2, ry2 = rx * rx, ry * ry
        err = ry2 - (2 * ry - 1) * rx2
        while dy_val >= 0:
            self._set_pixel(cx + dx, cy + dy_val, c)
            self._set_pixel(cx - dx, cy + dy_val, c)
            self._set_pixel(cx + dx, cy - dy_val, c)
            self._set_pixel(cx - dx, cy - dy_val, c)
            e2 = 2 * err
            if e2 < (2 * dx + 1) * ry2:    dx += 1;    err += (2 * dx + 1) * ry2
            if e2 > -(2 * dy_val - 1) * rx2: dy_val -= 1; err -= (2 * dy_val - 1) * rx2

    def fill_polygon(self, x_points, y_points, n_points: int):
        c = self._color.pack()
        min_y = min(y_points[:n_points]); max_y = max(y_points[:n_points])
        for scan_y in range(min_y, max_y + 1):
            nodes = []; j = n_points - 1
            for i in range(n_points):
                if ((y_points[i] < scan_y <= y_points[j]) or
                        (y_points[j] < scan_y <= y_points[i])):
                    if y_points[j] != y_points[i]:
                        nx = (x_points[i] + (scan_y - y_points[i]) *
                              (x_points[j] - x_points[i]) //
                                (y_points[j] - y_points[i]))
                        nodes.append(nx)
                j = i
            nodes.sort()
            for k in range(0, len(nodes) - 1, 2):
                for px in range(nodes[k], nodes[k + 1] + 1):
                    self._set_pixel(px, scan_y, c)

    def draw_polygon(self, x_points, y_points, n_points: int):
        for i in range(n_points):
            j = (i + 1) % n_points
            self.draw_line(x_points[i], y_points[i], x_points[j], y_points[j])

    def draw_string(self, string: str, x: int, y: int):
        # === DISPLAY IMPL:
        pass

    def draw_image(self, image: "GameImage", x: int, y: int):
        for row in range(image.height):
            for col in range(image.width):
                self._set_pixel(x + col, y + row, image._get_pixel(col, row))

    def rotate(self, degrees: int):
        degrees = degrees % 360
        if degrees == 0: return
        if degrees == 90:
            new_buf = bytearray(self.width * self.height * self._BYTES_PER_PIXEL)
            nw, nh = self.height, self.width
            for y in range(self.height):
                for x in range(self.width):
                    nx = self.height - 1 - y; ny = x
                    ni = (ny * nw + nx) * self._BYTES_PER_PIXEL
                    oi = self._idx(x, y)
                    new_buf[ni] = self._buf[oi]; new_buf[ni+1] = self._buf[oi+1]
            self._buf = new_buf; self.width, self.height = nw, nh
        elif degrees == 180:
            new_buf = bytearray(len(self._buf))
            total = self.width * self.height
            for i in range(total):
                j = (total - 1 - i) * self._BYTES_PER_PIXEL
                k = i * self._BYTES_PER_PIXEL
                new_buf[j] = self._buf[k]; new_buf[j+1] = self._buf[k+1]
            self._buf = new_buf
        elif degrees == 270:
            self.rotate(90); self.rotate(90); self.rotate(90)

    def scale(self, new_w: int, new_h: int):
        new_buf = bytearray(new_w * new_h * self._BYTES_PER_PIXEL)
        for ny in range(new_h):
            for nx in range(new_w):
                ox = nx * self.width  // new_w
                oy = ny * self.height // new_h
                c  = self._get_pixel(ox, oy)
                ni = (ny * new_w + nx) * self._BYTES_PER_PIXEL
                new_buf[ni] = (c >> 8) & 0xFF; new_buf[ni+1] = c & 0xFF
        self._buf = new_buf; self.width = new_w; self.height = new_h

    def mirror_horizontally(self):
        for y in range(self.height):
            for x in range(self.width // 2):
                a = self._idx(x, y); b = self._idx(self.width - 1 - x, y)
                self._buf[a], self._buf[b]     = self._buf[b], self._buf[a]
                self._buf[a+1], self._buf[b+1] = self._buf[b+1], self._buf[a+1]

    def mirror_vertically(self):
        for y in range(self.height // 2):
            for x in range(self.width):
                a = self._idx(x, y); b = self._idx(x, self.height - 1 - y)
                self._buf[a], self._buf[b]     = self._buf[b], self._buf[a]
                self._buf[a+1], self._buf[b+1] = self._buf[b+1], self._buf[a+1]

    def __repr__(self):
        return "GameImage({}x{})".format(self.width, self.height)


class GameSound:
    def __init__(self, source):
        # source: note str, melody list, or filename str
        self._source  = source
        self._volume  = 1.0      # 0.0 - 1.0
        self._playing = False
        self._looping = False

    def _play_once(self):
        drv = Game._sound
        if drv is None:
            return
        src = self._source
        if isinstance(src, list):
            drv.play_melody(src)
        elif isinstance(src, str): # try as note name; fall back to beep for filenames
            try:
                drv.play_note(src, volume=self._volume)
            except (ValueError, AttributeError):
                drv.beep()
        else:
            drv.beep()

    def play(self):
        self._playing = True
        self._play_once()
        self._playing = False

    def play_loop(self):
        self._looping = True
        self._playing = True
        self._play_once()

    def stop(self):
        drv = Game._sound
        if drv:
            drv.off()
        self._playing = False
        self._looping = False

    def pause(self):
        drv = Game._sound
        if drv:
            drv.off()
        self._playing = False

    def is_playing(self) -> bool:
        return self._playing

    def get_volume(self) -> int:
        return int(self._volume * 100)

    def set_volume(self, level: int):
        self._volume = max(0.0, min(1.0, level / 100.0))
        drv = Game._sound
        if drv:
            drv.volume(self._volume)

    def __repr__(self):
        return "GameSound({}, playing={})".format(self._source, self._playing)



#  Game - simulation controller
class Game: # static class
    _world      = None
    _display    = None
    _sound      = None   # SoundDriver or subclass or None
    _running    = False
    _speed      = 50
    _keys_down  = set()
    _last_key   = None
    _prev_render_ms = 0
    _prev_ui_ms     = 0
    @classmethod
    def init(cls, display: DisplayDriver, world: "World", sound=None, fps: int = 30, ui_fps: int = 30):
        """
        @display - DisplayDriver (or subclass / adapter)
        @world   - World instance
        @sound   - Optional SoundDriver or subclass
        @fps     - Count of main game loop cycles per second
        @ui_fps  - draw_ui() calls per second
        """
        cls._display = display
        cls._world   = world
        cls._sound   = sound
        cls._fps     = fps
        cls._ui_fps  = ui_fps
        display.init()

    @classmethod
    def set_sound(cls, driver): 
        cls._sound = driver

    @classmethod
    def get_sound(cls):
        return cls._sound

    @classmethod
    def start(cls):
        cls._running = True

    @classmethod
    def stop(cls):
        cls._running = False

    @classmethod
    def set_world(cls, world: "World"):
        cls._world = world

    @classmethod
    def set_fps(cls, fps: int):
        cls._fps = max(1, min(60, fps))

    @classmethod
    def run(cls): 
        cls._running = True
        while cls._running:
            current_ms = time.ticks_ms() 

            if cls._world and current_ms - cls._prev_render_ms >= const(1000 / cls._fps):
                cls._world.act()
                for actor in list(cls._world._actors):
                    actor.act()
                cls._world._render()
                cls._prev_render_ms = current_ms

            if cls._world and current_ms - cls._prev_ui_ms >= const(1000 / cls._ui_fps):
                cls._world.draw_ui()
                cls._prev_ui_ms = current_ms

    @classmethod
    def _tick_input(cls):
        # === DISPLAY IMPL: fill _keys_down and _last_key from GPIO/UART/USB ===
        pass

    @staticmethod
    def get_random_number(limit: int) -> int:
        return random.randint(0, limit - 1)

    @staticmethod
    def play_sound(source):
        GameSound(source).play()

    @staticmethod
    def get_mic_level() -> int:
        # === DISPLAY IMPL: ADC / PWM / I2S ===
        return 0

class World:
    def __init__(self, world_width: int, world_height: int,
                cell_size: int = 1, input=None, bounded: bool = True):
        self._width = world_width
        self._height = world_height
        self._cell_size = cell_size
        self._bounded = bounded
        self._actors = []
        self._bg = None
        self._bg_color: Color = Color.BLACK
        self.input:Input = input
        self._paint_order = ()

        self._dirty_rects = []
    
    def get_display(self):
        return Game._display
    
    def set_background(self, source):
        if isinstance(source, Color):
            self._bg_color = source
            self._bg = None
        elif isinstance(source, (str, GameImage)):
            self._bg = GameImage(source) if isinstance(source, str) else source

    def add_object(self, actor: "Actor", x: int, y: int):
        actor._world = self
        actor._x = x
        actor._y = y
        actor._prev_x = x
        actor._prev_y = y
        self._actors.append(actor)
        actor.added_to_world(self)

    def remove_object(self, actor: "Actor"):
        if actor in self._actors:
            if actor._prev_x is not None and actor.get_image():
                img = actor.get_image()
                px = actor._prev_x * self._cell_size
                py = actor._prev_y * self._cell_size
                self._clear_area(Game._display, px, py, img.width, img.height)
            self._actors.remove(actor)
            actor._world = None
    
    def remove_objects(self, actors: list["Actor"]):
        for actor in actors:
            if actor in self._actors:
                if actor._prev_x is not None and actor.get_image():
                    img = actor.get_image()
                    px = actor._prev_x * self._cell_size
                    py = actor._prev_y * self._cell_size
                    self._clear_area(Game._display, px, py, img.width, img.height)
                self._actors.remove(actor)
                actor._world = None

    def get_objets(self):
        return self._actors
    
    def set_paint_order(self, *classes):
        self._paint_order = classes

    def _render(self):
        drv = Game._display
        if not drv:
            return

        cs = self._cell_size
        ordered = self._get_ordered_actors()

        for actor in ordered:
            img = actor.get_image()
            if not img:
                continue

            nx = actor._x * cs
            ny = actor._y * cs
            w  = img.width
            h  = img.height

            ox = (actor._prev_x * cs) if actor._prev_x is not None else nx
            oy = (actor._prev_y * cs) if actor._prev_y is not None else ny
            moved = (nx != ox or ny != oy)

            drv.draw_image(img, nx, ny)

            if moved:
                dx = nx - ox
                dy = ny - oy

                if 0 < dx < w:
                    self._clear_area(drv, ox, oy, dx, h)
                elif -w < dx < 0:
                    self._clear_area(drv, nx + w, oy, -dx, h)
                elif abs(dx) >= w:
                    self._clear_area(drv, ox, oy, w, h)

                if abs(dx) < w:
                    sx = ox + max(dx, 0)
                    sw = w - abs(dx)
                    if 0 < dy < h:
                        self._clear_area(drv, sx, oy, sw, dy)
                    elif -h < dy < 0:
                        self._clear_area(drv, sx, ny + h, sw, -dy)
                    elif abs(dy) >= h:
                        self._clear_area(drv, sx, oy, sw, h)

            actor._prev_x = actor._x
            actor._prev_y = actor._y
        drv.show()

    def _clear_old_positions(self, drv):
        cs = self._cell_size

        for actor in self._actors:
            img = actor.get_image()
            if not img or actor._prev_x is None:
                continue

            px = actor._prev_x * cs
            py = actor._prev_y * cs

            if actor._x != actor._prev_x or actor._y != actor._prev_y:
                self._clear_area(drv, px, py, img.width, img.height)

    def _draw_actors(self, drv):
        cs = self._cell_size
        ordered = self._get_ordered_actors()

        for actor in ordered:
            img = actor.get_image()
            if not img:
                continue

            px = actor._x * cs
            py = actor._y * cs

            drv.draw_image(img, px, py)

            actor._prev_x = actor._x
            actor._prev_y = actor._y

    def _clear_area(self, drv, x: int, y: int, w: int, h: int):
        if self._bg:
            for dy in range(h):
                for dx in range(w):
                    if 0 <= x + dx < self._width and 0 <= y + dy < self._height:
                        c = self._bg._get_pixel(x + dx, y + dy)
                        drv.pixel(x + dx, y + dy, c)
        else:
            drv.fill_rect(x, y, w, h, self._bg_color.pack())

    def _get_ordered_actors(self):
        ordered = []
        seen = set()
        for cls in self._paint_order:
            for a in self._actors:
                if isinstance(a, cls) and id(a) not in seen:
                    ordered.append(a)
                    seen.add(id(a))
        for a in self._actors:
            if id(a) not in seen:
                ordered.append(a)
        return ordered
    
    def get_object_by_cls(self, cls):
        for a in self._actors:
            if (cls is None or isinstance(a, cls)):
                return a
        return None
    
    def get_objects_by_cls(self, cls) -> list:
        return [
            a for a in self._actors
            if (cls is None or isinstance(a, cls))
        ]

    def get_objects_at(self, x: int, y: int, cls) -> list:
        return [
            a for a in self._actors
            if (cls is None or isinstance(a, cls)) and a._x == x and a._y == y
        ]
    
    def draw_ui(self):
        pass

    def get_width(self):     return self._width
    def get_height(self):    return self._height
    def get_cell_size(self): return self._cell_size
    def act(self):           pass

class Actor: 
    #* Base class for world objects. Override act() in subclass.
    def __init__(self):
        self._world:World = None
        self._x           = 0
        self._y           = 0
        self._rotation    = 0
        self._image:GameImage = None
        self._sleep       = 0
        self._prev_x:int  = None
        self._prev_y:int  = None

    def act(self):          pass
    def added_to_world(self, world: World): pass

    def get_width(self) -> int:
        return self._image.get_width()

    def get_height(self) -> int:
        return self._image.get_height()
    
    def get_x(self) -> int:
        if self._world is None: raise RuntimeError("Actor not in world")
        return self._x
    
    def get_y(self) -> int:
        if self._world is None: raise RuntimeError("Actor not in world")
        return self._y

    def set_location(self, x: int, y: int):
        if self._world and self._world._bounded:
            x = max(0, min(self._world.get_width()  - 1, x))
            y = max(0, min(self._world.get_height() - 1, y))
        self._x = x; self._y = y

    def get_rotation(self) -> int:  return self._rotation

    def set_rotation(self, rotation: int):
        self._rotation = rotation % 360

    def turn(self, amount: int):
        self.set_rotation(self._rotation + amount)

    def turn_towards(self, x: int, y: int):
        dx = x - self._x; dy = y - self._y
        self.set_rotation(int(math.degrees(math.atan2(dy, dx))) % 360)

    def move_with_rotation(self, distance: int):
        rad = math.radians(self._rotation)

        x = self._x + int(round(math.cos(rad) * distance))
        y = self._y + int(round(math.sin(rad) * distance))

        x = max(0, min(self._world.get_width() - self.get_width(), x))
        y = max(0, min(self._world.get_height() - self.get_height(), y))
        self.set_location(
            x,
            y
        )

    def move(self, x: int, y: int):
        x = self._x + x
        y = self._y + y

        x = max(0, min(self._world.get_width() - self.get_width(), x))
        y = max(0, min(self._world.get_height() - self.get_height(), y))
        self.set_location(
            x,
            y
        )
        
    def is_at_edge(self) -> bool:
        if self._world is None: return False
        return (self._x <= 0 or self._x >= self._world.get_width()  - 1 or
                self._y <= 0 or self._y >= self._world.get_height() - 1)

    def sleep_for(self, n: int):   self._sleep = n
    def _should_act(self) -> bool:
        if self._sleep == 0: return True
        if self._sleep > 0:  self._sleep -= 1
        return False

    def get_image(self):            return self._image

    def set_image(self, source):
        if isinstance(source, str):         self._image = GameImage(source)
        elif isinstance(source, GameImage): self._image = source

    def get_world(self) -> World:   return self._world

    def get_world_of_type(self, world_class):
        if self._world is None: return None
        if not isinstance(self._world, world_class):
            raise TypeError("World is not an instance of {}".format(world_class))
        return self._world

    def _bounds(self):
        cs  = self._world._cell_size if self._world else 1
        img = self._image
        w   = img.width  if img else cs
        h   = img.height if img else cs
        return self._x * cs, self._y * cs, w, h

    @staticmethod
    def _rects_intersect(ax, ay, aw, ah, bx, by, bw, bh) -> bool:
        return (ax < bx + bw and ax + aw > bx and
                ay < by + bh and ay + ah > by)

    def intersects(self, other: "Actor") -> bool:
        return self._rects_intersect(*self._bounds(), *other._bounds())

    def is_touching(self, cls) -> bool:
        if self._world is None: return False
        for a in self._world._actors:
            if a is self: continue
            if cls and not isinstance(a, cls): continue
            if self.intersects(a): return True
        return False

    def get_intersecting_objects(self, cls) -> list:
        if self._world is None: return []
        return [a for a in self._world._actors
                if a is not self and
                (cls is None or isinstance(a, cls)) and
                self.intersects(a)]

    def get_one_intersecting_object(self, cls):
        lst = self.get_intersecting_objects(cls)
        return lst[0] if lst else None
    
    def get_objects_at_offset(self, dx: int, dy: int, cls) -> list:
        if self._world is None: return []
        return self._world.get_objects_at(self._x + dx, self._y + dy, cls)

    def get_one_object_at_offset(self, dx: int, dy: int, cls):
        lst = self.get_objects_at_offset(dx, dy, cls)
        return lst[0] if lst else None

    def get_neighbours(self, distance: int, diagonal: bool, cls) -> list:
        if self._world is None: return []
        result = []
        for a in self._world._actors:
            if a is self: continue
            if cls and not isinstance(a, cls): continue
            ddx = abs(a._x - self._x); ddy = abs(a._y - self._y)
            if diagonal:
                if ddx <= distance and ddy <= distance: result.append(a)
            else:
                if ddx + ddy <= distance: result.append(a)
        return result

    def get_objects_in_range(self, radius: int, cls) -> list:
        if self._world is None: return []
        return [a for a in self._world._actors
                if a is not self and
                (cls is None or isinstance(a, cls)) and
                math.sqrt((a._x - self._x)**2 + (a._y - self._y)**2) <= radius]

    def remove_touching(self, cls):
        target = self.get_one_intersecting_object(cls)
        if target and self._world:
            self._world.remove_object(target)

    def __repr__(self):
        return "{}(x={}, y={}, rot={})".format(
            type(self).__name__, self._x, self._y, self._rotation)