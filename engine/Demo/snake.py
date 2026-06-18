import random
from engine import Actor, Color, GameImage, World, Input, Display, Game

CELL = 12
GRID_W = 12
GRID_H = 12
BORDER = 2
START_LEN = 3
MOVE_INTERVAL_BY_DIFF = {"easy": 8, "normal": 6, "hard": 4}

bg = Color(15, 15, 15)
wall_color = Color.GRAY

PLAY_W = GRID_W * CELL
PLAY_H = GRID_H * CELL

img_segment_body = GameImage(CELL, CELL)
img_segment_body.set_color(Color.GREEN)
img_segment_body.fill_rect(0, 0, CELL, CELL)
img_segment_body.set_color(Color.BLACK)
img_segment_body.draw_rect(0, 0, CELL, CELL)

img_segment_head = GameImage(CELL, CELL)
img_segment_head.set_color(Color.BLUE)
img_segment_head.fill_rect(0, 0, CELL, CELL)
img_segment_head.set_color(Color.BLACK)
img_segment_head.draw_rect(0, 0, CELL, CELL)

img_food = GameImage(CELL, CELL)
img_food.set_color(bg)
img_food.fill()
img_food.set_color(Color.RED)
img_food.fill_oval(0, 0, CELL, CELL)


img_wall = GameImage(CELL, CELL)
img_wall.set_color(wall_color)
img_wall.fill_rect(0, 0, CELL, CELL)
img_wall.set_color(Color.BLACK)
img_wall.draw_rect(0, 0, CELL, CELL)



class Segment(Actor):
    def __init__(self, is_head=False):
        super().__init__()
        self.set_image(img_segment_head if is_head else img_segment_body)

    def set_head(self, is_head):
        self.set_image(img_segment_head if is_head else img_segment_body)

    def act(self):
        pass


class Food(Actor):
    def __init__(self):
        super().__init__()
        self.set_image(img_food)

    def act(self):
        pass


class Wall(Actor):
    def __init__(self):
        super().__init__()
        self.set_image(img_wall)

    def act(self):
        pass


def build_maze():
    g = [[0] * GRID_W for _ in range(GRID_H)]
    for x in range(GRID_W):
        g[0][x] = 1
        g[GRID_H - 1][x] = 1
    for y in range(GRID_H):
        g[y][0] = 1
        g[y][GRID_W - 1] = 1
    for y in range(3, GRID_H - 3):
        if y % 2 == 1:
            for x in range(3, GRID_W - 3):
                if x % 4 == 0:
                    g[y][x] = 1
    return g


LEVELS = ["bounded", "borderless", "maze"]
LEVEL_NAMES = {"bounded": "Ограниченная", "borderless": "Бесконечная", "maze": "Лабиринт"}
DIFFS = ["easy", "normal", "hard"]
DIFF_NAMES = {"easy": "Лёгкая", "normal": "Средняя", "hard": "Сложная"}


