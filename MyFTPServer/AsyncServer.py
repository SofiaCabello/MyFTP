import asyncio
import fcntl
import requests
import socket
import struct
import subprocess
import os

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

async def handle_client(reader, writer):
    client_socket = writer.get_extra_info('socket')
    print(f"[+] New client connected: {client_socket.getpeername()}")
    try:
        while True:
            command = (await reader.readline()).decode().strip()

            if not command:
                break

            command_list = command.split()

            # 下载文件
            if command_list[0] == "get":
                filename = command_list[1]
                if not os.path.isfile(filename):
                    writer.write("0\n".encode())
                    await writer.drain()
                    continue

                file_size = os.path.getsize(filename)
                writer.write(f"{file_size}\n".encode())
                await writer.drain()

                with open(filename, "rb") as f:
                    while True:
                        chunk = f.read(1024)
                        if not chunk:
                            break
                        writer.write(chunk)
                        await writer.drain()

            # 上传文件
            elif command_list[0] == "put":
                filename = command_list[1]
                file_size = int(command_list[2])

                with open(filename, "wb") as f:
                    while file_size > 0:
                        buffer = await reader.read(min(1024, file_size))
                        f.write(buffer)
                        file_size -= len(buffer)

            # 列出目录
            elif command_list[0] == "ls":
                dirs = "\n".join(os.listdir('.'))
                writer.write(f"{dirs}\nEND_OF_LS\n".encode())
                await writer.drain()

            # 切换目录
            elif command_list[0] == "cd":
                try:
                    os.chdir(command_list[1])
                except NotADirectoryError:
                    writer.write("[-] Not a directory\n".encode())
                    await writer.drain()
                    continue
                except FileNotFoundError:
                    writer.write("[-] Directory not found\n".encode())
                    await writer.drain()
                    continue
                writer.write("[+] Directory changed successfully\n".encode())
                await writer.drain()

            # 退出
            elif command_list[0] == "exit":
                break
    except Exception as e:
        print(f"[-] Client disconnected: {client_socket.getpeername()}. Errorr: {e}")
    finally:
        print(f"[-] Client disconnected: {client_socket.getpeername()}")
        writer.close()
        await writer.wait_closed()

async def main():
    print("[+] Do you want to use public IP? (y/n)")
    use_public_ip = input()
    if use_public_ip == "y" :
        # 获取公网IP地址
        server_ip = get_public_ip()
        if not server_ip:
            print("[-] Failed to get public IP address. Exiting...")
            return
    else:
        # 获取本机IP地址
        print("[+] Do you want to use localhost? (y/n)")
        use_localhost = input()
        if use_localhost == "y":
            server_ip = "127.0.0.1"
        else:
            server_ip = get_ip_address()
        if not server_ip:
            print("[-] Failed to get local IP address. Exiting...")
            return

    server_port = 8888  # 你可以选择其他的端口号
    server = await asyncio.start_server(handle_client, server_ip, server_port)

    print(f"[+] Server is running on {server_ip}:{server_port}")

    async with server:
        await server.serve_forever()

asyncio.run(main()) 