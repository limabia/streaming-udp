import argparse
import socket
import threading
from os import listdir

import cv2
import numpy as np
import time

SERVER_ADDRESS_TCP = "localhost"  # endereco IP padrao
SERVER_PORT_TCP = 65430  # porta padrao para conexao TCP
VIDEOS_PATH = 'videos'  # pasta padrao para os videos
MESSAGE_BUFFER_SIZE = 1024  # tamanho padrao de buffer
FPS = 30  # numero de frames por segundo padrao
VIDEO_BUFFER_SIZE = 65536  # Tamanho máximo do pacote (em bytes)
# Tamanho maximo do frame (em bytes)
MAX_FRAME_SIZE = VIDEO_BUFFER_SIZE - 8  # tamanho do pacote menos 8 bytes de tempo do vídeo


def create_udp_socket():
    """ cria conexao udp """
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def create_tcp_socket(args):
    """ cria conexao tcp """
    print(args)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # abre o socket mesmo que ainda exista outro socket aberto
    s.bind((args.ip, args.port))  # liga o socket de fato
    s.listen()
    return s


def videos_list(path):
    """ constroi a lista de videos para enviar ao cliente """
    videos_available = listdir(path)

    videos_available_bytes = bytearray()
    for video in videos_available:
        videos_available_bytes.extend(bytearray(video, "utf-8"))
        videos_available_bytes.extend(bytearray("\n", "utf-8"))

    return videos_available, videos_available_bytes


def on_new_client(tcp, client_address_tcp, udp, args):
    """ para cada cliente conectado: envia os vídeos disponíveis, recebe o vídeo selecionado,
    abre conexao UDP e faz a transmissão do vídeo escolhido """
    
    print("Enviando videos disponiveis...", client_address_tcp)

    videos_available, videos_available_bytes = videos_list(args.video)  # obtém os videos disponíveis na pasta
    tcp.sendall(videos_available_bytes)  # envia a lista de videos para o cliente

    print("Esperando selecionar video. Cliente: ", client_address_tcp)

    selected_video_bytes = tcp.recv(MESSAGE_BUFFER_SIZE)  # servidor recebe do cliente qual vídeo será enviado

    selected_video = int.from_bytes(selected_video_bytes, 'big') - 1  # converte os bytes recebidos para inteiro e subtrai 1
    # está sendo subtraído 1, pois o servidor se perde ao converter os bytes do inteiro 0, 
    # logo a lista para o cliente escolher começa com o índice 1

    print("Video selecionado: ", selected_video, " por cliente: ", client_address_tcp)

    port_bytes = tcp.recv(MESSAGE_BUFFER_SIZE)  # servidor recebe do cliente qual porta UDP deverá enviar o vídeo
    port = int.from_bytes(port_bytes, 'big') 
    client_address_udp = (client_address_tcp[0], port)  # endereço UDP do cliente

    path = args.video + '/' + videos_available[selected_video]  # encontra o video na pasta de video definida
    video = cv2.VideoCapture(path)
    desired_fps = args.fps

    processing_start = time.time()
    jpg_quality = 80

    print('Transmissao inciada para cliente: ', client_address_tcp)

    try:
        while video.isOpened():
            ret, frame = video.read() #obtém o frame do vídeo
            if not ret:
                break

            # compacta o frame
            encoded_img, result = compress_frame(frame, jpg_quality)

            # diminui a qualidade de compactação, se caso o frame for maior que o tamanho máximo de pacotess
            while encoded_img.nbytes > MAX_FRAME_SIZE:
                jpg_quality -= 5
                encoded_img, result = compress_frame(frame, jpg_quality)

            if not result:
                break

            # concatena o tempo de vídeo aos bytes do frame
            vt = np.array([video.get(cv2.CAP_PROP_POS_MSEC) / 1000], dtype=np.float64)
            data = encoded_img.tobytes() + vt.tobytes()

            udp.sendto(data, client_address_udp) # envia frame para o cliente

            end = time.time()

            # calcula o fps de acordo com o tempo ocorrido para envio de 1 frame e ajusta caso esteja maior que o desejado
            processing_time = end - processing_start
            desired_time = 1 / desired_fps
            if desired_time > processing_time:
                time.sleep(desired_time - processing_time)
            processing_start = time.time()

    finally:
        # libera o vídeo e encerra conexão
        print('Encerrando conexão com o cliente: ', client_address_tcp)
        video.release()
        tcp.close()


def compress_frame(frame, jpg_quality):
    """ comprime o frame utilizando .jpg """
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpg_quality]
    result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
    return encoded_img, result


def main(args):
    """ cria a conexao tcp """
    tcp = create_tcp_socket(args)
    udp = create_udp_socket()

    print('\nServidor iniciado! Esperando por clientes...')

    try:
        while True:
            """ espera o(s) cliente(s) conectarem e estabelece uma conexao TCP """
            conn, client_address_tcp = tcp.accept()
            print('\n\nConectado com o cliente: ', client_address_tcp)
            threading.Thread(target=on_new_client, args=(conn, client_address_tcp, udp, args)).start()

    except:
        pass
    finally:
        tcp.close()
        udp.close()


def arg_parse():
    """ analisa e separa os argumentos passados ao iniciar a execucao do server """
    parser = argparse.ArgumentParser(description='Server')
    parser.add_argument("--video", help="Pasta raiz de arquivos utilizada", default=VIDEOS_PATH)
    parser.add_argument("--fps", help="Definicao de frames por segundo para a transmissao", type=int, default=FPS)
    parser.add_argument("--port", help="Numero da porta TCP do servidor", type=int, default=SERVER_PORT_TCP)
    parser.add_argument("--ip", help="Endereco IP do servidor", default=SERVER_ADDRESS_TCP)

    return parser.parse_args()


if __name__ == '__main__':
    """ recebe os argumentos e inicia uma thread com os argumentos passados na inicializacao do servidor """
    try:
        arguments = arg_parse()
        print("Server.py iniciando a execucao. Argumentos recebidos: ", arguments)

        t = threading.Thread(target=main, args=(arguments,), daemon=True)
        t.start()

        while t.is_alive():
            t.join(.5)
    finally:
        print('\nEncerrando servidor...')