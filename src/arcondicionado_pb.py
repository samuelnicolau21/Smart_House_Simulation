import socket
import struct
import json
import os
import threading
import random
import time
import mensagens_pb2

MULTICAST_GROUP = '224.1.1.5'
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
temperatura_do_ambiente= 24 
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
    t_oscilar_temperatura = threading.Thread(target= oscilar_temperatura)
    t_oscilar_temperatura.start()
    
    aguardando_comandos(sock_ac)

    t_ouvir_heartbeat.join()
    t_oscilar_temperatura.join()
    
def ouvindo_heartbeat(sock_heartbeat,sock):
    global GATEWAY_IP, GATEWAY_PORT,AC_PORT,AC_IP,AC_ID,HEARTBEAT_PORT,GATEWAY_HEARTBEAT_PORT,tamanho_lista_no_gateway   
    while True:
        try:
            sock_heartbeat.settimeout(tamanho_lista_no_gateway)
            dados, endereco = sock_heartbeat.recvfrom(1024)
            heartbeat=mensagens_pb2.GatewayHB()
            heartbeat.ParseFromString(dados)
            
            if heartbeat.comando == "heartbeat":
                tamanho_lista_no_gateway=5 + (5*( int(heartbeat.tamanho_lista) )  )  
                heartbeat=mensagens_pb2.DispositivoHB()
                heartbeat.tipo="heartbeat"
                heartbeat.heartbeat_port=f"{HEARTBEAT_PORT}"
                GATEWAY_HEARTBEAT_PORT=int(GATEWAY_HEARTBEAT_PORT)
                sock_heartbeat.sendto(heartbeat.SerializeToString(), (GATEWAY_IP,GATEWAY_HEARTBEAT_PORT))

        except TimeoutError:
                ouvindo_multicast(sock)
                        
def ouvindo_multicast(sock):
    global GATEWAY_IP, GATEWAY_PORT,AC_PORT,AC_IP,AC_ID,HEARTBEAT_PORT,GATEWAY_HEARTBEAT_PORT,MULTICAST_PORT,MULTICAST_GROUP
    print(f"Ar-condicionado {AC_ID} escutando no endereço multicast {MULTICAST_GROUP}:{MULTICAST_PORT}")
    while True:
            dados, endereco = sock.recvfrom(1024) 
            mensagem=mensagens_pb2.GatewayM()
            mensagem.ParseFromString(dados)
            
            print(f"Mensagem recebida de {endereco}: {mensagem}")
            if mensagem.comando == "descobrir":
                # Criar o objeto Lampada e preencher os atributos
                resposta = mensagens_pb2.DispositivoR()
                resposta.tipo = "descoberta"
                resposta.nome = "ar-condicionado"
                resposta.id = f"{AC_ID}" 
                resposta.status = "pronto"
                resposta.endereco.extend([f"{AC_IP}", f"{AC_PORT}"])  
                resposta.heartbeat_port = f"{HEARTBEAT_PORT}"  
                funcionalidade1 = resposta.funcionalidades.add()
                funcionalidade1.nome = "ligar/desligar"
        
                funcionalidade2 = resposta.funcionalidades.add()
                funcionalidade2.nome = "temperatura"
                parametro2 = funcionalidade2.parametros.add()
                parametro2.nome = "valor da temperatura"
                parametro2.tipo = "int"
                
                funcionalidade3 = resposta.funcionalidades.add()
                funcionalidade3.nome = "modo"
                parametro3 = funcionalidade3.parametros.add()
                parametro3.nome = "modo de funcionamento"
                parametro3.tipo = "resfriar, aquecer, ventilar"
                
                endereco_completo_do_gateway=mensagem.enderecoGateway
                GATEWAY_IP, GATEWAY_PORT = endereco_completo_do_gateway
                GATEWAY_PORT = int(GATEWAY_PORT)
                GATEWAY_HEARTBEAT_PORT=mensagem.gateway_heartbeat_port
                sock.sendto(resposta.SerializeToString(), (GATEWAY_IP,GATEWAY_PORT))
                print(f"Respondendo ao gateway {endereco_completo_do_gateway}")
                break

