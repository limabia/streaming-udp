import argparse
import socket
import time
import _thread
import keyboard
from os import listdir

import cv2
import numpy as np

VIDEOS_PATH = 'videos'
BUFFER_SIZE = 1024


def create_udp_socket():
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def create_tcp_socket(args):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((args.ip, args.port))
    s.listen()
    return s


def on_new_client(tcp, udp, client_address_tcp, args):
    videos_available = listdir(VIDEOS_PATH)

    print("Sending available videos...", client_address_tcp)

    videos_available_bytes = bytearray()
    for video in videos_available:
        # tcp.sendall(bytearray(video,"utf-8"))
        videos_available_bytes.extend(bytearray(video, "utf-8"))
        videos_available_bytes.extend(bytearray("\n", "utf-8"))

    tcp.sendall(videos_available_bytes)

    print("Waiting client to select video", client_address_tcp)

    selected_video_bytes = tcp.recv(BUFFER_SIZE)  # server receive from client which port it should send the video data
    selected_video = int.from_bytes(selected_video_bytes, 'big') - 1

    print("Video selected: ", videos_available[selected_video], client_address_tcp)

    path = 'videos/' + videos_available[selected_video]

    port_bytes = tcp.recv(BUFFER_SIZE)  # server receive from client which port it should send the video data
    port = int.from_bytes(port_bytes, 'big')
    client_address_udp = ((client_address_tcp[0], port))  # create clientAddress

    video = cv2.VideoCapture(path)  # TODO Enviar para o cliente o video escolhido dado a lista
    video_fps = video.get(cv2.CAP_PROP_FPS)
    desired_fps = args.fps
    max_size = 65536 - 8  # less 8 bytes of video time
    if desired_fps > video_fps:
        desired_fps = video_fps

    transmission_start = time.time()
    processing_start = time.time()
    jpg_quality = 80

    print('Transmission started')
    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break

        if args.gray:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

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
        _thread.start_new_thread(on_new_client, (conn, udp, client_address_tcp, args))
    tcp.close()
    s.close()


def arg_parse():
    parser = argparse.ArgumentParser(description='Server')
    parser.add_argument("--video", help="Path to video file", default=0)
    parser.add_argument("--fps", help="Set video FPS", type=int, default=15)
    parser.add_argument("--gray", help="Convert video into gray scale", action="store_true")
    parser.add_argument("--port", help="Server TCP port number", type=int, default=65430)
    parser.add_argument("--ip", help="Server IP address", default="localhost")

    return parser.parse_args()


if __name__ == '__main__':
    arguments = arg_parse()
    print(arguments)

    _thread.start_new_thread(main, (arguments,))

    while True:
        try:
            if keyboard.is_pressed('Esc'):
                print("\nServer is shutting down...")
                sys.exit(0)
        except:
            break
