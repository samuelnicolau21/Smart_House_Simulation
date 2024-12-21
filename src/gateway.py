import socket
import json
import threading
import os
import time


MULTICAST_GROUP = '224.1.1.1'
MULTICAST_PORT = 5007
IP_GATEWAY='192.168.1.2'
PORT=5008



#classe para guardar informações de cada dispositivo no grupo 
class Dispositivo:
    nome=''
    id=''
    ip=''
    porta=0;
    funcionalidades=""
    
    def __init__(self, nome_dispo, id_dispo, ip_dispo, porta_dispo, funcionalidades_dipo):
        self.nome=nome_dispo
        self.id=id_dispo
        self.ip=ip_dispo
        self.porta=porta_dispo
        self.funcionalidades=funcionalidades_dipo
    
#lista de objetos do tipo dispositivo
dispositivos=[]

def mostrar_lista():
    print("\n\n\n-------------------------------------------------------------------------------------")
    for dispositivo in dispositivos:
        print(f"Nome: {dispositivo.nome}, ID: {dispositivo.id} IP: {dispositivo.ip}, Porta: {dispositivo.porta}, Funcionalidades: {dispositivo.funcionalidades}")
    print("-------------------------------------------------------------------------------------\n\n\n")

def listar_dispositivos():
    i=1
    for dispositivo in dispositivos:
        print(f"{i}:{dispositivo.nome}\n")
        i=i+1
        
def listar_funcionalidades(funcionalidades):
    i=1
    for funcionalidade in funcionalidades:
        print(f"{i}: {funcionalidade}")
        i=i+1

def enviar_multicast(sock):
    mensagem_json = {
        "comando": "descobrir",
        "enderecoGateway":[f"{IP_GATEWAY}",f"{PORT}"],
    }
    sock.sendto(json.dumps(mensagem_json).encode('utf-8'), (MULTICAST_GROUP, MULTICAST_PORT))
    print(f"Mensagem de descoberta enviada para {MULTICAST_GROUP}:{MULTICAST_PORT}")

def adcionar_novos_dispositivos(sock_gateway,sock_multicast):
   
    print(f"Gateway escutando respostas no endereço {IP_GATEWAY}:{PORT}")
    while True:
        print("enviando multicast")
        time.sleep(3)
        enviar_multicast(sock_multicast)
        dados, endereco = sock_gateway.recvfrom(1024)
        r_json = json.loads(dados.decode('utf-8'))
        print(f"Resposta recebida de {endereco}: {r_json}")
        ip,porta=r_json.get("endereco")
        dispositivos.append( Dispositivo(r_json.get("nome"),r_json.get("id"),ip,porta,r_json.get("funcionalidades")) )


def enviar_comandos_para_dispositivos():
    while True:
        print("escolha o dispositivo que deseja utilizar:\n")
        listar_dispositivos()
        print("\n")
        x=input()
        x=int(x)
        listar_funcionalidades(dispositivos[x-1].funcionalidades)
        input()
        os.system('cls')
        
def iniciar_gateway():
    # Criar o socket UDP
    sock_multicast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_multicast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_multicast.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock_multicast.bind(('', MULTICAST_PORT))
    
    sock_gateway = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_gateway.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_gateway.bind(('', PORT))
    
    
    t_adc_dispositivos = threading.Thread(target= adcionar_novos_dispositivos,args=(sock_gateway,sock_multicast))
    t_adc_dispositivos.start()
    
    """
    while True:
        dados, endereco = sock_gateway.recvfrom(1024)
        r_json = json.loads(dados.decode('utf-8'))
        print(f"Resposta recebida de {endereco}: {r_json}")
        ip,porta=r_json.get("endereco")
        dispositivos.append( Dispositivo(r_json.get("nome"),r_json.get("id"),ip,porta,r_json.get("funcionalidades")) )
    """
    time.sleep(10)
    enviar_comandos_para_dispositivos()
    
    t_adc_dispositivos.join()

if __name__ == "__main__":
    iniciar_gateway()