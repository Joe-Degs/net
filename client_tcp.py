import sys
from net import address as addr
from net import conn

def handle_conn(c: conn.TCPConn):
    data = b"random test data"
    c.write(data)
    b = c.read()
    if data == b:
        print('======> read write into socket successful')
        print(f'sent and recieved => {b.encode("utf8")}')
    else:
        print('<=== reading and writing sockets not working as expected')
        print(f'recieved => {b.encode("utf8")}')

def use_dial(address, network):
    tcp_client = dial(address, network)
    handle_conn(tcp_client)

def use_dial_tcp(addr, addr2, network):
    laddr = None
    if addr:
        laddr = addr.resolve_tcp_addr(addr, network)
    raddr = addr.resolve_tcp_addr(addr2, network)
    tcp_client = (laddr, raddr, network)


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print('<=== expected address "host:port" and network "network" but got', *args)
        exit(1)
    
    if len(args) == 3:
        use_dial_tcp(args[0], args[1],  args[2])
    else:
        use_dial(args[0], args[1])


if __name__ == '__main__':
    main()