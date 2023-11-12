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
        self.room = room
        self.sensors = [self.DeviceSensor(device_id, sens_type) for sens_type in SENSOR_TYPES]
        self.register()

    def register(self):
        message = json.dumps({'type': 'register', 'device_id': self.device_id})
        self.device_socket.sendall(message.encode('utf-8'))

    def listen_for_data(self):
        while True:
            data = self.device_socket.recv(1024)
            if data:
                print(f"Received data: {data.decode('utf-8')}")

    def run_sensors(self):
        while True:
            for sensor in self.sensors:
                sensor.emit(sensor.get_reading(self.room))

    def turn_on(self):
        threads = {"lt": threading.Thread(target=self.listen_for_data), # Listening Thread
                   "rt": threading.Thread(target=self.run_sensors)}     # Sensor Thread
        for _ , t in threads.items():
            t.daemon = True
            t.start()


    class DeviceSensor:
        def __init__(self, device_id, sensor_type):
            self.name = device_id + '@' + sensor_type
            self.sensor_type = sensor_type
            self.last_reading = None

        def get_reading(self, room):
            return round(room.stats[self.sensor_type], 3)
        
        def emit(self, new_reading):
            # Todo, implement actual emit logic
            if new_reading != self.last_reading:
                print(f"{self.name}: {new_reading}")
                self.last_reading = new_reading

