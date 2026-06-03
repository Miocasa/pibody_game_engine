from machine import Pin, SoftI2C  # type: ignore
from LSM6DS3 import LSM6DS3 # type: ignore

class Input():
    def __init__(
        self,
        pin_left  = Pin(0, Pin.IN, Pin.PULL_UP),
        pin_right = Pin(2, Pin.IN, Pin.PULL_UP),
        pin_up    = Pin(1, Pin.IN, Pin.PULL_UP),
        pin_down  = Pin(3, Pin.IN, Pin.PULL_UP),
        pin_b     = Pin(5, Pin.IN, Pin.PULL_UP),
        pin_a     = Pin(4, Pin.IN, Pin.PULL_UP),
        # if true, low level on pin will be active
        active_low_left:  bool = False,
        active_low_right: bool = False,
        active_low_up:    bool = False,
        active_low_down:  bool = False,
        active_low_b:     bool = False,
        active_low_a:     bool = False,

        imu_sda = Pin(8),
        imu_scl = Pin(9),
        i2c:SoftI2C = None
    ):
        self.PIN_LEFT  = pin_left
        self.PIN_RIGHT = pin_right
        self.PIN_UP    = pin_up
        self.PIN_DOWN  = pin_down
        self.PIN_B     = pin_b
        self.PIN_A     = pin_a


        # dictionary
        self._active_low = {
            self.PIN_LEFT:  active_low_left,
            self.PIN_RIGHT: active_low_right,
            self.PIN_UP:    active_low_up,
            self.PIN_DOWN:  active_low_down,
            self.PIN_B:     active_low_b,
            self.PIN_A:     active_low_a,
        }
        if i2c == None:
            self._i2c = SoftI2C(sda = imu_sda, scl = imu_scl)
        self._imu = LSM6DS3(self._i2c)

    # Imu gyro/accel methods
    def read_gyro(self):
        return self._imu.read_gyro()

    def read_accel(self):
        return self._imu.read_accel()

    def read_imu(self):
        return self._imu.read()
    
    # Button methods
    def btn(self, pin: Pin) -> bool:
        """helper"""
        if pin not in self._active_low:
            return False
            
        value = pin.value()
        # if active_low=True -> pressed when 0
        # if active_low=False -> pressed when 1
        return (value == 0) if self._active_low[pin] else (value == 1)

    # ==================== Удобные методы ====================
    def is_left(self)  -> bool: return self.btn(self.PIN_LEFT)
    def is_right(self) -> bool: return self.btn(self.PIN_RIGHT)
    def is_up(self)    -> bool: return self.btn(self.PIN_UP)
    def is_down(self)  -> bool: return self.btn(self.PIN_DOWN)
    def is_A(self)     -> bool: return self.btn(self.PIN_A)
    def is_B(self)     -> bool: return self.btn(self.PIN_B)