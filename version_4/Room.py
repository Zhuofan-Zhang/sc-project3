"""
Room class
- Simulates 'natural changes' and changes due to turned on apparatus (like heaters, lights)
- Gets initialised with one device, but more can be added if needed
"""
from random import uniform
from time import sleep
from Device import Device
from Apparatus import Apparatus

class Room:
    def __init__(self, room_id):
        self.device = Device(room_id+"device1", "localhost", 69, self)
        self.stats = {
            "temp": 20,         # Temp in degrees Celsius
            "humidity": 0.4,    # Humidity percentage as decimal
            "CO": 30,           # CO level in ppm (parts per million)
            "CO2": 400,         # CO2 level in ppm (parts per million)
            "motion": 0,        # Whether or not something is moving in the room (0 or 1)
            "light": 0,         # Light level in lux
        }
        self.apparatus = {
            "heater":     Apparatus(room_id, "heater", "temp", "increase_by", 0.1),
            "lights":     Apparatus(room_id, "lights", "light", "set_to", 100),
            "ac":         Apparatus(room_id, "ac", "temp", "decrease_by", 0.05),
            "humidifier": Apparatus(room_id, "humidifier", "humidity", "increase_by", 0.0001)
        }

    def simulate(self):
        while True:
            self.update_via_apparatus()
            self.update_via_natural_changes()

    def update_via_apparatus(self):
        for _, app in self.apparatus.items():
            if app.on and app.affected_stat in self.stats.keys():
                if app.change_type == "set_to":
                    self.stats[app.affected_stat] = app.change_amount
                elif app.change_type == "increase_by":
                    self.stats[app.affected_stat] += app.change_amount
                elif app.change_type == "decrease_by":
                    self.stats[app.affected_stat] -= app.change_amount

    def update_via_natural_changes(self):
        # Simulate temperature fluctuation within a realistic range
        self.stats["temp"] += uniform(-0.01, 0.01)
        self.stats["temp"] = min(max(self.stats["temp"], -10), 40)

        # Simulate humidity fluctuation within a realistic range
        self.stats["humidity"] += uniform(-0.005, 0.005)
        self.stats["humidity"] = min(max(self.stats["humidity"], 0), 1)

        # Keep CO and CO2 levels within a realistic range
        self.stats["CO"] += uniform(-0.01, 0.01)
        self.stats["CO"] = min(max(self.stats["CO"], 0), 100)
        self.stats["CO2"] += uniform(-0.01, 0.01)
        self.stats["CO2"] = min(max(self.stats["CO2"], 300), 1000)
        sleep(1)   

    def toggle_value(self, value):
        if value in ["motion", "heater", "light"]:
            self.stats[value] = 1 if self.stats[value] == 0 else 0

    def set_apparatus(self, apparatus: Apparatus):
        self.apparatus[apparatus.apparatus_type] = apparatus

    def main(self):
        self.device.turn_on()
        self.simulate()
            
room = Room("room")
room.main()
