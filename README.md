# Summary
This is a sockets networking library of sorts written in python for learning
the basics of socket programming, it follows some of the design principles
of the golang net package. If you want to test sockets and do some other
sockets related scripting and don't want to deal with os api's and other stuff
use this. I'm calling this `net` just like its parent package `net` golang.

It is essentially just a wrapper around python socket objects and might not be
good for any kind of production work but for testing and fast scripting for
maybe ctf's and all the other kind of script kiddie stuff, this will do.

Requirements
------------
__This is still in development__

You need ``Python 3.9`` to try this library right now. It uses type hinting to help
me develop faster and catch bug earlier in the development process.

It works well on Linux and it kinda works on Windows too. I haven't really
tested it on windows for some time now.

If you want to contribute or test this, all you need to do is:
    
    $ git clone https://github.com/Joe-Degs/net.git

And then reach out to me if you have some ideas that can make this better
or help me learn more stuff about sockets. Its open to everybody and i want
to make more friends so hit me up :>)

# Usage

This socket library currently supports `tcp`, `udp`, and `unix` sockets. It is relatively
easy to start new socket clients and servers with this package. It doesnt really
work like its golang muse but it kinda works and its a work in progress so its cool.

Following are implementations of the echo server using this library.


## Address Resolution and Other Address Related Stuff
This library is just a wrapper around sockets in python and it wraps around
some of the important functions for address resolution and other address related
stuff.

All the major sockets types "tcp", "udp" and "unix" sockets have equivalent address
classes that end with `Addr` suffix and they all inherit from the toplevel `Addr` type.

*i think i need a function to convert between `Addr` and  subclasses of `Addr`*

So effectively, there are the following address types in this module:
    
        Addr, TCPAddr, UDPAddr, UnixAddr

### Resolving Addresses
`net` uses the `socket.getaddrinfo` function to network and service names to
ip addresses.

```python
# resolving tcp addresses
gaddr = resolve_tcp_addr('google.com:www', 'tcp') # resolve network and service name to ip, port

# resolving IPv6  udp addresses
udp_addr = resolve_udp_addr('us.pool.ntp.org:ntp', 'udp6')

# unix stream socket  addresses.
unix_addr = resolve_tcp_addr('/tmp/test.sock', 'unix')

# resolve unix datagram sockets.
unixgram_addr = resolve_unix_addr('/tmp/test.sock2', 'unixgram')

```

## Connections.
`net` provides couple of classes with the `Conn` suffix that are the real wrappers around
the socket objects in python.

The `Conn` subclasses in this module are:

    UDPConn, TCPConn, TCPListener, UnixConn, UnixListener

The types suffixed `Listener` wrap around sockets listeners that
are stream oriented.


### TCP Sockets
TCP sockets are fully supported by this library.
```python

import net

def handler(conn):
    buf = conn.read() # read some bytes from connection
    n = conn.write(buf) # write the bytes back into connection
    assert(len(buf), n)

# an IPv6 tcp socket server on localhost.
tcp_addr = net.resolve_tcp_addr('localhost:5055', 'tcp6')
tcp_srv = net.listen_tcp(tcp_addr, 'tcp6')
while True:
    tcp_client = tcp_srv.accept()
    handler(tcp_client)      
```

### UDP Sockets
```python
import net

# IPv4 udp socket server on localhost
udp_addr = net.resolve_udp_addr('localhost:5055', 'udp')
udp_srv = net.listen_udp(udp_addr, 'udp')
while True:
    buf, raddr = udp_srv.read_from() # wait and read from connection
    n = udp_srv.write_to(buf, raddr) # write data back to sender
    assert(len(buf), n)
```

### Unix domain sockets
The library supports both unix stream sockets and unix datagram sockets, both
work on linux but i'm not sure about windows. I know unix stream sockets work on
windows but maybe not the datagram sockets. So thread with caution.

