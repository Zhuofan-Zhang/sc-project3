import socket
import json
import threading

class Device:
    def __init__(self, device_id, registry_host, registry_port):
        self.device_id = device_id
        self.registry_host = registry_host
        self.registry_port = registry_port
        self.device_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.device_socket.connect((self.registry_host, self.registry_port))
        self.lock = threading.Lock()
        self.sensors = {"sensor1": 0, "sensor2": 0, "sensor8": 0}  # 示例传感器
        self.register()

    def register(self):
        message = json.dumps({'type': 'register', 'device_id': self.device_id})
        self.device_socket.sendall(message.encode('utf-8'))

    def update_sensor_data(self, sensor_id, value):
        with self.lock:
            self.sensors[sensor_id] = value

    def get_sensor_data(self, sensor_id):
        with self.lock:
            return self.sensors[sensor_id]

    def listen_for_data(self):
        while True:
            data = self.device_socket.recv(1024)
            if data:
                print(f"Device {self.device_id} received data: {data.decode('utf-8')}")

if __name__ == "__main__":
    devices = []
    for i in range(5):
        devices.append(Device(f'device{i+1}', 'localhost', 12345))

    for device in devices:
        threading.Thread(target=device.listen_for_data).start()
