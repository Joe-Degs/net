from .netconn import *
from .netaddr import *

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
        conn_type: ConnType = ConnType.REMOTE, sock: Optional[socket.socket] = None):

        # TODO(Joe):
        # the socket is not factoring in the type of address being passed
        # during creation. if the addresses are ipv6, create an ipv6 socket.
        # else ipv4 socket.
        if sock == None:
            super().__init__(socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                socket.IPPROTO_UDP))
        else:
            super().__init__(sock)

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
        data, raddr = self.sock.recvfrom(RECV_MAX)
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
