from datetime import datetime, timezone

API_VERSION = 'v4'


def build_packet(packet_type, name, data):
    """
    Presence packet:
        version = version of the API
        type = "discovery"
        name = node name e.g. "/group1/house1/room1/device1"
        data = dict with port and status. status can be "online" or "offline"
        timestamp = timestamp when the packet was created
        
    Routing packet:
        version = version of the API
        type = "routing"
        name = node name e.g. "/group1/house1/room1/device1"
        data = distance vector
        timestamp = timestamp when the packet was created
        
    Interest packet:
        version = version of the API
        type = "interest"
        name = data name e.g. "/group1/house1/room1/device1/sensor1"
        data = None
        timestamp = timestamp when the packet was created
        
    Data packet:
        version = version of the API
        type = "data"
        name = data name e.g. "/group1/house1/room1/device1/sensor1"
        data = data to be sent
        timestamp = timestamp when the packet was created

    """
    
    current_time_utc = datetime.now(timezone.utc)
    time_stamp = current_time_utc.isoformat()
    
    json_packet = {'type': packet_type,
                   'version': API_VERSION,
                   #'sender': sender,
                   #'destination': destination,
                   'timestamp': time_stamp,
                   'name': name,
                   'data': data}
    
    return json_packet


numerical_sensor_list = ['temperature', 'light', 'humidity', 'radiation', 'co2', 'smoke',
                         'rpm', 'duration', 'load', 'electricity_usage', 'water_usage']
binary_sensor_list = ['light_switch', 'motion', 'motor', 'lock']


def decode_command(name, data):
    actuator = name.split('/')[-1]
    command = data.split('/')[-1]
    return actuator, command


def is_alertable(name, data):
    sensor_type = name.split('/').pop(4)
    if sensor_type in numerical_sensor_list:
        if int(data) > 0:
            return True
    elif sensor_type in binary_sensor_list:
        if data:
            return True
    else:
        return False
