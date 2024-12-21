import socket
import struct
import json



MULTICAST_GROUP = '224.1.1.1'
MULTCAST_PORT = 5007

GATEWAY_IP=''
GATEWAY_PORT=0

LAMPADA_IP=''
LAMPADA_PORT=0


LAMP_ID = "lampada-123"
estado_da_lampada='desligado'
cor_da_lampada ='branco'
luminosidade = 50


def entrar_no_grupo(sock, grp):
    grupo = socket.inet_aton(grp)
    mreq = struct.pack('4sL', grupo, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

def iniciar_lampada():
    # Criar o socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MULTCAST_PORT))
    entrar_no_grupo(sock, MULTICAST_GROUP)
    
    sock_lampada = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_lampada.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_lampada.bind(('', 0))
    
    LAMPADA_IP,LAMPADA_PORT=sock_lampada.getsockname()
    LAMPADA_IP = socket.gethostbyname(socket.gethostname())
    
    print(f"Lâmpada {LAMP_ID} escutando no endereço multicast {MULTICAST_GROUP}:{MULTCAST_PORT}")

    while True:
        dados, endereco = sock.recvfrom(1024)
        mensagem_json = json.loads(dados.decode('utf-8'))
        
        print(f"Mensagem recebida de {endereco}: {mensagem_json}")
        if mensagem_json.get("comando") == "descobrir":
            resposta_json = {
                "nome":"lampada",
                "id": LAMP_ID,
                "status": "pronto",
                "funcionalidades": ["ligar/desligar", "brilho", "cor"],
                "endereco":[f"{LAMPADA_IP}",f"{LAMPADA_PORT}"]
            }
            endereco_completo_do_gateway=mensagem_json.get("enderecoGateway")
            GATEWAY_IP, GATEWAY_PORT = endereco_completo_do_gateway
            GATEWAY_PORT = int(GATEWAY_PORT)
            sock.sendto(json.dumps(resposta_json).encode('utf-8'), (GATEWAY_IP,GATEWAY_PORT))
            print(f"Respondendo ao gateway {endereco_completo_do_gateway}")
            break
    
    aguardando_comandos(sock_lampada)      
            
            
def ligar_desligar():
    if estado_da_lampada == 'desligado':
        estado_da_lampada='ligado'
    else:
        estado_da_lampada = 'desligado'

def brilho(valor):
    if valor>=0 and valor<=100:
        luminosidade = valor
    else:
        print("o valor de brilho não é válido")

def cor(cor_escolhida):
    cor=cor_escolhida;
 
def aguardando_comandos(sock_lampada):

    
    while True:
        dados, endereco = sock_lampada.recvfrom(1024)
        mensagem_json = json.loads(dados.decode('utf-8'))
        
        print(f"Mensagem recebida de {endereco}: {mensagem_json}")
        if mensagem_json.get("comando") == "ligar/desligar":
            ligar_desligar()
            resposta_json = {
                "estado da lampada": f"{estado_da_lampada}",
                "cor da lampada": f"{cor_da_lampada}",
                "luminosidade": luminosidade
            }
            
            sock_lampada.sendto(json.dumps(resposta_json).encode('utf-8'), (GATEWAY_IP,GATEWAY_PORT))
            print(f"Atualizando o status da lampada para o gateway")
        break


if __name__ == "__main__":
    print("digite o nome da lampada:\n")
    LAMP_ID=input()
    iniciar_lampada()
    
