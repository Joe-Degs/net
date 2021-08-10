import unittest
from net import *

class TestSplitHostPort(unittest.TestCase):
    def test_host_port_split(self):
        test_table = [
            { 'arg': 'python.org:http', 'expected': ('python.org', 'http') },
            { 'arg': 'us.pool.ntp.org:ntp', 'expected': ('us.pool.ntp.org', 'ntp') },
            { 'arg': '192.168.116.2:5555', 'expected': ('192.168.116.2', '5555') },
            { 'arg': '[2001:db8::1]:53', 'expected': ('2001:db8::1', '53') },
            { 'arg': '[localhost]:80', 'expected': ('localhost', '80') },
            { 'arg': ':80', 'expected': ('', '80') },
            { 'arg': '[::]:1234', 'expected': ('::', '1234') },
            { 'arg': '[ffff::/128]:1199', 'expected': ('ffff::/128', '1199') },
            { 'arg': '[2001:fed:bed::1%eth0]:65536', 'expected': ('2001:fed:bed::1%eth0', '65536') }
        ]
        for _, tc in enumerate(test_table):
            self.assertEqual(split_host_port(tc['arg']), tc['expected'])

    def test_raises_errors(self):
        # every arg in arg_table should raise an AddressError
        arg_table = [ '', '::', '[::]:', '[::]', '2001::1]:3333',
                '[2001::1:80', '[ffe8::]::4444', '127.0.0.1:::4444']
        for arg in arg_table:
            with self.assertRaises(AddressError):
                split_host_port(arg)

class TestConfigInetAddr(unittest.TestCase):
    def test_inet_addr_config(self):

        # family
        inet = socket.AF_INET
        inet6 = socket.AF_INET6
        unix = socket.AF_UNIX
        unspec = socket.AF_UNSPEC
        # socktype
        stream = socket.SOCK_STREAM
        dgram = socket.SOCK_DGRAM
        # proto
        tcp_ip = socket.IPPROTO_TCP
        udp_ip = socket.IPPROTO_UDP
        # flags
        ai_addr = socket.AI_ADDRCONFIG
        ai_v4 = socket.AI_V4MAPPED
        passive = socket.AI_PASSIVE
        # zero fields
        none = 0

    
        def gen_config(host, port, family, socktype, proto=none, flags=none):
            return {
               'host': host,
               'port': port,
               'family': family,
               'socktype': socktype,
               'proto': proto,
               'flags': flags,
            }

        tt = [{'args': ('localhost', '80', 'tcp'),
                'want': gen_config('localhost', '80', inet, stream, tcp_ip, ai_addr)
            },{'args': ('2001:db8::1', '53', 'udp6'),
                'want': gen_config('2001:db8::1', '53', inet6, dgram, udp_ip,
                    ai_addr)
            },{'args': ('localhost', '3939', ''),
                'want': gen_config('localhost', '3939', unspec, stream, none,
                    passive)
            },{'args': ('./test.sock', '', 'unix'),
                'want': gen_config('./test.sock', '', unix, stream)
            },{'args': ('./test.sock', '', 'unixgram'),
                'want': gen_config('./test.sock', '', unix, dgram)}]

        for tc in tt:
            self.assertEqual(config_inetaddr(*tc['args']).get_config(),
                    tc['want'])
