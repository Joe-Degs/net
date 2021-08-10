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


## Address Resolution
This library is just a wrapper around sockets in python and it wraps around
some of the important functions for address resolution and other address related
stuff.

All the major sockets types "tcp", "udp" and "unix" sockets have equivalent address
classes that end with `Addr` suffix and they all inherit from the toplevel `Addr` type.


So effectively, there are the following address types in this module:
    
        Addr, TCPAddr, UDPAddr, UnixAddr

### Resolving Addresses
`net` uses the `socket.getaddrinfo` function to resolve network and service names to
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

The `Conn` subclasses wrap around the various socket protocols, the ones implemented are;
- `UDPConn` provides a generic wrapper udp socket connections.
- `TCPConn` wraps around tcp socket connections.
- `UnixConn` wraps around unix domain socket connections.

This module is totally extensible and more socket connection protocols can be added, that's
 like my plan for the future, use this module to play with enough socket protocols.

There are also couple of types suffixed `Listener` and they are generic listeners for
stream oriented protocols.
- `TCPListener` wraps around a tcp network listener socket
- `UnixListener` does what the above does for unix domain sockets.

### TCP Sockets

#### server
```python

import net

def handler(conn):
    buf = conn.read() # read some bytes from connection
    n = conn.write(buf) # write the bytes back into connection
    assert(len(buf) == n)

# an IPv6 tcp socket server on localhost.
tcp_addr = net.resolve_tcp_addr('localhost:5055', 'tcp6')
tcp_srv = net.listen_tcp(tcp_addr, 'tcp6')
while True:
    tcp_client = tcp_srv.accept()
    handler(tcp_client)      
```

#### client
```python
import net

raddr = net.resolve_tcp_addr('localhost:5055', 'tcp6') # get remote endpoint address
tcp_client = net.dial_tcp(None, raddr, 'tcp6') # connect to remote endpoint
n = tcp_client.write(b'some random data')
buf = tcp_client.read()
assert(n == len(buf))
```

### UDP Sockets

#### server
```python
import net

# IPv4 udp socket server on localhost
udp_addr = net.resolve_udp_addr('localhost:5055', 'udp')
udp_srv = net.listen_udp(udp_addr, 'udp')
while True:
    buf, raddr = udp_srv.read_from() # wait and read from connection
    n = udp_srv.write_to(buf, raddr) # write data back to sender
    assert(len(buf) == n)
```

#### client
```python
import net

laddr = net.resolve_udp_addr('localhost:5055', 'udp')    # get local endpoint address
srv_addr = net.resolve_udp_addr('localhost:5056', 'udp') # get remote endpoint address
client_conn = net.dial_udp(laddr, None, 'udp')           # bind to local address
n = client_conn.write_to(b'some random data', srv_addr)  # write data to remote endpoint
buf = client_conn.read_from()
assert(n == len(buf))
```

### Unix domain sockets

#### unix stream sockets
```python
import net

def handler(conn):
    buf = conn.read() # read some bytes from connection
    n = conn.write(buf) # write the bytes back into connection
    assert(len(buf) == n)

# an unix socket server on localhost.
unix_addr = net.resolve_unix_addr('/tmp/test.sock', 'unix')
unix_srv = net.listen_unix(unix_addr, 'unix')
unix_srv.set_unlink_on_close(True)
while True:
    unix_client = unix_srv.accept()
    handler(unix_client)      
```

#### unix stream socket client
```python
import net

raddr = net.resolve_unix_addr('/tmp/test.sock', 'unix6') # get remote endpoint address
unix_client = net.dial_unix(None, raddr, 'unix6') # connect to remote endpoint
n = unix_client.write(b'some random data')
buf = unix_client.read()
assert(n == len(buf))
```


#### unix datagram sockets.
```python
import net

# unixgram socket server on localhost
unixgram_addr = net.resolve_unixgram_addr('/tmp/test.sock2', 'unixgram')
unixgram_srv = net.listen_unixgram(unixgram_addr, 'unixgram')
while True:
    buf, raddr = unixgram_srv.read_from() # wait and read from connection
    n = unixgram_srv.write_to(buf, raddr) # write data back to sender
    assert(len(buf) == n)
```

#### unix datagram socket client
```python
import net

laddr = net.resolve_unix_addr('/tmp/test.sock3', 'unixgram')    # get local endpoint address
srv_addr = net.resolve_unix_addr('/tmp/test.sock2', 'unixgram') # get remote endpoint address
client_conn = net.dial_unix(laddr, None, 'unixgram')           # bind to local address
n = client_conn.write_to(b'some random data', srv_addr)  # write data to remote endpoint
buf = client_conn.read_from()
assert(n == len(buf))
```
## TODO
