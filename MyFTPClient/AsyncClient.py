import asyncio
import os
from tqdm import tqdm

async def get(reader, writer, filename):
    if not filename:
        print("[-] Please specify a file.")
        return
    writer.write(f"get {filename}\n".encode("utf-8"))
    await writer.drain() 

    file_size = int((await reader.readline()).decode().strip())
    if file_size == 0:
        print(f"[-]{filename} not found")
        return

    progress = tqdm(total=file_size, unit="B", unit_scale=True, desc=filename)
    with open(filename, "wb") as f:
        while file_size > 0:
            buffer = await reader.read(min(1024, file_size))
            f.write(buffer)
            file_size -= len(buffer)
            progress.update(len(buffer))

    progress.close()
    print(f"[+] {filename} downloaded successfully")

async def put(reader, writer, filename):
    if not os.path.isfile(filename):
        print(f"[-]{filename} not found")
        return

    file_size = os.path.getsize(filename)
    writer.write(f"put {filename} {file_size}\n".encode())
    await writer.drain()

    progress = tqdm(total=file_size, unit="B", unit_scale=True, desc=filename)
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(1024)
            if not chunk:
                break
            writer.write(chunk)
            await writer.drain()
            progress.update(len(chunk))

    print(f"[+] {filename} uploaded successfully")

async def main():
    print('[+] This FTP Client is running...')
    while True:
        try:
            server_ip = input("[+] Server IP: ")
            server_port = int(input("[+] Server Port: "))
            reader, writer = await asyncio.open_connection(server_ip, server_port)
            print(f"[+] Connected to {server_ip}:{server_port}")
            print(f"[+] Client running on {reader._transport.get_extra_info('sockname')}")
            break
        except Exception as e:
            print(f"[-] Failed to establish connection: {str(e)}")
            continue

    while True:
        command = input("FTP> ")
        command_list = command.split(" ")
        if command_list[0] == "get":
            try: 
                await get(reader, writer, command_list[1])
            except IndexError:
                print("[-] Please specify a file.")
        elif command_list[0] == "ls":
            writer.write("ls\n".encode())
            await writer.drain()
            while True:
                message = await reader.readline()
                if message.decode().strip() == "END_OF_LS":
                    break
                print("   | " + message.decode().strip())
        elif command_list[0] == "cd":
            if not command_list[1]:
                print("[-] Please specify a directory.")
                continue
            try:
                writer.write(f"cd {command_list[1]}\n".encode())
            except IndexError:
                print("[-] Please specify a directory.")
            message = await reader.readline()
            print(message.decode().strip())
            await writer.drain()
        elif command_list[0] == "put":
            try:
                await put(reader, writer, command_list[1])
            except IndexError:
                print("[-] Please specify a file.")
        elif command_list[0] == "exit":
            writer.write("exit\n".encode())
            await writer.drain()
            break
    
asyncio.run(main())