def __getattr__(name):
    if name in ("Display", "st7789"):
        from .display_drivers.st7789_adapter import ST7789Driver
        return ST7789Driver

    if name == "Input":
        from .input import Input
        return Input
    
    if name == "IMU":
        from .IMU import IMU
        return IMU
    
    if name == "Actor":
        from .engine import Actor
        return Actor
    
    if name == "Color":
        from .engine import Color
        return Color
    
    if name == "DisplayDriver":
        from .engine import DisplayDriver
        return DisplayDriver
    
    if name == "Font":
        from .engine import Font
        return Font
    
    if name == "Game":
        from .engine import Game
        return Game
    
    if name == "GameImage":
        from .engine import GameImage
        return GameImage
    
    if name == "GameSound":
        from .engine import GameSound
        return GameSound
    
    if name == "World":
        from .engine import World
        return World
    if name == "Font":
        from .engine import Font
        return Font
    
    if name == "Buzzer":
        from .Buzzer import Buzzer
        return Buzzer
    
    if name == "demo":
        from .Demo import demo
        return demo
    
    if name == "iotest":
        from .IO_Test import iotest
        return iotest
    
    raise AttributeError("module '{}' has no attribute '{}'".format(__name__, name))


#! Fake import, don't touch
try:
    _ = 1 / 0
except ZeroDivisionError:
    FAKE_IMPORT = False

if FAKE_IMPORT:  # type: ignore
    from .engine import *
    from .display_drivers.st7789_adapter import ST7789Driver as st7789
    from .display_drivers.st7789_adapter import ST7789Driver as Display
    from .Demo import demo
    from .input import Input
    from .IO_Test import iotest
    from .Buzzer import Buzzer