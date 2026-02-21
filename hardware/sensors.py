import numpy as np
import socket
import json
import time
from scipy.spatial.transform import Rotation as R
# from vnpy import VnSensor
import zmq
from math import sin, cos

from ezauv.hardware.sensor_interface import Sensor

class VectorNav:
    def __init__(self, port, baud):
        # self.vectornav = VnSensor()
        self.vectornav.connect(port, baud)

    def read_data(self):
        rot = self.vectornav.read_yaw_pitch_roll()
        accel = self.vectornav.read_yaw_pitch_roll_magnetic_acceleration_and_angular_rates().accel
        return {
            "rotation": R.from_euler(rot.x, rot.y, rot.z, "zyx"),
            "acceleration": np.array([accel.x, accel.y, accel.z])
        }

class DebugVectorNav:
    def __init__(self, port, baud):
        ...

    def read_data(self):
        return {
            "rotation": R.from_euler("zyx", [0, 0, 0]),
            "acceleration": np.array([0, 0, 0])
        }

class VectorNavIMU(Sensor):
    def __init__(self, port, baud):
        self.vectornav = DebugVectorNav(port, baud)
        self.calibrated_heading = 0

    def get_data(self) -> dict:
        data = self.vectornav.read_data()
        # adjust the heading based on the calibrated heading
        rot = data["rotation"] * R.from_euler('z', -self.calibrated_heading)
        return {
            "rotation": rot,
            "acceleration": data["acceleration"],
            "heading": (rot.as_euler('zyx')[0] + self.calibrated_heading) % 360
        }

    def initialize(self) -> None:
        interval = 0.1
        total = int(5 / interval)
        self.log(f"Calibrating IMU heading over 5 seconds ({total} checks)...")
        heading_sum = 0
        for i in np.linspace(0, 5, total):
            heading_sum += self.vectornav.read_data()["rotation"].as_euler('zyx')[0]
            time.sleep(interval)
        self.calibrated_heading = heading_sum / total

    def overview(self) -> None:
        print(f"VectorNav IMU")
import time
class DebugGPS(Sensor):
    def __init__(self):
        self.start = 0

    def get_data(self) -> dict:
        return {"position": [5 * (time.time() - self.start) ** 2, 0]}

    def initialize(self) -> None:
        self.start = time.time()

    def overview(self) -> None:
        print(f"Debug GPS")

# class Camera(Sensor):
#     def __init__(self):
#         ...
#
#     def initialize(self) -> None:
#         ...
#
#     def get_data(self) -> dict:
#         angle = socket.get()
#         return {
#             "angle_to_buoy": angle
#         }
#
#     def overview(self) -> None:
#         ...


class NetCam(Sensor):
    def initialize(self, port, addr, context):
        context = zmq.Context()
        global socket
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://" + addr + ":" + port)

    def get_data():
        list_data = []
        data_packed = socket.recv_json()

        classes = data_packed[::3]
        distences = data_packed[1::3]
        rotations = data_packed[2::3]

        id = 0
        for i in range(rotations):
            x = sin(i) * distences[id]
            y = cos(i) * distences[id]

            list_data.append((classes[id], float(x), float(y)))

            id = id + 1

        data = {"buoy": list_data}
        return data