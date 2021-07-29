from typing import Union, Optional
import ipaddress as ipaddr
import socket

from  .errors import *

class Addr:
    """Addr is a generic wrapper around socket addresses

    socket addresses are gotten either from socket.getaddrinfo or
    they are returned from reading from udp sockets.
    specific address types maybe derived from this class and the str
    function implemented to suit the conventional string representation
    of address type.

    Attributes
    ----------
    addrinfo: tuple
        a socket address
    """
    def __init__(self, addrinfo: tuple):
        """
        Parameters
        -----------
        addrinfo: tuple
            The addrinfo is the tuple that is returned by socket.getaddrinfo
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
        return f'{self.addrinfo[0]}:{self.addrinfo[1]}'

    def __repr__(self) -> str:
        return self.__str__()

class IPAddr(Addr):
    """IPAddr is a wrapper around a ip socket address
    """
    def __init__(self, addrinfo: tuple):
        Addr.__init__(self, addrinfo)
        if addrinfo[0]:
            ip = ''
            if self.scope_id():
                ip = f'{self.addrinfo[0]}%{self.scope_id()}'
            else:
                ip = self.addrinfo[0]
            self.ipaddr = ipaddr.ip_address(ip)
        else:
            self.ipaddr = self.addrinfo

    def is_ipv6(self):
        if len(self.addrinfo) == 4:
            return True
        return False

    def scope_id(self) -> int:
        if self.is_ipv6():
            return self.addrinfo[2]
        return 0

    def flowinfo(self) -> int:
        if self.is_ipv6():
            return self.addrinfo[3]
        return 0

    def __str__(self):
        return join_host_port(str(self.ipaddr))

class TCPAddr(IPAddr):
    """TCPAddr wraps around an addrinfo associated with a tcp socket.
    """
    def __init__(self, addrinfo: tuple):
        IPAddr.__init__(self, addrinfo)
        self.port = self.addrinfo[1]

    def __str__(self):
        return join_host_port(str(self.ipaddr), self.port)

class UDPAddr(IPAddr):
    """UDPAddr wraps an addrinfo associated with a udp socket.
    """
    def __init__(self, addrinfo: tuple):
        IPAddr.__init__(self, addrinfo)
        self.port = self.addrinfo[1]

    def __str__(self):
        return join_host_port(str(self.ipaddr), self.port)

class AddrConfig:
    """AddrConfig is used to configure parameters to resolve names
    """
    def __init__(self,
            host: str = '',
            port: str = '',
            family: Union[socket.AddressFamily, int] = 0,
            socktype: Union[socket.SocketKind, int] = 0,
            proto: int = 0, # integer of protocol to use.
            flags: int = 0, # multiple flags can be or-ed together
        ) -> None:
            self.__addr_config = {
               'host': host,
               'port': port,
               'family': family,
               'socktype': socktype,
               'proto': proto,
               'flags': flags,
            }

    def add_flag(self, flag: int):
        self.__addr_config['flags'] |= flag

    def set_socktype(self, socktype: Union[socket.SocketKind, int]):
        self.__addr_config['socktype'] = socktype

    def set_family(self, family: Union[socket.AddressFamily, int]):
        self.__addr_config['family'] = family

    def set_proto(self, proto: int):
        self.__addr_config['proto'] = proto

    def get_config(self) -> dict:
        return self.__addr_config

    def get_socket(self) -> socket.socket:
        return socket.socket(self.__addr_config['family'], self.__addr_config['socktype'],
                self.__addr_config['proto'])

def join_host_port(host: str, port: str = '') -> str:
    """join_host_port combines host and port into into representation format

    if the host is an ipv4 it joins as 'host:port', if host contains a ':' as
    in a literal ipv6 then it join as '[host]:port'
    """
    if ':' in host:
        return f'[{host}]:{port}'
    return f'{host}:{port}'

def split_host_port(hostport: str):
    """return a combined address into individual host, port

    it splits network address of the form 'host:port', '[host]:port',
    'host%zone:port' or '[host%zone]:port' into host or host%zone and
    port

    see function resolve_addr for more info on form of hostport
    """
    if not hostport:
        # wtf do you want to split?
        raise AddressError(hostport, "missing host and port in address")

    missing_port = "missing port in address"
    too_many_colons = "too many colons in address"
    host = ''
    port = ''

    i = hostport.rfind(':')
    # if there is no ':' in hostport or ':' is the last thing
    # hostport then throw an error into the callers face
    if i < 0 or len(hostport) == i+1:
        raise AddressError(hostport, missing_port)

    if '[' in hostport and ']' in hostport:
        # we are treading ipv6 zone
        end = hostport.rfind(']') # get index of ]
        if end+1 == len(hostport):
            # if index of ] is the last thing then there is no port
            raise AddressError(hostport, missing_port)
        elif end+1 == i:
            # this is what we expect
            pass
        else:
            if hostport[end+1] == ':':
                # either ']' is followed by a colon or it is
                # but its not the last one
                raise AddressError(hostport, too_many_colons)
            raise AddressError(hostport, missing_port)
        # host port is worthy ipv6 and should be stripped now.
        host, port = hostport[0 : i], hostport[i+1:]
        host = host.strip('[]')
    elif '[' in hostport or ']' in hostport:
        # contains only one of '[' ']'
        raise AddressError(hostport, "address has only one of '[' and ']'")
    else:
        # not string representation of ipv6 but has more than one ':'
        host, port = hostport[0 : i], hostport[i+1:]
        if ':'in host:
            raise AddressError(hostport, too_many_colons)
    
    # we've made it this far and its cool. we can now start the splitting.
    return host, port

def resolve_addr_list(addr_config: dict):
    # runs the address resolution parameters through socket.getaddrinfo
    # function and returns the resulting addresses
    return socket.getaddrinfo(
            addr_config['host'],
            addr_config['port'],
            addr_config['family'],
            addr_config['socktype'],
            addr_config['proto'],
            addr_config['flags']
        )

def inet_addr_list(addr_config: dict, network: str):
    """internet_addr_list returns a list of TCPAddr | UDPAddr | IPAddr
    """
    if network:
        addrinfo_list = resolve_addr_list(addr_config)
        addr_obj = None
        if network == 'tcp' or network == 'tcp4' or network == 'tcp6':
            addr_obj = TCPAddr
        elif network == 'udp' or network == 'udp4' or network == 'udp6':
            addr_obj = UDPAddr
        elif network == 'ip' or network == 'ip4' or network == 'ip6':
            addr_obj = IPAddr
        else:
            raise UnknownNetworkError(network)
        addr_list = []
        for addrinfo in addrinfo_list:
            addr_list.append(addr_obj(addrinfo[-1])) # addrinfo is always the last
        return addr_list
    else:
        raise UnknownNetworkError(network)

def config_inetaddr(host: str, port: str, network: str) -> AddrConfig:
    """config_inetadr returns an AddrConfig suitable to resolve host:port.

    this instance can be resolved into an address endpoint
    that can be connected to, sent into or listened on.

    Parameters
    -----------
    host: str
        the host node of the address

    port: str
        the literal port number or service name

    network: str, optional
        the network endpoint type of address

    Raises
    ------
    UnknowNetworkError
    """
    config = AddrConfig(host, port)

    if '6' in network:
        # address family for ipv6
        config.set_family(socket.AF_INET6)
        if not socket.has_ipv6:
            # for machines without ipv6
            config.add_flag(socket.AI_V4MAPPED)
    else:
        config.set_family(socket.AF_INET)

    if network:
        # if we have a network to connect to, we want
        # addresses we can reach.
        config.add_flag(socket.AI_ADDRCONFIG)
        if network == 'udp' or network == 'udp4' or network == 'udp6':
            config.set_socktype(socket.SOCK_DGRAM)
            config.set_proto(socket.IPPROTO_UDP)
            return config
        elif network == 'tcp' or network == 'tcp4' or network == 'tcp6':
            config.set_socktype(socket.SOCK_STREAM)
            config.set_proto(socket.IPPROTO_TCP)
            return config
        else:
            raise UnknownNetworkError(network)
    else:
        config.set_socktype(socket.SOCK_STREAM)
        config.set_family(socket.AF_UNSPEC)
        config.add_flag(socket.AI_PASSIVE)
        return config

def resolver(host: str, port: str, network: str) -> tuple[list, AddrConfig]:
    """resolve endpoints and return the parameters used to resolve them.

    Parameters
    ----------
    host: str
        the network host to resolve

    port: str
        the port number or service name

    network: str
       type of network to resolved address is related to. 
    """
    config = config_inetaddr(host, port, network)
    addr_list = inet_addr_list(config.get_config(), network)
    return addr_list, config

def loopback_addr(network) -> str:
    # loopback ip address for network interface.
    if '6' in network:
        return '::1'
    return '127.0.0.1'

def resolve_udp_addr(address: str, network: str='udp') -> Optional[UDPAddr]:
    """resolve_udp_addr returns an address of a udp endpoint

    if the address is not a literal ip address and port number,
    resolve_udp_addr resolves the address to an endpoint of a udp network.
    if address is empty or None, it defaults to using the appropriate
    loopback ip

    see resolve_addr for more info on structure of address and network

    Parameters:
    -----------
    address: str
        the udp endpoint to resolve

    network: str
        the type of udp network to resolve.

    Raises
    ------
    UnknownNetworkError
    """
    if 'udp' in network:
        host, port = split_host_port(address)
        if not host:
            host = loopback_addr(network)
        udp_addr_list, _ = resolver(host, port, network)
        return udp_addr_list[0]
    else:
        raise UnknownNetworkError(network)

def resolve_tcp_addr(address: str, network: str='tcp') -> TCPAddr:
    """resolve_tcp_addr returns the address of the tcp endpoint

    if the address is not a literal ip address and port number,
    resolve_tcp_addr resolves the address to an endpoint of a tcp network.
    if address is empty or None, it defaults to using the appropriate
    loopback ip

    see resolve_addr for more info on the structure of address and network.

    Parameters:
    -----------
    address: str
        address endpoint of the tcp connection

    network: str

    Parameter
    ---------
    address: str
        the network endpoint to connect to in "host:port" format.

    network: str
        type of network to connect to.
        see resolve_addr for types of network supported.
        a tcp network name

    """
    if 'tcp' in network:
        host, port = split_host_port(address)
        if not host:
            host = loopback_addr(network)
        tcp_addr_list, _ = resolver(host, port, network)
        return tcp_addr_list[0]
    else:
        raise UnknownNetworkError(network)

def resolve_ip_addr(address: str, network: str = 'ip'):
    pass

def resolve_addr(address: str, network: str):
    """
    resolve_addr returns an address that you can connect to, sendto or
    listen on.

    for TCP and UDP networks the address is of the form "host:port". The
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
    so make sure to input correct ip addresses or the underlying socket
    layer will throw errors related to incorrect supplied to it.

    examples:
    --------    
        resolve_addr("python.org:http" "tcp") -> TCPAddr
        resolve_addr("us.pool.ntp.org:ntp", "udp") -> UDPAddr
        resolve_addr("192.168.116.2:5555", "tcp") -> TCPAddr
        resolve_addr("[2001:db8::1]:53", "udp") -> UDPAddr
        resolve_addr(":80", "tcp6") -> TCPAddr

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
    TCPAddr | UDPAddr | IPAddr

    Raises:
    -------
    UnknownNetworkError
    """
    if 'tcp' in network:
        return resolve_tcp_addr(address, network)
    elif 'udp' in network:
        return resolve_udp_addr(address, network)
    elif 'ip' in network:
        return resolve_ip_addr(address, network)
    else:
        raise UnknownNetworkError(network)
