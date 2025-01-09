import socket
import json
import os
import time
import mensagens_pb2


# Configurações do Gateway e Cliente
GATEWAY_IP = 'localhost'
GATEWAY_PORT = 5010
CLIENT_PORT = 5009
CLIENT_IP = ''

def conectar():
    """
    Estabelece a conexão com o servidor e retorna o socket conectado.
    """
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_sock.bind(('', CLIENT_PORT))

    try:
        client_sock.connect((GATEWAY_IP, GATEWAY_PORT))
        print("Conexão estabelecida com sucesso.")
        return client_sock
    except Exception as e:
        print(f"Erro ao conectar ao servidor: {e}")
        return None
    
def desconectar(client_sock):
    """
    Encerra a conexão com o servidor.
    """
    if client_sock:
        client_sock.close()
        print("Conexão encerrada com sucesso.")

def lista_dispositivos(dispositivos):
    """
    Exibe os dispositivos conectados na rede e permite ao usuário selecionar um deles.
    Retorna o nome e o ID do dispositivo selecionado.
    """
    if  dispositivos[0].nome=="vazia":
        print("Ainda não existem dispositivos conectados na rede...")
        time.sleep(2)
        os.system('cls')
        return "", ""

    print("Selecione um dispositivo:")
    for i in range(len(dispositivos)):
        print(f"{i}) {dispositivos[i].nome} - {dispositivos[i].id}")

    try:
        escolha = int(input())
        while escolha < 0 or escolha >= len(dispositivos):
            print("Digite uma opção válida")
            escolha = int(input())
    except ValueError:
        print("Você digitou uma opção inválida")
        return "", ""

    dispositivo = dispositivos[escolha]
    return dispositivo.nome, dispositivo.id

def lista_opcoes_de_acoes():
    """
    Exibe as opções de ações disponíveis para o dispositivo selecionado.
    Retorna a ação escolhida pelo usuário.
    """
    acoes = {
        "1": "função",
        "2": "renomear",
        "3": "status"
    }

    print("Selecione uma ação:")
    print("1) Chamar uma função do dispositivo selecionado")
    print("2) Renomear o ID do dispositivo selecionado")
    print("3) Ver o status do dispositivo selecionado")

    while True:
        escolha = input("Digite uma opção válida: ")
        if escolha in acoes:
            return acoes[escolha]

def listar_funcionalidades(lista_funcionalidades_proto):
    """
    Exibe as funcionalidades do dispositivo e permite ao usuário selecionar uma.
    Retorna o nome da funcionalidade e seus parâmetros preenchidos.
    """
    funcionalidades = lista_funcionalidades_proto.funcionalidades

    if funcionalidades[0].nome=="vazia":
        print("A lista de funcionalidades para esse dispositivo está vazia ou o dispositivo se desconectou.")
        return "-1", ""

    print("Selecione uma funcionalidade:")
    for i in range(len(funcionalidades)):
        print(f"{i}) {funcionalidades[i].nome}")

    try:
        escolha = int(input())
        while escolha < 0 or escolha >= len(funcionalidades):
            print("Digite uma opção válida")
            escolha = int(input())
    except ValueError:
        print("Você digitou uma opção inválida")
        time.sleep(2)
        return "", ""

    funcionalidade = funcionalidades[escolha]
    parametros = []

    for parametro in funcionalidade.parametros:
        while True:
            try:
                valor = input(f"Digite um valor para {parametro.nome} ({parametro.tipo}): ")
                if parametro.tipo == 'int':
                    parametros.append(int(valor))
                elif parametro.tipo == 'str':
                    parametros.append(str(valor))
                else:
                    opcoes = parametro.tipo.replace(" ","").split(',')
                    if valor not in opcoes:
                        raise ValueError("Valor inválido")
                    parametros.append(valor)
                break
            except ValueError:
                print("Você digitou um valor inválido. Tente novamente.")

    return funcionalidade.nome, parametros

