import socket

BYTE = 1024
HOST = 'localhost'
PORT = 8080

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientName = (HOST, PORT)
udp.bind(clientName)  # aqui é onde se estabelece a comunicacao

print('SERVIDOOOOOORRRR')

while True:
    print('esperando nova msg:')
    message, client = udp.recvfrom(BYTE)  # aqui temos que ver certinho a questão da mensagem
    message = message.decode()
    print(message)
udp.close()


# para executar python3 server.py