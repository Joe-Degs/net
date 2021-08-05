from typing import Union, Optional
from enum import Enum
import socket
import io
import os

from .address import *

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

class Conn:
    """Conn is a generic wrapper around socket objects.

    Conn is implements a generic wrapper around socket connections.
    It is implemented to look exactly like the way the net.Conn type
    in golang is. But i'm not sure it works the same way. it obviously
    does not work the same way.
    """
    def __init__(self, sock: socket.socket):
        self.sock = sock
        # make the socket non blocking so it doesnt block the thread
        # self.sock.setblocking(False)

        # local and remote address of the socket connection.
        self.laddr: Optional[Union[Addr, UDPAddr, TCPAddr]] = None
        self.raddr: Optional[Union[Addr, UDPAddr, TCPAddr]] = None

        self.__conn = io.BufferedRWPair(self.sock.makefile('rb'),
                self.sock.makefile('wb'))
    
    def write(self, buf: bytes) -> int:
        # write bytes to the underlying socket connection
        return self.__conn.write(buf)

    def read(self, n: int = 0) -> bytes:
        # read data from the underlying socket connection.
        buf = []
        b = b''
        while True:
            self.settimeout(0.2)
            try:
                if n:
                    b = self.sock.recv(n)
                    buf.append(b)
                else:
                    b = self.__conn.read()
                    buf.append(b)
                if len(b) < n:
                    return b''.join(buf)
            except Exception:
                pass

    def file(self) -> Union[_SocketWriter, io.BufferedRWPair]:
        # file returns the file object that conn is wrapped in.
        return self.__conn

    def connect(self, addr: Union[Addr, TCPAddr, UDPAddr]):
        # connects underlying socket to addr.
        self.sock.connect(addr.addrinfo)

    def bind(self, addr: Union[Addr, TCPAddr, UDPAddr], reuse=True):
        # bind binds socket to addr. And it reuse is set to true
        # it sets socket option for address reuse.
        if reuse:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(addr.addrinfo)
    
    def setblocking(self, flag: bool) -> None:
        # set whether socket should block or not.
        self.sock.setblocking(flag)

    def settimeout(self, timeout: float) -> None:
        # set a timeout value for socket.
        self.sock.settimeout(timeout)

    def close(self) -> None:
        # close all open file descriptors. both socket and io stream.
        self.sock.close()
        self.__conn.close()

    def shutdown(self, flag: int) -> None:
        # shutdown the socket connection(read, write or both) and close
        # all open file descriptors.
        # options === (SHUT_RD = 0, SHUT_WR = 1, SHUT_RDWR = 3)
        if flag >= socket.SHUT_RD and flag <= socket.SHUT_RDWR:
            self.sock.shutdown(flag)
        else:
            raise SocketError(f'invalid flag constant used on shutdown {flag}')

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
        conn_type: ConnType = ConnType.REMOTE, sock: Optional[socket.socket]=None
    ):
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

class UDPConn(Conn):
    """UDPConn is a wrapper around udp sockets

    it provides a friendly way to interract with udp sockets.

    Parameters
    ----------
    laddr: UDPAddr, optional
        the local address of the socket been created.

    raddr: UDPAddr, optional
        the remote address of the udp socket.

    conn_type: ConnType
        specify the type of socket connection to open

    sock: socket.socket, optional
        the socket object to open for network communication. if none is supplied,
        One can be created based on the address parameters.
    """
    def __init__(self, laddr: Optional[UDPAddr], raddr: Optional[UDPAddr],
        conn_type: ConnType = ConnType.REMOTE, sock: Optional[socket.socket] = None
    ):

        # TODO(Joe):
        # the socket is not factoring in the type of address being passed
        # during creation. if the addresses are ipv6, create an ipv6 socket.
        # else ipv4 socket.
        if sock == None:
            super().__init__(socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                socket.IPPROTO_UDP))
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

    def read_from(self) -> tuple[bytes, UDPAddr]:
        # read_from reads from the socket connection and returns
        # the bytes read with the remote host address read from
        data, raddr = self.sock.recvfrom(self.max_packet_size)
        return data, UDPAddr(raddr)

    def write_to(self, buf: bytes, addr: UDPAddr) -> int:
        # write_to write buf[bytes] to the underlying socket connection.
        return self.sock.sendto(buf, addr.addrinfo)

    def local_addr(self):
        # return the local addr associated with socket.
        if self.laddr:
            return self.laddr
        self.laddr = UDPAddr(self.sock.getsockname())
        return self.laddr

    def remote_addr(self):
        # return remote address associated with socket.
        if self.raddr:
            return  self.raddr
        self.raddr = UDPAddr(self.sock.getpeername())
        return self.raddr

