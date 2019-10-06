import argparse
import socket
import time

import cv2
import numpy as np


def arg_parse():
    parser = argparse.ArgumentParser(description='Server')
    parser.add_argument("--video", help="Path to video file", default=0)
    parser.add_argument("--fps", help="Set video FPS", type=int, default=14)
    parser.add_argument("--gray", help="Convert video into gray scale", action="store_true")
    parser.add_argument("--ip", help="Client IP address", default="localhost")
    parser.add_argument("--port", help="UDP port number", type=int, default=60444)

    return parser.parse_args()


def main(args):
    video = 'teste.mp4'
    address = (args.ip, args.port)

    cap = cv2.VideoCapture(video) # args.video

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    desired_fps = args.fps
    max_size = 65536 - 8  # less 8 bytes of video time
    if desired_fps > video_fps:
        desired_fps = video_fps

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        transmission_start = time.time()
        processing_start = time.time()
        jpg_quality = 80
        while cap.isOpened():
            ret, frame = cap.read()
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

            vt = np.array([cap.get(cv2.CAP_PROP_POS_MSEC) / 1000], dtype=np.float64)
            data = encoded_img.tobytes() + vt.tobytes()

            sock.sendto(data, address)

            end = time.time()
            print('FPS: {0:0.2f}'.format(1 / (end - transmission_start)))
            transmission_start = time.time()

            processing_time = end - processing_start
            desired_time = 1 / desired_fps
            if desired_time > processing_time:
                time.sleep(desired_time - processing_time)
            processing_start = time.time()

    except KeyboardInterrupt:
        cap.release()
        sock.close()

    cap.release()
    sock.close()


if __name__ == '__main__':
    arguments = arg_parse()
    main(arguments)