def aguardando_comandos(sock_ac):
    global GATEWAY_IP, GATEWAY_PORT, AC_ID, estado_ac, temperatura, modo
    while True:
        dados, endereco = sock_ac.recvfrom(1024)
        comando=mensagens_pb2.ClienteC()
        comando.ParseFromString(dados)
        mensagem_json = ""
        #print(f"Mensagem recebida de {endereco}: {mensagem_json}")
        
        if comando.comando == "ligar/desligar":
            os.system("cls")
            ligar_desligar()
            mostrar_status()
            status=mensagens_pb2.DispositivoS()
            
            status1=status.status.add()
            status1.nomeDoStatus="tipo"
            status1.valorDoStatus="atualização"
            
            status2=status.status.add()
            status2.nomeDoStatus="nome"
            status2.valorDoStatus="ar-condicionado"
            
            status3=status.status.add()
            status3.nomeDoStatus="id"
            status3.valorDoStatus=f"{AC_ID}"
            
            status4=status.status.add()
            status4.nomeDoStatus="estado da ar-condicionado"
            status4.valorDoStatus=f"{estado_ac}"
            
            status5=status.status.add()
            status5.nomeDoStatus="temperatura"
            status5.valorDoStatus=f"{temperatura}"
            
            status6=status.status.add()
            status6.nomeDoStatus="modo ar-condicionado"
            status6.valorDoStatus=f"{modo}"

            status6=status.status.add()
            status6.nomeDoStatus="temp ambiente"
            status6.valorDoStatus=f"{temperatura_do_ambiente}"

            
            sock_ac.sendto(status.SerializeToString(), (GATEWAY_IP,GATEWAY_PORT))
            print(f"Atualizando o status da lampada para o gateway")


        elif comando.comando=="temperatura":
            os.system("cls")
            param=comando.parametrosEscolhidos[0]
            ajustar_temperatura(int(param))
            mostrar_status()
            status=mensagens_pb2.DispositivoS()

            status1=status.status.add()
            status1.nomeDoStatus="tipo"
            status1.valorDoStatus="atualização"
            
            status2=status.status.add()
            status2.nomeDoStatus="nome"
            status2.valorDoStatus="ar-condicionado"
            
            status3=status.status.add()
            status3.nomeDoStatus="id"
            status3.valorDoStatus=f"{AC_ID}"
            
            status4=status.status.add()
            status4.nomeDoStatus="estado da ar-condicionado"
            status4.valorDoStatus=f"{estado_ac}"
            
            status5=status.status.add()
            status5.nomeDoStatus="temperatura"
            status5.valorDoStatus=f"{temperatura}"
            
            status6=status.status.add()
            status6.nomeDoStatus="modo ar-condicionado"
            status6.valorDoStatus=f"{modo}"

            status6=status.status.add()
            status6.nomeDoStatus="temp ambiente"
            status6.valorDoStatus=f"{temperatura_do_ambiente}"

            
            sock_ac.sendto(status.SerializeToString(), (GATEWAY_IP,GATEWAY_PORT))
            print(f"Atualizando o status da lampada para o gateway")
            
        elif comando.comando=="modo":
            os.system("cls")
            mudar_modo(comando.parametrosEscolhidos[0])
            mostrar_status()
            status=mensagens_pb2.DispositivoS()

            status1=status.status.add()
            status1.nomeDoStatus="tipo"
            status1.valorDoStatus="atualização"
            
            status2=status.status.add()
            status2.nomeDoStatus="nome"
            status2.valorDoStatus="ar-condicionado"
            
            status3=status.status.add()
            status3.nomeDoStatus="id"
            status3.valorDoStatus=f"{AC_ID}"
            
            status4=status.status.add()
            status4.nomeDoStatus="estado da ar-condicionado"
            status4.valorDoStatus=f"{estado_ac}"
            
            status5=status.status.add()
            status5.nomeDoStatus="temperatura"
            status5.valorDoStatus=f"{temperatura}"
            
            status6=status.status.add()
            status6.nomeDoStatus="modo ar-condicionado"
            status6.valorDoStatus=f"{modo}"

            status6=status.status.add()
            status6.nomeDoStatus="temp ambiente"
            status6.valorDoStatus=f"{temperatura_do_ambiente}"

            
            sock_ac.sendto(status.SerializeToString(), (GATEWAY_IP,GATEWAY_PORT))
            print(f"Atualizando o status da lampada para o gateway")

        elif comando.comando=="status":
            os.system("cls")
            mostrar_status()
            status=mensagens_pb2.DispositivoS()

            status1=status.status.add()
            status1.nomeDoStatus="tipo"
            status1.valorDoStatus="atualização"
            
            status2=status.status.add()
            status2.nomeDoStatus="nome"
            status2.valorDoStatus="ar-condicionado"
            
            status3=status.status.add()
            status3.nomeDoStatus="id"
            status3.valorDoStatus=f"{AC_ID}"
            
            status4=status.status.add()
            status4.nomeDoStatus="estado da ar-condicionado"
            status4.valorDoStatus=f"{estado_ac}"
            
            status5=status.status.add()
            status5.nomeDoStatus="temperatura"
            status5.valorDoStatus=f"{temperatura}"
            
            status6=status.status.add()
            status6.nomeDoStatus="modo ar-condicionado"
            status6.valorDoStatus=f"{modo}"

            status6=status.status.add()
            status6.nomeDoStatus="temp ambiente"
            status6.valorDoStatus=f"{temperatura_do_ambiente}"

            
            sock_ac.sendto(status.SerializeToString(), (GATEWAY_IP,GATEWAY_PORT))
            print(f"Atualizando o status da lampada para o gateway")


        elif comando.comando=="renomear":
            os.system("cls")
            AC_ID=comando.novo_id
            mostrar_status()
            status=mensagens_pb2.DispositivoS()

            status1=status.status.add()
            status1.nomeDoStatus="tipo"
            status1.valorDoStatus="atualização"
            
            status2=status.status.add()
            status2.nomeDoStatus="nome"
            status2.valorDoStatus="ar-condicionado"
            
            status3=status.status.add()
            status3.nomeDoStatus="id"
            status3.valorDoStatus=f"{AC_ID}"
            
            status4=status.status.add()
            status4.nomeDoStatus="estado da ar-condicionado"
            status4.valorDoStatus=f"{estado_ac}"
            
            status5=status.status.add()
            status5.nomeDoStatus="temperatura"
            status5.valorDoStatus=f"{temperatura}"
            
            status6=status.status.add()
            status6.nomeDoStatus="modo ar-condicionado"
            status6.valorDoStatus=f"{modo}"

            status6=status.status.add()
            status6.nomeDoStatus="temp ambiente"
            status6.valorDoStatus=f"{temperatura_do_ambiente}"

            
            sock_ac.sendto(status.SerializeToString(), (GATEWAY_IP,GATEWAY_PORT))
            print(f"Atualizando o status da lampada para o gateway")

