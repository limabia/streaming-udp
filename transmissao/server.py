import argparse
import socket
import time

import cv2
import numpy as np


def create_udp_socket():
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def create_tcp_socket(args):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((args.ip, args.port))
    s.listen()
    return s


def main(args):

    tcp = create_tcp_socket(args)

    conn, addr = tcp.accept()           #waits for client to connect
    print('Connected by client', addr)

    data = conn.recv(1024) # server receive from client which port it should send the video data
    port = int.from_bytes(data, 'big')
    clientAddress = (("localhost", port)) #create clientAddress



    udp = create_udp_socket()

    video = cv2.VideoCapture('teste.mp4')  # TODO Enviar para o cliente o video escolhido dado a lista
    video_fps = video.get(cv2.CAP_PROP_FPS)
    desired_fps = args.fps
    max_size = 65536 - 8  # less 8 bytes of video time
    if desired_fps > video_fps:
        desired_fps = video_fps

    try:
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

            udp.sendto(data, clientAddress)

            end = time.time()

            processing_time = end - processing_start
            desired_time = 1 / desired_fps
            if desired_time > processing_time:
                time.sleep(desired_time - processing_time)
            processing_start = time.time()

    except KeyboardInterrupt:
        video.release()
        udp.close()

    video.release()
    udp.close()


def arg_parse():
    parser = argparse.ArgumentParser(description='Server')
    parser.add_argument("--video", help="Path to video file", default=0)
    parser.add_argument("--fps", help="Set video FPS", type=int, default=14)
    parser.add_argument("--gray", help="Convert video into gray scale", action="store_true")
    parser.add_argument("--port", help="Server TCP port number", type=int, default=65430)
    parser.add_argument("--ip", help="Server IP address", default="localhost")

    return parser.parse_args()


if __name__ == '__main__':
    arguments = arg_parse()
    print(arguments)
    main(arguments)
