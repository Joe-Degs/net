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

def stream_listener(conn):
    try:
        while True:
            nc = conn.accept()
            b = nc.read()
            print(len(b))
            nc.write(b)
            nc.shutdown()
    except Exception as e:
        conn.close()
        raise e

def datagram_listener(conn):
    try:
        while True:
            b, raddr = conn.read_from()
            print(len(b))
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

def test_dial(address, network):
    conn = net.dial(address, network)
    print(f'{network} client on {conn.local_addr()}')
    conn.close()
    return

def main():
    argv = sys.argv[1:]
    opts, _ = getopt.getopt(argv, 'dln:a:')
    dial = False
    listen = False
    network = ''
    address = ''

    for opt, arg in opts:
        if '-d' == opt:
            if listen:
                usage()
                exit(2)
            dial = True
        elif '-l' == opt:
            if dial:
                usage()
                exit(2)
            listen = True
        elif '-n' == opt:
            network = arg
        elif '-a' == opt:
            address = arg
        else:
            print('Invalid argument: ', opt)
            usage()
            exit(2)

    if dial:
        test_dial(address, network)
    elif listen:
        test_listen(address, network)
    else:
        usage()
        exit(2)

if __name__ == '__main__':
    main()
