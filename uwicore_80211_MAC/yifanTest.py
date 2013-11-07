import socket, pickle

PHY_PORT = 8013
PHY_RX_PORT = 8513

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((socket.gethostname(), PHY_PORT))

pkt = pickle.dumps({"DATA":"RTS", "HEADER":"TAIL"}, 1)
s.send(pkt)

p = s.recv(10000)

print p

info = pickle.loads(p)

print info


