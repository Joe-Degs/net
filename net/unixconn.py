from .netconn import *
from .netaddr import *

import os

class UnixConn(Conn):
    """UnixConn is a wrapper around unix domain sockets.
    It wraps around socket connections to unix domain sockets.

    The defualt socket object returned is a stream connection,
    for connections to datagram unix sockets you need to provide the 
    socket object yourself or use the dial or dial_unix functions.

    Parameters
    ----------
    laddr: UnixAddr, optional
        the local address of the socket been created.

    raddr: UnixAddr, optional
        the remote address of the Unix socket.

    conn_type: ConnType
        specify the type of socket connection to open

    sock: socket.socket, optional
        the socket object to open for network communication. if none is supplied,
        One can be created based on the address parameters.
    """
    def __init__(self, laddr: Optional[UnixAddr], raddr: Optional[UnixAddr],
            conn_type: ConnType = ConnType.REMOTE, sock: Optional[socket.socket]=None):
        if not sock:
            super().__init__(socket.socket(socket.AF_UNIX, socket.SOCK_STREAM))
        else:
            super().__init__(sock)

        self.max_packet_size = 8192

        if conn_type == ConnType.LISTEN:
            if laddr:
                self.bind(laddr, reuse=False)
        elif conn_type == ConnType.CONNECT:
            # if we have a local address, we bind to it
            # if we have a remote addr we connect to it.
            # else we throw an error.
            if laddr:
                self.bind(laddr)
            if raddr:
                self.connect(raddr)
            else:
                self.sock.close()
                raise SocketError('connecting udp socket with an empty remote address')
        elif conn_type == ConnType.REMOTE:
            # remote socket conn, do not bind, do not connect
            return
        else:
            self.sock.close()
            raise SocketError(f'trying to perform an unsurported socket action - {conn_type}')

    def read_from(self) -> tuple[bytes, UnixAddr]:
        # read_from reads from the socket connection and returns
        # the bytes read with the remote host address read from
        data, raddr = self.sock.recvfrom(RECV_MAX)
        return data, UnixAddr(raddr)

    def write_to(self, buf: bytes, addr: UnixAddr) -> int:
        # write_to write buf[bytes] to the underlying socket connection.
        return self.sock.sendto(buf, addr.addrinfo)

    def local_addr(self):
        # return the local addr associated with socket.
        if self.laddr:
            return self.laddr
        self.laddr = UnixAddr(self.sock.getsockname())
        return self.laddr

    def remote_addr(self):
        # return remote address associated with socket.
        if self.raddr:
            return  self.raddr
        self.raddr = UnixAddr(self.sock.getpeername())
        return self.raddr

class UnixListener(Conn):
    """UnixListener is a unix domain socket listener.

    Parameters
    ----------
    laddr: UnixAddr, optional
        the local address to bind to.

    conn_type: ConnType
        specify the type of socket connection to open

    sock: socket.socket, optional
        the socket object to open for network communication. if none is supplied,
        One can be created based on the address parameters.
    """
    def __init__(self, laddr: UnixAddr, sock: Optional[socket.socket] = None):
        self.__path = laddr.addrinfo
        self.__unlink = False
        if not sock:
            sock = socket.socket(AF_UNIX, socket.SOCK_STREAM)
        super().__init__(sock)
        self.bind(laddr, reuse=False)
        self.sock.listen(socket.SOMAXCONN)

    def accept(self) -> UnixConn:
        sock, addrinfo = self.sock.accept()
        return UnixConn(UnixAddr(addrinfo), None, sock=sock)

    def local_addr(self):
        if self.laddr:
            return self.laddr
        self.laddr = UnixAddr(self.sock.getsockname())
        return self.laddr

    def set_unlink_on_close(self, unlink: bool):
        self.__unlink = unlink

    def close(self):
        self.sock.close()
        if self.__unlink:
            try:
                os.unlink(self.__path)
                print('file unlinked')
            except OSError as e:
                raise SocketError(e.strerror)
