"""
SmartHome class
Example Usage

python SmartHome.py --home_id 1 --n_rooms 5
"""
import threading
import random
import time
import argparse
from Room import Room

class SmartHome:
    def __init__(self, home_id, n_rooms):
        self.home_id = home_id
        self.n_rooms = n_rooms
        port = 8080
        self.rooms = []
        for i in range(n_rooms):
            self.rooms.append(Room(f"room_{i}", port, port+1))
            port+=2

    def main(self):
        threads = [threading.Thread(target=room.main) for room in self.rooms]
        for t in threads:
            t.daemon = True
            t.start()
        # simulate motion in the house
        while True:
            room = random.choice(self.rooms)
            print(f"Person in room {room.room_id}")
            room.stats['motion'] = 1
            walk_time = random.uniform(0, 15)
            time.sleep(walk_time)
            room.stats['motion'] = 0

def parse_args():
    parser = argparse.ArgumentParser(description='Simulate a Smart Home with motion detection in multiple rooms.')
    parser.add_argument('--home_id', type=int, required=True, help='Home ID')
    parser.add_argument('--rooms', type=int, required=True, help='Number of Rooms')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    home = SmartHome(home_id=args.home_id, n_rooms=args.rooms)
    home.main()