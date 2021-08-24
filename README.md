# Summary
This is a python networking module of sorts written as a project for learning
the basics of socket programming. It follows some of the design principles
of the golang net package. If you want to do network testing/scripiting and other
sockets related scripting but don't want to deal with os api's and other stuff,
this module could be useful for you. 
I'm calling this `net` just like its parent package `net` in golang.

It is essentially just a wrapper around python socket objects and might not be
useful for any kind of production work but for testing and any kind of network
scripting that is not production related this could be used.

Requirements
------------
__This is still in development__

You need `Python 3.9` to try this library right now. It uses type hinting to help
me develop faster and catch type bugs early in the development process.

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

The code examples are implementations of a simple echo server and their clients using this module.

## Address Resolution
This module is just a wrapper around python socket objects and it also wraps around
some of the important functions for address resolution and other networking related stuff.

All the major sockets types `tcp`, `udp` and `unix` sockets have their equivalent address
classes that end with `Addr` suffix and they all inherit from the toplevel `Addr` type.

There are the following address types in this module:
    
        Addr(base class), TCPAddr, UDPAddr, UnixAddr

### Resolving Addresses
`net` uses the `socket.getaddrinfo` function to resolve network and service names to
ip addresses.

```python
# resolving tcp addresses
goggle = resolve_tcp_addr('google.com:www', 'tcp') # resolve network and service name to ip, port

# resolving IPv6  udp addresses
ntp_udp_addr = resolve_udp_addr('us.pool.ntp.org:ntp', 'udp6')

# unix stream socket  addresses.
unix_addr = resolve_unix_addr('/tmp/test.sock', 'unix')

# resolve unix datagram sockets.
unixgram_addr = resolve_unix_addr('/tmp/test.sock2', 'unixgram')
```

## Connections.
`net` provides couple of classes with the `Conn` suffix that are wrappers around
socket objects in python.

The `Conn` subclasses wrap around python socket objects for different protocols, 
the ones implemented are;
- `UDPConn` provides a generic wrapper udp socket objects.
- `TCPConn` wraps around tcp socket objects.
- `UnixConn` wraps around unix domain socket objects.

This module is totally extensible and more network protocols can be added and that is
 the plan for the future, to use this module to play with as much network protocols as I can.

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

### Testing
The package contains a `test` directory that holds all the tests for the package. test
coverage for now is not good at all, only a couple of functions in `net/netaddr.py`
have tests and that is not acceptable but i'm still figuring the whole test thing out so
i'm not worried.
To run the scanty tests i have:

    $ python -m unittest discover -s test -v

For manual testing which is common with sockets, i have bunch of scripts in the root direcotry
that are just good for doing that. There is a `testnet.sh` bash script that used socat
to test echo socket servers.

The `testnet.py` is a cli tool for spinning up clients/servers of the various network
interfaces supported by this module

      Use the net module to open socket servers or clients

      Atleast one of the following should be specified:
        -d    Dial, connect to a client
        -l    Listen, open a server to listen for connections

      The following are not optional:
        -n    Specify the network type to connect to
        -a    Specify address to bind connection to

couple of examples;

to open a unix domain socket server on /tmp/test.sock

    $ python testnet.py -l -n unix -a /tmp/test.sock

or a ipv6 udp server on localhost:5055

    $ python testnet.py -l -n udp6 -a localhost:5055

The `testnet.sh` supports testing couple of socket servers by spinning up clients
to test the network interface that is specified.
    
    testnet.sh <options>

    Atleast one of the following should be specified:
    -n          network type to connect to. supported is  
                "unix-client" -> connect to unix datagram socket 
                "unix-connect" -> connect to unix stream socket
                "tcp" -> IPv4 tcp socket connect
                "tcp6" -> IPv6 tcp socket connect
                "udp" -> IPv4 udp socket connect 
                "udp6" -> IPv6 udp socket connect
                this option can be supplied as a  space separated string of multiple 
                supported network types.

    -all        Connect to all supported network interfaces.

    The following options are not optional
    -a          Specify address to connect to in "ip:port" format for tcp and udp networks

    -u          Specify unix domain socket address to connect to

    -t | -f     -t text to write into socket | -f path of file to write into socket.

To test servers open on any network interface.

connect and send data to ipv6 tcp server on localhost:1234

    $ ./testnet.sh -t "random data to sent to server" -n tcp6 -a localhost:1234

connect to unix domain socket server listening on /tmp/test.sock

    $ ./testnet.sh -t "random data into socket" -n unix -u /tmp/test.sock

## TODO
- Things seem to work now but i'm rethinking the whole listener thing. I do not
fancy the idea of stream oriented network listener objects inheriting from the base `Conn`
class anymore. This is because the listener objects inheriting from the Conn class end up with
all methods declared on the Conn class which they should not have. I want to change this
and create a more tailor made base class called `Listener` for stream oriented listeners
to inherit from.
- Socket clients opened with this package are blocking the socket on `read/recv` and i can't
seem to find a way to make it them not block. This has been a problem since the beginning and
it is literally driving me nuts now. The socket `read/write` uses the same methods on `io.BufferedRWPair`
to perform reads and writes to the underlying socket. From the documentation of `io.BufferedRWPair.read`,
calling read without arguments should read and return till EOF is encountered in which case it
stops and returns an empty byte. But the `read`s are causing both sockets to block forever unless
i do a close on the socket or i Ctrl+c on the client socket.This sh!t is frustrating.
