
import socket
import sys
import os
from multiprocessing import Process, Lock

def handle_client(client_socket, client_address, lock):
    try:
        while True:
            command = client_socket.recv(1024).decode('utf-8')

            if not command:
                break

            command_list = command.split(' ')

            # 列出当前目录下的文件
            if command_list[0] == "ls":
                directory = "\n".join(os.listdir("."))
                client_socket.send(directory.encode("utf-8"))

            # 进入目录
            elif command_list[0] == "cd":
                try:
                    os.chdir(command_list[1])
                    client_socket.send("success".encode("utf-8"))
                except FileNotFoundError:
                    client_socket.send("File not exists".encode("utf-8"))
                continue

            # 下载
            elif command_list[0] == "get":
                filename = command_list[1]

                if not os.path.isfile(filename):
                    client_socket.send("0".encode("utf-8"))
                    continue

                file_size = os.path.getsize(filename)
                client_socket.send(str(file_size).encode("utf-8"))

                with open(filename, "rb") as f:
                    for chunk in iter(lambda: f.read(1024), b""):
                        client_socket.send(chunk)

            # 上传
            elif command_list[0] == "put":
                filename = command_list[1]
                file_size = command_list[2]

                with open(filename, "wb") as f:
                    buffer_bytes = 0
                    while buffer_bytes < float(file_size):
                        buffer = client_socket.recv(1024)
                        if not buffer:
                            break
                        f.write(buffer)
                        buffer_bytes += len(buffer)
                
            # 退出
            elif command_list[0] == "exit":
                break
        

        client_socket.close()
        with lock:
            print(f'[-] Disconnected from {client_address[0]}:{client_address[1]}')

    except Exception as e:
        print(f"[-] Error: {e}")
        client_socket.close()
        with lock:
            print(f'[-] Disconnected from {client_address[0]}:{client_address[1]}')
            


def main():
    try:
        print('This FTP Server is running...')
        print('Server IP:' + sys.argv[1])
        print('Server Port:' + sys.argv[2])

        # Socket创建
        server_ip = sys.argv[1]
        server_port = int(sys.argv[2])
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("", server_port))
        server_socket.listen(16)

        # 打印信息
        print(f'[+] Listening on {server_ip}:{server_port}')

        lock = Lock()

        while True:
            client_socket, client_address = server_socket.accept()
            with lock:
                print(f'[+] Accepted connection from {client_address[0]}:{client_address[1]}')
            
            p = Process(target=handle_client, args=(client_socket, client_address, lock))
            p.start()

    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == '__main__':
    main()