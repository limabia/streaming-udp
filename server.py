import socket

BYTE = 1024
HOST = ''
PORT = 8080

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientName = (HOST, PORT)
udp.bind(clientName)  # aqui é onde se estabelece a comunicacao

print('SERVIDOOOOOORRRR')

while True:
    print('esperando msg')
    message, client = udp.recvfrom(BYTE)  # aqui temos que ver certinho a questão da mensagem
    print(client, message)
udp.close()


