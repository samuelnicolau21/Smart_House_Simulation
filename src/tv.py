import socket
import struct
import json
import os

MULTICAST_GROUP = '224.1.1.2'
MULTICAST_PORT = 5007

GATEWAY_IP = ''
GATEWAY_PORT = 0

TV_IP = ''
TV_PORT = 0

TV_ID = "tv-123"
estado_tv = 'desligado'
canal = 1
volume = 15

def entrar_no_grupo(sock, grp):
    grupo = socket.inet_aton(grp)
    mreq = struct.pack('4sL', grupo, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

def iniciar_tv():
    global GATEWAY_IP, GATEWAY_PORT
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MULTICAST_PORT))
    entrar_no_grupo(sock, MULTICAST_GROUP)
    
    sock_tv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_tv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_tv.bind(('', 0))
    
    global TV_IP, TV_PORT
    TV_IP, TV_PORT = sock_tv.getsockname()
    TV_IP = socket.gethostbyname(socket.gethostname())
    
    print(f"TV {TV_ID} escutando no endereço multicast {MULTICAST_GROUP}:{MULTICAST_PORT}")

    while True:
        dados, endereco = sock.recvfrom(1024)
        mensagem_json = json.loads(dados.decode('utf-8'))
        
        print(f"Mensagem recebida de {endereco}: {mensagem_json}")
        if mensagem_json.get("comando") == "descobrir":
            resposta_json = {
                "tipo": "descoberta",
                "nome": "tv",
                "id": TV_ID,
                "status": "pronto",
                "endereco": [f"{TV_IP}", f"{TV_PORT}"],
                "funcionalidades": [
                    {"nome": "ligar/desligar", "parametros": []},
                    {"nome": "mudar canal", "parametros": [{"nome": "canal", "tipo": "inteiro"}]},
                    {"nome": "ajustar volume", "parametros": [{"nome": "volume", "tipo": "inteiro"}]}
                ]
            }
            endereco_completo_do_gateway = mensagem_json.get("enderecoGateway")
            GATEWAY_IP, GATEWAY_PORT = endereco_completo_do_gateway
            GATEWAY_PORT = int(GATEWAY_PORT)
            sock.sendto(json.dumps(resposta_json).encode('utf-8'), (GATEWAY_IP, GATEWAY_PORT))
            print(f"Respondendo ao gateway {endereco_completo_do_gateway}")
            break
    
    aguardando_comandos(sock_tv)

def aguardando_comandos(sock_tv):
    global GATEWAY_IP, GATEWAY_PORT, TV_ID, estado_tv, canal, volume
    while True:
        dados, endereco = sock_tv.recvfrom(1024)
        mensagem_json = json.loads(dados.decode('utf-8'))
        
        print(f"Mensagem recebida de {endereco}: {mensagem_json}")
        
        if mensagem_json.get("comando") == "ligar/desligar":
            os.system("cls")
            ligar_desligar()
            mostrar_status()
            enviar_status(sock_tv)
        elif mensagem_json.get("comando") == "mudar canal":
            os.system("cls")
            mudar_canal(int(mensagem_json.get("parametros")[0]))
            mostrar_status()
            enviar_status(sock_tv)
        elif mensagem_json.get("comando") == "ajustar volume":
            os.system("cls")
            ajustar_volume(int(mensagem_json.get("parametros")[0]))
            mostrar_status()
            enviar_status(sock_tv)
        elif mensagem_json.get("comando") == "status":
            os.system("cls")
            mostrar_status()
            enviar_status(sock_tv)
        elif mensagem_json.get("comando") == "renomear":
            os.system("cls")
            TV_ID = mensagem_json.get("novo_id")
            mostrar_status()
            enviar_status(sock_tv)

def ligar_desligar():
    global estado_tv
    estado_tv = 'ligado' if estado_tv == 'desligado' else 'desligado'

def mudar_canal(novo_canal):
    global canal
    if novo_canal > 0:
        canal = novo_canal
    else:
        print("Número de canal inválido.")

def ajustar_volume(novo_volume):
    global volume
    if 0 <= novo_volume <= 100:
        volume = novo_volume
    else:
        print("Volume fora do intervalo permitido (0-100).")

def enviar_status(sock_tv):
    global estado_tv, canal, volume, GATEWAY_IP, GATEWAY_PORT
    resposta_json = {
        "status": [
            {"tipo": "atualização"}, {"nome": "TV"},
            {"id": TV_ID}, {"estado": estado_tv},
            {"canal": canal}, {"volume": volume}
        ]
    }
    sock_tv.sendto(json.dumps(resposta_json).encode('utf-8'), (GATEWAY_IP, GATEWAY_PORT))
    print(f"Atualizando o status da TV para o gateway")

def mostrar_status():
    global TV_ID, estado_tv, canal, volume
    print(f"id: {TV_ID}")
    print(f"estado: {estado_tv}")
    print(f"canal: {canal}")
    print(f"volume: {volume}")

if _name_ == "_main_":
    print("Digite o nome da TV:")
    TV_ID = input()
    iniciar_tv()