import socket
import json

class Device:
    def __init__(self, device_id, registry_host, registry_port):
        self.device_id = device_id
        self.registry_host = registry_host
        self.registry_port = registry_port
        self.device_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.device_socket.connect((self.registry_host, self.registry_port))
        self.register()

    def register(self):
        message = json.dumps({'type': 'register', 'device_id': self.device_id})
        self.device_socket.sendall(message.encode('utf-8'))

    def listen_for_data(self):
        while True:
            data = self.device_socket.recv(1024)
            if data:
                print(f"Received data: {data.decode('utf-8')}")

if __name__ == "__main__":
    device = Device('device1', 'localhost', 12345)
    device.listen_for_data()
