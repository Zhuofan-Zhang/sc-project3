"""
Room class
"""
import threading
from random import uniform
from time import sleep
from S import Sensor
from Device import Device

SENSOR_TYPES = ["temp", "humidity", "CO", "CO2", "motion", "radiation"]

class Room:
    def __init__(self):
        self.sensors = [Sensor(sens_type) for sens_type in SENSOR_TYPES]
        self.stats = {
            "temp": 20,         # Temp in degrees Celsius
            "humidity": 0.4,    # Humidity percentage as decimal
            "CO": 30,           # CO level in ppm (parts per million)
            "CO2": 400,         # CO2 level in ppm (parts per million)
            "radiation": 0.2,   # Radiation level in microsieverts per hour (uSv/h)
            "motion": 0,        # Whether or not something is moving in the room (0 or 1)
            "heater": 0,        # Whether or not heater is on
            "light": 0,         # Whether or not light is on
        }

    def simulate(self):
        # simulate a change in the room stats
        while True:
            # Simulate temperature fluctuation within a realistic range
            self.stats["temp"] += uniform(-0.01, 0.01)
            self.stats["temp"] = min(max(self.stats["temp"], -10), 40)

            # Simulate humidity fluctuation within a realistic range
            self.stats["humidity"] += uniform(-0.005, 0.005)
            self.stats["humidity"] = min(max(self.stats["humidity"], 0), 1)

            # Simulate CO and CO2 levels dropping in the absence of motion
            self.stats["CO"] -= uniform(0, 2)
            self.stats["CO2"] -= uniform(-2, 2)

            # Keep CO and CO2 levels within a realistic range
            self.stats["CO"] = min(max(self.stats["CO"], 0), 100)
            self.stats["CO2"] = min(max(self.stats["CO2"], 300), 1000)

            # Simulate radiation slightly fluctuating
            self.stats["radiation"] += uniform(-0.05, 0.05)
            self.stats["radiation"] = min(max(self.stats["radiation"], 0), 0.5)

            # todo find a good way to adjust motion

            sleep(1)    

    def main(self):
        for sensor in self.sensors:
            sensor.main(self)
        self.simulate()
            
room = Room()
room.main()
