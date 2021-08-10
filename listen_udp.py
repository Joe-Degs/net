from net import address as addr
from net import conn
import sys

def udp_srv(laddr, network):
	laddr = addr.resolve_udp_addr(laddr, network)
	c = conn.listen_udp(laddr, network)
	print(f'udp server on {c.local_addr()}')
	while True:
		b, naddr = c.read_from()
		print(f'recieved connection from {c.remote_addr()}')
		c.write_to(b, naddr)

def main():
	args = sys.argv[1:]
	if len(args) < 2:
		print('args not up to kpa!')
		sys.exit(1)
	udp_srv(args[0], args[1])

if __name__ == '__main__':
	main()

