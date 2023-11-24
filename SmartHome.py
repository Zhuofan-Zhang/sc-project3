"""
SmartHome class
Example Usage

python SmartHome.py --home_id 1 --n_rooms 5
"""
import threading
import random
import time
import os
import argparse
from Room import Room

class SmartHome:
    def __init__(self, home_id, n_rooms):
        self.home_id = home_id
        self.n_rooms = n_rooms
        broadcast_port = 33000
        port = 8080
        self.rooms = []
        for i in range(n_rooms):
            self.rooms.append(Room(f"room_{i}", port, broadcast_port))
            port+=1
        
    def simulate_walking(self):
        # simulate motion in the house
        while True:
            room = random.choice(self.rooms)
            room.stats['motion'] = 1
            walk_time = random.uniform(0, 5)
            time.sleep(walk_time)
            room.stats['motion'] = 0

    def main(self):
        threads = [threading.Thread(target=room.main) for room in self.rooms] + [threading.Thread(target=self.simulate_walking)]
        for t in threads:
            t.daemon = True
            t.start()

        while True:
            print("Select a room via room number below (or 'quit'):")
            for i, room in enumerate(self.rooms, start=0):
                print(f"{i}: {room.room_id}")
            selection = input().strip()
            if selection.lower() == 'quit':
                break  # Exit the loop if the user enters 'quit'
            selection_index = int(selection)
            if 0 <= selection_index < len(self.rooms):
                room = self.rooms[selection_index]
                print(room.device.node.node_name)
                selection_valid = False
                while not selection_valid:
                    selection = input("Select action: 'turn on/off', 'send interest': ")
                    if selection == 'turn on':
                        selection_valid = True
                        if not room.device.on:
                            print("Turning device on...")
                            room.device.turn_on()
                        print("Device is on")
                    elif selection == 'turn off':
                        selection_valid = True
                        if room.device.on:
                            print("Turning device off...")
                            room.device.turn_off()
                        print("Device is off")
                    elif selection == 'send interest':
                        selection_valid = True
                        print("Choose destination device:")
                        for i, r in enumerate(self.rooms, start=0):
                            print(f"{i}: {r.device.device_id}")
                        selection = input()
                        selection_index = int(selection)
                        if 0 <= selection_index < len(self.rooms):
                            data_name = input('Type in data name (eg "temp", "humidity", "CO", "CO2", "motion", "light"): ')
                            # create_send_intrest_packet(self, data_name, destination)
                            dest_node = self.rooms[selection_index].device.node.node_name
                            room.device.node.create_send_interest_packet(f"{dest_node}/{data_name}", dest_node)
                            print(room.device.node.node_name)
                            print(dest_node)
                            
                    else:
                        print("Invalid selection")

            else:
                print("Invalid selection. Please enter a valid room number.")

            
       
        

def parse_args():
    parser = argparse.ArgumentParser(description='Simulate a Smart Home with motion detection in multiple rooms.')
    parser.add_argument('--home_id', type=int, required=True, help='Home ID')
    parser.add_argument('--rooms', type=int, required=True, help='Number of Rooms')
    return parser.parse_args()

if __name__ == "__main__":
    if not os.path.exists("device_logs"):
        os.makedirs("device_logs")
    if not os.path.exists("room_stats"):
        os.makedirs("room_stats")
    args = parse_args()
    home = SmartHome(home_id=args.home_id, n_rooms=args.rooms)
    home.main()