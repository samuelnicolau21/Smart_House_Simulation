import socket
import struct
import json
import os
import time


GATEWAY_IP='192.168.1.5'
GATEWAY_PORT=5010

CLIENT_PORT=5009
CLIENT_IP=''

def lista_dispositivos(json_lista_dispositivos):
    list=json_lista_dispositivos["dispositivos"]
    tam=len(list)
    if tam==0:
        print("Ainda não existem dispositivos conectados na rede...")
        time.sleep(2)
        os.system('cls')
        return "",""
    else:
        i=0
        print("Selecione um dispositivo")
        for i in range(tam):
            print(f"{i}) {list[i]['nome']}-{list[i]['id']}\n")
        try:
            x=int(input())
            while (x>tam-1 or x<0):
                print("Digite uma opção válida")
                x=int(input())
        except:
            print("Você digitou uma opção inválida")
            return "",""
        return list[x]["nome"],list[x]["id"]
def lista_opcoes_de_acoes():
    print("1) Chamar uma função do dispositivo selecionado")
    print("2) Renomear o id do dispositivo selecionado")
    print("3) Ver o status do dispositivo selecionado")
    x=""
    while(x!='1' or x!='1' or x!='3'):
        print("Digite uma opção válida")
        x=input()
        if x=='1':
            return "função"
        elif x=='2':
            return "renomear"
        elif x=='3':
            return "status"        
