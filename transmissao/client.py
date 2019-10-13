import argparse
import socket
from random import choice
import cv2
import numpy as np

SERVER_ADDRESS_TCP = "localhost"  # endereco IP padrao
SERVER_PORT_TCP = 65430  # porta padrao para conexao TCP
MESSAGE_BUFFER_SIZE = 1024  # tamanho padrao de buffer de mensagens
VIDEO_BUFFER_SIZE = 65536  # tamanho padrao do buffer de vídeo
VIDEO_TIMEOUT = 2  # tempo de timeout sem receber dados de video do server
SERVER_PORT_UDP = choice(range(4800, 65530))  # porta criada aleatoriamente entre os numeros possiveis para evitar conflitos


def get_video_writer(frame):
    """ responsavel por gravar o video no cliente """
    print("\n\nSalvando video...")
    w, h = frame.shape[1], frame.shape[0]
    is_color = True

    try:
        frame.shape[2]
    except IndexError:
        is_color = False

    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    name = "video-salvo.avi"
    vr = cv2.VideoWriter(name, fourcc, 10, (w, h), is_color)

    print("\n\nVideo salvo!")
    return vr


def create_udp_socket(ip, port):
    """ cria conexao udp utilizando ip e porta passado """
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind((ip, port))
    return udp


def get_videos_list(videos_available_bytes):
    """ monta a lista de video no cliente dado os bytes passados pelo server """
    videos_available = videos_available_bytes.decode("utf-8")
    videos = []
    video = ""

    for letter in videos_available:
        if letter == "\n":
            videos.append(video)
            video = ""
        else:
            video += letter
    return videos


def select_video(max_value, min_value):
    """ solicita ao cliente que escolha o video dada a lista anteriormente disponibilizada e valida a escolha dele """
    selected_video = int(input("\nEscolha o video que voce deseja ver e digite o numero correspondente: "))
    while selected_video > max_value or selected_video < min_value:
        selected_video = int(input("Valor escolhido nao esta de acordo com o disponivel, tente novamente."))
    return selected_video

def video_choice(tcp):
    print("\nPegando vídeos disponiveis...")
    videos_available_bytes = tcp.recv(MESSAGE_BUFFER_SIZE)
    videos = get_videos_list(videos_available_bytes)

    print("\nAqui estao os videos disponiveis:")
    for idx, video in enumerate(videos):
        print("[", idx + 1, "] ", video)

    selected_video = select_video(len(videos), 1)

    return selected_video


def main(args):
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.connect((SERVER_ADDRESS_TCP, SERVER_PORT_TCP))

    print("\nOla, cliente. Voce esta conectado ao servidor, seja bem vindo!!! =) ")

    selected_video = video_choice(tcp)

    tcp.sendall(selected_video.to_bytes((selected_video.bit_length() + 7) // 8, 'big'))

    print("\nReproduzindo video...")

    print('args:', args)

    port = int(args.port)
    tcp.sendall(port.to_bytes((port.bit_length() + 7) // 8, 'big'))

    udp = create_udp_socket(args.ip, args.port)
    udp.settimeout(VIDEO_TIMEOUT)

    window = 'Transmissao de Video'
    if not args.save:
        # configura a janela que exibira o video
        cv2.namedWindow(window, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window, 600, 600)

    data = b''
    out = None

    try:
        # TODO refatorar para rodar so enqt tiver video - fechar a janela e dar print que o video acabou
        while True:
            data += udp.recv(VIDEO_BUFFER_SIZE)
            a = data.find(b'\xff\xd8')
            b = data.find(b'\xff\xd9')
            if a == -1 or b == -1:
                break

            jpg = data[a:b + 2]
            vt = data[b + 2: b + 2 + 8]
            data = data[b + 2 + 8:]

            # decode frame e tempo do video
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            vt = np.frombuffer(vt, dtype=np.float64)[0]

            # escreve na imagem
            if args.show_time:
                frame = write_frame_time(frame, vt)

            # escala de cinza para video em preto e branco
            if args.gray:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # salva o video no cliente
            if args.save:
                if out is None:
                    out = get_video_writer(frame)
                out.write(frame)
            else:
                cv2.imshow(window, frame)
                if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                    break
    finally:
        cv2.destroyAllWindows()
        udp.close()
        tcp.close()
        if args.save:
            out.release()


def write_frame_time(frame, vt):
    height, width, channels = frame.shape
    frame = cv2.putText(
        frame, '%.2f' % vt, (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255)
    )
    return frame


def arg_parse():
    """ analisa e separa os argumentos passados ao iniciar a execucao do cliente """
    parser = argparse.ArgumentParser(description='Client')
    parser.add_argument('--save', default=False, help='Salvar o video', action='store_true')
    parser.add_argument("--ip", help="Endereço IP do cliente", default="localhost")
    parser.add_argument("--port", help="Numero da porta de escuta (UDP)", type=int, default=SERVER_PORT_UDP)
    parser.add_argument("--gray", help="Converte video para escala de cinza", action="store_true")
    parser.add_argument("--show-time", help="Mostra o tempo de vídeo", action="store_true")

    return parser.parse_args()


if __name__ == '__main__':
    """ chama a func que analisa os argumentos e passa os argumentos para o main """
    arguments = arg_parse()
    print("Client.py iniciando a execucao. Argumentos recebidos: ", arguments)
    main(arguments)
