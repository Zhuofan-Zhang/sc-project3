# -*- coding: utf-8 -*-
"""
Scalable Computing - Project 3
Group 21

NDN Node Base Class

Authors: Zhuofan Zhang ()
         Kim Nolle (23345045)
"""

import json
#import os
#import re
import socket
import threading
import time
import logging
from datetime import datetime, timezone

import fib
#import sensor

API_VERSION = 'v3'

class NDNNode:
    def __init__(self, node_name, host, port, broadcast_port, presence_broadcast_interval=30, response_timeout=60, logging_level=logging.INFO):
        
        self.node_name = node_name
        
        # Networking
        self.host = host
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
        # Start threads
        # Set threads as daemon threads so that they terminate when main terminates
        listener_thread = threading.Thread(target=self.listen_for_connections)#, daemon=True)
        broadcast_thread = threading.Thread(target=self.broadcast_presence)#, daemon=True)
        discovery_thread = threading.Thread(target=self.listen_for_peer_broadcasts)#, daemon=True)
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
            data_name =+ '/'
        data_name += sensor_name
        
        # Create packet
        current_time_utc = datetime.now(timezone.utc)
        timestamp = current_time_utc.isoformat()
        json_packet = {"version": API_VERSION,
                       "type": "data",
                       "name" : data_name,
                       "data" : data,
                       "timestamp": timestamp
                      }
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
            current_time_utc = datetime.now(timezone.utc)
            timestamp = current_time_utc.isoformat()
            json_packet = {"version": API_VERSION,
                           "type": "interest",
                           "name" : data_name,
                           "timestamp": timestamp
                          }
            interest_packet = json.dumps(json_packet).encode('utf-8')
            self.send_interest(self, data_name, interest_packet)
        
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
                                        self.fib.add_entry(self, peer_name, peer_addr)
                                        # Send distance vector updates to neighbours
                                        self.broadcast_distance_vector()
                                        
                                # Remove from FIB
                                elif peer_status == "offline":
                                    if peer_name in self.fib:
                                        self.fib.remove_entry(peer_name)
                                        # Send distance vector updates to neighbours
                                        self.broadcast_distance_vector()
                                        
                            elif message["type"] == "routing":
                                peer_name = message["name"]
                                peer_vector = message["vector"]
                                
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
                    current_time_utc = datetime.now(timezone.utc)
                    timestamp = current_time_utc.isoformat()
                    json_packet = {"version": API_VERSION,
                                   "type": "discovery",
                                   "name" : self.node_name,
                                   "port" : self.port,
                                   "status" : "online",
                                   "timestamp": timestamp
                                  }
                    
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
            current_time_utc = datetime.now(timezone.utc)
            timestamp = current_time_utc.isoformat()
            json_packet = {"version": API_VERSION,
                           "type": "discovery",
                           "name" : self.node_name,
                           "port" : self.port,
                           "status" : "offline",
                           "timestamp": timestamp
                           }
            
            logging.info(f"{self.node_name} broadcasting offline announcment on port {self.broadcast_port}")
            s.sendto(json.dumps(json_packet).encode('utf-8'), ('<broadcast>', self.broadcast_port))
            

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
                           "name" : self.node_name,
                           "vector" : self.fib.get_distance_vector(),
                           "timestamp": timestamp
                           }
            
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
                    threading.Thread(target=self.handle_connection, args=(conn, addr)).start() #, daemon=True).start()
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
            if self.running.is_set():
                data = conn.recv(1024)
                
                if data:
                    packet = json.loads(data.decode())
                    
                    if packet["version"] == API_VERSION:
                        if packet['type'] == 'interest':
                            logging.debug(f"{self.node_name} received interest packet from {addr}")
                            self.handle_interest(data, addr)
                            
                        elif packet['type'] == 'data':
                            logging.debug(f"{self.node_name} received interest packet from {addr}")
                            self.handle_data(data)
                        
                        
    def handle_interest(self, intrest_packet, source_addr):
        message = json.loads(intrest_packet.decode())
        name = message['name']
            
        # Check Content Store
        if name in self.cs:
            data_packet = self.cs.get(name)
            logging.debug(f"{self.name} sending data {name}")
            self.send_packet(source_addr, data_packet)
            
        else:
            self.send_interest(self, name, source_addr, intrest_packet)
            
                
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
            
    
    def send_interest(self, name, source_addr, intrest_packet):
        # Add interest to PIT
        if name not in self.pit:
            self.pit[name] = set([source_addr])
        else:
            self.pit[name].add(source_addr)
            
        # Get neighbours to forward intrest to
        addr_to_try = self.fib.get_routes(name)
        
        success = False
        for addr in addr_to_try:
            try:
                self.send_packet(addr, intrest_packet)
                success = True
                break
            except Exception as err:
                logging.debug(f"{self.node_name} failed to forward interest to {addr}: {err}")
                # TODO: remove addr from FIB?
                
        if success:
            logging.debug(f"{self.node_name} forwarded interest in {name} to {addr}")
        else:
            logging.warning(f"{self.node_name} failed to forwarded interest in {name}")
        
        
    def send_packet(self, peer, packet):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(peer)
                s.sendall(packet)
            except ConnectionRefusedError:
                print(f"Failed to connect to {peer}")



