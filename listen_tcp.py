import sys
from net import address as addr
from net import conn

def handle_conn(c: conn.TCPConn):
    print(f'recieved connection from {c.remote_addr()}')
    b = c.read(1024)
    print('in listens handle conn after reading')
    c.write(b)
    print(f'read and wrote msg: {b.decode("utf8")} of len {len(b)} bytes to client connection')
    c.close()

"""
yeah guesss what! keyboard interrupts on the sockets do not work.
its only on windows as usual, this people are crazy, nobody wants
to be thinking about special ways of handling keyboard interrupts
this should be a straightforward thing on every platform.
"""

def use_listen_tcp(address, network):
    laddr = addr.resolve_tcp_addr(address, network)
    lstn = conn.listen_tcp(laddr, network)
    # lstn.settimeout(20.0)
    print(f'listening and serving tcp on {lstn.local_addr()}')
    while True:
        tcp_conn = lstn.accept()
        handle_conn(tcp_conn)

def main():
    args = sys.argv[1:]
    if len(args) != 2:
        print('you a valid address and network for this to work', args)
        exit(1)

    use_listen_tcp(args[0], args[1])

if __name__ == '__main__':
    main()
