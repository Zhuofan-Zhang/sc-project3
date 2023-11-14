import socket_helper
import threading
import json
import argparse
from collections import defaultdict

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Node(threading.Thread):
    def __init__(self, node_id, host, port):
        super().__init__()
        self.node_id = node_id
        self.host = host
        self.port = port
        self.cs = {'/node1': 'test'}  # Content Store
        self.pit = defaultdict(list)  # Pending Interest Table
        self.fib = {}  # Forwarding Information Base
        self.daemon = True
        self.start()  # Start the thread

    def run(self):
        # Set up the server socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen()

            while True:
                # Accept connections from other nodes
                connection, address = server_socket.accept()
                with connection:
                    threading.Thread(target=self.handle_connection, args=(connection,)).start()

    def handle_connection(self, connection):
        try:
            while True:
                data = connection.recv(1024)
                if not data:
                    break  # Client disconnected, so exit the loop
                packet = json.loads(data.decode('utf-8'))
                if packet['type'] == 'interest':
                    self.handle_interest(packet, connection)
                elif packet['type'] == 'data':
                    self.handle_data(packet, connection)
        except Exception as e:
            logging.error(f"Error in handle_connection: {e}")
        finally:
            connection.close()

    def handle_interest(self, interest, connection):
        name = interest['name']
        if name in self.cs:  # Check Content Store
            # If data is in the CS, send it back
            data_packet = self.cs[name]
            connection.sendall(json.dumps({"type": 'data', "name": "device1", "message": 'message'}).encode('utf-8'))
        else:
            # Otherwise, add to PIT and forward based on FIB
            self.pit[name].append(connection)
            self.forward_interest(interest)

    def forward_interest(self, interest):
        # Forward interest based on FIB
        # In a real implementation, this would involve network communication
        # Here we will just print the interest for simplicity
        fib_entry = self.fib.get(interest['name'])
        if fib_entry:
            next_hop = fib_entry['next_hop']
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect(next_hop)
                client_socket.sendall(json.dumps(interest).encode('utf-8'))

    def add_fib_entry(self, name, next_hop):
        # Add or update an entry in the FIB
        self.fib[name] = {'next_hop': next_hop}

    def send_interest(self, name):
        interest = {'type': 'interest', 'name': name}
        self.forward_interest(interest)

    def send_data(self, name, data):
        def send_data(self, data):
            message = json.dumps({'type': 'data', 'data': data})

            self.server_socket.sendall(message.encode('utf-8'))

    def handle_data(self, data, connection):
        name = data['name']
        logging.info(f"Node {self.node_id} received data: {data}")
        # Store in CS
        self.cs[name] = data
        # Check for waiting interests in PIT
        if name in self.pit:
            for waiting_connection in self.pit[name]:
                # Send data back to waiting interests
                waiting_connection.sendall(json.dumps(data).encode('utf-8'))
            del self.pit[name]  # Clear PIT entry


def parse_arguments():
    parser = argparse.ArgumentParser(description='Run a NDN node.')
    parser.add_argument('--id', required=True, help='The ID of the node.')
    parser.add_argument('--host', default='localhost', help='The host IP to bind the node to.')
    parser.add_argument('--port', type=int, required=True, help='The port number to bind the node to.')
    return parser.parse_args([
        '--id', 'node1',
        '--host', 'localhost',
        '--port', '5001'
    ])


def main():
    args = parse_arguments()

    # Start the node
    node = Node(args.id, args.host, args.port)

    # Main loop for command line interface
    while True:
        command = input(f'Node {args.id} - Enter command (interest/data/exit/add_fit): ').strip()
        if command == 'interest':
            name = input('Enter name for interest: ').strip()
            node.send_interest(name)
        elif command == 'data':
            name = input('Enter name for data: ').strip()
            data_content = input('Enter data content: ').strip()
            node.send_data(name, data_content)
        elif command == 'add_fit':
            name = input('Enter name for FIT entry: ').strip()
            next_hop_host = 'localhost'
            next_hop_port = int(input('Enter next hop port for FIB entry: ').strip())  # Port should be an integer
            node.add_fib_entry(name, (next_hop_host, next_hop_port))
            print(f'FIT entry added for {name} to next hop {next_hop_host}:{next_hop_port}')
        elif command == 'exit':
            break
        else:
            print('Invalid command. Try again.')


if __name__ == "__main__":
    main()
