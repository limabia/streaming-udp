import socket

BYTE = 1024
HOST = ''
PORT = 8080

udp = socket.newSocket(socket.AF_INET, socket.SOCK_DGRAM)
clientName = (HOST, PORT)
udp.bind(clientName)  # aqui é onde se estabelece a comunicacao

while True:
    message, client = udp.receive(BYTE)  # aqui temos que ver certinho a questão da mensagem

udp.close()
