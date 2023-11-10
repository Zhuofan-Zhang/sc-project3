import json
import os
import socket
import threading
import time

from helper import build_packet


class NDNNode:
    def __init__(self, port, broadcast_port):
        self.host = '0.0.0.0'
        self.port = port
        self.node_name = f"/Node_{self.port}"
        self.broadcast_port = broadcast_port
        self.fib = {}  # Forwarding Information Base
        self.pit = {}  # Pending Interest Table
        self.peers = set()
        self.running = True
        self.cs = {'/Node_8000': 'test1', '/Node_8001': 'test2'}
        self.threads = []

    def start(self):
        listener_thread = threading.Thread(target=self.listen_for_connections)
        broadcast_thread = threading.Thread(target=self.broadcast_presence)
        discovery_thread = threading.Thread(target=self.listen_for_peer_broadcasts)
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
                s.sendto(f"NDNNode:ONLINE:{self.node_name}:{self.port}".encode(), ('<broadcast>', self.broadcast_port))
                time.sleep(1)

    def broadcast_offline(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(f"NDNNode:OFFLINE:{self.node_name}:{self.port}".encode(), ('<broadcast>', self.broadcast_port))

    def listen_for_peer_broadcasts(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            s.bind((self.host, self.broadcast_port))
            while self.running:
                data, addr = s.recvfrom(1024)
                message = data.decode()
                if message.startswith("NDNNode:"):
                    _, status, node_name, port = message.split(":")
                    peer_port = int(port)
                    if peer_port != self.port:
                        if status == "ONLINE":
                            peer = (addr[0], peer_port)
                            if peer not in self.peers:
                                print(f"Discovered peer {node_name} at {addr[0]}:{peer_port}")
                                self.peers.add(peer)
                                self.fib[node_name] = peer
                                print(f"Added {node_name} to FIB with next hop {peer}")
                        elif status == "OFFLINE":
                            self.peers.discard(peer)
                            if node_name in self.fib:
                                del self.fib[node_name]
                                print(f"Removed {node_name} from FIB")
                            print(f"Peer {node_name} at {addr[0]}:{peer_port} went offline")

    def handle_connection(self, conn, addr):
        with conn:
            print(f"Connected by {addr}")
            while self.running:
                data = conn.recv(1024)
                if not data:
                    break
                packet = json.loads(data.decode())
                print(f"Received packet from {addr}")
                if packet['type'] == 'interest':
                    self.handle_interest(packet, packet['from'])
                elif packet['type'] == 'data':
                    self.handle_data(packet, addr)

    def handle_interest(self, interest_packet, requester):
        name = interest_packet['name']
        # Check Content Store first
        if name in self.cs:
            json_packet = build_packet('data', self.cs[name], name, '')
            self.send_packet(self.fib.get(requester), json_packet)
        else:
            # Add to Interest Table and forward based on FIB
            self.pit[name] = requester
            print(f'added interest {name} with requester {requester}')
            # if next_hop in self.peers:
            #     self.send_packet(next_hop, interest_packet)

    def handle_data(self, data_packet, addr):
        print(f"Received from {addr} : {data_packet}")
        name = data_packet['name']
        self.cs[name] = data_packet['data']
        # Check Interest Table for pending interests
        if name in self.pit:
            requester = self.pit.get(name)
            net_hop = self.fib.get(requester)
            self.send_packet(net_hop, data_packet)

    def send_packet(self, peer, json_packet):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(peer)
                packet = json.dumps(json_packet).encode('utf-8')
                s.sendall(packet)
                packet_type = json_packet['type']
                print(f"Sent {packet_type} '{json_packet['name']}' to {peer}")
            except ConnectionRefusedError:
                print(f"Failed to connect to {peer}")


def main():
    # parser = argparse.ArgumentParser(description='Run a NDN node.')
    # parser.add_argument('--id', required=True, help='The port number to bind the node to.')
    # parser.add_argument('--port', type=int, required=True, help='The port number to bind the node to.')
    # parser.add_argument('--broadcast_port', type=int, required=True, help='The port number to bind the node to.')
    # args = parser.parse_args()
    # args = parser.parse_args([
    #     '--id', 'node2',
    #     '--port', '8001',
    #     '--broadcast_port', '5001',
    # ])
    id = os.environ['ID']
    port = int(os.environ['PORT'])
    broadcast_port = int(os.environ['BROADCAST_PORT'])

    node = NDNNode(port, broadcast_port)
    node.start()
    try:
        while True:
            command = input(f'Node {id} - Enter command (interest/data/exit/add_fit): ').strip()
            if command == 'interest':
                name = input('Enter name for interest: ').strip()
                json_packet = build_packet('interest', node.node_name, name, '')
                node.send_packet(node.peers.pop(), json_packet)
            elif command == 'data':
                name = input('Enter name for data: ').strip()
                data_content = input('Enter data content: ').strip()
                json_packet = build_packet('data', node.node_name, name, data_content)
                node.send_packet(node.peers.pop(), json_packet)
            else:
                print('Invalid command. Try again.')
    except KeyboardInterrupt:
        node.broadcast_offline()


if __name__ == "__main__":
    main()
