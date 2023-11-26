"""
@author: C. Jonathan Cicai
"""

import os
from Device import Device

broadcast_port = 33000
port = 8079
home_id = input("Input home id: ").strip()
home_id =  f"home_{home_id}"

device = Device(None, home_id, "untrusted_device", port, broadcast_port, trusted=False)
device.turn_on_untrusted()
while True:
    active_rooms = os.listdir(f'{home_id}/room_stats')
    print("Choose destination device (or 'quit'):")
    for i, file_name in enumerate(active_rooms):
        room_name = file_name[:-10]  # Remove "_stats.txt" to get "room_X"
        print(f"{i}: {room_name}_device")

    dest_selection = input().strip()

    while not dest_selection.isdigit():
        if dest_selection == 'quit':
            os._exit(0)
        print("Invalid input. Please enter a device number.")
        dest_selection = input().strip()

    dest_index = int(dest_selection)

    if 0 <= dest_index < len(active_rooms):
        data_name = input('Type in data name (e.g., "temp", "humidity", "CO", "CO2", "motion", "light"): ')
        dest_node = f"{home_id}/room_{dest_index}_device"
        device.node.create_send_interest_packet(f"{dest_node}/{data_name}", dest_node)
    else:
        print("Invalid device selection. Please enter a valid device number.")
