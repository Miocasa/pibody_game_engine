import random
from engine import Actor
from engine import Color
from engine import GameImage
from engine import World
from engine import Input
from engine import Display
from engine import Game

class Person(Actor):
  def __init__(self):
    super().__init__()
    img = GameImage(20, 20)
    img.set_color(Color.GREEN)
    img.fill_rect(0, 0, 20, 20)
    img.set_color(Color.WHITE)
    img.draw_rect(0, 0, 20, 20)
    self.set_image(img)
  def act(self):
    if self.get_world().input.is_B() == True:
      self.get_world().add_object(bullet(), (random.randint(0, 20)), (random.randint(0, 20)))

class bullet(Actor):
  def __init__(self):
    super().__init__()
    img = GameImage(10, 5)
    img.set_color(Color.RED)
    img.fill_rect(0, 0, 10, 5)
    img.set_color(Color.WHITE)
    img.draw_rect(0, 0, 10, 5)
    self.set_image(img)
  def act(self):
    pass

input_conf = Input()

display_conf = Display()

class MyWorld(World):
  def __init__(self, width, height, input_handler):
    super().__init__(width, height, cell_size=1, input=input_handler, bounded=True)
    pass

  def draw_ui(self):
    pass

  def act(self):
    if self.input.is_A() == True:
      self.add_object(Person(), (random.randint(20, 100)), (random.randint(20, 100)))
      print( len(self.get_objects_by_cls(Person)) )

world_Hello = MyWorld(display_conf.width, display_conf.height, input_conf)


Game._running = True
Game.init(display_conf, world_Hello, sound=None)
Game.start()
Game.run()
