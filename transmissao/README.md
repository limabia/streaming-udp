
# Execução

Execução da transmissão UDP de um determinado video.


## - Cliente: 
    1. Dentro da pasta "transmissão" execute: `$ python3 server.py`
  - `--save` - Para salvar o vídeo no cliente
  - `--ip IP` - Endereço IP do cliente
  - `--port PORTA` - Porta de escuta do UDP
  - `--gray` - Transforma o vídeo em escala de cinza
  - `Ctrl+C` - Finalizar a transmissão
  - `--show-time` - Exibe na tela o tempo do video 
  
## - Servidor: 
    1. Dentro da pasta "transmissão" execute: `$python3 client.py` 
  - `--video` - Raiz de arquivos a ser utilizada para buscar os vídeos
  - `--fps FPS` - Definicao de frames por segundo para a transmissão
  - `--port PORT` - Número da porta TCP do servidor
  - `--ip IP` - Endereço de IP do servidor
  - `Ctrl+C` para finalizar a transmissão
