import socket
import time
import json

class Server:
    def __init__(self, registry_host, registry_port):
        self.registry_host = registry_host
        self.registry_port = registry_port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((self.registry_host, self.registry_port))

    def send_data(self, data):
        message = json.dumps({'type': 'data', 'data': data})
        self.server_socket.sendall(message.encode('utf-8'))

    def run(self):
        while True:
            self.send_data(f"Data from server at {time.ctime()}")
            time.sleep(2)

if __name__ == "__main__":
    server = Server('localhost', 12345)
    server.run()
