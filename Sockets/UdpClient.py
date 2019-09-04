import socket

HOST = '192.168.0.1'
PORT = 8080

udp = socket.newSocket(socket.AF_INET, socket.SOCK_DGRAM)
# Quando criamos um socket, precisamos definir a família de endereços que ele vai conhecer
# O AF_INET se refere à familia do IPV4, protocolo de internet;
# Geralmente se usa esse cara mesmo;

# No segundo parâmetro temos o que realmente define se o protocolo é upd ou tcp. O tcp geralmente
# utiliza o SOCK_STREAM;
# o SOCK_DGRAM significa 'datagram-based protocol': vc manda um datagrama (que seria o D do uDp) e recebe uma resposta
# e fim da sua conexão

serverName = (HOST, PORT)
message = 'mensagem a ser enviada pelo socket'  # aqui mudaremos quando definirmos os tipos das mensagens

udp.send(message, serverName)
udp.close()
