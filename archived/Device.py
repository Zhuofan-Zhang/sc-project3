import socket
import json
import argparse


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

    def send_data(self, data):
        message = json.dumps({'type': 'data', 'data': data})
        self.device_socket.sendall(message.encode('utf-8'))

    def listen_for_data(self):
        while True:
            data = self.device_socket.recv(1024)
            if data['type'] == 'interest':
                self.handle_interest()
            elif data['type'] == 'interest':
                print(f"Received data: {data.decode('utf-8')}")

    def handle_interest(self):
        self.send_data('data')


def parse_arguments():
    parser = argparse.ArgumentParser(description='Run a NDN node.')
    parser.add_argument('--device_id', required=True, help='The ID of the node.')
    parser.add_argument('--host', default='localhost', help='The host IP to bind the node to.')
    parser.add_argument('--port', default=12345, type=int, required=True, help='The port number to bind the node to.')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    device = Device(args.device_id, 'localhost', 12345)

    while True:
        command = input(f'Node {args.id} - Enter command (send/data): ').strip()
        if command == 'interest':
            name = input('Enter name for interest: ').strip()
            device.listen_for_data()
        elif command == 'data':
            data = input('Enter message: ').strip()
            device.send_data(data)
        else:
            print('Invalid command. Try again.')
