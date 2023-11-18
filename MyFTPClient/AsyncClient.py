import asyncio
import os
import sys

async def get(reader, writer, filename):
    writer.write(f"get {filename}\n".encode())
    await writer.drain()

    file_size = int((await reader.readline()).decode().strip())
    if file_size == 0:
        print(f"[-]{filename} not found")
        return

    with open(filename, "wb") as f:
        while file_size > 0:
            buffer = await reader.read(min(1024, file_size))
            f.write(buffer)
            file_size -= len(buffer)

    print(f"[+] {filename} downloaded successfully")

async def put(reader, writer, filename):
    if not os.path.isfile(filename):
        print(f"[-]{filename} not found")
        return

    file_size = os.path.getsize(filename)
    writer.write(f"put {filename} {file_size}\n".encode())
    await writer.drain()

    with open(filename, "rb") as f:
        while True:
            chunk = f.read(1024)
            if not chunk:
                break
            writer.write(chunk)
            await writer.drain()

    print(f"[+] {filename} uploaded successfully")

async def main():
    print('[+] This FTP Client is running...')
    print('[+] Server IP:' + sys.argv[1])
    print('[+] Server Port:' + sys.argv[2])

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    
    reader, writer = await asyncio.open_connection(server_ip, server_port)

    while True:
        command = input("FTP> ")
        command_list = command.split(" ")
        if command_list[0] == "get":
            await get(reader, writer, command_list[1])
        elif command_list[0] == "ls":
            writer.write("ls\n".encode())
            await writer.drain()
            data = await reader.readline()
            print(data.decode().strip())
        elif command_list[0] == "cd":
            writer.write(f"cd {command_list[1]}\n".encode())
            await writer.drain()
        elif command_list[0] == "put":
            await put(reader, writer, command_list[1])
        elif command_list[0] == "exit":
            writer.write("exit\n".encode())
            await writer.drain()
            break
    
asyncio.run(main())