class MenuWorld(World):
    def __init__(self, width, height, input_handler):
        super().__init__(width, height, cell_size=1, input=input_handler, bounded=False)
        self.set_background(bg)
        self.level_idx = 0
        self.diff_idx = 0
        self.selecting_level = True
        self.cooldown = 0

        self.y_level = 40
        self.y_diff  = 60

        self._drawn_static = False
        self._last_level_idx = None
        self._last_diff_idx = None
        self._last_selecting_level = None

    def act(self):
        inp = self.input
        
        if inp.is_B():
            print("B pressed")
            Game.stop()

        if self.cooldown > 0:
            self.cooldown -= 1
            return

        if inp.is_left() or inp.is_right():
            if self.selecting_level:
                if inp.is_left():
                    self.level_idx = (self.level_idx - 1) % len(LEVELS)
                else:
                    self.level_idx = (self.level_idx + 1) % len(LEVELS)
            else:
                if inp.is_left():
                    self.diff_idx = (self.diff_idx - 1) % len(DIFFS)
                else:
                    self.diff_idx = (self.diff_idx + 1) % len(DIFFS)
            self.cooldown = 6

        if inp.is_up() or inp.is_down():
            self.selecting_level = not self.selecting_level
            self.cooldown = 6

        if inp.is_A():
            level = LEVELS[self.level_idx]
            diff = DIFFS[self.diff_idx]
            self.get_display().fill(bg.pack())
            new_world = SnakeWorld(self.get_width(), self.get_height(), self.input, level, diff)
            Game.set_world(new_world)
            Game._prev_render_ms = 0
            Game._prev_ui_ms = 0

    def _draw_static(self, drv):
        drv.fill(bg.pack())

        title = "ЗМЕЙКА"
        tw, th = drv.get_text_size(title)
        drv.print(title, self.get_width() // 2 - tw // 2, 10,
                    color=Color.GREEN.pack(), bg=bg.pack())

        y = self.y_diff + 30
        drv.print("Влево/Вправо - переключить", 10, y,
                    color=Color.GRAY.pack(), bg=bg.pack())
        y += 16
        drv.print("Вверх/Вниз - выбрать", 10, y,
                    color=Color.GRAY.pack(), bg=bg.pack())
        y += 16
        drv.print("A - начать", 10, y,
                    color=Color.GRAY.pack(), bg=bg.pack())

        drv.show()
        self._drawn_static = True

    def _clear_line(self, drv, y, w=200, h=15):
        drv.fill_rect(10, y, w, h, bg.pack())

    def _draw_level_line(self, drv):
        lvl_color = Color.YELLOW.pack() if self.selecting_level else Color.WHITE.pack()
        prefix = "> " if self.selecting_level else "  "
        
        self._clear_line(drv, self.y_level, w = 300)
        drv.print(prefix + "Уровень: " + LEVEL_NAMES[LEVELS[self.level_idx]], 10, self.y_level,
                    color=lvl_color, bg=bg.pack())

    def _draw_diff_line(self, drv):
        diff_color = Color.YELLOW.pack() if not self.selecting_level else Color.WHITE.pack()
        prefix = "> " if not self.selecting_level else "  "
        self._clear_line(drv, self.y_diff)
        drv.print(prefix + "Сложность: " + DIFF_NAMES[DIFFS[self.diff_idx]], 10, self.y_diff,
                    color=diff_color, bg=bg.pack())

    def draw_ui(self):
        drv = self.get_display()
        if not drv:
            return

        if not self._drawn_static:
            self._draw_static(drv)
            self._draw_level_line(drv)
            self._draw_diff_line(drv)
            self._last_level_idx = self.level_idx
            self._last_diff_idx = self.diff_idx
            self._last_selecting_level = self.selecting_level
            drv.show()
            return

        changed = False

        if (self.level_idx != self._last_level_idx or
                self.selecting_level != self._last_selecting_level):
            self._draw_level_line(drv)
            changed = True

        if (self.diff_idx != self._last_diff_idx or
                self.selecting_level != self._last_selecting_level):
            self._draw_diff_line(drv)
            changed = True

        if changed:
            self._last_level_idx = self.level_idx
            self._last_diff_idx = self.diff_idx
            self._last_selecting_level = self.selecting_level
            drv.show()


