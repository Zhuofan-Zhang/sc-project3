import base64
import json
import os
import re
import socket
import threading
import time

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from ECCManager import ECCManager
from helper import build_packet, decode_command, is_alertable, decode_broadcast_packet, build_broadcast_packet
from sensor import Sensor


class NDNNode:
    def __init__(self, node_name, port, broadcast_port, sensor_type):
        self.host = '0.0.0.0'
        self.port = port
        self.node_name = node_name
        self.broadcast_port = broadcast_port
        self.fib = {}  # Forwarding Information Base
        self.interest_fib = {}
        self.pit = {}  # Pending Interest Table
        self.cs = {}
        self.sensor_type = sensor_type
        self.ecc_manager = ECCManager()
        self.public_key_pem = self.ecc_manager.get_public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        self.shared_secrets = {}
        self.threads = []
        self.running = threading.Event()
        self.running.set()

    def start(self):
        listener_thread = threading.Thread(target=self.listen_for_connections)
        broadcast_thread = threading.Thread(target=self.broadcast_presence)
        discovery_thread = threading.Thread(target=self.listen_for_peer_broadcasts)
        self.threads.extend([listener_thread, broadcast_thread, discovery_thread])
        for t in self.threads:
            t.start()

    def stop(self):
        self.broadcast_offline()
        self.running.clear()
        os._exit(0)

    def listen_for_connections(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f"Node is listening on port {self.port}")
            while self.running:
                s.getsockname()
                conn, addr = s.accept()
                threading.Thread(target=self.handle_connection, args=(conn, addr)).start()

    def broadcast_presence(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            while self.running:
                json_packet = build_broadcast_packet('discovery', 'online', self.node_name, self.port,
                                                     self.public_key_pem, ','.join(self.sensor_type))
                s.sendto(json.dumps(json_packet).encode('utf-8'), ('<broadcast>', self.broadcast_port))
                time.sleep(1)

    def broadcast_offline(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            json_packet = build_broadcast_packet('discovery', 'offline', self.node_name, self.port, self.public_key_pem,
                                                 ','.join(self.sensor_type))
            s.sendto(json.dumps(json_packet).encode('utf-8'), ('<broadcast>', self.broadcast_port))
        print('offline')

    def listen_for_peer_broadcasts(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            s.bind((self.host, self.broadcast_port))
            while self.running:
                data, addr = s.recvfrom(1024)
                message = json.loads(data.decode())
                packet_type, status, node_name, peer_port, public_key_pem, sensor_types = decode_broadcast_packet(
                    message)
                if packet_type == 'discovery':
                    if peer_port != self.port:
                        if status == "online":
                            peer = (addr[0], peer_port)
                            if node_name not in self.fib:
                                print(f"Discovered peer {node_name}")
                                self.fib[node_name] = peer
                                peer_public_key = serialization.load_pem_public_key(
                                    public_key_pem.encode('utf-8'),
                                    backend=default_backend()
                                )
                                shared_secret = self.ecc_manager.generate_shared_secret(peer_public_key)
                                self.shared_secrets[node_name] = shared_secret
                                for sensor in sensor_types:
                                    self.interest_fib[sensor] = peer
                        elif status == "offline":
                            if node_name in self.fib:
                                del self.fib[node_name]
                                del self.shared_secrets[node_name]
                                for sensor in sensor_types:
                                    del self.interest_fib[sensor]
                                print(f"Peer {node_name} went offline")

    def handle_connection(self, conn, addr):
        with conn:
            while self.running:
                try:
                    data = conn.recv(1024)
                    if data:
                        packet = json.loads(data.decode())
                        sender = packet['sender']
                        if sender in self.shared_secrets:
                            try:
                                # Decrypt data
                                encrypted_data = base64.b64decode(packet['data'])
                                key = self.shared_secrets[sender]
                                decrypted_data = self.ecc_manager.decrypt_data(key, encrypted_data)
                                packet['data'] = decrypted_data.decode('utf-8')
                            except Exception as e:
                                print(f"Error decrypting data: {e}")
                                continue
                            if packet['type'] == 'interest':
                                print(f"Received interest packet from {packet['sender']}")
                                self.handle_interest(packet, packet['sender'])
                            elif packet['type'] == 'data':
                                print(f"Received data packet from {packet['sender']}")
                                self.handle_data(packet)
                            else:
                                print("Unknown data packet type.")
                        else:
                            print("Received packet without encryption.")
                except ConnectionResetError:
                    continue

    def handle_interest(self, interest_packet, requester):
        name = interest_packet['name']
        # Check Content Store first
        if name in self.cs:
            data = self.cs.get(name)
            json_packet = build_packet('data', self.node_name, requester, name, data)
            self.send_packet(requester, json_packet)
        else:
            # Add to Interest Table and forward based on FIB
            sensor_type = interest_packet['name'].split('/').pop()
            if sensor_type in self.sensor_type:
                data = str(Sensor.generators.get(sensor_type, lambda: None)())
                # print(f'Generated {name} for requester {requester}')
                json_packet = build_packet('data', self.node_name, requester, name, data)
                self.send_packet(requester, json_packet)
            else:
                self.pit[name] = requester
                print(f'added interest {name} with requester {requester}')
                available_destinations = [value for key, value in self.fib.items() if key == sensor_type]
                if len(available_destinations) > 0:
                    destination = [key for key, value in self.fib.items() if
                                   value == self.interest_fib[sensor_type]][0]
                    json_packet = build_packet('interest', self.node_name, destination, name, '')
                    self.send_packet(destination, json_packet)
                else:
                    json_packet = build_packet('data', self.node_name, requester, name,
                                               f'no sensor {sensor_type} available')
                    self.send_packet(requester, json_packet)

    def handle_data(self, data_packet):
        name = data_packet['name']
        data = str(data_packet['data'])
        if re.compile(r'command').search(data):
            sensor_type = data_packet['name'].split('/').pop()
            if sensor_type in self.sensor_type:
                actuator, command = decode_command(name, data)
                print(f'{actuator.capitalize()} is turned {command}.')
            else:
                destination = [key for key, value in self.fib.items() if value == self.interest_fib[sensor_type]].pop(0)
                self.send_packet(destination, data_packet)
        elif re.compile(r'alert').search(data):
            if self.node_name.__contains__('phone'):
                print(f"Alert {name.split('/')[-1]} is set off.")
            else:
                destination = [key for key in self.fib.keys() if key.__contains__('phone')]
                self.send_packet(destination.pop(), data_packet)
        elif name in self.pit:
            destination = self.pit.get(name)
            print(f"Transmitting data packet from {data_packet['sender']} to {destination}")
            data_packet['sender'] = self.node_name
            data_packet['destination'] = destination
            self.send_packet(destination, data_packet)
        else:
            self.cs[name] = data
            alert = is_alertable(name, data)
            if alert:
                if self.node_name.__contains__('phone'):
                    print(f"Alert {name.split('/')[-1]} is set off.")
                else:
                    destinations = [key for key in self.fib.keys() if key.__contains__('phone')]
                    # if there's no phone available the alerts are discarded
                    if len(destinations) > 0:
                        data_packet['data'] = 'alert'
                        print(f"Alerting {destinations}.")
                        for phone in destinations:
                            self.send_packet(phone, data_packet)
                    else:
                        print("Alert is discarded.")
            else:
                print(f"Received {data_packet}")

    def send_packet(self, peer_node_name, json_packet):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                if peer_node_name in self.fib:
                    peer = self.fib.get(peer_node_name)
                    s.connect(peer)
                    key = self.shared_secrets[peer_node_name]
                    encrypted_data = self.ecc_manager.encrypt_data(key, json_packet['data'].encode('utf-8'))
                    json_packet['data'] = base64.b64encode(encrypted_data).decode('utf-8')
                    packet = json.dumps(json_packet).encode('utf-8')
                    s.sendall(packet)
                    packet_type = json_packet['type']
                    print(f"Sent {packet_type} '{json_packet['name']}' to {json_packet['destination']}")
                else:
                    print(f"{peer_node_name.capitalize()} is not available.")
            except ConnectionRefusedError:
                print(f"Failed to connect to {peer}")


def main():
    node_name = os.environ['NODE_NAME']
    port = int(os.environ['PORT'])
    broadcast_port = int(os.environ['BROADCAST_PORT'])
    sensor_type = os.environ['SENSOR_TYPE'].split(',')

    node = NDNNode(node_name, port, broadcast_port, sensor_type)
    node.start()
    try:
        while True:
            command = input(f'Node {node.node_name} - Enter command (interest/data/exit/add_fit): ').strip()
            if command == 'interest':
                destination = input('Enter destination node for interest packet: ').strip()
                sensor_name = input('Enter sensor name: ').strip()
                json_packet = build_packet('interest', node.node_name, destination, f'{node.node_name}/{sensor_name}',
                                           '')
                # send interest to node according to fib
                node.send_packet(destination, json_packet)
            elif command == 'data':
                destination = input('Enter destination node for data packet: ').strip()
                sensor_name = input('Enter sensor name: ').strip()
                data_content = input('Enter data content: ').strip()
                json_packet = build_packet('data', node.node_name, destination, f'{destination}/{sensor_name}',
                                           data_content)
                # send data to node with the same data name
                node.send_packet(destination, json_packet)
            elif command == 'exit':
                node.stop()
            else:
                print('Invalid command. Try again.')
    except KeyboardInterrupt:
        node.stop()


if __name__ == "__main__":
    main()
