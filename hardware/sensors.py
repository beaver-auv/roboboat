import numpy as np
import socket
import json
import time
from scipy.spatial.transform import Rotation as R
# from vnpy import VnSensor
import zmq
from math import sin, cos
import serial
import time
import pynmea2
import math

from ezauv.hardware.sensor_interface import Sensor

class VectorNav:
    def __init__(self, port, baud):
        self.vectornav = VnSensor()
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
        self.vectornav = VectorNav(port, baud)
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

def latlon_to_xy(lat, lon, lat0, lon0): #
    R = 6378137.0
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    lat0_rad = math.radians(lat0)
    lon0_rad = math.radians(lon0)

    dlat = lat_rad - lat0_rad
    dlon = lon_rad - lon0_rad

    x = dlon * math.cos(lat0_rad) * R
    y = dlat * R
    return x, y

def handle_line(line):
    if not line.startswith('$') or 'GGA' not in line:
        return None
    try:
        msg = pynmea2.parse(line)

        return {
            "lat": msg.latitude,
            "lon": msg.longitude,
            "alt": msg.altitude,
            "sats": int(msg.num_sats)
        }

        # for debugging
        print(
            label,
            "Lat:", msg.latitude,
            "Lon:", msg.longitude,
            "Alt:", msg.altitude,
            "Sats:", msg.num_sats
        )

    except (pynmea2.ParseError, AttributeError):
        return None

class GPS(Sensor):
    def __init__(self, port_1 = '/dev/ttyAMA0', port_2 = '/dev/ttyAMA1', baud = 9600):
        self.gps_1 = serial.Serial(port_1, baudrate=baud, timeout=0.5)
        self.gps_2 = serial.Serial(port_2, baudrate=baud, timeout=0.5)
        self.latest = None
        self.origin = None

    def get_data(self):
        line_1 = self.gps_1.readline().decode(errors='ignore').strip()
        line_2 = self.gps_2.readline().decode(errors='ignore').strip()

        data_1 = handle_line(line_1)
        data_2 = handle_line(line_2)

        average = None
        if data_1 is not None:
            if data_2 is not None:
                average = {
                    "lat": (data_1["lat"] + data_2["lat"]) / 2,
                    "lon": (data_1["lon"] + data_2["lon"]) / 2,
                    "alt": (data_1["alt"] + data_2["alt"]) / 2,
                    "sats": max(data_1["sats"], data_2["sats"])
                }
            else:
                average = data_1
        elif data_2 is not None:
            average = data_2
        if average is None:
            if self.latest is None:
                return [0,0]
            return self.latest


        # Set origin on first valid averaged fix
        if self.origin is None:
            self.origin = {"lat": average["lat"], "lon": average["lon"]}

        x, y = latlon_to_xy(average["lat"], average["lon"], self.origin["lat"], self.origin["lon"])
        self.latest = [x,y]
        return {"position": [x,y]}

    def initialize(self):
        pass

    def overview(self):
        print(f"GPS with ports {self.gps_1.port} and {self.gps_2.port}")

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

    def get_data(self):
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