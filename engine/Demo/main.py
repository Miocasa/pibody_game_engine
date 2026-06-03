from engine import (st7789, Input)
from .games_list import GamesInfoList
from time import sleep
input = Input()


class Demo:
    def __init__(self, display=st7789()):
        self.drv = display

        self._sel_pos  = 0
        self._prv_pos  = 0
        self._needs_redraw = True
        self._header_h = 0  # populated by _draw_header(), used by _draw_list()

        #* Layout constants
        self._item_h   = 22
        self._item_gap = 2

        #* Button debounce - init from current pin state to avoid phantom press on start
        self._btn_up_lock   = input.is_up()
        self._btn_down_lock = input.is_down()
        self._btn_a_lock    = input.is_A()

    # -- Main loop ----------------------------------------------
    def run(self):
        self.drv.fill(self.drv.BLACK)
        # self.drv.show()              # initialize display state BEFORE drawing anything

        self.drv.draw_logo()
        sleep(5)
        self.drv.fill(self.drv.BLACK)

        self._header_h = self._draw_header()
        self._needs_redraw = True
        
        
        
        while True:
            self._handle_input()
            if self._needs_redraw:
                self._draw_list()
                self.drv.show()
                self._needs_redraw = False

    # -- Input --------------------------------------------------
    def _handle_input(self):
        if input.is_up():
            if not self._btn_up_lock:
                self._move(-1)
                self._btn_up_lock = True
        else:
            self._btn_up_lock = False

        if input.is_down():
            if not self._btn_down_lock:
                self._move(1)
                self._btn_down_lock = True
        else:
            self._btn_down_lock = False

        if input.is_A():
            if not self._btn_a_lock:
                self._select()
                self._btn_a_lock = True
        else:
            self._btn_a_lock = False

    # -- Navigation ---------------------------------------------
    def _move(self, delta: int):
        new_pos = self._sel_pos + delta
        if 0 <= new_pos < len(GamesInfoList):
            self._prv_pos = self._sel_pos
            self._sel_pos = new_pos
            self._needs_redraw = True

    def _select(self):
        self.drv.fill(self.drv.BLACK)
        self.drv.show()
        GamesInfoList[self._sel_pos].call_func(self.drv, input)

        # game returned - restore menu
        self.drv.fill(self.drv.BLACK)
        self.drv.show()              # flush clear before redrawing menu
        self._header_h = self._draw_header()
        self._prv_pos  = self._sel_pos   # prevent ghost-erase on first redraw
        self._needs_redraw = True
        self._btn_a_lock   = input.is_A()

    # -- Drawing ------------------------------------------------
    def _draw_header(self) -> int:
        """Draw header bar, return its pixel height so _draw_list can sit below it."""
        text  = "Choose Game"
        bg    = self.drv.color(128, 128, 128)
        w     = self.drv.width
        (tw, th) = self.drv.get_text_size(text)
        bar_h = int(th * 1.6)
        self.drv.fill_rect(0, 0, w, bar_h, bg)
        self.drv.print(
            string = text,
            x      = int((w - tw) / 2),
            y      = int((bar_h - th) / 2),
            color  = self.drv.BLACK,
            size   = 2,
            bg     = bg,
        )
        return bar_h

    def _draw_list(self):
        x        = 20
        y        = self._header_h + 8   # dynamic: always 8px below actual header
        w        = self.drv.width
        txt_size = 1
        sel_bg   = self.drv.color(40, 40, 100)

        for i, game in enumerate(GamesInfoList):
            ty = y + i * (self._item_h + self._item_gap)

            if i == self._sel_pos:
                self.drv.fill_round_rectangle(
                    x - 4, ty - 2,
                    w - (x - 4) * 2, self._item_h,
                    4, sel_bg,
                )
                self.drv.print(
                    string = ">" + game.name,
                    x      = x,
                    y      = ty,
                    color  = self.drv.WHITE,
                    size   = txt_size,
                    bg     = sel_bg,
                )
            else:
                if i == self._prv_pos:
                    self.drv.fill_rect(
                        x - 4, ty - 2,
                        w - (x - 4) * 2, self._item_h,
                        self.drv.BLACK,
                    )
                self.drv.print(
                    string = " " + game.name,
                    x      = x,
                    y      = ty,
                    color  = self.drv.WHITE,
                    size   = txt_size,
                    bg     = self.drv.BLACK,
                )


if __name__ == "__main__":
    Demo().run()