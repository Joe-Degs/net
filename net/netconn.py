from typing import Union, Optional
from enum import Enum
import socket, io, sys

class _SocketWriter(io.BufferedIOBase):
    """A writtable and readable BufferedIOBase implementation for a socket.

    copied from https://github.com/python/cpython/blob/302df02789d041a09760f86295ea6b4dcd81aa1d/Lib/socketserver.py#L814
    """
    def __init__(self, sock):
        self.__sock = sock

    def writable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def read(self) -> bytes:
        # read from the socket until eof then return read bytes.
        # if an error occurs while reading throw it.
        chunks = []
        while True:
            buf = self.__sock.recv(2048)
            chunks.append(buf)
            if not buf:
                break
        return b''.join(chunks)

    def write(self, buf) -> int:
        # write the buf of bytes to the underlying socket connection.
        self.__sock.sendall(buf)
        with memoryview(buf) as view:
            return view.nbytes

RECV_MAX = 0xffff

class ConnType(Enum):
    """ConnType represents the type of socket connection to initiate

    Possible options are;
    LISTEN => to create listening sockets
    CONNECT => create sockets that are used connect to a remote endpoint
    REMOTE => a socket connection recieved from a listening socket.
    """
    LISTEN = 0b01
    REMOTE = 0b10
    CONNECT = 0b11

class Addr:
    """Addr is a generic wrapper around socket addresses

    socket addresses are gotten either from socket.getaddrinfo,
    returned from recvfrom functions or user entered.
    specific address types are derived from this class and the str
    function implemented to suit the conventional string representation
    of that address type.

    Attributes
    ----------
    addrinfo: object
        a socket address
    """
    def __init__(self, addrinfo):
        """
        Parameters
        -----------
        addrinfo: object
            The addrinfo socket address that is returned by socket.getaddrinfo
            or is returned as a socket address from any socket connection.

        network: str, optional
            The network that the addrinfo represents. could be "tcp", "udp"
            or any other network. It also represents the type of socket
            connection Addr is associated with.
        """
        self.addrinfo = addrinfo

    def __str__(self) -> str:
        # return a string representation of addrinfo. The representation
        # is different for different socket connection types so
        # the individual addr classes should implement their own.
        return repr(self.addrinfo)

    def __repr__(self) -> str:
        return self.__str__()

class Conn:
    """Conn is a generic wrapper around socket objects.

    Conn is implements a generic wrapper around socket connections.
    It is implemented to look exactly like the way the net.Conn type
    in golang is. But i'm not sure it works the same way. it obviously
    does not work the same way.

    Socket read, write methods read from the file object returned from the
    makefile method on sockets. This may not work every specific use case so
    the socket object can be accessed and the send and recv used to achieve
    every specific use case.

    The Conn objects present a more beginner friendly interface
    to dealing with sockets. That been, said after a fair amount of use
    beginners should try and play with the real socket api's provided by their
    os to really understand how this things work.
    """
    def __init__(self, sock, laddr=None):
        if sock:
            assert isinstance(sock, socket.socket), 'socket not a socket object'

        if laddr:
            assert isinstance(laddr, Addr), 'address not an Addr object'

        self.sock = sock
        # make the socket non blocking so it doesnt block the thread
        # self.sock.setblocking(False)

        # local and remote address of the socket connection.
        self.laddr = laddr
        self.raddr = None
        
        # create a buffered read, the socket object for buffered
        # io support.
        self.__conn = io.BufferedRWPair(self.sock.makefile('rb'),
                self.sock.makefile('wb'))

    def write(self, buf: bytes) -> int:
        # write bytes to the underlying socket connection
        return self.__conn.write(buf)

    def read(self, n: int = 0) -> bytes:
        # read data from the underlying socket connection.
        if n:
            while True:
                buf = []
                b = self.sock.recv(n)
                buf.append(b'')
                if len(b) < n:
                    return b''.join(buf)
        else:
            return self.__conn.read()

    def file(self) -> Union[_SocketWriter, io.BufferedRWPair]:
        # file returns the file object that conn is wrapped in.
        return self.__conn

    def connect(self, addr):
        # connects underlying socket to addr.
        # addr is an instance of Addr or an instance of its subclass
        assert isinstance(addr, Addr), 'addr not instance of Addr'
        self.sock.connect(addr.addrinfo)

    def bind(self, addr, reuse=True):
        # bind binds socket to addr. And it reuse is set to true
        # it sets socket option for address reuse.
        if reuse:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        assert isinstance(addr, Addr), 'bind to a non Addr object'
        self.sock.bind(addr.addrinfo)

    def setblocking(self, flag: bool) -> None:
        # set whether socket should block or not.
        self.sock.setblocking(flag)

    def settimeout(self, timeout: float) -> None:
        # set a timeout value for socket.
        self.sock.settimeout(timeout)

    def close_read(self):
        self.sock.shutdown(socket.SHUT_RD)

    def close_write(self):
        self.sock.shutdown(socket.SHUT_WR)

    def shutdown(self) -> None:
        # shutdown the socket connection(read, write or both) and close
        # all open file descriptors.
        # options === (SHUT_RD = 0, SHUT_WR = 1, SHUT_RDWR = 3)
        self.sock.shutdown(socket.SHUT_RDWR)
    
    def close(self) -> None:
        # close all open file descriptors. both socket and io stream.
        self.sock.close()
        self.__conn.close()

class Listener:
    """Listener in experimental phase.
    work getting started on the generic wrapper around stream oriented
    listening protocols.

    this is been done because i do not want the listening sockets inheriting
    methods from the normal Conn objects.

    the golang net interface has the following methods that i'll implement
    first on the socket. accept, close, addr.

    testing all my new ideas out here to see how they work for now. I have the 
    casting interface and almost done with the Listener thing. save for testing
    it with real socket connections and things.

    i am also things
    """
    def __init__(self, addr, sock, conn_type = ConnType.REMOTE):
        if sock:
            assert isinstance(sock, socket.socket), 'sock not a socket object'
        if addr:
            assert isinstance(addr, Addr), 'addr is not an Addr object'
        self.sock = sock
        self.laddr = addr
        # bind to address and set socket options.
        # consider redoing this socket options into something
        # like how AddrConfig is.
        if conn_type == ConnType.LISTEN:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(self.laddr.addrinfo)
            self.sock.listen(socket.SOMAXCONN)

    def accept(self) -> Conn:
        """accept waits for and returns the next connection to the listener"""
        sock, addrinfo = self.sock.accept()
        return Conn(sock, Addr(addrinfo))

    def addr(self) -> Addr:
        """addr returns the listeners address"""
        if self.laddr:
            return self.laddr
        self.laddr = Addr(self.sock.getsockname())
        return self.laddr

    def from_listener(self, listen_type):
        """cast generic listener to a specific listener
        """
        assert issubclass(listen_type, Listener), \
                'listener type not subclass of Listener'
        return listen_type(self.laddr, self.sock)
        
    def close(self):
        self.sock.close()