#funcionalidades do arcondicionado
def ligar_desligar():
    global estado_ac,temperatura_do_ambiente
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
            {"modo": modo},{"temperatura do ambiente":temperatura_do_ambiente}]
        }
            
    sock_ac.sendto(json.dumps(resposta_json).encode('utf-8'), (GATEWAY_IP, GATEWAY_PORT))
    print(f"Atualizando o status do ar-condicionado para o gateway")

def mostrar_status():
    global LAMP_ID,estado_da_lampada,cor_da_lampada,luminosidade
    print(f"id:{AC_ID}")
    print(f"estado:{estado_ac}")
    print(f"temperatura:{temperatura}")
    print(f"modo:{modo}")

def oscilar_temperatura():
    global temperatura, temperatura_do_ambiente
    while True:
        time.sleep(5)
        taxa_de_oscilacao=(temperatura/100)
        taxa_de_oscilacao = random.uniform(0, taxa_de_oscilacao)
        aumentar_diminuir=random.randint(1,2)
        if aumentar_diminuir==1:
            temperatura_do_ambiente=temperatura_do_ambiente-taxa_de_oscilacao
        else:
            temperatura_do_ambiente=temperatura_do_ambiente+taxa_de_oscilacao
    

if __name__ == "__main__":
    print("Digite o nome do ar-condicionado:")
    AC_ID = input()
    iniciar_ac()