def apresenta_status(status_proto):
    """
    Exibe o status do dispositivo com base no JSON recebido e aguarda interação do usuário para continuar.
    """
    status = status_proto.status
    if status[0].nomeDoStatus=="erro":
        input("O dispositivo ficou inacessível. Tente novamente.")
        return
    for i in range(len(status)):
        print(f"{status[i].nomeDoStatus}:{status[i].valorDoStatus}")
    input("Pressione Enter para continuar...")

def enviar_e_receber(client_sock, mensagem, resposta):
    """
    Envia uma mensagem JSON ao servidor e recebe a resposta.
    """
    try:
        mensagem_proto = mensagem.SerializeToString()
        client_sock.sendall(mensagem_proto)
        dados = client_sock.recv(1024)
        resposta.ParseFromString(dados)
        return resposta
    except Exception as e:
        print(f"Erro na comunicação: {e}")
        return {}

def main():
    try:
        global CLIENT_PORT, CLIENT_IP, GATEWAY_IP, GATEWAY_PORT
    
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_sock.bind(('', CLIENT_PORT))
    
        CLIENT_IP = socket.gethostbyname(socket.gethostname())
    
        try:
            client_sock.connect((GATEWAY_IP, GATEWAY_PORT))
        except Exception as e:
            print(f"Falha ao conectar com o gateway: {e}")
            print("Programa encerrando...")
            time.sleep(5)
            client_sock.close()
            return
    
        
        while True:
            os.system('cls')
            comando=mensagens_pb2.ClienteC()
            comando.comando="dispositivos"
            dispositivos=mensagens_pb2.GatewayLD()
            dispositivos = enviar_e_receber(client_sock, comando, dispositivos)
            dispositivo, id_dispositivo = lista_dispositivos(dispositivos.dispositivos)
            if not dispositivo:
                continue
    
            acao = lista_opcoes_de_acoes()
    
            if acao == "função":
                comando=mensagens_pb2.ClienteC()
                comando.comando="funcionalidades"
                disp=comando.dispositivo
                disp.nome=f"{dispositivo}"
                disp.id=f"{id_dispositivo}"
                funcionalidades=mensagens_pb2.GatewayLF()
                funcionalidades = enviar_e_receber(client_sock,comando,funcionalidades)
                func, parametros = listar_funcionalidades(funcionalidades)
                if func != "-1":
                    comando=mensagens_pb2.ClienteC()
                    comando.comando="função"
                    comando.dispositivo.nome=f"{dispositivo}"
                    comando.dispositivo.id=f"{id_dispositivo}"
                    comando.funcionalidade=f"{func}"
                    for i in range(len(parametros)):  
                        comando.parametrosEscolhidos.append(str(parametros[i]))
                    resposta=mensagens_pb2.DispositivoS()
                    resposta = enviar_e_receber(client_sock,comando,resposta)
                    apresenta_status(resposta)
    
            elif acao == "status":
                comando=mensagens_pb2.ClienteC()
                comando.comando="status"
                comando.dispositivo.nome=f"{dispositivo}"
                comando.dispositivo.id=f"{id_dispositivo}"
                #mensagem = {"comando": "status", "dispositivo": {"nome": dispositivo, "id": id_dispositivo}}
                resposta=mensagens_pb2.DispositivoS()
                resposta = enviar_e_receber(client_sock,comando,resposta)
                apresenta_status(resposta)
    
            elif acao == "renomear":
                novo_id=input("Digite o novo id do dispositivo")
                comando=mensagens_pb2.ClienteC()
                comando.comando="renomear"
                comando.dispositivo.nome=f"{dispositivo}"
                comando.dispositivo.id=f"{id_dispositivo}"
                comando.novo_id=novo_id
                #mensagem = {"comando": "renomear", "dispositivo": {"nome": dispositivo, "id": id_dispositivo}, "novo_id": novo_id}
                resposta=mensagens_pb2.DispositivoS()
                resposta = enviar_e_receber(client_sock,comando,resposta)
                apresenta_status(resposta)
    
            else:
                print("Encerrando o programa...")
                break  # Sai do loop principal
    except Exception as e:  
        print(f"erro:{e}")      
        client_sock.close()


if __name__ == "__main__":
    main()