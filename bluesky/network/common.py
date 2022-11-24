import socket

def get_ownip():
    local_addrs = socket.gethostbyname_ex(socket.gethostname())[-1]
    # print(local_addrs)
    for addr in local_addrs:
        print('Current IP ', addr)
        if not addr.startswith('172'):
            #print(addr)
            return addr
    return '127.0.0.1'
