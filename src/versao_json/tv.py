import socket
import struct
import json
import os
import threading

MULTICAST_GROUP = '224.1.1.2'
MULTICAST_PORT = 5007

GATEWAY_IP = ''
GATEWAY_PORT = 0

TV_IP = ''
TV_PORT = 0

HEARTBEAT_PORT=0
GATEWAY_HEARTBEAT_PORT=0

TV_ID = "tv-123"
estado_tv = 'desligado'
canal = 1
volume = 15
tamanho_lista_no_gateway=5

def entrar_no_grupo(sock, grp):
    grupo = socket.inet_aton(grp)
    mreq = struct.pack('4sL', grupo, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

def iniciar_tv():
    global GATEWAY_IP, GATEWAY_PORT,TV_PORT,TV_IP,TV_ID,HEARTBEAT_PORT,GATEWAY_HEARTBEAT_PORT
    # Criando e configurando um socket para o multicast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MULTICAST_PORT))
    entrar_no_grupo(sock, MULTICAST_GROUP)

    #criando e configurando um socket para o ar-condicionado    
    sock_tv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_tv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_tv.bind(('', 0))
    TV_IP, TV_PORT = sock_tv.getsockname()
    TV_IP = socket.gethostbyname(socket.gethostname())

    #criando e configurando um socket para o heartbeat
    sock_heartbeat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_heartbeat.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_heartbeat.bind(('', 0))
    AC_IP,HEARTBEAT_PORT=sock_heartbeat.getsockname()
    AC_IP = socket.gethostbyname(socket.gethostname())
     
    ouvindo_multicast(sock)
    
    t_ouvir_heartbeat = threading.Thread(target= ouvindo_heartbeat,args=(sock_heartbeat,sock))
    t_ouvir_heartbeat.start()
    
    aguardando_comandos(sock_tv)

    t_ouvir_heartbeat.join()

    
    aguardando_comandos(sock_tv)

def ouvindo_heartbeat(sock_heartbeat,sock):
    global GATEWAY_IP, GATEWAY_PORT,TV_PORT,TV_IP,TV_ID,HEARTBEAT_PORT,GATEWAY_HEARTBEAT_PORT,tamanho_lista_no_gateway
    while True:
            try:
                sock_heartbeat.settimeout(tamanho_lista_no_gateway)
                dados, endereco = sock_heartbeat.recvfrom(1024)
                mensagem_json = json.loads(dados.decode('utf-8'))
                
                if mensagem_json.get("comando") == "heartbeat":
                    tamanho_lista_no_gateway=5 + ( 5 * ( int(mensagem_json.get("tamanho_lista")) ) )
                    resposta_json = {"tipo":"heartbeat","heartbeat_port":f"{HEARTBEAT_PORT}"}
                    GATEWAY_HEARTBEAT_PORT=int(GATEWAY_HEARTBEAT_PORT)
                    sock_heartbeat.sendto(json.dumps(resposta_json).encode('utf-8'), (GATEWAY_IP,GATEWAY_HEARTBEAT_PORT))

            except TimeoutError:
                    ouvindo_multicast(sock)

def ouvindo_multicast(sock):
    global GATEWAY_IP, GATEWAY_PORT,TV_PORT,TV_IP,TV_ID,HEARTBEAT_PORT,GATEWAY_HEARTBEAT_PORT,tamanho_lista_no_gateway
    print(f"Tv {TV_ID} escutando no endereço multicast {MULTICAST_GROUP}:{MULTICAST_PORT}")
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
                "heartbeat_port":f"{HEARTBEAT_PORT}",
                "funcionalidades": [
                    {"nome": "ligar/desligar", "parametros": []},
                    {"nome": "mudar canal", "parametros": [{"nome": "canal", "tipo": "inteiro"}]},
                    {"nome": "ajustar volume", "parametros": [{"nome": "volume", "tipo": "inteiro"}]}
                ]
            }
            endereco_completo_do_gateway = mensagem_json.get("enderecoGateway")
            GATEWAY_IP, GATEWAY_PORT = endereco_completo_do_gateway
            GATEWAY_PORT = int(GATEWAY_PORT)
            GATEWAY_HEARTBEAT_PORT=mensagem_json.get("gateway_heartbeat_port")
            sock.sendto(json.dumps(resposta_json).encode('utf-8'), (GATEWAY_IP, GATEWAY_PORT))
            print(f"Respondendo ao gateway {endereco_completo_do_gateway}")
            break

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

#funcionalidades da tv

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

if __name__ == "__main__":
    print("Digite o nome da TV:")
    TV_ID = input()
    iniciar_tv()