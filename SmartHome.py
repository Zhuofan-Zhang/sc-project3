"""
SmartHome class
Example Usage

python SmartHome.py --home_id 1 --n_rooms 5

@author: C. Jonathan Cicai
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
            for i, room in enumerate(self.rooms):
                print(f"{i}: {room.room_id}")

            selection = input().strip().lower()

            if selection == 'quit':
                break  # Exit the loop if the user enters 'quit'

            while not selection.isdigit():
                print("Invalid input. Please enter a room number or 'quit'.")
                selection = input().strip().lower()

            selection_index = int(selection)

            if 0 <= selection_index < len(self.rooms):
                room = self.rooms[selection_index]
                print(room.device.node.node_name)
                
                while True:
                    print("Select action: 'turn on/off', 'send interest', 'actuate' (or 'back' to go back):")
                    action = input().strip().lower()

                    if action == 'back':
                        break

                    while action not in ['turn on', 'turn off', 'send interest', 'actuate']:
                        print("Invalid selection. Please enter a valid action.")
                        action = input().strip().lower()

                    if action in ['turn on', 'turn off']:
                        if (action == 'turn on' and not room.device.on) or (action == 'turn off' and room.device.on):
                            print(f"Turning device {action.split()[1]}...")
                            room.device.toggle()
                            print(f"Device is {'on' if room.device.on else 'off'}")
                        else:
                            print(f"Device is already {'on' if room.device.on else 'off'}")
                    elif action == 'send interest':
                        print("Choose destination device:")
                        for i, r in enumerate(self.rooms):
                            print(f"{i}: {r.device.device_id}")

                        dest_selection = input().strip()

                        while not dest_selection.isdigit():
                            print("Invalid input. Please enter a device number.")
                            dest_selection = input().strip()

                        dest_index = int(dest_selection)

                        if 0 <= dest_index < len(self.rooms):
                            data_name = input('Type in data name (e.g., "temp", "humidity", "CO", "CO2", "motion", "light"): ')
                            dest_node = self.rooms[dest_index].device.node.node_name
                            room.device.node.create_send_interest_packet(f"{dest_node}/{data_name}", dest_node)
                        else:
                            print("Invalid device selection. Please enter a valid device number.")
                    elif action == 'actuate':
                        print("Select device to actuate:")
                        for k in room.apparatus:
                            print(k)

                        apparatus_selection = input().strip()

                        while apparatus_selection not in room.apparatus:
                            print("Not a valid apparatus. Please select a valid device.")
                            apparatus_selection = input().strip()

                        room.device.actuate(apparatus_selection)
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
    print("Turning off devices safely...")
    for room in home.rooms:
        room.device.turn_off()