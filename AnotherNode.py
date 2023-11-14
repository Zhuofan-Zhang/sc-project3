import json
import logging
import os
import re
import socket
import threading
import time
from datetime import datetime, timezone

import fib
from helper import build_packet, decode_command, is_alertable
from sensor import Sensor

API_VERSION = 'v2'


class AnotherNode:
    def __init__(self, node_name, host, port, broadcast_port, sensor_types, presence_broadcast_interval=30,
                 response_timeout=60,
                 logging_level=logging.INFO):

        self.node_name = node_name

        # Networking
        self.host = host
        self.port = port
        self.broadcast_port = broadcast_port
        self.fib = fib.ForwardingInfoBase(self.node_name)
        self.interest_fib = {}
        self.presence_broadcast_interval = presence_broadcast_interval
        self.response_timeout = response_timeout
        # Data storage
        self.pit = {}
        self.cs = {}
        self.sensor_type = sensor_types
        # TODO: Generate/Load public and private keys
        # self.pub_key_CA = None
        # self.pub_key = None
        # self.priv_key = None
        # self.key_store = {} # Like content store except for keys

        # Logging verbosity
        logging.basicConfig(format="%(asctime)s.%(msecs)04d [%(levelname)s] %(message)s", level=logging_level,
                            datefmt="%H:%M:%S:%m")

        # Threading
        self.threads = []
        self.running = threading.Event()
        self.running.set()

    def start(self):
        # Start threads
        # Set threads as daemon threads so that they terminate when main terminates
        listener_thread = threading.Thread(target=self.listen_for_connections)  # , daemon=True)
        broadcast_thread = threading.Thread(target=self.broadcast_presence)  # , daemon=True)
        discovery_thread = threading.Thread(target=self.listen_for_peer_broadcasts)  # , daemon=True)
        self.threads.extend([listener_thread, broadcast_thread, discovery_thread])
        for t in self.threads:
            t.start()

    def stop(self):
        # Stop threads
        self.running.clear()
        # Wait for other threads to terminate
        logging.debug(f"{self.node_name} : running: {self.running.is_set()} - waiting for threads to terminate")
        for t in self.threads:
            t.join()

    def set(self, sensor_name, data):
        """
        Create data packet with data, send if interest in PIT and store in content store.

        Note: sensor_name should just be name of the sensor.
              Node name is automatically added as prefix!

        """
        # Get data name as <node_name>/<sensor_name>
        data_name = self.node_name.copy()
        if not data_name.endswith('/'):
            data_name = + '/'
        data_name += sensor_name

        # Create packet
        current_time_utc = datetime.now(timezone.utc)
        timestamp = current_time_utc.isoformat()
        json_packet = {"version": API_VERSION,
                       "type": "data",
                       "name": data_name,
                       "data": data,
                       "timestamp": timestamp
                       }
        data_packet = json.dumps(json_packet).encode('utf-8')

        # TODO: sign packet

        # If in PIT forward data and remove entry from PIT
        if data_name in self.pit:
            # Send data if interest is in PIT
            self.send_packet(data_name, data_packet)

        # Store in content store
        self.cs[data_name] = data_packet

    def get(self, data_name):
        # If in content store return
        if data_name in self.cs:
            data_packet = self.cs.get(data_name)

        # If not in content store, send interest package
        else:
            # Create packet
            current_time_utc = datetime.now(timezone.utc)
            timestamp = current_time_utc.isoformat()
            json_packet = {"version": API_VERSION,
                           "type": "interest",
                           "name": data_name,
                           "timestamp": timestamp
                           }
            interest_packet = json.dumps(json_packet).encode('utf-8')
            self.send_interest(self, data_name, interest_packet)

            # Block until it is in the content store or until timeout
            timer = threading.Thread(target=self.wait_for_data,
                                     args=(data_name, self.response_timeout))  # , daemon=True)
            timer.start()
            timer.join()  # Block untill data incontent store or timeout

            if data_name in self.cs:
                data_packet = self.cs.get(data_name)
            else:
                data_packet = None

        return data_packet

    def wait_for_data(self, data_name, timeout):
        while self.running.is_set():
            try:
                time.sleep(1)
                timeout -= 1
                if timeout <= 0 or data_name in self.cs:
                    break
            except Exception as err:
                # Stop threads
                self.stop()
                logging.error(f"{self.node_name}: wait_for_data(): {err}")
                raise err

    def listen_for_peer_broadcasts(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            s.bind((self.host, self.broadcast_port))
            while self.running.is_set():
                try:
                    data, addr = s.recvfrom(1024)
                    message = json.loads(data.decode())

                    if message["version"] == API_VERSION:

                        # Ignore own broadcasts
                        if addr[0] != self.host and addr[1] != self.port:
                            # Try except if key error ignore message
                            if message['type'] == 'discovery':
                                peer_name = message["name"]
                                peer_port = message["port"]
                                peer_status = message["status"]
                                # Add to FIB
                                if peer_status == "online":
                                    if peer_name not in self.fib:
                                        peer_addr = (addr[0], peer_port)
                                        self.fib.add_entry(peer_name, peer_addr)
                                        # Send distance vector updates to neighbours
                                        self.broadcast_distance_vector()
                                        print(f"{peer_name} is online")
                                # Remove from FIB
                                elif peer_status == "offline":
                                    if peer_name in self.fib:
                                        self.fib.remove_entry(peer_name)
                                        # Send distance vector updates to neighbours
                                        self.broadcast_distance_vector()
                                        print(f"{peer_name} is offline")
                            elif message["type"] == "routing":
                                peer_name = message["name"]
                                peer_vector = message["data"]
                                dv_changed = self.fib.update_distance_vector(peer_name, peer_vector)
                                if dv_changed:
                                    # Send distance vector updates to neighbours
                                    self.broadcast_distance_vector()
                except KeyError as err:
                    logging.warning(f"{self.node_name} recieved and ignoring broadcast message with bad format: {err}")
                except Exception as err:
                    # Stop threads
                    self.stop()
                    logging.error(f"{self.node_name}: listen_for_peer_broadcasts(): {err}")
                    raise err

    def broadcast_presence(self):
        """
        Regularly broadcast presence to neighbours

        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while self.running.is_set():
                logging.debug(f"{self.node_name} running: {self.running.is_set()}")
                try:
                    json_packet = build_packet('discovery', self.node_name, 'broadcast_node', 'online',
                                               f"{self.port}:{','.join(self.sensor_type)}")
                    logging.debug(f"{self.node_name} broadcasting presence on port {self.broadcast_port}")
                    s.sendto(json.dumps(json_packet).encode('utf-8'), ('<broadcast>', self.broadcast_port))
                    time.sleep(self.presence_broadcast_interval)
                except Exception as err:
                    # Stop threads
                    self.stop()
                    logging.error(f"{self.node_name}: broadcast_presence(): {err}")
                    raise err

    def broadcast_offline(self):
        """
        Broadcast when leaving the network

        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            json_packet = build_packet('discovery', self.node_name, 'broadcast_node', 'offline',
                                       f"{self.port}:{','.join(self.sensor_type)}")
            s.sendto(json.dumps(json_packet).encode('utf-8'), ('<broadcast>', self.broadcast_port))
        logging.info(f"{self.node_name} broadcasting offline announcement on port {self.broadcast_port}")

    def broadcast_distance_vector(self):
        """
        Broadcast when distance vector changes

        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            current_time_utc = datetime.now(timezone.utc)
            timestamp = current_time_utc.isoformat()
            json_packet = {"version": API_VERSION,
                           "type": "routing",
                           "name": self.node_name,
                           "vector": self.fib.get_distance_vector(),
                           "timestamp": timestamp
                           }
            json_packet = build_packet('routing', self.node_name, 'broadcast_node', self.node_name,
                                       self.fib.get_distance_vector())

            logging.debug(f"{self.node_name} broadcasting distance vector on port {self.broadcast_port}")
            s.sendto(json.dumps(json_packet).encode('utf-8'), ('<broadcast>', self.broadcast_port))

    def listen_for_connections(self):
        """
        Listen for TCP connections (for intrest and data packets)

        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            logging.info(f"{self.node_name} is listening on port {self.port}")
            while self.running.is_set():
                try:
                    conn, addr = s.accept()
                    threading.Thread(target=self.handle_connection, args=(conn, addr)).start()  # , daemon=True).start()
                except Exception as err:
                    # Stop threads
                    self.stop()
                    logging.error(f"{self.node_name}: listen_for_connections(): {err}")
                    raise err

    def handle_connection(self, conn, addr):
        """
        Handle incomming TCP packets

        """
        with conn:
            while self.running:
                data = conn.recv(1024)
                if not data:
                    break
                packet = json.loads(data.decode())
                if packet['type'] == 'interest':
                    print(f"{self.node_name} received interest packet from {packet['sender']}")
                    self.handle_interest(packet, packet['sender'])
                elif packet['type'] == 'data':
                    print(f"{self.node_name} received data packet from {packet['sender']}")
                    self.handle_data(packet)

    def handle_interest(self, interest_packet, source_addr):
        message = json.loads(interest_packet.decode())
        name = message['name']
        # Check Content Store
        if name in self.cs:
            data_packet = self.cs.get(name)
            logging.debug(f"{self.node_name} sending data {name}")
            self.send_packet(source_addr, data_packet)
        else:
            sensor_type = interest_packet['name'].split('/').pop(4)
            if sensor_type in self.sensor_type:
                data = Sensor.generators.get(sensor_type, lambda: None)()
                # print(f'Generated {name} for requester {requester}')
                json_packet = build_packet('data', self.node_name, 'requester', name, data)
                self.send_packet(source_addr, json_packet)
            else:
                self.pit[name] = source_addr
                # print(f'added interest {name} with requester {requester}')
                destination = [key for key, value in self.fib.peer_list.items() if
                               value == self.interest_fib[sensor_type]].pop(0)
                json_packet = build_packet('interest', self.node_name, destination, name, '')
                self.send_packet(destination, json_packet)

    def handle_data(self, data_packet):
        name = data_packet['name']
        data = str(data_packet['data'])
        if re.compile(r'command').search(data):
            actuator, command = decode_command(name, data)
            print(f'{actuator.capitalize()} is turned {command}.')
        elif re.compile(r'alert').search(data):
            if self.node_name.__contains__('phone'):
                print(f"Alert {name.split('/')[-1]} is set off.")
            else:
                destination = [key for key in self.fib.keys() if key.__contains__('phone')]
                self.send_packet(self.fib.get(destination.pop()), data_packet)
        elif name in self.pit:
            destination = self.pit.get(name)
            print(f"Transmitting data packet from {data_packet['sender']} to {destination}")
            data_packet['sender'] = self.node_name
            data_packet['destination'] = destination
            self.send_packet(self.fib.get(destination), data_packet)
        else:
            self.cs[name] = data
            alert = is_alertable(name, data)
            if alert:
                if self.node_name.__contains__('phone'):
                    print(f"Alert {name.split('/')[-1]} is set off.")
                else:
                    destinations = [key for key in self.fib.keys() if key.__contains__('phone')]
                    data_packet['data'] = 'alert'
                    print(f"Alerting {destinations}.")
                    for phone in destinations:
                        self.send_packet(self.fib.get(phone), data_packet)
            else:
                print(f"Received {data_packet}")

    def send_packet(self, peer, json_packet):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(peer)
                packet = json.dumps(json_packet).encode('utf-8')
                s.sendall(packet)
                packet_type = json_packet['type']
                print(f"Sent {packet_type} '{json_packet['name']}' to {json_packet['destination']}")
            except ConnectionRefusedError:
                print(f"Failed to connect to {peer}")


def main():
    # parser = argparse.ArgumentParser(description='Run a NDN node.')
    # parser.add_argument('--id', required=True, help='The port number to bind the node to.')
    # parser.add_argument('--port', type=int, required=True, help='The port number to bind the node to.')
    # parser.add_argument('--broadcast_port', type=int, required=True, help='The port number to bind the node to.')
    # args = parser.parse_args()
    # a = RoomDevice("/group21/house1/room1", "0.0.0.0", 8000, 33333, logging_level=logging.DEBUG)
    # b = RoomDevice("/group21/house1/phone", "0.0.0.0", 8001, 33333, logging_level=logging.DEBUG)

    node = AnotherNode("/group21/house1/room1", "0.0.0.0", 8000, 33333, ['light', 'speed'])
    node.start()
    # try:
    while True:
        command = input(f'Node {node.node_name} - Enter command (interest/data/exit/add_fit): ').strip()
        if command == 'interest':
            destination = input('Enter destination node for interest packet: ').strip()
            sensor_name = input('Enter sensor name: ').strip()
            json_packet = build_packet('interest', node.node_name, destination, f'{node.node_name}/{sensor_name}', '')
            # send interest to node according to fib
            node.send_packet(node.fib.get_route(f'{node.node_name}/{sensor_name}'), json_packet)
        elif command == 'data':
            destination = input('Enter destination node for data packet: ').strip()
            sensor_name = input('Enter sensor name: ').strip()
            data_content = input('Enter data content: ').strip()
            json_packet = build_packet('data', node.node_name, destination, f'{destination}/{sensor_name}',
                                       data_content)
            # send data to node with the same data name
            node.send_packet(node.fib.get_route(f'{node.node_name}/{sensor_name}'), json_packet)
        elif command == 'exit':
            node.broadcast_offline()
            node.stop()
            os._exit(0)
        else:
            print('Invalid command. Try again.')


if __name__ == "__main__":
    main()