class TCPListener(TCPConn):
    """ 
    TCPListener is a wrapper around TCPConn that provides capabilities
    to listen for connections.
    """
    queue_size = 10

    def __init__(self, laddr: TCPAddr, sock: Optional[socket.socket] = None,
            queue_size: int=queue_size):
        # create a tcp socket ready to listen on addr.
        super().__init__(laddr, None, ConnType.LISTEN, sock)
        self.sock.listen(queue_size)

    def accept(self) -> TCPConn:
        # return a TCPConn from the underlying listening socket.
        sock, addrinfo = self.sock.accept()
        return TCPConn(TCPAddr(addrinfo), None, sock=sock)

def _config_from_net(addr, net):
    # return the config from an already resolve address.
    if addr:
        return config_inetaddr(addr.addrinfo[0], addr.addrinfo[1], net)
    return config_inetaddr('', '', net)

def dial_udp(laddr: Optional[UDPAddr], raddr: UDPAddr, network = 'tcp'):
    """dial_udp acts like a dial for tcp networks.

    see dial and resolve_addr for more info on address formats and network.

    Parameters
    ----------
    laddr: UDPAdr, optional
        the local address of the socket connection.

    raddr: UDPAddr
        the remote address of the connection

    network: str
        tcp network type of the socket. it must be a tcp network name.
    """
    if net_is_valid('udp', network):
        config = _config_from_net(laddr, network)
        return UDPConn(laddr, raddr, ConnType.CONNECT, config.get_socket())
    else:
        raise UnknownNetworkError(network)

def dial_tcp(laddr: Optional[TCPAddr], raddr: TCPAddr, network = 'tcp'):
    """dial_tcp acts like a dial for tcp networks.
    
    see dial and resolve_addr for more info on address formats and network.

    Parameters
    ----------
    laddr: TCPAdr, optional
        the local address of the socket connection.

    raddr: TCPAddr
        the remote address of the connection

    network: str
        tcp network type of the socket. it must be a tcp network name.
    """
    if net_is_valid('tcp', network):
        config = _config_from_net(laddr, network)
        return TCPConn(laddr, raddr, ConnType.CONNECT, config.get_socket())
    else:
        raise UnknownNetworkError(network)

def dial(address: str, network: str):
    """dial connects to network the address endpoint

    see resolve_addr function for more on structure of arguments.

    Parameter
    ---------
    address: str
        the network name you are dialing.

    network: str
        type of network to connect to.
        see resolve_addr for types of network supported.
    """
    host, port = split_host_port(address)
    if net_is_valid('tcp', network) or net_is_valid('udp', network):
        addr_list, config = resolver(host, port, network)
        conn_obj = None
        if net_is_valid('tcp', network):
            conn_obj = TCPConn
        elif net_is_valid('udp', network):
            conn_obj = UDPConn
        else:
            raise UnknownNetworkError(network)
        # TODO(Joe):
        # this loop will terminate on first try if the connection raises an
        # exception. This is unacceptable and must be handled. Do so soon!
        for raddr in addr_list:
            conn = conn_obj(None, raddr, ConnType.CONNECT, config.get_socket())
            return conn
    else:
        raise UnknownNetworkError(network)

def listen_udp(laddr: UDPAddr, network = 'udp'):
    """listen_udp returns a udp socket that's ready to listen for connections
    on the specified local address.

    we all know udp is special, so it does not have a listener function
    because technically every udp socket is a listener and a sender at the
    time.

    Parameters
    ----------
    laddr: UDPAddr
        the local address to initialize the socket to listen on.

    network: str
        the tcp network socket type to listen on.
    """
    if net_is_valid('udp', network):
        config = _config_from_net(laddr, network)
        return UDPConn(laddr, None, ConnType.LISTEN, config.get_socket())
    else:
        raise UnknownNetworkError(network)

def listen_tcp(laddr: TCPAddr, network = 'tcp'):
    """listen_tcp returns a tcp listener that is ready to listen on
    the local addr specified.

    Parameters
    ----------
    laddr: TCPAddr
        the local address to initialize the socket to listen on.

    network:
        the tcp network socket type to listen on.
    """
    if net_is_valid('tcp', network):
        config = _config_from_net(laddr, network)
        return TCPListener(laddr, config.get_socket())
    else:
        raise UnknownNetworkError(network)

def listen(address: str, network: str) -> Optional[Union[TCPListener, UDPConn]]:
    """ listen announces and waits for connections on a local network address.

    the network must be a "tcp", "tcp4", "tcp6", "udp", "udp4" or "udp6"
    """
    host, port = split_host_port(address)
    if net_is_valid('tcp', network) or net_is_valid('udp', network):
        addr_list, config = resolver(host, port, network)
        # TODO(Joe):
        # do not fail until you've tried to connect to all the adresses
        # resolved. the way this is implemented right now, if the first
        # attempt throws an error the whole thing halts. So fix it!
        for addr in addr_list:
            if net_is_valid('tcp', network):
                return TCPListener(addr, config.get_socket())
            elif net_is_valid('udp', network):
                return UDPConn(addr, None, ConnType.LISTEN, config.get_socket())
            else:
                raise UnknownNetworkError(network)
    else:
        raise UnknownNetworkError(network)
