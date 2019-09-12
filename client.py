import socket

from builtins import input

HOST = '192.168.0.10'
PORT = 8080
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print('CLIENTEEEEE')
# Quando criamos um socket, precisamos definir a família de endereços que ele vai conhecer
# O AF_INET se refere à familia do IPV4, protocolo de internet;
# Geralmente se usa esse cara mesmo;
# No segundo parâmetro temos o que realmente define se o protocolo é upd ou tcp. O tcp geralmente
# utiliza o SOCK_STREAM;
# o SOCK_DGRAM significa 'datagram-based protocol': vc manda um datagrama (que seria o D do uDp) e recebe uma resposta
# e fim da sua conexão

serverName = (HOST, PORT)
dest = (HOST, PORT)
print('Para sair use crtl+x\n')
msg = input()
while msg != '\x18':
    udp.sendto (msg.encode(), dest)
    msg = input()
udp.close()


