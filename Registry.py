import socket
import threading
import json

class RegistryServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.devices = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Registry running on {host}:{port}")

    def handle_client(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                data = json.loads(data.decode('utf-8'))
                if data['type'] == 'register':
                    self.devices[data['device_id']] = client_socket
                    print(f"Device registered: {data['device_id']}")
                elif data['type'] == 'data':
                    self.forward_data(data['data'])
            except Exception as e:
                print(f"Error: {e}")
                break

    def forward_data(self, data):
        for device_socket in self.devices.values():
            device_socket.sendall(json.dumps(data).encode('utf-8'))

    def run(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

if __name__ == "__main__":
    registry_server = RegistryServer('localhost', 12345)
    registry_server.run()
