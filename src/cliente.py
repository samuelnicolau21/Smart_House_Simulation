import socket
import struct
import json
import os
import time


GATEWAY_IP='192.168.3.116'
GATEWAY_PORT=5010

CLIENT_PORT=5009
CLIENT_IP=''

def lista_dispositivos(json_lista_dispositivos):
    
    list=json_lista_dispositivos["dispositivos"]
    tam=len(list)
    i=0
    print("Selecione um dispositivo")
    for i in range(tam):
        print(f"{i}) {list[i]['nome']}-{list[i]['id']}\n")
    x=int(input())
    return list[x]["nome"],list[x]["id"]

def lista_opcoes_de_acoes():
    print("1) Chamar uma função do dispositivo selecionado")
    print("2) Renomear o id do dispositivo selecionado")
    print("3) Ver o status do dispositivo selecionado")
    x=int(input())
    if x==1:
        return "função"
    elif x==2:
        return "renomear"
    elif x==3:
        return "status"
    
def listar_funcionalidades(json_lista_funcionalidades):
    list=json_lista_funcionalidades["funcionalidades"]
    tam=len(list)
    
    i=0
    print("Selecione uma funcionalidade\n")
    for i in range(tam):
        print(f"{i}) {list[i]['nome']}")
    x=int(input())
    nome_da_funcionalidade_escolhida=list[x]["nome"]
    list_2=list[x]["parametros"]
    tam_2=len(list_2)
    parametros=[]
    i=0
    for i in range(tam_2):
        parametros.append(input(f"Digite um valor para: {list_2[i]['nome']} do tipo: {list_2[i]['tipo']} ."))
         
    return nome_da_funcionalidade_escolhida, parametros

def apresenta_status(json_status):
    list=json_status["status"]
    for tupla in list:
        for chave, valor in tupla.items():
            print(f"{chave}: {valor}")


def main():
    global CLIENT_PORT,CLIENT_IP,GATEWAY_IP,GATEWAY_PORT
    
    #cria socket do cliente
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_sock.bind(('', CLIENT_PORT))
    
    #descobrindo o ip do cliente
    CLIENT_IP,CLIENT_PORT=client_sock.getsockname()
    CLIENT_IP = socket.gethostbyname(socket.gethostname())
    
    #tentando se conectar com o scoket do gateway
    client_sock.connect((GATEWAY_IP, GATEWAY_PORT))
   

    
    while True:
        time.sleep(2)
        mensagem = {"comando":"dispositivos"}
        mensagem_json = json.dumps(mensagem).encode('utf-8')
        client_sock.sendall(mensagem_json)
        client_sock.settimeout(None)
        r_json = client_sock.recv(1024)
        r_json=r_json.decode('utf-8')
        r_json=json.loads(r_json)
        #o que eu espero receber aqui: {"dispositivos":[{"nome":"lampada","id":"01"},{"nome":"","id":""},{"nome":"","id":""},{"nome":"","id":""}]}
        dispositivo_escolhido , id_dispositivo_escolhido = lista_dispositivos(r_json) #retorna o nome e id do dispositivo escolhida
        os.system('cls')
        acao_escolhida=lista_opcoes_de_acoes()# retorna a ação escolhida pelo usuário: renomear (dispositivo), status(ver o status), função (chamar uma função)
        os.system('cls')
        
        if acao_escolhida=='função':
            mensagem = {"comando":"funcionalidades","dispositivo":{"nome":f"{dispositivo_escolhido}","id":f"{id_dispositivo_escolhido}"}}
            mensagem_json = json.dumps(mensagem).encode('utf-8')
            client_sock.sendall(mensagem_json)
            client_sock.settimeout(None)
            r_json = client_sock.recv(1024)
            r_json=r_json.decode('utf-8')
            #o que eu espero receber aqui:{"funcionalidades":[{"nome":"ligar/desligar","parametros":[{"nome":"","tipo":"",...}]} , {"nome":"brilho","parametros":[{"nome":"","tipo":"",...}]},...}
            
            r_json=json.loads(r_json)            
            funcionalidade_escolhida ,lista_de_parametros_preenchida =listar_funcionalidades(r_json)#retornar o nome da funcionalidade escolhida e uma lista de parâmetros preenchidos para aquela funcionalidade
            os.system('cls')
            mensagem = {"comando":"função","dispositivo":{"nome":f"{dispositivo_escolhido}","id":f"{id_dispositivo_escolhido}"},"funcionalidade":f"{funcionalidade_escolhida}","parametros":lista_de_parametros_preenchida}
            mensagem_json = json.dumps(mensagem).encode('utf-8')
            client_sock.sendall(mensagem_json)
            client_sock.settimeout(None)
            r_json = client_sock.recv(1024)
            r_json=r_json.decode('utf-8')
            r_json=json.loads(r_json)
            #o que eu espero receber aqui:{"chave":"valor",....}
            apresenta_status(r_json)
            input()
            os.system('cls')
            
        elif acao_escolhida=='status':
            mensagem = {"comando":"status","dispositivo":{"nome":f"{dispositivo_escolhido}","id":f"{id_dispositivo_escolhido}"}}
            mensagem_json = json.dumps(mensagem).encode('utf-8')
            client_sock.sendall(mensagem_json)
            client_sock.settimeout(None)
            r_json = client_sock.recv(1024)
            r_json=r_json.decode('utf-8')
            #o que eu espero receber aqui:{"chave":"valor",....}
            apresenta_status(r_json) 
        
        elif acao_escolhida=='renomear':
            novo_id_escolhido=input("Digite o novo id para o dispositivo escolhido:")
            
            mensagem = {"comando":"renomear","dispositivo":{"nome":f"{dispositivo_escolhido}","id":f"{id_dispositivo_escolhido}"},"novo_id":f"{novo_id_escolhido}"}
            mensagem_json = json.dumps(mensagem).encode('utf-8')
            client_sock.sendall(mensagem_json)
            client_sock.settimeout(None)
            r_json = client_sock.recv(1024)
            r_json=r_json.decode('utf-8')
            #o que eu espero receber aqui:{"chave":"valor",....}
            apresenta_status(r_json)
                       

    client_sock.close()
        

    
    
if __name__=="__main__":
    main()   