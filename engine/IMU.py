from machine import SoftI2C, Pin  # type: ignore
from LSM6DS3 import LSM6DS3       # type: ignore
import json

_CALIB_FILE = 'gyro_offset.json'


class IMUCalibration:
    __slots__ = ('gx', 'gy', 'gz', 'ax', 'ay', 'az', '_file')

    def __init__(self, gx=0.0, gy=0.0, gz=0.0, ax=0.0, ay=0.0, az=0.0, file=_CALIB_FILE):
        self.gx = gx; self.gy = gy; self.gz = gz
        self.ax = ax; self.ay = ay; self.az = az
        self._file = file

    @classmethod
    def load(cls, file=_CALIB_FILE):
        try:
            with open(file, 'r') as f:
                d = json.load(f)
            return cls(d.get('gx',0.0), d.get('gy',0.0), d.get('gz',0.0),
                        d.get('ax',0.0), d.get('ay',0.0), d.get('az',0.0), file)
        except Exception:
            return cls(file=file)

    def set(self, gx, gy, gz, ax, ay, az):
        self.gx = gx; self.gy = gy; self.gz = gz
        self.ax = ax; self.ay = ay; self.az = az

    def reset(self):
        self.gx = self.gy = self.gz = 0.0
        self.ax = self.ay = self.az = 0.0

    def save(self, file=None):
        try:
            with open(file or self._file, 'w') as f:
                json.dump({'gx':self.gx,'gy':self.gy,'gz':self.gz,
                            'ax':self.ax,'ay':self.ay,'az':self.az}, f)
            return True
        except Exception:
            return False

    def apply_gyro(self, gx, gy, gz):
        return gx - self.gx, gy - self.gy, gz - self.gz

    def apply_accel(self, ax, ay, az):
        return ax - self.ax, ay - self.ay, az - self.az

    def __repr__(self):
        return 'IMUCalibration(g={},{},{} a={},{},{})'.format(
            self.gx, self.gy, self.gz, self.ax, self.ay, self.az)


class IMU:
    def __init__(self, sda=Pin(8), scl=Pin(9), i2c=None,
                calib_file=None, load_calib=True):
        self._imu  = LSM6DS3(i2c or SoftI2C(sda=sda, scl=scl))
        cf         = calib_file or _CALIB_FILE
        self.calib = IMUCalibration.load(cf) if load_calib else IMUCalibration(file=cf)

    def read_gyro_raw(self):
        return self._imu.read_gyro()

    def read_accel_raw(self):
        return self._imu.read_accel()

    def read_gyro(self):
        return self.calib.apply_gyro(*self._imu.read_gyro())

    def read_accel(self):
        return self.calib.apply_accel(*self._imu.read_accel())

    def read_imu(self):
        return (self.read_gyro(), self.read_accel())

    def set_calibration(self, gx, gy, gz, ax, ay, az):
        self.calib.set(gx, gy, gz, ax, ay, az)
        return self.calib.save()

    def save_calibration(self, file=None):
        return self.calib.save(file)

    def load_calibration(self, file=None):
        self.calib = IMUCalibration.load(file or self.calib._file)

    def reset_calibration(self):
        self.calib.reset()