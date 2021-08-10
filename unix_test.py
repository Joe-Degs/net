import socket
import os
import sys

def bind(sock):
    addr = './test.sock'
    try:
        os.unlink(addr)
    except OSError:
        if os.path.exists(addr):
            raise
    sock.bind(addr)

def unix_socket():
    return socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

def unixgram_socket():
    return socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

def printlen(b):
    print(f"recieved {b} bytes from connection")

def main():
    args = sys.argv[1:]

    if not len(args):
        print('what type of unix domain socket do you want.')

    if args[0] == 'unix':
        sock = unix_socket()
        bind(sock)
        sock.listen()
        print(f"socket listening on {sock.getsockname()}")
        while True:
            conn, addr = sock.accept()
            buf = conn.recv(1024)
            printlen(len(buf))
            conn.send(buf)
    elif args[0] == 'unixgram':
        # use unixgram
        sock = unixgram_socket()
        bind(sock)
        print(f"socket listening on {sock.getsockname()}")
        while True:
            buf, addr = sock.recvfrom(1024)
            printlen(len(buf))
            print(type(buf), type(addr))
            sock.sendto(buf)
    else:
        print('Fuck YOu!')

if __name__ == '__main__':
    main()
