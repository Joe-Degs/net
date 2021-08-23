from .netconn  import *
from .netaddr  import *
from .tcpconn  import *
from .udpconn  import *
from .unixconn import *

def _config_from_net(addr, net):
    # return the config from an already resolve address.
    if addr and (net_is_valid('tcp', net)):
        return config_inetaddr(addr.addrinfo[0], addr.addrinfo[1], net)
    return config_inetaddr('', '', net)

def dial_udp(laddr: Optional[UDPAddr], raddr: UDPAddr, network = 'tcp'):
    """dial_udp acts like a dial for tcp networks.

    see dial and resolve_addr for more info on address formats and network.

    Parameters
    ----------
    laddr: UDPAddr, optional
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

def dial_unix(laddr: Optional[UnixAddr], raddr: UnixAddr, network = 'unix'):
    """dial_unix acts like a dial for  networks.
    
    see dial and resolve_addr for more info on address formats and network.

    Parameters
    ----------
    laddr: UnixAdr, optional
        the local address of the socket connection.

    raddr: UnixAddr
        the remote address of the connection

    network: str
        Unix network type of the socket. it must be a Unix network name.
    """
    if net_is_valid('unix', network):
        config = _config_from_net(laddr, network)
        return UnixConn(laddr, raddr, ConnType.CONNECT, config.get_socket())
    else:
        raise UnknownNetworkError(network)

def dial(address: str, network: str):
    """dial connects to network on the address endpoint

    For TCP and UDP networks the address is of the form "host:port". The
    host must be a literal ip, a hostname that can be resolved to a literal
    ip address or an empty or unspecified address, this will be passed to the
    underlying address resolvers.

    If the host is a literal IPv6 address, it must be enclosed in square brackets,
    as in "[::1]:80", "[2001::1]:80" or "[fe80::1%zone]:80". The zone specifies
    the scope of the literal IPv6 address as defined in RFC 4007.

    ports must be a literal number wrapped in a string or a service name. ex:
    "80" for a literal port number or "http" for the service name, both are valid.
    
    for TCP and UDP if the address is empty of literal unspecified address as in
    ":80", "0.0.0.0:80" or "[::]:80" the ip address part results in "",
    "0.0.0.0", "::" and the part is parsed as usual.

    Note that there is no verification of ip addresses going on in this package
    so make sure to input correct ip addresses or names else the underlying socket
    layer will throw errors related to incorrect input supplied to it.

    examples:
    --------    
        dial("python.org:http" "tcp") -> TCPConn
        dial("us.pool.ntp.org:ntp", "udp") -> UDPConn
        dial("192.168.116.2:5555", "tcp") -> TCPConn
        dial("[2001:db8::1]:53", "udp") -> UDPConn
        dial(":80", "tcp6") -> TCPConn
        dial("/tmp/file.sock", "unix") -> UnixConn
        dial("/tmp/test.sock", "unixgram") -> UnixConn

    For unix sockets the address must be file system path

    Parameters
    ----------
    address: str, optional
        address is an network endpoint.

    network: str, optional
        network represents the network of the endpoint. networks supported
        this package are "tcp", "tcp4" (IPv4 only), "tcp6" (IPv6 only),
        "udp", "upd4" (IPv4 only), "udp6" (IPv6 only)

    Returns:
    --------
    TCPConn | UDPConn | UnixConn |

    Raises:
    -------
    UnknownNetworkError

    Returns
    --------
    returns the conn type that corresponds to the network specified.
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
    elif net_is_valid('unix', network):
        return dial_unix(UnixAddr(address), network)
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
    assert isinstance(laddr, UDPAddr), 'laddr not a UDPAddr object'
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
    assert isinstance(laddr, TCPAddr), 'laddr not a TCPAddr object'
    if net_is_valid('tcp', network):
        config = _config_from_net(laddr, network)
        return TCPListener(laddr, config.get_socket())
    else:
        raise UnknownNetworkError(network)

def listen_unix(laddr: UnixAddr, network = 'unix'):
    """listen_unix opens a unix domain socket listener.

    we all know unix is special, so it does not have a listener function
    because technically every unix socket is a listener and a sender at the
    time.

    Parameters
    ----------
    laddr: UnixAddr
        the local address to initialize the socket to listen on.

    network: str
        the unix network socket type to listen on.
    """
    assert isinstance(laddr, UnixAddr), 'laddr not a UnixAddr object'
    if net_is_valid('unix', network):
        config = _config_from_net(laddr, network)
        if network == 'unix':
            return UnixListener(laddr, config.get_socket())
        elif network == 'unixgram':
            return UnixConn(laddr, None, ConnType.LISTEN, sock=config.get_socket())
    else:
        raise UnknowNetworkError(network)

def listen(address: str, network: str):
    """listen announces and waits for connections on a local network address.

    the networks supported are "tcp", "tcp4", "tcp6", "udp", "udp4" or "udp6",
    "unix", "unixgram"
    
    """
    if net_is_valid('tcp', network) or net_is_valid('udp', network):
        host, port = split_host_port(address)
        addr_list, config = resolver(host, port, network)
        # TODO(Joe):
        # do not fail until you've tried to connect to all the adresses
        # resolved. the way this is implemented right now, if the first
        # attempt throws an error the whole thing halts. So fix it!
        for addr in addr_list:
            if 'tcp' in network:
                return TCPListener(addr, config.get_socket())
            elif 'udp' in network:
                return UDPConn(addr, None, ConnType.LISTEN, config.get_socket())
            else:
                raise UnknownNetworkError(network)
    elif net_is_valid('unix', network):
        return listen_unix(UnixAddr(address), network)
    else:
        raise UnknownNetworkError(network)
