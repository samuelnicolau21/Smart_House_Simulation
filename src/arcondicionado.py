import socket
import struct
import json
import os
import threading

MULTICAST_GROUP = '224.1.1.2'
MULTICAST_PORT = 5007

GATEWAY_IP = ''
GATEWAY_PORT = 0

AC_IP = ''
AC_PORT = 0

HEARTBEAT_PORT=0
GATEWAY_HEARTBEAT_PORT=0

AC_ID = "arcondicionado-123"
estado_ac = 'desligado'
temperatura = 24
modo = 'resfriar'  # Modos possíveis: resfriar, aquecer, ventilar
tamanho_lista_no_gateway=5

def entrar_no_grupo(sock, grp):
    grupo = socket.inet_aton(grp)
    mreq = struct.pack('4sL', grupo, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

def iniciar_ac():
    global GATEWAY_IP, GATEWAY_PORT,AC_PORT,AC_IP,AC_ID,HEARTBEAT_PORT,GATEWAY_HEARTBEAT_PORT
    # Criando e configurando um socket para o multicast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MULTICAST_PORT))
    entrar_no_grupo(sock, MULTICAST_GROUP)
    
    #criando e configurando um socket para o ar-condicionado
    sock_ac = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_ac.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_ac.bind(('', 0))
    AC_IP, AC_PORT = sock_ac.getsockname()
    AC_IP = socket.gethostbyname(socket.gethostname())
    
    #criando e configurando um socket para o heartbeat
    sock_heartbeat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_heartbeat.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_heartbeat.bind(('', 0))
    AC_IP,HEARTBEAT_PORT=sock_heartbeat.getsockname()
    AC_IP = socket.gethostbyname(socket.gethostname())
    
    ouvindo_multicast(sock)
    
    t_ouvir_heartbeat = threading.Thread(target= ouvindo_heartbeat,args=(sock_heartbeat,sock))
    t_ouvir_heartbeat.start()
    
    aguardando_comandos(sock_ac)

    t_ouvir_heartbeat.join()
    
def ouvindo_heartbeat(sock_heartbeat,sock):
    global GATEWAY_IP, GATEWAY_PORT,AC_PORT,AC_IP,AC_ID,HEARTBEAT_PORT,GATEWAY_HEARTBEAT_PORT,tamanho_lista_no_gateway   
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
    global GATEWAY_IP, GATEWAY_PORT,AC_PORT,AC_IP,AC_ID,HEARTBEAT_PORT,GATEWAY_HEARTBEAT_PORT,MULTICAST_PORT,MULTICAST_GROUP
    print(f"Ar-condicionado {AC_ID} escutando no endereço multicast {MULTICAST_GROUP}:{MULTICAST_PORT}")
    while True:
        dados, endereco = sock.recvfrom(1024)
        mensagem_json = json.loads(dados.decode('utf-8'))
        print(f"Mensagem recebida de {endereco}: {mensagem_json}")
        if mensagem_json.get("comando") == "descobrir":
            resposta_json = {"tipo": "descoberta","nome": "ar-condicionado","id": AC_ID,"status": "pronto","endereco": [f"{AC_IP}", f"{AC_PORT}"],"heartbeat_port":f"{HEARTBEAT_PORT}","funcionalidades": [{"nome": "ligar/desligar", "parametros": []},{"nome": "temperatura", "parametros": [{"nome": "valor", "tipo": "inteiro"}]},{"nome": "modo", "parametros": [{"nome": "modo de operação", "tipo": "resfriar,aquecer,ventilar"}]}]}
            endereco_completo_do_gateway = mensagem_json.get("enderecoGateway")
            GATEWAY_IP, GATEWAY_PORT = endereco_completo_do_gateway
            GATEWAY_PORT = int(GATEWAY_PORT)
            GATEWAY_HEARTBEAT_PORT=mensagem_json.get("gateway_heartbeat_port")
            sock.sendto(json.dumps(resposta_json).encode('utf-8'), (GATEWAY_IP, GATEWAY_PORT))
            print(f"Respondendo ao gateway {endereco_completo_do_gateway}")
            break

def aguardando_comandos(sock_ac):
    global GATEWAY_IP, GATEWAY_PORT, AC_ID, estado_ac, temperatura, modo
    while True:
        dados, endereco = sock_ac.recvfrom(1024)
        mensagem_json = json.loads(dados.decode('utf-8'))
        print(f"Mensagem recebida de {endereco}: {mensagem_json}")
        
        if mensagem_json.get("comando") == "ligar/desligar":
            os.system("cls")
            ligar_desligar()
            mostrar_status()
            enviar_status(sock_ac)
        elif mensagem_json.get("comando") == "temperatura":
            os.system("cls")
            ajustar_temperatura(int(mensagem_json.get("parametros")[0]))
            mostrar_status()
            enviar_status(sock_ac)
        elif mensagem_json.get("comando") == "modo":
            os.system("cls")
            mudar_modo(mensagem_json.get("parametros")[0])
            mostrar_status()
            enviar_status(sock_ac)
        elif mensagem_json.get("comando") == "status":
            os.system("cls")
            mostrar_status()
            enviar_status(sock_ac)
        elif mensagem_json.get("comando") == "renomear":
            os.system("cls")
            AC_ID=mensagem_json.get("novo_id")
            mostrar_status()
            enviar_status(sock_ac)

#funcionalidades do arcondicionado
def ligar_desligar():
    global estado_ac
    estado_ac = 'ligado' if estado_ac == 'desligado' else 'desligado'

def ajustar_temperatura(valor):
    global temperatura
    if 16 <= valor <= 30:
        temperatura = valor
    else:
        print("Temperatura fora do intervalo permitido (16-30).")

def mudar_modo(novo_modo):
    global modo
    if novo_modo in ['resfriar', 'aquecer', 'ventilar']:
        modo = novo_modo
    else:
        print("Modo inválido.")

def enviar_status(sock_ac):
    global estado_ac, temperatura, modo,GATEWAY_IP,GATEWAY_PORT
    resposta_json = {
        "status": [
            {"tipo":"atualização"},{"nome":"Ar-condicionado"},
            {"id": AC_ID},{"estado": estado_ac},{"temperatura": temperatura},
            {"modo": modo}]
        }
            
    sock_ac.sendto(json.dumps(resposta_json).encode('utf-8'), (GATEWAY_IP, GATEWAY_PORT))
    print(f"Atualizando o status do ar-condicionado para o gateway")

def mostrar_status():
    global LAMP_ID,estado_da_lampada,cor_da_lampada,luminosidade
    print(f"id:{AC_ID}")
    print(f"estado:{estado_ac}")
    print(f"temperatura:{temperatura}")
    print(f"modo:{modo}")

if __name__ == "__main__":
    print("Digite o nome do ar-condicionado:")
    AC_ID = input()
    iniciar_ac()
