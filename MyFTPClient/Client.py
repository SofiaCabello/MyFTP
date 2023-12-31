import socket
import os
import sys
import threading


def get(client_socket, filename):
    client_socket.send(f"get {filename}".encode("utf-8"))
    file_size = client_socket.recv(1024).decode("utf-8")
    
    if file_size == "0":
        print(f"[-]{filename} not found")
        return
    
    with open(filename,  "wb") as f:
        buffer_bytes = 0
        while buffer_bytes < int(file_size):
            buffer = client_socket.recv(1024)
            if not buffer:
                break
            f.write(buffer)
            buffer_bytes += len(buffer)

    print(f"[+] {filename} downloaded successfully")
    
def put(client_socket, filename):
    if not os.path.isfile(filename):
        print(f"[-]{filename} not found")
        return
    
    file_size = os.path.getsize(filename)
    client_socket.send(f"put {filename} {file_size}".encode("utf-8"))

    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(1024), b""):
            client_socket.send(chunk)

    print(f"[+] {filename} uploaded successfully")


def main():
    # 该客户端在启动时需要将服务器IP和端口号作为参数传入
    print('This FTP Client is running...')
    print('Server IP:' + sys.argv[1])
    print('Server Port:' + sys.argv[2])

    #　Socket创建
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 连接服务器
    client_socket.connect((server_ip, server_port))

    # 打印信息
    print(f'[+] Connected to {server_ip}:{server_port}')

    # 交互界面，客户端支持以下命令
    # 1. ？？ 我还没想好做什么，也许是登录吧
    # 2. ls 列出当前目录下的文件
    # 3. cd <dir> 进入目录
    # 4. get <filename> 下载文件
    # 5. put <filename> 上传文件
    # 6. exit 退出
    while True:
        command = input("MyFTP> ").strip()
        command_list = command.split(' ')

        if not command:
            continue

        # 列出当前目录下的文件
        if command_list[0] == "ls":
            client_socket.send("ls".encode("utf-8"))
            data = client_socket.recv(1024)
            for dir in data.decode("utf-8").split('\n'):
                print("     | " + dir)

        # 进入目录
        elif command_list[0] == "cd":
            client_socket.send(command.encode("utf-8"))
            data = client_socket.recv(1024)
            if data.decode("utf-8") == "success":
                print("     < Change directory success")
            else:
                print("Directory not exists")

        # 下载文件
        elif command_list[0] == "get":
            file_name = command_list[1]
            t = threading.Thread(target=get, args=(client_socket, file_name))
            t.start()
            t.join()

        # 上传文件
        elif command_list[0] == "put":
            file_name = command_list[1]
            t = threading.Thread(target=put, args=(client_socket, file_name))
            t.start()
            t.join()

        # 退出
        elif command_list[0] == "exit":
            client_socket.send("exit".encode("utf-8"))
            break

        elif command_list[0] == "help":
            print("ls\t\tList files in current directory")
            print("cd\t\tChange directory")
            print("get\t\tDownload file from server")
            print("put\t\tUpload file to server")
            print("exit\t\tExit")


if __name__ == '__main__':
    main()