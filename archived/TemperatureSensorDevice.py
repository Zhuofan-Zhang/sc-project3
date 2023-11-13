import socket_helper
import json
import threading
import random
import time

class TemperatureSensorDevice:
    def __init__(self, device_id, registry_host, registry_port):
        self.device_id = device_id
        self.registry_host = registry_host
        self.registry_port = registry_port
        self.device_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.device_socket.connect((self.registry_host, self.registry_port))
        self.lock = threading.Lock()
        self.temperature = 0  # 初始温度
        self.register()
        self.start_sending_temperature_data()

    def register(self):
        message = json.dumps({'type': 'register', 'device_id': self.device_id})
        self.device_socket.sendall(message.encode('utf-8'))

    def simulate_temperature_change(self):
        with self.lock:
            # 模拟温度变化，可以根据需要调整生成温度的逻辑
            self.temperature = 20 + random.randint(-5, 5)

    def send_temperature_data(self):
        self.simulate_temperature_change()
        data = json.dumps({'device_id': self.device_id, 'temperature': self.temperature})
        self.device_socket.sendall(data.encode('utf-8'))

    def start_sending_temperature_data(self):
        # 每隔一定时间发送温度数据
        threading.Timer(5, self.start_sending_temperature_data).start()
        print('sending temperature')
        self.send_temperature_data()

if __name__ == "__main__":
    temp_sensor = TemperatureSensorDevice('temp_sensor1', 'localhost', 12345)
