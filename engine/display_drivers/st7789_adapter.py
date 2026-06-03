from machine import Pin, SPI      # type: ignore
import st7789                     # type: ignore
import vga2_8x16  as _font_small  # type: ignore
import vga2_10x20 as _font_medium # type: ignore
import vga2_16x32 as _font_bold   # type: ignore

import math
from engine.GameEngine import DisplayDriver, Color



class ST7789Driver(DisplayDriver):
    """
    Adapter ST7789 (240x320) -> DisplayDriver.

    Parametres
    ----------
    rotation : int
        Display orientation (0-3). default 1 (landscape).
    spi_id : int
        Number of SPI bus. default 0.
    baudrate : int
        Frecquency of SPI. default 40 МГц.
    pin_sck, pin_mosi : int
        SPI pins.
    pin_reset, pin_cs, pin_dc : int
        Controll pins.
    """

    # -- Цвета (RGB565) ------------------------------------------------------
    BLACK   = st7789.BLACK
    WHITE   = st7789.WHITE
    RED     = st7789.RED
    GREEN   = st7789.GREEN
    BLUE    = st7789.BLUE
    CYAN    = st7789.CYAN
    MAGENTA = st7789.MAGENTA
    YELLOW  = st7789.YELLOW

    # -- fonst --------------------------------------------------------------
    FONT_SMALL  = _font_small
    FONT_MEDIUM = _font_medium
    FONT_BOLD   = _font_bold

    def __init__(
        self,
        width = 240, # sizes in default orientation
        height = 320,
        rotation: int = 1,
        spi_id: int = 0,
        baudrate: int = 40_000_000,
        pin_sck: int  = 18,
        pin_mosi: int = 19,
        pin_reset: int = 22,
        pin_cs: int   = 21,
        pin_dc: int   = 20,
        options: int  = 0,
        buffer_size: int = 0,
    ):
        self._rotation = rotation
        
        # Physical sizes 
        if self._rotation in (0, 2):
            self.width  = width
            self.height = height
        else:
            self.width  = height
            self.height = width

        super().__init__(self.width, self.height)

        
        self._spi = SPI(
            spi_id,
            baudrate=baudrate,
            sck=Pin(pin_sck),
            mosi=Pin(pin_mosi),
        )
        self._drv = st7789.ST7789(
            self._spi,
            240, 320,
            reset=Pin(pin_reset, Pin.OUT),
            cs=Pin(pin_cs,    Pin.OUT),
            dc=Pin(pin_dc,    Pin.OUT),
            rotation=rotation,
            options=options,
            buffer_size=buffer_size,
        )
        self._drv.init()
        self._font = _font_medium   # default font for text()
        


    def init(self):
        # Init/reset display.
        self._drv.init()
        self._drv.fill(st7789.BLACK)

    def show(self):
        # ST7789 update after every write and don't use buffer, leave function for compatibility.
        pass

    def fill(self, color: int):
        self._drv.fill(color)

    def pixel(self, x: int, y: int, color: int):
        self._drv.pixel(x, y, color)

    def get_pixel(self, x: int, y: int) -> int:
        # ST7789 not support read state of pixel using spi
        return 0

    def color(self, r, g, b):
        return st7789.color565(r, g, b)


    def hline(self, x: int, y: int, w: int, color: int):
        self._drv.hline(x, y, w, color)

    def vline(self, x: int, y: int, h: int, color: int):
        self._drv.vline(x, y, h, color)

    def line(self, x1: int, y1: int, x2: int, y2: int, color: int):
        self._drv.line(x1, y1, x2, y2, color)

    def rect(self, x: int, y: int, w: int, h: int, color: int):
        self._drv.rect(x, y, w, h, color)

    def fill_rect(self, x: int, y: int, w: int, h: int, color: int):
        self._drv.fill_rect(x, y, w, h, color)

    def ellipse(self, x: int, y: int, rx: int, ry: int, color: int, fill: bool = False):
        super().ellipse(x, y, rx, ry, color, fill)

    def polygon(self, xs, ys, n: int, color: int, fill: bool = False):
        super().polygon(xs, ys, n, color, fill)

    def print(self, string: str, x: int, y: int, color: int,
            size: int = 1, bg: int = st7789.BLACK, font=None):
        fnt = font if font is not None else self._font
        self._drv.text(fnt, string, x, y, color, bg)

    def get_text_size(self, text: str, font=None):
        fnt = font if font is not None else self._font

        width = len(text) * fnt.WIDTH
        height = fnt.HEIGHT

        return width, height
    
    def draw_image(self, img, x: int, y: int):
        """
        Render GameImage to display using blit_buffer,
        which is significantly faster than pixel-by-pixel recording.
        """

        if isinstance(img, str):
            if ".png" in img:
                self._drv.png(img,x,y)
            if ".jpg" in img:
                self._drv.jpg(img,x,y)
            return

        self._drv.blit_buffer(img._buf, x, y, img.width, img.height)


    def set_rotation(self, rotation: int):
        self._rotation = rotation % 4
        
        if self._rotation in (0, 2):
            self.width = 240
            self.height = 320
        else:
            self.width = 320
            self.height = 240
        
        self._drv.rotation(self._rotation)

    def color565(self, r: int, g: int, b: int) -> int:
        return st7789.color565(r, g, b)

    def color_from(self, color: Color) -> int:
        return color.pack_rgb565()

    def set_font(self, font):
        self._font = font

    def draw_circle(
        self,
        color: int,
        cx: int, cy: int,
        r: int,
        width: int = 1,
        start_angle: int = 0,
        end_angle: int = 360,
    ):
        for dr in range(r, r + width):
            for deg in range(start_angle, end_angle):
                rad = math.pi / 180 * deg
                self.pixel(
                    round(cx + dr * math.cos(rad)),
                    round(cy + dr * math.sin(rad)),
                    color,
                )

    def draw_round_rectangle(
        self, x: int, y: int, w: int, h: int, r: int, color: int, width: int = 1
    ):
        r = max(1, min(r, min(w, h) // 2))
        for s in range(max(1, width)):
            xi, yi = x + s, y + s
            wi, hi = w - 2 * s, h - 2 * s
            ri = r - s
            self.hline(xi + ri,         yi,          wi - 2 * ri, color)
            self.hline(xi + ri,         yi + hi - 1, wi - 2 * ri, color)
            self.vline(xi,              yi + ri,     hi - 2 * ri, color)
            self.vline(xi + wi - 1,     yi + ri,     hi - 2 * ri, color)
            self._draw_quarter_circle(xi + ri,          yi + ri,          ri, color, 2)
            self._draw_quarter_circle(xi + wi - ri - 1, yi + ri,          ri, color, 3)
            self._draw_quarter_circle(xi + ri,          yi + hi - ri - 1, ri, color, 1)
            self._draw_quarter_circle(xi + wi - ri - 1, yi + hi - ri - 1, ri, color, 0)

    def fill_round_rectangle(self, x: int, y: int, w: int, h: int, r: int, color: int):
        r = max(1, min(r, min(w, h) // 2))
        self.fill_rect(x + r, y,         w - 2 * r, h,         color)
        self.fill_rect(x,     y + r,     r,         h - 2 * r, color)
        self.fill_rect(x + w - r, y + r, r,         h - 2 * r, color)
        for i in range(r):
            dx = int(math.sqrt(r * r - (r - i - 1) * (r - i - 1)))
            self.hline(x + r - dx,     y + i,          dx, color)
            self.hline(x + w - r,      y + i,          dx, color)
            self.hline(x + r - dx,     y + h - i - 1,  dx, color)
            self.hline(x + w - r,      y + h - i - 1,  dx, color)

    def circular_bar(
        self,
        cx: int, cy: int,
        r: int,
        value: float,
        min_value: float,
        max_value: float,
        width: int = 2,
        color: int = st7789.GREEN,
        background_color: int = st7789.WHITE,
    ):
        angle = int(
            min(max(value - min_value, 0), max_value - min_value)
            / (max_value - min_value)
            * 360
        )
        self.draw_circle(background_color, cx, cy, r, width, angle - 90, 270)
        self.draw_circle(color,            cx, cy, r, width, -90,       angle - 90)

    def _draw_quarter_circle(self, cx: int, cy: int, r: int, color: int, quadrant: int):
        """Draw quater of circle for rounded corners of draw_round_rectangle().
        quadrant: 0=bottom-right, 1=bottom-left, 2=top-left, 3=top-right
        """
        start = quadrant * 90
        for deg in range(start, start + 90):
            rad = math.pi / 180 * deg
            self.pixel(round(cx + r * math.cos(rad)), round(cy + r * math.sin(rad)), color)

    def __repr__(self):
        return "ST7789Driver({}x{}, rotation={})".format(
            self.width, self.height, self._rotation
        )
    
    def draw_polygon(self, center_x, center_y, r, n, bump=1.0, angle_offset=None, color=st7789.WHITE, fill=False):
        buf = []
        angle = 0
        angle_step = 360 / n
        if angle_offset is None:
            angle_offset = angle_step / 2 if n % 2 == 0 else 90
        for i in range(n + 1):
            dx = center_x + r * math.cos(math.pi/180*(angle-angle_offset))
            dy = center_y + r * math.sin(math.pi/180*(angle-angle_offset))
            angle += angle_step
            ddx = center_x + r * math.cos(math.pi/180*(angle-angle_offset))
            ddy = center_y + r * math.sin(math.pi/180*(angle-angle_offset))

            mid_x = dx + (ddx - dx) / 2
            mid_y = dy + (ddy - dy) / 2

            bdx = center_x + (mid_x - center_x) * bump
            bdy = center_y + (mid_y - center_y) * bump

            buf.append((round(dx), round(dy)))
            buf.append((round(bdx), round(bdy)))

        if fill:
            self._drv.fill_polygon(buf, 0, 0, color)
        else:
            self.polygon(buf, 0, 0, color)
            
    def draw_logo(self, x=120, y=100, r=80):

        self.fill(self.WHITE)

        first_str  = "Artisan"
        second_str = "Education"
        link_str    = "artisan.education"

        if self._rotation % 2 == 0 and self.width <= self.height:
            self.draw_polygon(x, y, r, 8, bump=0.7, fill=True, color=self.BLACK)
            self.draw_polygon(x, y, r * 0.7, 4, bump=0.3, fill=True, color=self.WHITE, angle_offset=0)
            self.print(first_str, x - r, y + r, font=self.FONT_BOLD, color=self.BLACK, bg=self.WHITE)
            self.print(second_str, x - r, y + r + 32, font=self.FONT_BOLD, color=self.BLACK, bg=self.WHITE)
            
        else:
            icon_x = 80
            icon_y = 120
            icon_r = 70

            self.draw_polygon(icon_x, icon_y, icon_r, 8, bump=0.7, fill=True, color=self.BLACK)
            self.draw_polygon(icon_x, icon_y, icon_r * 0.7, 4, bump=0.3, fill=True, color=self.WHITE, angle_offset=0)

            text_x = icon_x + icon_r + 16
            self.print(first_str, text_x, icon_y - 36, font=self.FONT_BOLD, color=self.BLACK, bg=self.WHITE)
            self.print(second_str, text_x, icon_y - 4,  font=self.FONT_BOLD, color=self.BLACK, bg=self.WHITE)

        # === print link in botton right corner
        (tw, th) = self.get_text_size(link_str) # get text size
        self.print(link_str, self.width - tw, self.height - th, color=self.BLACK, bg=self.WHITE)

