import hashlib
import re
import urllib
import time
import socket

def compute_md5(file_name):
    hash_md5 = hashlib.md5()
    with open(file_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def ip_address_is_valid(ip_address):
    ip_v4_seg  = r'(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])'
    ip_v4_addr = r'(?:(?:' + ip_v4_seg + r'\.){3,3}' + ip_v4_seg + r')'

    ip_v6_seg  = r'(?:(?:[0-9a-fA-F]){1,4})'
    ip_v6_groups = (
        r'(?:' + ip_v6_seg + r':){7,7}' + ip_v6_seg,                  # 1:2:3:4:5:6:7:8
        r'(?:' + ip_v6_seg + r':){1,7}:',                           # 1::                                 1:2:3:4:5:6:7::
        r'(?:' + ip_v6_seg + r':){1,6}:' + ip_v6_seg,                 # 1::8               1:2:3:4:5:6::8   1:2:3:4:5:6::8
        r'(?:' + ip_v6_seg + r':){1,5}(?::' + ip_v6_seg + r'){1,2}',  # 1::7:8             1:2:3:4:5::7:8   1:2:3:4:5::8
        r'(?:' + ip_v6_seg + r':){1,4}(?::' + ip_v6_seg + r'){1,3}',  # 1::6:7:8           1:2:3:4::6:7:8   1:2:3:4::8
        r'(?:' + ip_v6_seg + r':){1,3}(?::' + ip_v6_seg + r'){1,4}',  # 1::5:6:7:8         1:2:3::5:6:7:8   1:2:3::8
        r'(?:' + ip_v6_seg + r':){1,2}(?::' + ip_v6_seg + r'){1,5}',  # 1::4:5:6:7:8       1:2::4:5:6:7:8   1:2::8
        ip_v6_seg + r':(?:(?::' + ip_v6_seg + r'){1,6})',             # 1::3:4:5:6:7:8     1::3:4:5:6:7:8   1::8
        r':(?:(?::' + ip_v6_seg + r'){1,7}|:)',                     # ::2:3:4:5:6:7:8    ::2:3:4:5:6:7:8  ::8       ::
        r'fe80:(?::' + ip_v6_seg + r'){0,4}%[0-9a-zA-Z]{1,}',       # fe80::7:8%eth0     fe80::7:8%1  (link-local IPv6 addresses with zone index)
        r'::(?:ffff(?::0{1,4}){0,1}:){0,1}[^\s:]' + ip_v4_addr,     # ::255.255.255.255  ::ffff:255.255.255.255  ::ffff:0:255.255.255.255 (IPv4-mapped IPv6 addresses and IPv4-translated addresses)
        r'(?:' + ip_v6_seg + r':){1,4}:[^\s:]' + ip_v4_addr,          # 2001:db8:3:4::192.0.2.33  64:ff9b::192.0.2.33 (IPv4-Embedded IPv6 Address)
    )
    ip_v6_addr = '|'.join(['(?:{})'.format(g) for g in ip_v6_groups[::-1]])  # Reverse rows for greedy match

    ip_v4 = None
    ip_v6 = None
    try:
        ip_v4 = re.search(ip_v4_addr, ip_address).group()
    except:
        pass
    try:
        ip_v6 = re.search(ip_v6_addr, ip_address).group()
    except:
        pass
    return bool(ip_v4 or ip_v6)

def get_public_ip():
    public_ip_service_url = "https://ipinfo.io/ip"
    result = None
    for i in range(3):
        try:
            response = urllib.request.urlopen(public_ip_service_url)
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            time.sleep(2)
            continue
        except socket.timeout as e:
            time.sleep(2)
            continue
        else:
            with response as f:
                public_ip = f.read().decode('utf-8')
                if ip_address_is_valid(public_ip):
                    result = public_ip
            break
    return result
