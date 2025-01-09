import socket
import json
import threading
import os
import time
import mensagens_pb2



MULTICAST_GROUP = '224.1.1.5' #IP usado para onde as mensagens do multicast vão 
MULTICAST_PORT = 5007 # porta usada para enviar as mensagens do multicast (UDP)

GATEWAY_IP='192.168.223.216' #ip do gateway para onde os dispositivos e clientes miram
GATEWAY_PORT=5008 #porta para onde os dispositivos enviam suas mensagens que não são heartbeat (UDP)

GATEWAY_CLIENT_PORT=5010 # porta para onde o cliente envia mensagens para o gateway (TCP)

CLIENT_IP='' #ip do cliente que é preenchido em tempo de execução
CLIENT_PORT=0 #porta do cliente que também é preencida em tempo de execução (é para cá que o gateway envia mensagens para o cliente)(TCP)

GATEWAY_HEARTBEAT_PORT=5011 #porta para onde os dispositivos enviam as mensagens de heartbeat (UDP)

thread_pausada=False
lock = threading.Lock()
#classe para guardar informações de cada dispositivo no grupo 
class Dispositivo:
    nome=''
    id=''
    ip=''
    porta='';
    funcionalidades=""
    heartbeat_port=0
    heartbeat=0
    def __init__(self, nome_dispo, id_dispo, ip_dispo, porta_dispo, funcionalidades_dipo, hb_port):
        self.nome=nome_dispo
        self.id=id_dispo
        self.ip=ip_dispo
        self.porta=porta_dispo
        self.funcionalidades=funcionalidades_dipo
        self.heartbeat_port=hb_port
    
class Dispositivos:
    dispositivos=[]
    def __init__(self):
        self.dispositivos=[]
    def mostrar_lista_completa(self):
        print("\n\n\n-------------------------------------------------------------------------------------")
        for dispositivo in ldd.dispositivos:
            print(f"Nome: {dispositivo.nome}, ID: {dispositivo.id} IP: {dispositivo.ip}, Porta: {dispositivo.porta}, Funcionalidades: {dispositivo.funcionalidades}")
        print("-------------------------------------------------------------------------------------\n\n\n")
    def listar_dispositivos(self):
        i=1
        for dispositivo in self.dispositivos:
            print(f"{i}) {dispositivo.nome}-{dispositivo.id}\n")
            i=i+1
    def listar_funcionalidades(self,funcionalidades):
        i=1
        for funcionalidade in funcionalidades:
            print(f"{i}: {funcionalidade}")
            i=i+1
    def retorna_id(self,ip,porta):
        i=0
        for i in range(len(self.dispositivos)):
            if (self.dispositivos[i].ip==ip and self.dispositivos[i].porta==str(porta)):
                return self.dispositivos[i].id
    def lista_nome_id_dos_dispositivos(self):
        tam = len(self.dispositivos)
        dicionario = []  # Inicializa a lista de dicionários
        for i in range(tam):
            # Adiciona um novo dicionário à lista
            dicionario.append({"nome": self.dispositivos[i].nome,"id": self.dispositivos[i].id})
        return dicionario

    def lista_de_funcionalidades_e_seus_parametros(self,nome_do_dispositivo_escolhido,id_do_dispositivo_escolhido):
        nome=nome_do_dispositivo_escolhido
        id=id_do_dispositivo_escolhido
        tam=len(self.dispositivos)
    
        dicionario=[]
        i=0
        for i in range(tam):
            if (nome==self.dispositivos[i].nome and id==self.dispositivos[i].id):
                    tam_2=len(self.dispositivos[i].funcionalidades)
                    j=0
                    for j in range(tam_2):
                        dicionario.append({"nome": self.dispositivos[i].funcionalidades[j].nome,"parametros":self.dispositivos[i].funcionalidades[j].parametros})       
        return dicionario
    def ip_e_porta(self,nome,id_):
        tam=len(self.dispositivos)
        i=0
        for i in range(tam):
            if (nome==self.dispositivos[i].nome and id_==self.dispositivos[i].id):
                return self.dispositivos[i].ip,self.dispositivos[i].porta
    def atualizar_id_dispositivo_gateway(self, nome, id_original, novo_id):
        tam=len(self.dispositivos)
        i=0
        for i in range(tam):  
            if (self.dispositivos[i].nome==nome and self.dispositivos[i].id==id_original):
                    self.dispositivos[i].id=novo_id
    def aumentar_heartbeat(self,heartbeat_proto):
        tam=len(self.dispositivos)
        i=0
        for i in range(tam):
            if self.dispositivos[i].heartbeat_port==heartbeat_proto.heartbeat_port:
                self.dispositivos[i].heartbeat=self.dispositivos[i].heartbeat+1
    def diminuir_heartbeat(self):
        tam=len(self.dispositivos)
        i=0
        for i in range(tam):
            self.dispositivos[i].heartbeat=self.dispositivos[i].heartbeat-1
            #print("Diminuindo o heartbeat")
            if self.dispositivos[i].heartbeat<-2:
                print(f"Dispositivo com heartbeat = {self.dispositivos[i].heartbeat} foi tirado da lista")
                self.dispositivos.pop(i)
                return