def listar_funcionalidades(json_lista_funcionalidades):
    list=json_lista_funcionalidades["funcionalidades"]
    tam=len(list) 
    i=0
    print("Selecione uma funcionalidade\n")
    for i in range(tam):
        print(f"{i}) {list[i]['nome']}")
    try:
        x=int(input())
        while(x>tam-1 and x<0):
            print("Digite uma opção válida")
            x=int(input())  
    except:
        print("Você digitou uma opção inválida")
        time.sleep(2)
        return "",""
    
    nome_da_funcionalidade_escolhida=list[x]["nome"]
    list_2=list[x]["parametros"]
    tam_2=len(list_2)
    parametros=[]
    i=0
    for i in range(tam_2):
        print(f"Digite um valor para: {list_2[i]['nome']} ({list_2[i]['tipo']})\n")
        x=input()
        try:
            if list_2[i]['tipo']=='int':
                aux=int(x)
                
            elif list_2[i]['tipo']=='str':
                aux=str(x)
                
            else:
                #tirando os espaços da string
                string_sem_speaço=list_2[i]['tipo'].replace(" ", "")
                #transformando a string em uma lista de strings
                lista_de_string=string_sem_speaço.split(',')
                if x in lista_de_string:
                    pass
                else:
                    print("Você digitou uma valor inválido para o parâmetro da funcionalidade escolhida")
                    time.sleep(2)
                    return "","" 
        except:
            print("Você digitou uma valor inválido para o parâmetro da funcionalidade escolhida")
            time.sleep(2)
            return "",""
        parametros.append(x)    
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
    
    try:
        #tentando se conectar com o scoket do gateway
        client_sock.connect((GATEWAY_IP, GATEWAY_PORT))
    except:
        print("falha ao tentar se conectar com o gateway.")
        print("programa encerrando...")
        time.sleep(5) 
        client_sock.close()
        return
    
    while True:
        time.sleep(1)
        mensagem = {"comando":"dispositivos"}
        mensagem_json = json.dumps(mensagem).encode('utf-8')
        try:
            client_sock.sendall(mensagem_json)
            client_sock.settimeout(None)
            r_json = client_sock.recv(1024)
            r_json=r_json.decode('utf-8')
            r_json=json.loads(r_json)
            #o que eu espero receber aqui: {"dispositivos":[{"nome":"lampada","id":"01"},{"nome":"","id":""},{"nome":"","id":""},{"nome":"","id":""}]}
            dispositivo_escolhido , id_dispositivo_escolhido = lista_dispositivos(r_json) #retorna o nome e id do dispositivo escolhida
            if(dispositivo_escolhido!="" and id_dispositivo_escolhido!=""):
                os.system('cls')
                acao_escolhida=lista_opcoes_de_acoes()# retorna a ação escolhida pelo usuário: renomear (dispositivo), status(ver o status), função (chamar uma função)

                if acao_escolhida=='função':
                    os.system('cls')
                    mensagem = {"comando":"funcionalidades","dispositivo":{"nome":f"{dispositivo_escolhido}","id":f"{id_dispositivo_escolhido}"}}
                    mensagem_json = json.dumps(mensagem).encode('utf-8')
                    client_sock.sendall(mensagem_json)
                    client_sock.settimeout(None)
                    r_json = client_sock.recv(1024)
                    r_json=r_json.decode('utf-8')
                    #o que eu espero receber aqui:{"funcionalidades":[{"nome":"ligar/desligar","parametros":[{"nome":"","tipo":"",...}]} , {"nome":"brilho","parametros":[{"nome":"","tipo":"",...}]},...}
                    r_json=json.loads(r_json)            
                    funcionalidade_escolhida ,lista_de_parametros_preenchida =listar_funcionalidades(r_json)#retornar o nome da funcionalidade escolhida e uma lista de parâmetros preenchidos para aquela funcionalidade
                    while (funcionalidade_escolhida=="" and lista_de_parametros_preenchida==""):
                        os.system('cls')
                        print("Digite uma opção válida")
                        funcionalidade_escolhida ,lista_de_parametros_preenchida =listar_funcionalidades(r_json)
                        
                    os.system('cls')
                    mensagem = {"comando":"função","dispositivo":{"nome":f"{dispositivo_escolhido}","id":f"{id_dispositivo_escolhido}"},"funcionalidade":f"{funcionalidade_escolhida}","parametros":lista_de_parametros_preenchida}
                    mensagem_json = json.dumps(mensagem).encode('utf-8')
                    client_sock.sendall(mensagem_json)
                    client_sock.settimeout(None)
                    r_json = client_sock.recv(1024)
                    r_json=r_json.decode('utf-8')
                    r_json=json.loads(r_json)
                    #######verificar se o retorno do gateway não é uma mensagem de erro porque o dispositivo ficou off line
                    if r_json.get('tipo')=='erro':
                        print(r_json.get('erro'))
                    else:    
                        apresenta_status(r_json) 
                        input()
                        os.system('cls')
                    
                elif acao_escolhida=='status':
                    os.system('cls')
                    mensagem = {"comando":"status","dispositivo":{"nome":f"{dispositivo_escolhido}","id":f"{id_dispositivo_escolhido}"}}
                    mensagem_json = json.dumps(mensagem).encode('utf-8')
                    client_sock.sendall(mensagem_json)
                    client_sock.settimeout(None)
                    r_json = client_sock.recv(1024)
                    r_json=r_json.decode('utf-8')
                    r_json=json.loads(r_json)
                    #######verificar se o retorno do gateway não é uma mensagem de erro porque o dispositivo ficou off line
                    if r_json.get('tipo')=='erro':
                        print(r_json.get('erro'))
                    else:    
                        apresenta_status(r_json) 
                        input()
                        os.system('cls')
                
                elif acao_escolhida=='renomear':
                    os.system('cls')
                    novo_id_escolhido=input("Digite o novo id para o dispositivo escolhido:")
                    mensagem = {"comando":"renomear","dispositivo":{"nome":f"{dispositivo_escolhido}","id":f"{id_dispositivo_escolhido}"},"novo_id":f"{novo_id_escolhido}"}
                    mensagem_json = json.dumps(mensagem).encode('utf-8')
                    client_sock.sendall(mensagem_json)
                    client_sock.settimeout(None)
                    r_json = client_sock.recv(1024)
                    r_json=r_json.decode('utf-8')
                    r_json=json.loads(r_json)
                    #######verificar se o retorno do gateway não é uma mensagem de erro porque o dispositivo ficou off line
                    if r_json.get('tipo')=='erro':
                        print(r_json.get('erro'))
                    else:    
                        apresenta_status(r_json) 
                        input()
                        os.system('cls')
                                  
                        
        except:
            print("Falha ao enviar mensagem para o gateway")
            print("programa encerrando...")
            time.sleep(5) 
            break
                        

    client_sock.close()
    return
        
if __name__=="__main__":
    main()   