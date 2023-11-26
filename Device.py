"""
@author: C. Jonathan Cicai
Device:
    - 6 sensors ("temp", "humidity", "CO", "CO2", "motion", "light")
    - 4 actuators ("heater", "a/c",  "humidifier", "lights")
    - Sensors read from the room stats of the passed in Room
    - Triggers are stored on device but passed down to DeviceSensor (read DeviceSensor to see how they work)
    - Trigger condition defaults set, but no default trigger functions yet
"""

import logging
import threading
from NDNNode import NDNNode

SENSOR_TYPES = ["temp", "humidity", "CO", "CO2", "motion", "light"]

class Device:
    def __init__(self, room, home_id, device_id, listening_port, broadcast_port, trusted=True):
        self._room = room
        self.device_id = device_id
        self.full_id = home_id + '/' + device_id
        self.trusted = trusted
        self.logger = logging.getLogger(f"{self.full_id}_logger")
        handler = logging.FileHandler(f"{home_id}/device_logs/{self.device_id}.log")
        formatter = logging.Formatter("%(asctime)s.%(msecs)04d [%(levelname)s] %(message)s", datefmt="%H:%M:%S:%m")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        
        self._sensors = [self.DeviceSensor(device_id, sens_type, self._room) 
                         for sens_type in SENSOR_TYPES]
        self.node = NDNNode(self.full_id, listening_port, broadcast_port, SENSOR_TYPES, self._sensors)
        

        # Default Triggers
        self._triggers = {
            # trigger format: ('comparer', 'value', 'actuator' 'effect')
            "temp":     [("<", 19, "heater", "on"),
                         (">", 26, "heater", "off"),
                         ("<", 19, "ac", "off"),
                         (">", 26, "ac", "on")],       
            "humidity": [("<", 0.4, "humidifier", "on"),
                         (">", 0.5, "humidifier", "off")], 
            "CO":       [("<", 40, "alarm", "off"),
                         (">", 75, "alarm", "on")],                  
            "CO2":      [("<", 40, "alarm", "off"),
                         (">", 75, "alarm", "on")], 
            "motion":   [("<", 1, "lights", "off"),
                         (">", 0, "lights", "on")]               
        }
        
        self.on = False

    def _check_commands(self):
        while self.on:
            for apparatus, effect in self.node.commands:
                self._room.apparatus[apparatus].on = effect
                self.logger.debug(f"{self.device_id}: Recieved command to turn '{apparatus}' '{effect}'")
                self.node.commands.remove((apparatus, effect))

    def _run_sensors(self):
        while self.on:
            for sensor in self._sensors:
                reading = sensor.get_reading()
                if reading != sensor.last_reading:
                    sensor.last_reading = reading
                    self._actuate(sensor.sensor_type, reading)

    def _actuate(self, sensor_type, reading):
        if sensor_type in self._triggers:
            for (comparer, value, apparatus, effect) in self._triggers[sensor_type]:
                compare_string = f"{reading} {comparer} {value}"
                if eval(compare_string) and apparatus in self._room.apparatus:
                    if self._room.apparatus[apparatus].on != (effect == "on"):
                        self._room.apparatus[apparatus].on = (effect == "on")
                        self.logger.debug(f"{self.device_id}: actuating {apparatus} {effect}")

    def actuate(self, apparatus_name):
        # public version of actuate, it just toggles on/off an apparatus
        apparatus = self._room.apparatus[apparatus_name]
        apparatus.on = not apparatus.on
        self.logger.debug(f"{self.device_id}: actuating {apparatus_name} {'on' if apparatus.on else 'off'}")

    def turn_on(self):
        self.on = True
        threads = {"ct": threading.Thread(target=self._check_commands), 
                   "rt": threading.Thread(target=self._run_sensors)}     
        for _ , t in threads.items():
            t.daemon = True
            t.start()
        self.node.start()
        self.logger.debug(f"{self.device_id} is on")

    def turn_on_untrusted(self):
        self.on = True
        self.node.start_untrusted()
        self.logger.debug(f"{self.device_id} (untrusted) is on")

    def turn_off(self):
        self.on = False
        self.node.stop()
        self.logger.debug(f"{self.device_id} is off")
    
    def toggle(self):
        if self.on:
            self.turn_off() 
        else:
            self.turn_on() if self.trusted else self.turn_on_untrusted()

    """
    DeviceSensor:
        - Reads the correct stat from the room (eg 'temp' sensor reads 'temp' stat)
    """
    class DeviceSensor:
        def __init__(self, device_id, sensor_type, room):
            self.room = room
            self.name = device_id + '/' + sensor_type
            self.sensor_type = sensor_type
            self.last_reading = None

        def get_reading(self):
            return round(self.room.stats[self.sensor_type], 3)
