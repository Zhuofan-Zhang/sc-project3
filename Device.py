"""
Device class
- Has sensors and triggers
- Sensors read from the room stats of the passed in Room
- Triggers are stored on device but passed down to DeviceSensor (read DeviceSensor to see how they work)
- Trigger condition defaults set, but no default trigger functions yet
"""

import socket
import json
import threading

SENSOR_TYPES = ["temp", "humidity", "CO", "CO2", "motion", "radiation"]

class Device:
    def __init__(self, device_id, registry_host, registry_port, room):
        self.device_id = device_id
        self.registry_host = registry_host
        self.registry_port = registry_port
        self.device_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.device_socket.connect((self.registry_host, self.registry_port))
        self._register()
        # default triggers
        self._triggers = {
            "temp": ("<->", (19, 22)),       # Temp in degrees Celsius
            "humidity": ("<->",(0.4, 0.45)), # Humidity percentage as decimal
            "CO": ("<", 65),                 # CO level in ppm (parts per million)
            "CO2": ("<", 600),               # CO2 level in ppm (parts per million)
            "radiation": ("<", 15),          # Radiation level in microsieverts per hour (uSv/h)
        }
        self._room = room
        self._sensors = [self.DeviceSensor(device_id, sens_type, self._triggers[sens_type] if sens_type in self._triggers else None) 
                         for sens_type in SENSOR_TYPES]
        self._on = False

    def _register(self):
        message = json.dumps({'type': '_register', 'device_id': self.device_id})
        self.device_socket.sendall(message.encode('utf-8'))

    def _listen_for_data(self):
        while self._on:
            data = self.device_socket.recv(1024)
            if data:
                print(f"Received data: {data.decode('utf-8')}")

    def _run_sensors(self):
        while self._on:
            for sensor in self.sensors:
                sensor.sense(self._room)

    def update_trigger(self, target, trigger):
        if target in self._triggers:
            self._triggers[target] = trigger
            self._sensors[target].update_trigger(trigger)

    def turn_on(self):
        self._on = True
        threads = {"lt": threading.Thread(target=self._listen_for_data), # Listening Thread
                   "rt": threading.Thread(target=self._run_sensors)}     # Sensor Thread
        for _ , t in threads.items():
            t.daemon = True
            t.start()

    def turn_off(self):
        self._on = False

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
            self.trigger = trigger
            self.last_reading = None
            self.trigger_function = None

        def update_trigger(self, trigger):
            self.trigger = trigger

        def update_trigger_function(self, trigger_function):
            self.trigger_function = trigger_function

        def _get_reading(self, room):
            return round(room.stats[self.sensor_type], 3)
        
        def _check_trigger(self, reading):
            trigger_condition, trigger_value = self.trigger
            if trigger_condition == "<" and reading < trigger_value:
                self.trigger_function(reading)
            elif trigger_condition == ">" and reading > trigger_value:
                self.trigger_function(reading)
            elif trigger_condition == "<->":
                val_a, val_b = trigger_value
                if val_a < reading or reading > val_b:
                    self.trigger_function(reading)
        
        def _emit(self, new_reading):
            # Todo, implement actual emit logic
            print(f"{self.name}: {new_reading}")
            self.last_reading = new_reading
            
        def sense(self, room):
            reading = self._get_reading(room)
            if reading != self.last_reading:
                self._check_trigger(reading)
                self._emit(reading)
            

