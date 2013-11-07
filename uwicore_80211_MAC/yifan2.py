import uwicore_mac_utils as MAC
import socket
import pickle
import time

interp = 10
regime = "1"

MAC_PORT = 8001




s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((socket.gethostname(), MAC_PORT))
pkt = {"HEADER":"PAYLOAD", "DATA":"DATATATATATA"}
packet = pickle.dumps(pkt, 1);
s.send(packet)





