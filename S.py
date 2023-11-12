"""
Sensor Class
"""
import threading
import time
import traceback


class Sensor:
    def __init__(self, sensor_type):
        self.sensor_type = sensor_type
        self.last_reading = None

    def get_reading(self, room):
        return round(room.stats[self.sensor_type], 3)
    
    def emit(self, new_reading):
        if new_reading != self.last_reading:
            print(f"{self.sensor_type}: {new_reading}")
            self.last_reading = new_reading

    def reading_loop(self, room):
        try:
            while True:
                reading = self.get_reading(room) 
                self.emit(reading)
                time.sleep(0.5)
        except Exception as e:
            print("Exception in reading loop:", e)
            print(traceback.format_exc())

    def main(self, room):
        thread = threading.Thread(target=self.reading_loop, args=(room,))
        thread.daemon = True  
        thread.start()
