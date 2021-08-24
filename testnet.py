import getopt, sys, net

def usage():
    print('Usage: testnet.py <options>')
    print('  Use the net module to open socket servers or clients')
    print('')
    print('  Atleast one of the following should be specified:')
    print('    -d    Dial, connect to a client')
    print('    -l    Listen, open a server to listen for connections')
    print('')
    print('  The following are not optional:')
    print('    -n    Specify the network type to connect to')
    print('    -a    Specify address to bind connection to')

eol = b'\x05'

def stream_listener(conn):
    try:
        while True:
            nc = conn.accept()
            b = nc.read()
            print(len(b), b)
            nc.write(b + eol)
            nc.close()
    except Exception as e:
        conn.close()
        raise e

    def datagram_listener(conn):
        try:
            while True:
                b, raddr = conn.read_from()
                print(len(b), b)
                conn.write_to(b, raddr)
        except Exception as e:
            conn.close()
            raise e

def test_listen(address, network):
    conn = net.listen(address, network)
    print(f'{network} listener on {conn.local_addr()}')
    if 'nix' in network:
        conn.set_unlink_on_close(True)

    if 'nix' in network or 'tcp' in network:
        # stream listener
        stream_listener(conn)
    else:
        # datagram listener
        datagram_listener(conn)

# reads are still blocking for socket clients opened with this
# package and i cannot seem to find the reason it is doing that.
def test_dial(address, network, data=b'random data\n'):
    conn = net.dial(address, network) # connect to remote address
    print(f'{network} client on {conn.local_addr()}')
    n = conn.write(data)
    print(n)
    b = conn.read()
    print(len(b))
    return

def main():
    argv = sys.argv[1:]
    opts, _ = getopt.getopt(argv, 'dln:a:t:')
    dial = False
    listen = False
    network = ''
    address = ''
    data = b''

    for opt, arg in opts:
        if '-d' == opt:
            # specify a dialing socket
            if listen:
                usage()
                exit(2)
            dial = True
        elif '-l' == opt:
            # specify listening socket
            if dial:
                usage()
                exit(2)
            listen = True
        elif '-n' == opt:
            # parse network type to open connection to.
            network = arg
        elif '-a' == opt:
            # parse the address to connect to
            address = arg
        elif '-t' == opt:
            # parse text to send into connection
            data = b''.join(arg)
        else:
            print('Invalid argument: ', opt)
            usage()
            exit(2)

    # opening client sockets.
    if dial and data:
        test_dial(address, network, data)
    elif dial:
        test_dial(address, network)
    elif listen:
        # opening listening sockets.
        test_listen(address, network)
    else:
        usage()
        exit(2)

if __name__ == '__main__':
    main()
