import time
import os

class RoomMonitor:
    def monitor_input(self):
        while True:
            room_id_input = input("Enter room ID to monitor (or type 'quit' to exit): ").strip()
            if room_id_input.lower() == 'quit':
                break
            try:
                room_id = int(room_id_input)
                self.display_stats(room_id)
            except ValueError:
                print("Invalid input. Please enter a valid room ID or 'quit'.")

    def display_stats(self, room_id):
        
        stats_file = f"room_stats/room_{room_id}_stats.txt"
        while True:
            os.system('clear' if os.name == 'posix' else 'cls') 
            with open(stats_file, "r") as file:
                content = file.read().strip()
                print(content)
            time.sleep(1)


if __name__ == "__main__":
    monitor = RoomMonitor()
    monitor.monitor_input()
