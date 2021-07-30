from typing import Union, Optional
import socket
import io
import os

from .address import *

class _SocketWriter(io.BufferedIOBase):
    """
    A writtable and readable BufferedIOBase implementation for a socket. Most of it copied
    from https://github.com/python/cpython/blob/302df02789d041a09760f86295ea6b4dcd81aa1d/Lib/socketserver.py#L814
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
        self.__sock.sendall(buf)
        with memoryview(buf) as view:
            return view.nbytes

class Conn:
    """Conn is a generic wrapper around socket objects.

    Conn is implements a generic wrapper around socket connections.
    It is implemented to look exactly like the way the net.Conn type
    in golang is. But i'm not sure it works the same way.
    """
    def __init__(self, sock: socket.socket):
        self.sock = sock

        # local and remote address of the socket connection.
        self.laddr: Optional[Union[Addr, UDPAddr, TCPAddr]] = None
        self.raddr: Optional[Union[Addr, UDPAddr, TCPAddr]] = None

        # self.settimeout(2.0)
        if os.name == 'nt':
            # windows socket file descriptors are not treated as
            # normal file descriptors and so cannot be wrapped in
            # file object. So its wrapped in _SocketWriter insted.
            self.__conn = _SocketWriter(self.sock)
        elif os.name == 'posix':
            self.__conn = io.open(self.sock.fileno(), 'ab')
        else:
            NotImplementedError(os.name)
    
    def write(self, buf: bytes):
        # write bytes to the underlying socket connection
        return self.__conn.write(buf)

    def read(self) -> bytes:
        # read data from the underlying socket connection.
        return self.__conn.read()

    def file(self) -> Union[_SocketWriter, io.BufferedRandom]:
        # file returns the file object that conn is wrapped in.
        return self.__conn

    def connect(self, addr: Union[Addr, TCPAddr, UDPAddr]):
        # connects underlying socket to addr.
        self.sock.connect(addr.addrinfo)

    def srv_bind(self, addr: Union[Addr, TCPAddr, UDPAddr], reuse=True):
        # srv_bind binds socket to addr. And it reuse is set to true
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
        # options === (SHUT_RD, SHUT_WR, SHUT_RDWR)
        if flag >= socket.SHUT_RD and flag <= socket.SHUT_RDWR:
            self.sock.shutdown(flag)
        else:
            raise SocketError(f'invalid flag constant used on shutdown {flag}')

class TCPConn(Conn):
    """TCPConn is tcp socket wrapper.
    """
    def __init__(self, laddr: Optional[TCPAddr], raddr: Optional[TCPAddr], conn_type: Optional[str]=None,
            sock: Optional[socket.socket]=None) -> None:
        if sock == None:
            super().__init__(socket.socket(socket.AF_INET, socket.SOCK_STREAM,
                    socket.IPPROTO_TCP))
        else:
            super().__init__(sock)

        if conn_type == 'listen':
            # a socket opened for listening
            # bind socket to addr provided
            if laddr:
                self.srv_bind(laddr)
        elif conn_type == 'connect':
            # socket opened to connect to a remote host
            # connect to addr provided and change addr
            # to the arbitrary host:port from the kernel
            if laddr:
                self.srv_bind(laddr)
            if raddr:
                self.connect(raddr)
            else:
                self.sock.close()
                raise SocketError('connecting tcp socket with an empty remote address')
        elif not conn_type:
            # you listened and recieved a connection
            # you just assign it to self.sock and leave it
            # at that.
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
    """
    def __init__(self, laddr: Optional[UDPAddr], raddr: Optional[UDPAddr], conn_type: Optional[str]=None,
            sock: Optional[socket.socket]=None) -> None:
        if sock == None:
            super().__init__(socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                socket.IPPROTO_UDP))
        else:
            super().__init__(sock)

        self.max_packet_size = 8192

        if conn_type == 'listen':
            if laddr:
                self.srv_bind(laddr, reuse=False)
        elif conn_type == 'connect':
            # if we have a local address, we bind to it
            # if we have a remote addr we connect to it.
            # else we throw an error.
            if laddr:
                self.srv_bind(laddr)
            if raddr:
                self.connect(raddr)
            else:
                self.sock.close()
                raise SocketError('connecting udp socket with an empty remote address')
        elif not conn_type:
            # remote socket conn, do not bind, do not connect
            # don't do shit
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
        super().__init__(laddr, None, 'listen', sock)
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

def dial_udp(laddr: Optional[UDPAddr], raddr: UDPAddr, net = 'tcp'):
    if 'udp' in net:
        config = _config_from_net(laddr, net)
        return UDPConn(laddr, raddr, 'connect', config.get_socket())
    else:
        raise UnknownNetworkError(net)

def dial_tcp(laddr: Optional[TCPAddr], raddr: TCPAddr, net = 'tcp'):
    if 'tcp' in net:
        config = _config_from_net(laddr, net)
        return TCPConn(laddr, raddr, 'connect', config.get_socket())
    else:
        raise UnknownNetworkError(net)

def dial(address: str, network: str):
    """dial connects to network the address endpoint

    see resolve_addr function for more on structure of arguments.

    Parameter
    ---------
    address: str
        the network endpoint to connect to in "host:port" format.

    network: str
        type of network to connect to.
        see resolve_addr for types of network supported.
    """
    host, port = split_host_port(address)
    if 'tcp' in network or 'udp' in network:
        addr_list, config = resolver(host, port, network)
        conn_obj = None
        if 'tcp' in network:
            conn_obj = TCPConn
        else:
            conn_obj = UDPConn

        for addr in addr_list:
            try:
                conn = conn_obj(None, addr, 'connect', config.get_socket())
                return conn
            except:
                raise
    else:
        raise UnknownNetworkError(network)

def listen_udp(laddr: UDPAddr, network = 'udp'):
    if 'udp' in network:
        config = _config_from_net(laddr, network)
        return UDPConn(laddr, None, 'listen', config.get_socket())
    else:
        raise UnknownNetworkError(network)

def listen_tcp(laddr: TCPAddr, network = 'tcp'):
    if 'tcp' in network:
        config = _config_from_net(laddr, network)
        return TCPListener(laddr, config.get_socket())
    else:
        raise UnknownNetworkError(network)

def listen(address: str, network: str):
    """ listen announces and waits for connections on a local network address.

    the network must be a "tcp", "tcp4", "tcp6", "udp", "udp4" or "udp6"
    """
    host, port = split_host_port(address)
    if 'tcp' in network or 'udp' in network:
        addr_list, config = resolver(host, port, network)

        for addr in addr_list:
            try:
                if 'tcp' in network:
                    lstn = TCPListener(addr, config.get_socket())
                    return lstn
                return UDPConn(addr, None, 'listen', config.get_socket())
            except:
                raise
    else:
        raise UnknownNetworkError(network)
