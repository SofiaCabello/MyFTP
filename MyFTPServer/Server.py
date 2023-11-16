import socket
import os
import fcntl
import struct
import subprocess
import requests
from multiprocessing import Process, Lock
from concurrent.futures import ThreadPoolExecutor

def get_public_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json")
        return response.json()["ip"]
    except Exception as e:
        print(f"[-] Failed to get public IP. Check your network connection. {e}")
        return None


def get_ip_address(interface_name='en0'):
    try:
        # 尝试通过socket获取IP地址
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            local_ip = socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', interface_name.encode('utf-8')[:15])
            )[20:24])
            return local_ip

    except IOError:
        # 如果通过socket获取失败，尝试通过ifconfig命令获取
        try:
            result = subprocess.check_output(['ifconfig', interface_name], universal_newlines=True)
            lines = result.split('\n')
            for line in lines:
                if 'inet ' in line:
                    words = line.split()
                    return words[1]

        except subprocess.CalledProcessError as e:
            print(f"Error retrieving IP address: {e}")

    return None


def handle_client(client_socket, client_address, lock, current_connection_num):
    """
    处理客户端连接的函数。

    Args:
        client_socket: 客户端套接字对象。
        client_address: 客户端地址。
        lock: 线程锁对象。
        current_connection_num: 当前连接数。

    Returns:
        None
    """
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

    finally:
        with lock:
            current_connection_num[0] -= 1
            print(f"   >> Current connection number: {current_connection_num[0]}")
            


def main():
    try:
        # 询问用户是否使用公网IP
        print("[+] Do you want to use public IP? (y/n)")
        use_public_ip = input()
        if use_public_ip == "y":
            server_ip = get_public_ip()
            print("[+] FTP Server running on public IP.")
        else:
            server_ip = get_ip_address('en0')
            print("[+] FTP Server running on local IP.")
        session_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        session_socket.bind(("", 0))
        server_port = session_socket.getsockname()[1]
        session_socket.listen(8)
        print("[+] Server IP:" + server_ip)
        print("[+] Server Dialog Port:" + str(server_port))
        print("[+] You need to set the client's IP and port to connect to the server.")

        current_connection_num = [0]

        # 打印信息
        print(f'[+] Listening on {server_ip}:{server_port}')

        lock = Lock()

        while True:
            client_socket, client_address = session_socket.accept()
            with lock:
                current_connection_num[0] += 1
                print(f"[+] Accepted connection from {client_address[0]}:{client_address[1]}")
                print(f"   >> Current connection number: {current_connection_num[0]}")

            p = Process(target=handle_client, args=(client_socket, client_address, lock, current_connection_num))
            p.start()

    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == '__main__':
    main()