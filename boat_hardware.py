from hardware.motor_serial import MotorSerial
from hardware.sensors import VectorNavIMU, DebugGPS

class BoatHardware:
    def __init__(self, *, arduino_port, vectornav_port):
        self.motor_serial = MotorSerial(arduino_port)
        self.imu = VectorNavIMU(vectornav_port, 921600)
        self.gps = DebugGPS()

        self.prev = {}

    def set_motors(self, motor_speeds):
        self.motor_serial.set_speeds(motor_speeds)

    def initialize_motor(self, pin):
        pass

    def kill(self):
        self.motor_serial.kill()