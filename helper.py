from datetime import datetime, timezone

API_VERSION = 'v2'


def build_packet(packet_type, sender, destination, name, data):
    current_time_utc = datetime.now(timezone.utc)
    time_stamp = current_time_utc.isoformat()
    json_packet = {'type': packet_type,
                   'version': API_VERSION,
                   'sender': sender,
                   'destination': destination,
                   'time_stamp': time_stamp,
                   'name': name,
                   'data': data}
    return json_packet
