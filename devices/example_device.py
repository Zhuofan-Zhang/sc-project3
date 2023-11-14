# -*- coding: utf-8 -*-
"""
Scalable Computing - Project 3
Group 21

Example of a node with sensors and actuators

Authors: Kim Nolle (23345045)
"""

import node
import threading
import time
import random
import logging

class RoomDevice(node.NDNNode):

    def __init__(self, node_name, host, port, broadcast_port, presence_broadcast_interval=30, response_timeout=60,
                 logging_level=logging.INFO):
        node.NDNNode.__init__(self, node_name, host, port, broadcast_port, presence_broadcast_interval,
                              response_timeout, logging_level)

        self.generators = {'temperature': lambda: random.randint(0, 30),
                           'light': lambda: random.randint(0, 30),
                           'humidity': lambda: random.randint(0, 90),
                           'radiation': lambda: random.randint(0, 30),
                           'co2': lambda: random.randint(0, 30),
                           'smoke': lambda: random.randint(0, 30),
                           'light_switch': lambda: random.choice([True, False]),
                           'motion': lambda: random.choice([True, False]),
                           }

    def start(self):
        # Start threads
        # Set threads as daemon threads so that they terminate when main terminates
        listener_thread = threading.Thread(target=self.listen_for_connections)  # , daemon=True)
        broadcast_thread = threading.Thread(target=self.broadcast_presence)  # , daemon=True)
        discovery_thread = threading.Thread(target=self.listen_for_peer_broadcasts)  # , daemon=True)
        device_thread = threading.Thread(target=self.device_loop)  # , daemon=True)
        self.threads.extend([listener_thread, broadcast_thread, discovery_thread, device_thread])
        for t in self.threads:
            t.start()

    def device_loop(self):
        while self.running:
            try:
                # Use get and set functions to simulate sensors and actuators
                for sensor in self.generators.keys():
                    self.set(sensor, self.generators[sensor]())
                time.sleep(5)
            except Exception as err:
                # Stop threads
                self.stop()
                logging.error(f"{self.node_name}: listen_for_peer_broadcasts(): {err}")
                raise err


a = RoomDevice("/group21/house1/room1", "0.0.0.0", 8000, 33333, logging_level=logging.DEBUG)
b = RoomDevice("/group21/house1/phone", "0.0.0.0", 8001, 33333, logging_level=logging.DEBUG)
a.start()
b.start()
try:
    while True:
        time.sleep(1)
except Exception as err:
    print("exception caught")
    a.stop()
    raise err
