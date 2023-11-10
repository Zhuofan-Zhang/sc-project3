API_VERSION = 'v1'


def build_packet(packet_type, sender, data_name, data_content):
    json_packet = {'type': packet_type, 'from': sender, 'version': API_VERSION, 'name': data_name, 'data': data_content}
    return json_packet

    # def send_interest(self, peer, interest_name):
    #     with (socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s):
    #         try:
    #             s.connect(peer)
    #             interest_packet = {'type': 'interest', 'name': interest_name, 'from': self.node_name}
    #             s.sendall(json.dumps(interest_packet).encode('utf-8'))
    #             print(f"Sent interest '{interest_name}' to {peer}")
    #         except ConnectionRefusedError:
    #             print(f"Failed to connect to {peer}")
    #
    # def send_data(self, peer, data_name, data_content):
    #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #         s.connect(peer)
    #         data_packet = build_packet('data', data_content, data_name)
    #         s.sendall(json.dumps(data_packet).encode('utf-8'))
