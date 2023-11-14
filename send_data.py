import json
import socket

# 设置发送数据的时间间隔，单位为秒
INTERVAL_SECONDS = 5


class SendData:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port

    def send(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.server_host, self.server_port))
            data = json.dumps({'type': 'interest',
                               'version': 'v1',
                               'sender': '/house3/room3/device3',
                               'destination': '/house2/room2/device2',
                               'time_stamp': 'ttt',
                               'name': '/house3/room3/device3/speed',
                               'data': ''})
            s.sendall(data.encode('utf-8'))
            response = s.recv(1024).decode('utf-8')
            print(f"Server response: {response}")


# 实例化SendData对象
sender1 = SendData('localhost', 8002)
# 无限循环，定期发送数据
# 发送数据到特定设备
sender1.send()
