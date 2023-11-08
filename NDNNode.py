import argparse
import socket
import threading
import time


class NDNNode:
    def __init__(self, port, broadcast_port):
        self.host = '0.0.0.0'
        self.port = port
        self.broadcast_port = broadcast_port
        self.peers = set()
        self.running = True
        self.cs = {'/node1': 'test1', '/node2': 'test2'}
        self.threads = []

    def start(self):
        listener_thread = threading.Thread(target=self.listen_for_connections)
        broadcast_thread = threading.Thread(target=self.broadcast_presence)
        discovery_thread = threading.Thread(target=self.listen_for_broadcasts)
        self.threads.extend([listener_thread, broadcast_thread, discovery_thread])
        for t in self.threads:
            t.start()

    def listen_for_connections(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f"Node is listening on port {self.port}")
            while self.running:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_connection, args=(conn, addr)).start()

    def broadcast_presence(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while self.running:
                s.sendto(f"NDNNode:ONLINE:{self.port}".encode(), ('<broadcast>', self.broadcast_port))
                time.sleep(5)

    def broadcast_offline(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(f"NDNNode:OFFLINE:{self.port}".encode(), ('<broadcast>', self.broadcast_port))

    def listen_for_broadcasts(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            s.bind((self.host, self.broadcast_port))
            while self.running:
                data, addr = s.recvfrom(1024)
                message = data.decode()
                if message.startswith("NDNNode:"):
                    _, status, port = message.split(":")
                    peer_port = int(port)
                    if peer_port != self.port:
                        if status == "ONLINE":
                            if (addr[0], peer_port) not in self.peers:
                                self.peers.add((addr[0], peer_port))
                                print(f"Discovered peer at {addr[0]}:{peer_port}")
                        elif status == "OFFLINE":
                            self.peers.discard((addr[0], peer_port))
                            print(f"Peer at {addr[0]}:{peer_port} went offline")

    def handle_connection(self, conn, addr):
        with conn:
            print(f"Connected by {addr}")
            while self.running:
                data = conn.recv(1024)
                if not data:
                    break
                packet = data.decode()
                print(f"Received from {addr}: {packet}")
                # Handle interest and data here

    def send_interest(self, peer, interest_name):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(peer)
            s.sendall(f"Interest:{interest_name}".encode())
            print(f"Sent interest '{interest_name}' to {peer}")

    def send_data(self, peer, data_name, data_content):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(peer)
            s.sendall(f"Data:{data_name}:{data_content}".encode())
            print(f"Sent data '{data_name}' to {peer}")


def main():
    parser = argparse.ArgumentParser(description='Run a NDN node.')
    parser.add_argument('--id', required=True, help='The port number to bind the node to.')
    parser.add_argument('--port', type=int, required=True, help='The port number to bind the node to.')
    parser.add_argument('--broadcast_port', type=int, required=True, help='The port number to bind the node to.')
    args = parser.parse_args()

    node = NDNNode(args.port, args.broadcast_port)
    node.start()
    try:
        while True:
            command = input(f'Node {args.id} - Enter command (interest/data/exit/add_fit): ').strip()
            if command == 'interest':
                name = input('Enter name for interest: ').strip()
                node.send_interest(node.peers.pop(), name)
            elif command == 'data':
                name = input('Enter name for data: ').strip()
                data_content = input('Enter data content: ').strip()
                node.send_data(node.peers.pop(), name, data_content)
            else:
                print('Invalid command. Try again.')
    except KeyboardInterrupt:
        node.broadcast_offline()


if __name__ == "__main__":
    main()
