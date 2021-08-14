from net import Listener, Addr
import socket

class TCPListener(Listener):
    def __init__(self, addr, sock):
        super().__init__(addr, sock)

def listen():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    addr = socket.getaddrinfo('localhost', '5055', socket.AF_INET)[-1][-1]
    return TCPListener(Addr(addr), sock)
