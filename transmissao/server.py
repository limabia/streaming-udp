import argparse
import socket
import time

import cv2
import numpy as np


def get_video_writer(frame):
    w, h = frame.shape[1], frame.shape[0]
    is_color = True
    try:
        frame.shape[2]
    except IndexError:
        is_color = False
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    vr = cv2.VideoWriter('video.avi', fourcc, 10, (w, h), is_color)
    return vr


# estabelece a conexao udp
def estabelece_conexao(ip, porta):
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind((ip, porta))
    return udp


def main(args):
    udp = estabelece_conexao(args.ip, args.port)

    data = b''
    buffer_size = 65536
    window = 'Transmissao de Video'
    out = None

    if not args.save:
        cv2.namedWindow(window, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window, 600, 600)

    try:
        start = time.time()
        while True:
            data += udp.recv(buffer_size)
            a = data.find(b'\xff\xd8')
            b = data.find(b'\xff\xd9')
            if a != -1 and b != -1:
                jpg = data[a:b + 2]
                vt = data[b + 2: b + 2 + 8]
                data = data[b + 2 + 8:]
                # decode frame and video time
                frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                vt = np.fromstring(vt, dtype=np.float64)[0]
                if args.save:
                    if out is None:
                        out = get_video_writer(frame)
                    out.write(frame)
                else:
                    cv2.imshow(window, frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                end = time.time()
                start = time.time()

    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        udp.close()
        if args.save:
            out.release()

    cv2.destroyAllWindows()
    udp.close()
    if args.save:
        out.release()


def arg_parse():
    parser = argparse.ArgumentParser(description='Client')
    parser.add_argument('--save', default=False, help='Save video', action='store_true')
    parser.add_argument("--ip", help="Client IP address", default="localhost")
    parser.add_argument("--port", help="UDP port number", type=int, default=8080)
    return parser.parse_args()


if __name__ == '__main__':
    arguments = arg_parse()
    print(arguments)
    main(arguments)