ldd=Dispositivos() 
def preencher_dispositivos(destino, lista_dispositivos):
    if len(lista_dispositivos)==0:
        novo_dispositivo = destino.add()
        novo_dispositivo.nome = "vazia"
        novo_dispositivo.id = "vazia"  
        return
    for dispositivo in lista_dispositivos:
        novo_dispositivo = destino.add()
        novo_dispositivo.nome = dispositivo["nome"]
        novo_dispositivo.id = dispositivo["id"]                                    

def preencher_funcionalidades_proto(lista_funcionalidades):
    funcionalidades_proto = mensagens_pb2.GatewayLF()
    if len(lista_funcionalidades)==0:
        funcionalidade = funcionalidades_proto.funcionalidades.add()
        funcionalidade.nome = "vazia"
        return funcionalidades_proto
    for func in lista_funcionalidades:
        funcionalidade = funcionalidades_proto.funcionalidades.add()
        funcionalidade.nome = func["nome"]

        for param in func["parametros"]:
            parametro = funcionalidade.parametros.add()
            parametro.nome = param.nome
            parametro.tipo = param.tipo
    
    return funcionalidades_proto

def iniciar_gateway():
    # Criar o socket UDP
    print("Gateway iniciado") 
    time.sleep(1)
    #criando o socket para o multicas
    sock_multicast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_multicast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_multicast.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock_multicast.bind(('', MULTICAST_PORT))
    
    #criando o socket para os dispositivos enviarem mensagens sobre os comandos para o gateway
    sock_gateway = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_gateway.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_gateway.bind(('', GATEWAY_PORT))
    
    #criando o socket para os dispositivos enviarem o heartbeat para o gateway
    sock_gateway_heartbeat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_gateway_heartbeat.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_gateway_heartbeat.bind(('', GATEWAY_HEARTBEAT_PORT))
    
    #inciando a thread que adciona novos dispositivos que responderem ao multicast
    t_adc_dispositivos = threading.Thread(target= adcionar_novos_dispositivos,args=(sock_gateway,sock_multicast))
    t_adc_dispositivos.start()
    
    #inciando a thread que escuta novos clientes que quiserem se comunicar com o gateway
    t_escuta_cliente = threading.Thread(target= escuta_cliente,args=(sock_gateway,))
    t_escuta_cliente.start()
    
    print("Aguardando a entrada dos dispositivos e/ou cliente")
    
    #iniciando o envio do heartbeat para os dispositivos da lista (se houver)
    heartbeat(sock_gateway_heartbeat)
    
    #finalizando as duas threads anteriores    
    t_adc_dispositivos.join()
    t_escuta_cliente.join()
  
def enviar_multicast(sock):
    mensagem=mensagens_pb2.GatewayM(comando='descobrir',enderecoGateway=[f"{GATEWAY_IP}",f"{GATEWAY_PORT}"],gateway_heartbeat_port=f"{GATEWAY_HEARTBEAT_PORT}")
    sock.sendto(mensagem.SerializeToString(), (MULTICAST_GROUP, MULTICAST_PORT))

