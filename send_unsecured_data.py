import random
import socket
import json

def send_data_packet(destination_ip, destination_port):

    data_packet = {
        "type": "data",
        "version": "v1",
        "sender": "/house3/room3/device3",
        "destination": "/house2/room2/device2",
        "time_stamp": "ttt",
        "name": "/house3/room3/device3/light",
        "data": "command/off"
    }


    json_data = json.dumps(data_packet)


    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        s.connect((destination_ip, destination_port))

        s.sendall(json_data.encode('utf-8'))

        response = s.recv(1024)
        print(f"Received: {response.decode('utf-8')}")

# port = random.choice([33006])

send_data_packet("0.0.0.0", 33300)  # replace port