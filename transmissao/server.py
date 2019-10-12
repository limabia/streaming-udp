import argparse
import socket
import threading
from os import listdir

import cv2
import numpy as np
import time

VIDEOS_PATH = 'videos'  # pasta padrao para os videos
BUFFER_SIZE = 1024  # tamanho padrao de buffer


def create_udp_socket():
    """ cria conexao udp """
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def create_tcp_socket(args):
    """ cria conexao tcp """
    print(args)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((args.ip, args.port))
    s.listen()
    return s


def videos_list(client_address_tcp):
    """ constroi a lista de videos para enviar ao cliente """
    videos_available = listdir(VIDEOS_PATH)

    print("Enviando videos disponiveis...", client_address_tcp)

    videos_available_bytes = bytearray()
    for video in videos_available:
        videos_available_bytes.extend(bytearray(video, "utf-8"))
        videos_available_bytes.extend(bytearray("\n", "utf-8"))

    return videos_available, videos_available_bytes


def on_new_client(tcp, udp, client_address_tcp, args):
    """ estabelece a conexao TCP (listener), recebe cliente e abre conexao UDP para transmissao do video escolhido """

    videos_available, videos_available_bytes = videos_list(client_address_tcp)
    tcp.sendall(videos_available_bytes)  # envia a lista de videos para o cliente

    print("Esperando clientes para selecionar video", client_address_tcp)

    selected_video_bytes = tcp.recv(BUFFER_SIZE)  # servidor recebe do cliente qual porta deve enviar os dados de vídeo
    selected_video = int.from_bytes(selected_video_bytes, 'big') - 1  # TODO explicar essa linha

    print("Video selecionado: ", videos_available[selected_video], client_address_tcp)

    path = VIDEOS_PATH + '/' + videos_available[selected_video]  # encontra o video na pasta de video definida

    port_bytes = tcp.recv(BUFFER_SIZE)  # o recv precisa de buffer pra transmissão de dados
    port = int.from_bytes(port_bytes, 'big') # servidor recebe do cliente qual porta deve enviar os dados de vídeo
    client_address_udp = (client_address_tcp[0], port)  # cria clientAddress

    video = cv2.VideoCapture(path)
    video_fps = video.get(cv2.CAP_PROP_FPS)
    desired_fps = args.fps
    max_size = 65536 - 8  # less 8 bytes of video time
    if desired_fps > video_fps:
        desired_fps = video_fps

    processing_start = time.time()
    jpg_quality = 80

    print('Transmissao inciada para cliente')

    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpg_quality]
        result, encoded_img = cv2.imencode('.jpg', frame, encode_param)

        while encoded_img.nbytes > max_size:
            jpg_quality -= 5
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpg_quality]
            result, encoded_img = cv2.imencode('.jpg', frame, encode_param)

        if not result:
            break

        vt = np.array([video.get(cv2.CAP_PROP_POS_MSEC) / 1000], dtype=np.float64)
        data = encoded_img.tobytes() + vt.tobytes()

        udp.sendto(data, client_address_udp)

        end = time.time()

        processing_time = end - processing_start
        desired_time = 1 / desired_fps
        if desired_time > processing_time:
            time.sleep(desired_time - processing_time)
        processing_start = time.time()

    video.release()

    tcp.close()
    udp.close()


def main(args):
    tcp = create_tcp_socket(args)
    udp = create_udp_socket()

    print('\nServer started!')
    print('Waiting for clients...')

    while True:
        conn, client_address_tcp = tcp.accept()  # waits for client to connect
        print('\nConnected by client', client_address_tcp)
        threading.Thread(target=on_new_client, args=(conn, udp, client_address_tcp, args)).start()
    tcp.close()
    s.close()


def arg_parse():
    parser = argparse.ArgumentParser(description='Server')
    parser.add_argument("--video", help="Path to video file", default=VIDEOS_PATH)  #
    parser.add_argument("--fps", help="Set video FPS", type=int, default=15)  # Velocidade de transmissao do video
    parser.add_argument("--port", help="Server TCP port number", type=int, default=65430)
    parser.add_argument("--ip", help="Server IP address", default="localhost")

    return parser.parse_args()


if __name__ == '__main__':
    arguments = arg_parse()
    print(arguments)

    t = threading.Thread(target=main, args=(arguments,), daemon=True)
    t.start()

    while t.is_alive():
        t.join(.5)
