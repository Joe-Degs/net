import sys
import net

def handle_conn(c):
    print(f'local_addr: {c.local_addr()} | remote_addr: {c.remote_addr()}')
    data = b"random test data"
    n = c.write(data)
    c.write(b'') # eof
    # c.close()
    # sys.exit(0)
    b = c.read(n)
    if data == b:
        print('===> read write into socket successful')
        print(f'sent and recieved => {b.decode("utf8")} of len {len(b)}')
    else:
        print('<=== reading and writing sockets not working as expected')
        print(f'recieved => {b.deccode("utf8")} of len {len(b)}')
    c.close()

def use_dial(address, network):
    tcp_client = net.dial(address, network)
    # tcp_client.settimeout(20)
    handle_conn(tcp_client)

def use_dial_tcp(addr, addr2, network):
    laddr = None
    if addr:
        laddr = net.resolve_tcp_addr(addr, network)
    raddr = net.resolve_tcp_addr(addr2, network)
    tcp_client = net.dial_tcp(laddr, raddr, network)
    handle_conn(tcp_client)


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
