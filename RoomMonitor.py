"""
@author: C. Jonathan Cicai
Room Monitor:
    - When run in the terminal, will display rooms stats and apparatus in realtime
"""

import time
import os

class RoomMonitor:
    def __init__(self):
        self.existed = False

    def monitor_input(self):
        home_id_input = input("Enter a house id: ").strip()
        room_id_input = input("Enter room ID to monitor (or type 'quit' to exit): ").strip()
        try:
            home_id = int(home_id_input)
            room_id = int(room_id_input)
            self.display_stats(home_id, room_id)
        except ValueError:
            print("Invalid input. Please enter a valid room ID or 'quit'.")
        except FileNotFoundError:
            print("The file doesn't exist" if not self.existed else "The simulation ended")

    def display_stats(self, home_id, room_id):
        stats_file = f"home_{home_id}/room_stats/room_{room_id}_stats.txt"
        while True:
            os.system('clear' if os.name == 'posix' else 'cls') 
            with open(stats_file, "r") as file:
                content = file.read().strip()
                print(content)
                self.existed = True
            time.sleep(1)


if __name__ == "__main__":
    monitor = RoomMonitor()
    monitor.monitor_input()
