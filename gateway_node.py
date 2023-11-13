import socket
import threading
import json

class GatewayServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = {}  # 存储连接的客户端

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Gateway Server is listening on {self.host}:{self.port}")

        while True:
            client_socket, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()

    def handle_client(self, client_socket, addr):
        print(f"New connection from {addr}")
        self.clients[addr] = client_socket
        while True:
            try:
                message = client_socket.recv(1024)
                if not message:
                    break

                # 处理接收到的数据
                data = json.loads(message.decode())
                print(f"Received data from {addr}: {data}")

                # 可以在这里添加转发逻辑

            except ConnectionResetError:
                break
        print(f"Connection with {addr} closed")
        del self.clients[addr]
        client_socket.close()

def main():
    host = '0.0.0.0'  # 监听所有接口
    port = 12345  # 使用的端口号
    server = GatewayServer(host, port)
    server.start_server()

if __name__ == '__main__':
    main()
