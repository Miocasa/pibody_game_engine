from machine import Pin, SoftI2C  # type: ignore
from engine.IMU import IMU


class Input(IMU):
    def __init__(
        self,
        pin_left  = Pin(0, Pin.IN, Pin.PULL_UP),
        pin_right = Pin(2, Pin.IN, Pin.PULL_UP),
        pin_up    = Pin(1, Pin.IN, Pin.PULL_UP),
        pin_down  = Pin(3, Pin.IN, Pin.PULL_UP),
        pin_b     = Pin(5, Pin.IN, Pin.PULL_UP),
        pin_a     = Pin(4, Pin.IN, Pin.PULL_UP),
        active_low_left  = False,
        active_low_right = False,
        active_low_up    = False,
        active_low_down  = False,
        active_low_b     = False,
        active_low_a     = False,
        imu_sda    = Pin(8),
        imu_scl    = Pin(9),
        i2c        = None,
        calib_file = None,
        load_calib = True,
    ):
        IMU.__init__(self, sda=imu_sda, scl=imu_scl, i2c=i2c,
                    calib_file=calib_file, load_calib=load_calib)

        self.PIN_LEFT  = pin_left
        self.PIN_RIGHT = pin_right
        self.PIN_UP    = pin_up
        self.PIN_DOWN  = pin_down
        self.PIN_B     = pin_b
        self.PIN_A     = pin_a

        self._active_low = {
            pin_left: active_low_left, pin_right: active_low_right,
            pin_up:   active_low_up,   pin_down:  active_low_down,
            pin_b:    active_low_b,    pin_a:     active_low_a,
        }

    def btn(self, pin):
        if pin not in self._active_low:
            return False
        v = pin.value()
        return (v == 0) if self._active_low[pin] else (v == 1)

    def is_left(self):  return self.btn(self.PIN_LEFT)
    def is_right(self): return self.btn(self.PIN_RIGHT)
    def is_up(self):    return self.btn(self.PIN_UP)
    def is_down(self):  return self.btn(self.PIN_DOWN)
    def is_A(self):     return self.btn(self.PIN_A)
    def is_B(self):     return self.btn(self.PIN_B)