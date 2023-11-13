import socket
import json

def connect_to_gateway(gateway_ip, gateway_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((gateway_ip, gateway_port))
        # 发送数据示例
        data = {'message': 'Hello from Raspberry Pi'}
        s.send(json.dumps(data).encode('utf-8'))
        # 接收数据示例
        response = s.recv(1024)
        print("Received:", response.decode('utf-8'))

# 替换为Gateway的实际IP地址和端口
GATEWAY_IP = '172.17.0.2'
GATEWAY_PORT = 12345
connect_to_gateway(GATEWAY_IP, GATEWAY_PORT)
