# Summary
This is a sockets networking library of sorts written in python for learning
the basics of socket programming, it follows some of the design principles
of the golang net package. If you want to test sockets and do some other
sockets related scripting and don't want to deal with os api's and other stuff
use this. I'm calling this `net` just like its parent package `net` golang.

Requirements
------------
__This is still in development__

You need ``Python 3.9`` to try this library right now. It uses type hinting to help
me develop faster and catch bug earlier in the development process.

It works well on Linux and it kinda works on Windows too. I haven't really
tested it on windows for some time now.

To use this you have to pull from github:
    
    $ git clone https://github.com/Joe-Degs/net.git

# Usage
This socket library currently supports `tcp`, `udp`, and `unix` sockets. It is relatively
easy to start new socket clients and servers with this package. It doesnt really
work like its golang muse but it kinda works and its a work in progress so its cool.

Following are implementations of the echo server using this library.

### tcp server
spawning a tcp server on localhost is as simple as
```python

    import net

    def handler(conn):
        buf = conn.read() # read some bytes from connection
        n = conn.write(buf) # write the bytes back into connection
        assert(len(buf), n)

    tcp_addr = net.resolve_tcp_addr('localhost:5055', 'tcp')
    tcp_srv = net.listen_tcp(tcp_addr, 'tcp')
    while True:
        tcp_client = tcp_srv.accept()
        handler(tcp_client)
        
```
