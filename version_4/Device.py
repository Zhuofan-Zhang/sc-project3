"""
Device class
- 5 sensors ("temp", "humidity", "CO2", "motion", "light")
- 5 actuators ("heater", "a/c",  "humidifier", "smoke alarm", "lights")
- Sensors read from the room stats of the passed in Room
- Triggers are stored on device but passed down to DeviceSensor (read DeviceSensor to see how they work)
- Trigger condition defaults set, but no default trigger functions yet
"""

import json
import threading
from NDNNode import NDNNode
from Room import Room

SENSOR_TYPES = ["temp", "humidity", "CO", "CO2", "motion", "light"]
ACTUATOR_TYPES = ["heater", "ac", "humidifier", "smoke_alarm", "lights"]

class Device:
    def __init__(self, device_id, room: Room):
        self.device_id = device_id
        self.node = NDNNode(self.device_id)
        self._room = room
        self._triggers = {
            # trigger format: ('comparer', 'value', 'actuator' 'effect')
            "temp":     [("<", 19, "heater", "on"),
                         (">", 26, "heater", "off"),
                         ("<", 19, "ac", "off"),
                         (">", 26, "ac", "on")],       
            "humidity": [("<", 40, "humidifier", "on"),
                         (">", 50, "humidifier", "off")], 
            "CO":       [("<", 40, "alarm", "off"),
                         (">", 75, "alarm", "on")],                  
            "CO2":      [("<", 40, "alarm", "off"),
                         (">", 75, "alarm", "on")], 
            "motion":   [("<", 1, "lights", "off"),
                         (">", 0, "lights", "on")]               
        }
        self._sensors = [self.DeviceSensor(device_id, sens_type, self._triggers[sens_type] if sens_type in self._triggers else None) 
                         for sens_type in SENSOR_TYPES]
        self._on = False

    def _listen_for_data(self):
        while self._on:
            data = self.node.listen()
            print(f"Received data: {data.decode('utf-8')}")

    def _run_sensors(self):
        while self._on:
            for sensor in self._sensors:
                reading = sensor.get_reading(self._room)
                if reading != sensor.last_reading:
                    sensor.last_reading = reading
                    self._actuate(sensor.sensor_type, reading)
                    self.node.emit(sensor.name, reading)

    def _actuate(self, sensor_type, reading):
        for (comparer, value, apparatus, effect) in self._triggers[sensor_type]:
            compare_string = f"{reading} {comparer} {value}"
            if eval(compare_string) and apparatus in self._room.apparatus:
                self._room.apparatus[apparatus].on = (effect == "on")

    def update_trigger(self, target, trigger):
        if target in self._triggers:
            self._triggers[target] = trigger
            self._sensors[target].update_trigger(trigger)

    def turn_on(self):
        self._on = True
        threads = {"lt": threading.Thread(target=self._listen_for_data), 
                   "rt": threading.Thread(target=self._run_sensors)}     
        for _ , t in threads.items():
            t.daemon = True
            t.start()
        self.node.start()

    def turn_off(self):
        self._on = False
        self.node.broadcast_offline()

    """
    DeviceSensor class
    - Reads the correct stat from the room (eg 'temp' sensor reads 'temp' stat)
    - Has programmable trigger (trigger condition) and trigger function
    - Trigger function will run if trigger condition met
    - No Trigger function by default

    And example of a trigger function would be to tell the rooms heater to turn off if the 
    is within set range
    """
    class DeviceSensor:
        def __init__(self, device_id, sensor_type, trigger):
            self.name = device_id + '@' + sensor_type
            self.sensor_type = sensor_type
            self.last_reading = None

        def get_reading(self, room: Room):
            return round(room.stats[self.sensor_type], 3)