def heartbeat(sock_gateway_heartbeat):
    while True:
        time.sleep(1)
        ldd.diminuir_heartbeat()
        tam=len(ldd.dispositivos)
        if tam is None:
            tam=0
        else:
            heartbeat= mensagens_pb2.GatewayHB()
            heartbeat.comando="heartbeat"
            heartbeat.gateway_heartbeat_port=f"{GATEWAY_HEARTBEAT_PORT}"
            heartbeat.tamanho_lista=f"{tam}"
            i=0
            for i in range(tam):    
                sock_gateway_heartbeat.sendto(heartbeat.SerializeToString(), (ldd.dispositivos[i].ip,int(ldd.dispositivos[i].heartbeat_port)))
                
                try:
                    sock_gateway_heartbeat.settimeout(5)
                    dados, endereco = sock_gateway_heartbeat.recvfrom(1024)
                    heartbeatR=mensagens_pb2.DispositivoHB()
                    heartbeatR.ParseFromString(dados)
                    ldd.aumentar_heartbeat(heartbeatR)
                except Exception as e:
                    print(f"erro {e}")
                    pass    
 
def adcionar_novos_dispositivos(sock_gateway,sock_multicast):
    global ldd
    while True:
        if not thread_pausada:
            with lock:
                enviar_multicast(sock_multicast)
                sock_gateway.settimeout(5)
                try:
                    dados, endereco = sock_gateway.recvfrom(1024)
                    mensagem=mensagens_pb2.DispositivoR()
                    mensagem.ParseFromString(dados)
                    if mensagem.tipo=='descoberta':   
                        ip,porta=mensagem.endereco
                        ldd.dispositivos.append( Dispositivo(mensagem.nome,mensagem.id,ip,porta,mensagem.funcionalidades,mensagem.heartbeat_port) )
                        print(f"Dispositivo:{mensagem.nome} de ID:{mensagem.id} e ip:{ip} foi adcionado a lista de dispositivos\n")
                except:
                        pass

