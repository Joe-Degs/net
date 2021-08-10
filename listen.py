import sys
import net

def printlen(b):
    print(f'------ read {len(b)} from the connections ------')

def handle_grams(c):
    b, naddr = c.read_from()
    printlen(b)
    print(f'recieved connection from {c.local_addr()}')
    c.write_to(b, naddr)

def handle_streams(c):
    print('recieved connection from c.remote_addr()')
    b = c.read()
    printlen(b)
    c.write(b)
    c.close()



def use_listen(address, network):
    try:
        lstn = net.listen(address, network)
        # lstn.settimeout(20.0)
        print(f'listening and serving {network} on {lstn.local_addr()}')
        while True:
            if network == 'unix':
                lstn.unlink_on_close(True)
            if net.net_is_valid('tcp', network) or network == 'unix':
                nc = lstn.accept()
                handle_streams(nc)
            elif net.net_is_valid('udp', network) or network == 'unixgram':
                handle_grams(lstn)
            else:
                print('Invalid network i guess')
                lstn.close()
                sys.exit(1)
    except Exception as e:
        lstn.close()
        raise e

def main():
    args = sys.argv[1:]
    if len(args) != 2:
        print('you a valid address and network for this to work', args)
        exit(1)
    use_listen(*args)

if __name__ == '__main__':
    main()
