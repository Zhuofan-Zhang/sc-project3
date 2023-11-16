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

SENSOR_TYPES = ["temp", "humidity", "CO", "CO2", "motion", "light"]
ACTUATOR_TYPES = ["heater", "ac", "humidifier", "smoke_alarm", "lights"]

class Device:
    def __init__(self, room, device_id, listening_port, broadcast_port):
        self.device_id = device_id
        # self.node = NDNNode(self.device_id, listening_port, broadcast_port, SENSOR_TYPES)
        self._room = room
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
        self._sensors = [self.DeviceSensor(device_id, sens_type, self._triggers[sens_type] if sens_type in self._triggers else None) 
                         for sens_type in SENSOR_TYPES]
        self._on = False

    def _listen_for_data(self):
        pass
        while self._on:
            data = None # self.node.listen_for_command()
            # print(f"Received data: {data.decode('utf-8')}")
            if data is not None:
                data_type, data_contents = data
                if data_type == "command":
                    if data_contents == "off":
                        self.turn_off()
                    else:
                        (app, app_status) = data_contents
                        self._room.apparatus[app].on = app_status

    def _run_sensors(self):
        while self._on:
            for sensor in self._sensors:
                reading = sensor.get_reading(self._room)
                if reading != sensor.last_reading:
                    sensor.last_reading = reading
                    self._actuate(sensor.sensor_type, reading)
                    if sensor.sensor_type == 'light':
                        print(f"{self.device_id}/{sensor.sensor_type}: {reading}")
                    # self.node.emit(sensor.name, reading)

    def _actuate(self, sensor_type, reading):
        if sensor_type in self._triggers:
            for (comparer, value, apparatus, effect) in self._triggers[sensor_type]:
                compare_string = f"{reading} {comparer} {value}"
                if eval(compare_string) and apparatus in self._room.apparatus:
                    if self._room.apparatus[apparatus].on != (effect == "on"):
                        self._room.apparatus[apparatus].on = (effect == "on")
                        print(f"{self.device_id}: turning {apparatus} {'on' if (effect == 'on') else 'off'}")
                        # self.node.emit_actuation(sensor.name)

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
        # self.node.start()

    def turn_off(self):
        self._on = False
        # self.node.broadcast_offline()

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

        def get_reading(self, room):
            return round(room.stats[self.sensor_type], 3)