class SnakeWorld(World):
    def __init__(self, width, height, input_handler, level="bounded", difficulty="normal"):
        super().__init__(width, height, cell_size=1, input=input_handler, bounded=False)
        self.set_background(bg)

        self.level = level
        self.difficulty = difficulty
        self.move_interval = MOVE_INTERVAL_BY_DIFF.get(difficulty, 6)

        self.cols = GRID_W
        self.rows = GRID_H

        self.ox = (width - PLAY_W) // 2
        self.oy = (height - PLAY_H) // 2

        self.dir = (1, 0)
        self.next_dir = (1, 0)

        self.over = False
        self.score = 0
        self.timer = 0
        self._over_drawn = False

        self.maze = None
        if level == "maze":
            self.maze = build_maze()
            self._spawn_walls()

        self.cells = []
        start_x = self.cols // 2
        start_y = self.rows // 2
        for i in range(START_LEN):
            cx = start_x - (START_LEN - 1 - i)
            self.cells.append((cx, start_y))

        if self.maze:
            self._fix_start_position()

        self.segments = []
        for i, (cx, cy) in enumerate(self.cells):
            seg = Segment(is_head=(i == len(self.cells) - 1))
            self.add_object(seg, self._px(cx), self._py(cy))
            self.segments.append(seg)

        self.food = Food()
        self.spawn_food()

        self._draw_border()

    def _px(self, cx):
        return self.ox + cx * CELL

    def _py(self, cy):
        return self.oy + cy * CELL

    def _is_wall(self, cx, cy):
        if self.maze is None:
            return False
        if cx < 0 or cx >= self.cols or cy < 0 or cy >= self.rows:
            return True
        return self.maze[cy][cx] == 1

    def _spawn_walls(self):
        for y in range(self.rows):
            for x in range(self.cols):
                if self.maze[y][x] == 1:
                    w = Wall()
                    self.add_object(w, self._px(x), self._py(y))

    def _fix_start_position(self):
        for y in range(self.rows):
            run = 0
            for x in range(self.cols):
                if not self._is_wall(x, y):
                    run += 1
                    if run >= START_LEN:
                        sx = x - START_LEN + 1
                        self.cells = [(sx + i, y) for i in range(START_LEN)]
                        return
                else:
                    run = 0

    def _draw_border(self):
        drv = self.get_display()
        if not drv:
            return
        x0 = self.ox - BORDER
        y0 = self.oy - BORDER
        w = PLAY_W + BORDER * 2
        h = PLAY_H + BORDER * 2
        for i in range(BORDER):
            drv.rect(x0 + i, y0 + i, w - 2 * i, h - 2 * i, Color.WHITE.pack())

    def spawn_food(self):
        while True:
            fx = random.randint(0, self.cols - 1)
            fy = random.randint(0, self.rows - 1)
            if (fx, fy) in self.cells:
                continue
            if self._is_wall(fx, fy):
                continue
            break
        if self.food not in self._actors:
            self.add_object(self.food, self._px(fx), self._py(fy))
        else:
            self.food.set_location(self._px(fx), self._py(fy))
        self.food_cell = (fx, fy)

    def game_over(self):
        self.over = True
        self._over_drawn = False
        self.remove_objects(self.get_objets())

    def act(self):
        inp = self.input
        
        if inp.is_B():
            print("B pressed")
            Game.stop()
        if self.over:
            if inp.is_A():
                print("A pressed")
                run_snake()
            return
        
        dx, dy = self.dir
        if inp.is_left() and dx == 0:
            self.next_dir = (-1, 0)
        elif inp.is_right() and dx == 0:
            self.next_dir = (1, 0)
        elif inp.is_up() and dy == 0:
            self.next_dir = (0, -1)
        elif inp.is_down() and dy == 0:
            self.next_dir = (0, 1)

        self.timer += 1
        if self.timer < self.move_interval:
            return
        self.timer = 0

        self.dir = self.next_dir
        dx, dy = self.dir

        head_x, head_y = self.cells[-1]
        new_x = head_x + dx
        new_y = head_y + dy

        if self.level == "borderless":
            new_x %= self.cols
            new_y %= self.rows
        elif self.level == "bounded":
            if new_x < 0 or new_x >= self.cols or new_y < 0 or new_y >= self.rows:
                self.game_over()
                return
        elif self.level == "maze":
            if self._is_wall(new_x, new_y):
                self.game_over()
                return

        new_head = (new_x, new_y)

        if new_head in self.cells:
            self.game_over()
            return

        ate = (new_head == self.food_cell)

        self.cells.append(new_head)

        if not ate:
            self.cells.pop(0)
            tail_seg = self.segments.pop(0)
            self.remove_object(tail_seg)
        else:
            self.score += 1

        new_seg = Segment(is_head=True)
        self.add_object(new_seg, self._px(new_x), self._py(new_y))
        self.segments.append(new_seg)

        if len(self.segments) >= 2:
            self.segments[-2].set_head(False)

        if ate:
            self.spawn_food()

    def draw_ui(self):
        drv = self.get_display()
        if not drv:
            return

        if self.over:
            if self._over_drawn:
                return
            self._over_drawn = True

            w, h = drv.width, drv.height
            dw, dh = 170, 90
            bx = (w - dw) // 2
            by = (h - dh) // 2

            drv.fill_rect(bx, by, dw, dh, Color.BLACK.pack())
            drv.rect(bx, by, dw, dh, Color.RED.pack())
            drv.rect(bx + 1, by + 1, dw - 2, dh - 2, Color.RED.pack())

            go_text = "GAME OVER"
            tw, th = drv.get_text_size(go_text)
            drv.print(go_text, w // 2 - tw // 2, by + 8,
                      color=Color.RED.pack(), bg=Color.BLACK.pack())

            score_text = "Очки: {}".format(self.score)
            tw2, th2 = drv.get_text_size(score_text)
            drv.print(score_text, w // 2 - tw2 // 2, by + 26,
                      color=Color.YELLOW.pack(), bg=Color.BLACK.pack())

            hint_a = "A - заново"
            tw3, _ = drv.get_text_size(hint_a)
            drv.print(hint_a, w // 2 - tw3 // 2, by + 50,
                      color=Color.GREEN.pack(), bg=Color.BLACK.pack())

            hint_b = "B - выход"
            tw4, _ = drv.get_text_size(hint_b)
            drv.print(hint_b, w // 2 - tw4 // 2, by + 66,
                      color=Color.GRAY.pack(), bg=Color.BLACK.pack())

            drv.show()
            return

        level_info = "{}  |  {}".format(
            LEVEL_NAMES.get(self.level, self.level),
            DIFF_NAMES.get(self.difficulty, self.difficulty),
        )
        score = "Score: {}".format(self.score)

        drv.print(level_info, 4, 0,
            color=Color.WHITE.pack(), bg=bg.pack()
        )
        drv.print(score, 4, 16,
            color=Color.WHITE.pack(), bg=bg.pack()
        )


input_conf   = None
display_conf = None

def run_snake(display=None, input=None):
    global display_conf
    global input_conf

    if display_conf is None:
        if display is None:
            display = Display()
        display_conf = display
    if input_conf is None:
        if input is None:
            input = Input()
        input_conf = input

    world = MenuWorld(display_conf.width, display_conf.height, input_conf)

    Game._running = True
    Game.init(display_conf, world, sound=None, fps=30, ui_fps=30)

    Game.start()

    Game.run()

if __name__ == "__main__":
    run_snake()