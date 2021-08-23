from .netconn import *
from .netaddr import *

class TCPConn(Conn):
    """TCPConn is tcp socket wrapper.

    it provides a friendly way to interract with tcp sockets.

    Parameters
    ----------
    laddr: TCPAddr, optional
        the local address of the socket been created.

    raddr: TCPAddr, optional
        the remote address of the tcp socket.

    conn_type: ConnType
        specify the type of socket connection to open

    sock: socket.socket, optional
        the socket object to open for network communication. if none is supplied,
        One can be created based on the address parameters.
    """
    def __init__(self, laddr: Optional[TCPAddr], raddr: Optional[TCPAddr],
        conn_type: ConnType = ConnType.REMOTE, sock: Optional[socket.socket]=None):
        if sock == None:
            # TODO(Joe):
            # the socket is not factoring in the type of address being passed
            # during creation. if the addresses are ipv6, create an ipv6 socket.
            # else ipv4 socket.
            super().__init__(socket.socket(socket.AF_INET, socket.SOCK_STREAM,
                    socket.IPPROTO_TCP))
        else:
            super().__init__(sock)

        if conn_type == ConnType.LISTEN:
            # a socket opened for listening, bind socket to addr provided
            if laddr:
                self.bind(laddr)
        elif conn_type == ConnType.CONNECT:
            # socket opened to connect to a remote host, connect to addr provided and change addr
            # to the arbitrary host:port from the kernel
            if laddr:
                self.bind(laddr)
            if raddr:
                self.connect(raddr)
            else:
                self.sock.close()
                raise SocketError('connecting tcp socket with an empty remote address')
        elif conn_type == ConnType.REMOTE:
            # remote socket from a listening socket.
            return
        else:
            # we recieved a conn_type thats not any of the
            # of the 3 above so we throw an exception.
            # we don't know what it is.
            self.sock.close()
            raise SocketError(f'trying to perform an unsurported socket action - {conn_type}')
    
    def local_addr(self):
        # return the local addr associated with socket.
        if self.laddr:
            return self.laddr
        self.laddr = TCPAddr(self.sock.getsockname())
        return self.laddr

    def remote_addr(self):
        # return remote address associated with socket.
        if self.raddr:
            return  self.raddr
        self.raddr = TCPAddr(self.sock.getpeername())
        return self.raddr

class TCPListener(TCPConn):
    """ 
    TCPListener is a wrapper around TCPConn that provides capabilities
    to listen for connections.
    """
    def __init__(self, laddr: TCPAddr, sock: Optional[socket.socket] = None):
        # create a tcp socket ready to listen on addr.
        super().__init__(laddr, None, ConnType.LISTEN, sock)
        self.sock.listen(socket.SOMAXCONN)

    def accept(self) -> TCPConn:
        # return a TCPConn from the underlying listening socket.
        sock, addrinfo = self.sock.accept()
        return TCPConn(TCPAddr(addrinfo), None, sock=sock)
