import socket
import fcntl
import struct
import platform
import subprocess

def get_ip_address(interface_name='eth0'):
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

# 使用示例
en0_ip = get_ip_address('en0')

print(f"en0 IP Address: {en0_ip}")
