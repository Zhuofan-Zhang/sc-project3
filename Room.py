"""
Room class
- Simulates 'natural changes' and changes due to turned on apparatus (like heaters, lights)
- Gets initialised with one device which reads and can affect room stats

@author: C. Jonathan Cicai
"""
from random import uniform
from time import sleep
from Device import Device
from Apparatus import Apparatus

class Room:
    def __init__(self, room_id, device_l_port, device_b_port):
        self.room_id = room_id
        self.device = Device(self, str(room_id)+"_device", device_l_port, device_b_port)
        self.stats_file = f"room_stats/{self.room_id}_stats.txt"
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
            "humidifier": Apparatus(room_id, "humidifier", "humidity", "increase_by", 0.01)
        }

    def simulate(self):
        while True:
            self.update_via_apparatus()
            self.update_via_natural_changes()
            self.log_stats()

    def update_via_apparatus(self):
        for _, app in self.apparatus.items():
            if app.on and app.affected_stat in self.stats.keys():
                if app.change_type == "set_to":
                    self.stats[app.affected_stat] = app.change_amount
                elif app.change_type == "increase_by":
                    self.stats[app.affected_stat] += app.change_amount
                elif app.change_type == "decrease_by":
                    self.stats[app.affected_stat] -= app.change_amount
            if not app.on and app.affected_stat in self.stats.keys():
                if app.change_type == "set_to":
                    self.stats[app.affected_stat] = 0

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

    def log_stats(self):
        stats_content = f"Room {self.room_id}:\n" \
                        f"Temperature: {self.stats['temp']} °C\n" \
                        f"Humidity: {self.stats['humidity'] * 100} %\n" \
                        f"CO Level: {self.stats['CO']} ppm\n" \
                        f"CO2 Level: {self.stats['CO2']} ppm\n" \
                        f"Motion: {'Yes' if self.stats['motion'] else 'No'}\n" \
                        f"Light Level: {self.stats['light']} lux\n\n" 
        for _, app in self.apparatus.items():
            stats_content += f"{app.apparatus_type}: {'on' if app.on else 'off'}\n"              

        with open(self.stats_file, "w") as file:
            file.write(stats_content)

    def main(self):
        self.device.turn_on()
        self.simulate()
        