import json
#import os
#import re
import socket
import threading
import time
import logging
import random
import argparse

from helper import build_packet #, decode_command, is_alertable
#from sensor import Sensor
import fib

API_VERSION = 'v4'

class NDNNode:
    def __init__(self, node_name, sensors, port, broadcast_port, presence_broadcast_interval=30, response_timeout=60, logging_level=logging.INFO):
        
        self.node_name = node_name
        
        # Create list of data name as <node_name>/<sensor_name>
        if not node_name.endswith('/'):
            node_name += '/'
        self.data_names = [node_name+s for s in sensors]
        
        # Networking
        self.host = socket.gethostbyname(socket.gethostname()) # Automatically get correct host
        self.port = port
        self.broadcast_port = broadcast_port
        self.fib = fib.ForwardingInfoBase(self.node_name)
        self.presence_broadcast_interval = presence_broadcast_interval
        self.response_timeout = response_timeout

        # Data storage
        self.pit = {}
        self.cs = {}
        
        # TODO: Generate/Load public and private keys
        #self.pub_key_CA = None
        #self.pub_key = None
        #self.priv_key = None
        #self.key_store = {} # Like content store except for keys
        
        # Logging verbosity
        logging.basicConfig(format="%(asctime)s.%(msecs)04d [%(levelname)s] %(message)s", level=logging_level, datefmt="%H:%M:%S:%m")
        
        # Threading
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
        self.running.clear()
        print(self.running.is_set())
        
    def set(self, sensor_name, data):
        """
        Create data packet with data, send if interest in PIT and store in content store.
        
        Note: sensor_name should just be name of the sensor. 
              Node name is automatically added as prefix!

        """
        # Get data name as <node_name>/<sensor_name>
        data_name = self.node_name
        if not data_name.endswith('/'):
            data_name += '/'
        data_name += sensor_name
        
        # Create packet
        json_packet = build_packet(packet_type = 'data', 
                                   name = data_name, 
                                   data = data,
                                   api_version = API_VERSION
                                   )
        
        data_packet = json.dumps(json_packet).encode('utf-8')
        
        # TODO: sign packet
        
        # If in PIT forward data and remove entry from PIT
        if data_name in self.pit:
            # Send data if interest is in PIT
            self.send_data(data_name, data_packet)
        
        # Store in content store
        self.cs[data_name] = data_packet
            
            
    def get(self, data_name):
        # If in content store return
        if data_name in self.cs:
            data_packet = self.cs.get(data_name)
          
        # If not in content store, send interest package
        else:
            # Create packet
            json_packet = build_packet(packet_type = 'interest', 
                                       name = data_name, 
                                       data = None,
                                       api_version = API_VERSION
                                       )
            interest_packet = json.dumps(json_packet).encode('utf-8')
            self.send_interest(data_name, None, interest_packet)
        
            # Block until it is in the content store or until timeout
            timer = threading.Thread(target=self.wait_for_data, args=(data_name, self.response_timeout))#, daemon=True)
            timer.start()
            timer.join() # Block untill data incontent store or timeout
            
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
                    threading.Thread(target=self.handle_connection, args=(conn, addr)).start() #, daemon=True).start()
                except Exception as err:
                    # Stop threads
                    self.stop()
                    logging.error(f"{self.node_name}: listen_for_connections(): {err}")
                    raise err
                    
    def broadcast_presence(self):
        """
        Regularly broadcast presence to neighbours

        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while self.running.is_set():
                try:
                    logging.debug(f"{self.node_name} broadcasting prescence on port {self.broadcast_port}")
                    json_packet = build_packet(packet_type = 'discovery', 
                                               name = self.node_name, 
                                               data = {'port' : self.port,
                                                       'status' : 'online'},
                                               api_version = API_VERSION
                                               )
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
            json_packet = build_packet(packet_type = 'discovery', 
                                       name = self.node_name, 
                                       data = {'port' : self.port,
                                               'status' : 'offline'},
                                       api_version = API_VERSION
                                       )
            logging.info(f"{self.node_name} broadcasting offline announcment on port {self.broadcast_port}")
            s.sendto(json.dumps(json_packet).encode('utf-8'), ('<broadcast>', self.broadcast_port))
        
    def broadcast_distance_vector(self):
        """
        Broadcast when distance vector changes

        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            json_packet = build_packet(packet_type = 'routing', 
                                       name = self.node_name, 
                                       data = self.fib.get_distance_vector(),
                                       api_version = API_VERSION
                                       )
            logging.debug(f"{self.node_name} broadcasting distance vector on port {self.broadcast_port}")
            s.sendto(json.dumps(json_packet).encode('utf-8'), ('<broadcast>', self.broadcast_port))

    def listen_for_peer_broadcasts(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            s.bind((self.host, self.broadcast_port))
            logging.info(f"{self.node_name} is listening on port {self.broadcast_port}")
            while self.running.is_set():
                try:
                    data, addr = s.recvfrom(1024)
                    
                    if data:
                        logging.debug(f"{self.node_name} recieved broadcast from {addr}")
                        message = json.loads(data.decode())
                        
                        if message["version"] == API_VERSION:
                            
                            # Ignore own broadcasts
                            if addr[0] != self.host and addr[1] != self.port:
                                
                                if message['type'] == 'discovery':
                                    
                                    peer_name = message["name"]
                                    peer_port = message["data"]["port"]
                                    peer_status = message["data"]["status"]
                                    
                                    # Add to FIB
                                    if peer_status == "online":
                                        if peer_name not in self.fib:
                                            peer_addr = (addr[0], peer_port)
                                            logging.debug(f"{self.node_name} adding peer {peer_name} on {peer_addr} to FIB")
                                            self.fib.add_entry(peer_name, peer_addr)
                                            # Send distance vector updates to neighbours
                                            self.broadcast_distance_vector()
                                            
                                    # Remove from FIB
                                    elif peer_status == "offline":
                                        if peer_name in self.fib:
                                            logging.debug(f"{self.node_name} removing peer {peer_name} on {peer_addr} to FIB")
                                            self.fib.remove_entry(peer_name)
                                            # Send distance vector updates to neighbours
                                            self.broadcast_distance_vector()
                                            
                                elif message["type"] == "routing":
                                    peer_name = message["name"]
                                    peer_vector = message["data"]
                                    
                                    logging.debug(f"{self.node_name} updating peer {peer_name} on {peer_addr} in FIB")
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

    def handle_connection(self, conn, addr):
        """
        Handle incomming TCP packets

        """
        with conn:
            while self.running.is_set():
                data = conn.recv(1024)
                if not data:
                    break
                packet = json.loads(data.decode())
                
                if packet["version"] == API_VERSION:
                    if packet['type'] == 'interest':
                        logging.debug(f"{self.node_name} received interest packet from {addr}")
                        self.handle_interest(data, addr)
                    elif packet['type'] == 'data':
                        logging.debug(f"{self.node_name} received data packet from {addr}")
                        self.handle_data(data)

    def handle_interest(self, interest_packet, source_addr):
        message = json.loads(interest_packet.decode())
        name = message['name']
        
        # Check Content Store first
        if name in self.cs:
            data_packet = self.cs.get(name)
            logging.debug(f"{self.name} sending data {name}")
            self.send_packet(source_addr, data_packet)
        else:
            self.send_interest(self, name, source_addr, interest_packet)
            
    def send_interest(self, name, source_addr, interest_packet):
        # Add interest to PIT
        if name not in self.pit:
            self.pit[name] = set([source_addr])
        else:
            self.pit[name].add(source_addr)
            
        # Check if this node is source of the data
        # If not forward interest
        if name not in self.data_names:
            
            # Get neighbours to forward intrest to
            addr_to_try = self.fib.get_routes(name)
            
            success = False
            for addr in addr_to_try:
                try:
                    self.send_packet(addr, interest_packet)
                    success = True
                    break
                except Exception as err:
                    logging.debug(f"{self.node_name} failed to forward interest to {addr}: {err}")
                    # TODO: remove addr from FIB?
                    
            if success:
                logging.debug(f"{self.node_name} forwarded interest in {name} to {addr}")
            else:
                logging.warning(f"{self.node_name} failed to forwarded interest in {name}")

    def handle_data(self, data_packet):
        message = json.loads(data_packet.decode())
        name = message['name']
        
        if name in self.pit:
            # TODO: check signature
            
            # Send data if interest is in PIT
            self.send_data(name, data_packet)
        
            # Store in content store
            self.cs[name] = data_packet
            
    def send_data(self, name, data_packet):
        """
        If in PIT forward data and remove entry from PIT
        
        """
        success = False
        for addr in self.pit.pop(name):
            try:
                if addr != (self.host, self.port):
                    self.send_packet(addr, data_packet)
                success = True
                logging.debug(f"{self.node_name} forwarded data {name} to {addr}")
                break
            except Exception as err:
                logging.debug(f"{self.node_name} failed to forward data to {addr}: {err}")
                # TODO: remove addr from FIB?
                
        if not success:
            logging.warning(f"{self.node_name} failed to forwarded data {name}") 
        
        # TODO: Move this logic outside of this class
        """
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
                    # if there's no phone available the alerts are discarded
                    if len(destinations) > 0:
                        data_packet['data'] = 'alert'
                        print(f"Alerting {destinations}.")
                        for phone in destinations:
                            self.send_packet(self.fib.get(phone), data_packet)
                    else:
                        print("Alert is discarded.")
            else:
                print(f"Received {data_packet}")
                
        """

    def send_packet(self, peer, packet):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(peer)
                s.sendall(packet)
            except ConnectionRefusedError:
                print(f"Failed to connect to {peer}")


def main():
    parser = argparse.ArgumentParser(description='Run a NDN node.')
    parser.add_argument('--node-name', type=str, required=True, help='The node name.')
    parser.add_argument('--sensor-name', type=str, required=True, help='The sensor name.')
    parser.add_argument('--get', type=str, required=True, help='The data name to get.')
    parser.add_argument('--port', type=int, required=True, help='The port number to bind the node to.')
    parser.add_argument('--broadcast-port', type=int, required=True, help='The port number to bind the node to.')
    args = parser.parse_args()

    #house_name = 'house1'
    # house_name = os.environ['HOUSE_NAME']
    #room_name = 'room1'
    # room_name = os.environ['ROOM_NAME']
    #device_name = 'device1'
    # device_name = os.environ['DEVICE_NAME']
    #port = 8001
    # port = int(os.environ['PORT'])
    #broadcast_port = 
    # broadcast_port = int(os.environ['BROADCAST_PORT'])
    #sensor_type = ['foo', 'bar']
    # sensor_type = os.environ['SENSOR_TYPE'].split(',')

    node= NDNNode(args.node_name, sensors=[args.sensor_name], port=args.port, broadcast_port=args.broadcast_port, logging_level=logging.DEBUG)
    node.start()
    
    
    while True:
        node.set(args.sensor_name, random.randint(0, 10))
        node.get(args.get)        
        
        time.sleep(10)
    # try:
    #while True:
    #    command = input(f'Node {node.node_name} - Enter command (interest/data/exit/add_fit): ').strip()
    #    if command == 'interest':
    #        destination = input('Enter destination node for interest packet: ').strip()
    #        sensor_name = input('Enter sensor name: ').strip()
    #        json_packet = build_packet('interest', node.node_name, destination, f'{node.node_name}/{sensor_name}', '')
    #        # send interest to node according to fib
    #        node.send_packet(node.fib.get(destination), json_packet)
    #    elif command == 'data':
    #        destination = input('Enter destination node for data packet: ').strip()
    #        sensor_name = input('Enter sensor name: ').strip()
    #        data_content = input('Enter data content: ').strip()
    #        json_packet = build_packet('data', node.node_name, destination, f'{destination}/{sensor_name}',
    #                                   data_content)
    #        # send data to node with the same data name
    #        node.send_packet(node.fib.get(destination), json_packet)
    #    elif command == 'exit':
    #        node.broadcast_offline()
    #        node.stop()
    #        os._exit(0)
    #    else:
    #        print('Invalid command. Try again.')


if __name__ == "__main__":
    main()
