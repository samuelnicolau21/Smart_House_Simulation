import socket
import struct
import json
import os
import threading
import mensagens_pb2

MULTICAST_GROUP = '224.1.1.5'
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
    global GATEWAY_IP, GATEWAY_PORT,TV_PORT,TV_IP,TV_ID,HEARTBEAT_PORT,GATEWAY_HEARTBEAT_PORT,tamanho_lista_no_gateway
    print(f"Tv {TV_ID} escutando no endereço multicast {MULTICAST_GROUP}:{MULTICAST_PORT}")
    while True:
        dados, endereco = sock.recvfrom(1024) 
        mensagem=mensagens_pb2.GatewayM()
        mensagem.ParseFromString(dados)
        
        #print(f"Mensagem recebida de {endereco}: {mensagem}")


        if mensagem.comando == "descobrir":
            # Criar o objeto Lampada e preencher os atributos
            resposta = mensagens_pb2.DispositivoR()
            resposta.tipo = "descoberta"
            resposta.nome = "TV"
            resposta.id = f"{TV_ID}" 
            resposta.status = "pronto"
            resposta.endereco.extend([f"{TV_IP}", f"{TV_PORT}"])  
            resposta.heartbeat_port = f"{HEARTBEAT_PORT}"  
            funcionalidade1 = resposta.funcionalidades.add()
            funcionalidade1.nome = "ligar/desligar"
    
            funcionalidade2 = resposta.funcionalidades.add()
            funcionalidade2.nome = "mudar canal"
            parametro2 = funcionalidade2.parametros.add()
            parametro2.nome = "N do canal"
            parametro2.tipo = "int"
            
            funcionalidade3 = resposta.funcionalidades.add()
            funcionalidade3.nome = "ajustar volume"
            parametro3 = funcionalidade3.parametros.add()
            parametro3.nome = "valor do volume"
            parametro3.tipo = "int"
            
            endereco_completo_do_gateway=mensagem.enderecoGateway
            GATEWAY_IP, GATEWAY_PORT = endereco_completo_do_gateway
            GATEWAY_PORT = int(GATEWAY_PORT)
            GATEWAY_HEARTBEAT_PORT=mensagem.gateway_heartbeat_port
            sock.sendto(resposta.SerializeToString(), (GATEWAY_IP,GATEWAY_PORT))
            print(f"Respondendo ao gateway {endereco_completo_do_gateway}")
            break

def aguardando_comandos(sock_tv):
    global GATEWAY_IP, GATEWAY_PORT, TV_ID, estado_tv, canal, volume
    while True:
        dados, endereco = sock_tv.recvfrom(1024)
        comando=mensagens_pb2.ClienteC()
        comando.ParseFromString(dados)
        
        
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
            status2.valorDoStatus="tv"
            
            status3=status.status.add()
            status3.nomeDoStatus="id"
            status3.valorDoStatus=f"{TV_ID}"
            
            status4=status.status.add()
            status4.nomeDoStatus="estado da tv"
            status4.valorDoStatus=f"{estado_tv}"
            
            status5=status.status.add()
            status5.nomeDoStatus="n do canal"
            status5.valorDoStatus=f"{canal}"
            
            status6=status.status.add()
            status6.nomeDoStatus="valor do volume"
            status6.valorDoStatus=f"{volume}"
            
            sock_tv.sendto(status.SerializeToString(), (GATEWAY_IP,GATEWAY_PORT))
            print(f"Atualizando o status da lampada para o gateway")

        elif comando.comando=="mudar canal":
            os.system("cls")
            param=comando.parametrosEscolhidos[0]
            mudar_canal(int(param))
            mostrar_status()
            status=mensagens_pb2.DispositivoS()

            status1=status.status.add()
            status1.nomeDoStatus="tipo"
            status1.valorDoStatus="atualização"
            
            status2=status.status.add()
            status2.nomeDoStatus="nome"
            status2.valorDoStatus="tv"
            
            status3=status.status.add()
            status3.nomeDoStatus="id"
            status3.valorDoStatus=f"{TV_ID}"
            
            status4=status.status.add()
            status4.nomeDoStatus="estado da tv"
            status4.valorDoStatus=f"{estado_tv}"
            
            status5=status.status.add()
            status5.nomeDoStatus="n do canal"
            status5.valorDoStatus=f"{canal}"
            
            status6=status.status.add()
            status6.nomeDoStatus="valor do volume"
            status6.valorDoStatus=f"{volume}"
            
            sock_tv.sendto(status.SerializeToString(), (GATEWAY_IP,GATEWAY_PORT))
            print(f"Atualizando o status da lampada para o gateway")

        elif comando.comando=="ajustar volume":
            os.system("cls")
            param=comando.parametrosEscolhidos[0]
            ajustar_volume(int(param))
            mostrar_status()

            status=mensagens_pb2.DispositivoS()
            status1=status.status.add()
            status1.nomeDoStatus="tipo"
            status1.valorDoStatus="atualização"
            
            status2=status.status.add()
            status2.nomeDoStatus="nome"
            status2.valorDoStatus="tv"
            
            status3=status.status.add()
            status3.nomeDoStatus="id"
            status3.valorDoStatus=f"{TV_ID}"
            
            status4=status.status.add()
            status4.nomeDoStatus="estado da tv"
            status4.valorDoStatus=f"{estado_tv}"
            
            status5=status.status.add()
            status5.nomeDoStatus="n do canal"
            status5.valorDoStatus=f"{canal}"
            
            status6=status.status.add()
            status6.nomeDoStatus="valor do volume"
            status6.valorDoStatus=f"{volume}"
            
            sock_tv.sendto(status.SerializeToString(), (GATEWAY_IP,GATEWAY_PORT))
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
            status2.valorDoStatus="tv"
            
            status3=status.status.add()
            status3.nomeDoStatus="id"
            status3.valorDoStatus=f"{TV_ID}"
            
            status4=status.status.add()
            status4.nomeDoStatus="estado da tv"
            status4.valorDoStatus=f"{estado_tv}"
            
            status5=status.status.add()
            status5.nomeDoStatus="n do canal"
            status5.valorDoStatus=f"{canal}"
            
            status6=status.status.add()
            status6.nomeDoStatus="valor do volume"
            status6.valorDoStatus=f"{volume}"
            
            sock_tv.sendto(status.SerializeToString(), (GATEWAY_IP,GATEWAY_PORT))
            print(f"Atualizando o status da lampada para o gateway")

        elif comando.comando=="renomear":
            os.system("cls")
            TV_ID = comando.novo_id
            mostrar_status()
            status=mensagens_pb2.DispositivoS()

            status1=status.status.add()
            status1.nomeDoStatus="tipo"
            status1.valorDoStatus="atualização"
            
            status2=status.status.add()
            status2.nomeDoStatus="nome"
            status2.valorDoStatus="tv"
            
            status3=status.status.add()
            status3.nomeDoStatus="id"
            status3.valorDoStatus=f"{TV_ID}"
            
            status4=status.status.add()
            status4.nomeDoStatus="estado da tv"
            status4.valorDoStatus=f"{estado_tv}"
            
            status5=status.status.add()
            status5.nomeDoStatus="n do canal"
            status5.valorDoStatus=f"{canal}"
            
            status6=status.status.add()
            status6.nomeDoStatus="valor do volume"
            status6.valorDoStatus=f"{volume}"
            
            sock_tv.sendto(status.SerializeToString(), (GATEWAY_IP,GATEWAY_PORT))
            print(f"Atualizando o status da lampada para o gateway")

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