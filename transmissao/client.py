import argparse
import socket
import time
import keyboard

import cv2
import numpy as np

SERVER_ADDRESS = "localhost"  # Standard loopback interface address (localhost)
SERVER_PORT = 65430  # SERVER TCP PORT TO CONNECT


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


def create_udp_socket(ip, porta):
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind((ip, porta))
    return udp


def get_videos_list(videos_available_bytes):
    videos_available = videos_available_bytes.decode("utf-8")
    videos = []
    video = ""

    for letter in videos_available:
        if (letter == "\n"):
            videos.append(video)
            video = ""
        else:
            video += letter
    return videos


def main(args):
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.connect((SERVER_ADDRESS, SERVER_PORT))

    print("\n\nConnected to the server!!", (SERVER_ADDRESS, SERVER_PORT))

    print("Getting available videos...")

    videos_available_bytes = tcp.recv(1024)  # server receive from client which port it should send the video data

    videos = get_videos_list(videos_available_bytes)

    print("\nHere are the content available:")
    for idx, video in enumerate(videos):
        print("[", idx + 1, "] ", video)

    selected_video = int(input("Please select a video to play: "))
    tcp.sendall(selected_video.to_bytes((selected_video.bit_length() + 7) // 8, 'big'))

    print("\n\nPlaying video...")

    port = int(args.port)
    tcp.sendall(port.to_bytes((port.bit_length() + 7) // 8, 'big'))

    udp = create_udp_socket(args.ip, args.port)

    data = b''
    # buffer_size = 65536
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
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                vt = np.frombuffer(vt, dtype=np.float64)[0]
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
    parser.add_argument("--port", help="Listening port number (UDP)", type=int)
    return parser.parse_args()


if __name__ == '__main__':
    arguments = arg_parse()
    print(arguments)
    main(arguments)