def escuta_cliente(sock_gateway):
    global CLIENT_IP,CLIENT_PORT,GATEWAY_IP,GATEWAY_CLIENT_PORT,thread_pausada,ldd
    
    #criando um socket tcp
    gateway_client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    gateway_client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   
    #associando o socket tcp criado ao ip do gateway e a porta gateway_client_port
    gateway_client_sock.bind((GATEWAY_IP, GATEWAY_CLIENT_PORT))
    
    #socket do gateway_client está agora no modo de escutar conexões
    gateway_client_sock.listen(1)
    print("Escutando cliente")
    #aceitar conexão com o cliente quando ele tentar se conectar
    client_sock, client_endereco = gateway_client_sock.accept()
    CLIENT_IP,CLIENT_PORT=client_endereco
    print(f"Cliente do endereço  {client_endereco} se conectou ao gateway")
    while True:
        try:
            # ouvir o cliente 
            dados = client_sock.recv(1024)
            comando = mensagens_pb2.ClienteC()
            comando.ParseFromString(dados)
            
            if comando.comando=="dispositivos":
                dispositivos=mensagens_pb2.GatewayLD()
                preencher_dispositivos(dispositivos.dispositivos,ldd.lista_nome_id_dos_dispositivos() )
                client_sock.sendall(dispositivos.SerializeToString())
                
            elif comando.comando=="funcionalidades":
                try:
                    nome_do_dispositivo_escolhido=comando.dispositivo.nome
                    id_do_dispositivo_escolhido=comando.dispositivo.id
                    lista_funcionalidades=ldd.lista_de_funcionalidades_e_seus_parametros(nome_do_dispositivo_escolhido,id_do_dispositivo_escolhido)
                    funcionalidades=mensagens_pb2.GatewayLF()
                    funcionalidades=preencher_funcionalidades_proto(lista_funcionalidades)
                    client_sock.sendall(funcionalidades.SerializeToString())
                    
                except Exception as e:
                    print(f"Erro:{e}")
                    print("Algo deu errado ao receber a lista tentar enviar a lista de funcionalidades do dispositivo solicitado")
                    funcionalidades=mensagens_pb2.GatewayLF()
                    func=funcionalidades.funcionalidades.add()
                    func.nome="vazia"
                    print(f"Enviando uma lista de funcionalidades vazia:{funcionalidades}")
                    client_sock.sendall(funcionalidades.SerializeToString())
            
            elif comando.comando=="função":
                thread_pausada=True
                with lock:
                    try:
                        ip,porta=ldd.ip_e_porta(comando.dispositivo.nome,comando.dispositivo.id)
                        comando.comando=comando.funcionalidade
                        sock_gateway.sendto(comando.SerializeToString(), (ip,int(porta)))
                        print("mensagem enviada para o dispositivo")
                        sock_gateway.settimeout(5)
                        dados, endereco = sock_gateway.recvfrom(1024)
                        status = mensagens_pb2.DispositivoS()
                        status.ParseFromString(dados)
                        if status.status[0].valorDoStatus=='atualização':
                            client_sock.sendall(status.SerializeToString())
                            thread_pausada=False
                            print("Deu certo fazer o envio e receber uma resposta do dispositivo")
                    except Exception as e:
                        print(f"Erro:{e}")
                        print("Tempo limite esgotado. Dispositivo não respondeu a solicitação.")  
                        thread_pausada=False
                        status = mensagens_pb2.DispositivoS()
                        st=status.status.add()
                        st.nomeDoStatus="erro"
                        client_sock.sendall(status.SerializeToString())

            
            elif comando.comando=="status":
                thread_pausada=True    
                with lock:
                    try:
                        ip,porta=ldd.ip_e_porta(comando.dispositivo.nome,comando.dispositivo.id)
                        print("vou tentar enviar mensagem para o dispositivo agora")                    
                        sock_gateway.sendto(comando.SerializeToString(), (ip,int(porta)))
                        print("mensagem enviada para o dispositivo")
                        sock_gateway.settimeout(5)   
                        dados, endereco = sock_gateway.recvfrom(1024)
                        status=mensagens_pb2.DispositivoS()
                        status.ParseFromString(dados)
                        if status.status[0].valorDoStatus=='atualização':
                            client_sock.sendall(status.SerializeToString())
                            thread_pausada=False
                            print("Deu certo fazer o envio e receber uma resposta do dispositivo")
                    except Exception as e:
                        print(f"Erro:{e}")
                        print("Tempo limite esgotado. Dispositivo não respondeu a solicitação.")  
                        thread_pausada=False
                        status = mensagens_pb2.DispositivoS()
                        st=status.status.add()
                        st.nomeDoStatus="erro"
                        client_sock.sendall(status.SerializeToString())
                
            
            elif comando.comando=="renomear":
                thread_pausada=True
                with lock:
                    try:
                        ldd.atualizar_id_dispositivo_gateway(comando.dispositivo.nome,comando.dispositivo.id,comando.novo_id)
                        ip,porta=ldd.ip_e_porta(comando.dispositivo.nome,comando.novo_id)
                        print("enviando mensagem para o dispositivo")
                        sock_gateway.sendto(comando.SerializeToString(), (ip,int(porta)))
                        print("mensagem enviada para o dispositivo")
                        sock_gateway.settimeout(5)
                        dados, endereco = sock_gateway.recvfrom(1024)
                        status=mensagens_pb2.DispositivoS()
                        status.ParseFromString(dados)
                        if status.status[0].valorDoStatus=='atualização':
                            client_sock.sendall(status.SerializeToString())
                            thread_pausada=False
                            print("Deu certo fazer o envio e receber uma resposta do dispositivo")
                    except Exception as e:
                        print(f"Erro:{e}")
                        print("Tempo limite esgotado. Dispositivo não respondeu a solicitação.")  
                        thread_pausada=False
                        status = mensagens_pb2.DispositivoS()
                        st=status.status.add()
                        st.nomeDoStatus="erro"
                        client_sock.sendall(status.SerializeToString())
    
        except Exception as e:
            print(f"Ocorreu um erro: {e}")
            print("O cliente ficou inacessível")
            client_sock.close()
            print(f"Conexão com {client_endereco} encerrada.")
            #criando um socket tcp
            gateway_client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            gateway_client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   
            #associando o socket tcp criado ao ip do gateway e a porta gateway_client_port
            gateway_client_sock.bind((GATEWAY_IP, GATEWAY_CLIENT_PORT))
            #socket do gateway_client está agora no modo de escutar conexões
            gateway_client_sock.listen(1)
            print("Escutando cliente")
            #aceitar conexão com o cliente quando ele tentar se conectar
            client_sock, client_endereco = gateway_client_sock.accept()
            CLIENT_IP,CLIENT_PORT=client_endereco
            print(f"Cliente do endereço  {client_endereco} se conectou ao gateway")
                           
if __name__ == "__main__":  
    iniciar_gateway()