import socket
import json
import os
import time

# Configurações do Gateway e Cliente
GATEWAY_IP = '192.168.0.49'
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


def lista_dispositivos(json_lista_dispositivos):
    """
    Exibe os dispositivos conectados na rede e permite ao usuário selecionar um deles.
    Retorna o nome e o ID do dispositivo selecionado.
    """
    dispositivos = json_lista_dispositivos.get("dispositivos", [])
    if not dispositivos:
        print("Ainda não existem dispositivos conectados na rede...")
        time.sleep(2)
        os.system('cls')
        return "", ""

    print("Selecione um dispositivo:")
    for i, dispositivo in enumerate(dispositivos):
        print(f"{i}) {dispositivo['nome']} - {dispositivo['id']}")

    try:
        escolha = int(input())
        while escolha < 0 or escolha >= len(dispositivos):
            print("Digite uma opção válida")
            escolha = int(input())
    except ValueError:
        print("Você digitou uma opção inválida")
        return "", ""

    dispositivo = dispositivos[escolha]
    return dispositivo["nome"], dispositivo["id"]

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

def listar_funcionalidades(json_lista_funcionalidades):
    """
    Exibe as funcionalidades do dispositivo e permite ao usuário selecionar uma.
    Retorna o nome da funcionalidade e seus parâmetros preenchidos.
    """
    funcionalidades = json_lista_funcionalidades.get("funcionalidades", [])

    if not funcionalidades:
        print("A lista de funcionalidades para esse dispositivo está vazia ou o dispositivo se desconectou.")
        return "-1", ""

    print("Selecione uma funcionalidade:")
    for i, funcionalidade in enumerate(funcionalidades):
        print(f"{i}) {funcionalidade['nome']}")

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

    for parametro in funcionalidade["parametros"]:
        while True:
            try:
                valor = input(f"Digite um valor para {parametro['nome']} ({parametro['tipo']}): ")
                if parametro['tipo'] == 'int':
                    parametros.append(int(valor))
                elif parametro['tipo'] == 'str':
                    parametros.append(str(valor))
                else:
                    opcoes = parametro['tipo'].replace(" ", "").split(',')
                    if valor not in opcoes:
                        raise ValueError("Valor inválido")
                    parametros.append(valor)
                break
            except ValueError:
                print("Você digitou um valor inválido. Tente novamente.")

    return funcionalidade["nome"], parametros

def apresenta_status(json_status):
    """
    Exibe o status do dispositivo com base no JSON recebido e aguarda interação do usuário para continuar.
    """
    status = json_status.get("status", [])
    for item in status:
        for chave, valor in item.items():
            print(f"{chave}: {valor}")
    input("Pressione Enter para continuar...")

def enviar_e_receber(client_sock, mensagem):
    """
    Envia uma mensagem JSON ao servidor e recebe a resposta.
    """
    try:
        mensagem_json = json.dumps(mensagem).encode('utf-8')
        client_sock.sendall(mensagem_json)
        resposta = client_sock.recv(1024)
        return json.loads(resposta.decode('utf-8'))
    except Exception as e:
        print(f"Erro na comunicação: {e}")
        return {}

def main():
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
        dispositivos = enviar_e_receber(client_sock, {"comando": "dispositivos"})
        dispositivo, id_dispositivo = lista_dispositivos(dispositivos)

        if not dispositivo:
            continue

        acao = lista_opcoes_de_acoes()

        if acao == "função":
            funcionalidades = enviar_e_receber(client_sock, {"comando": "funcionalidades", "dispositivo": {"nome": dispositivo, "id": id_dispositivo}})
            func, parametros = listar_funcionalidades(funcionalidades)

            if func != "-1":
                mensagem = {"comando": "função", "dispositivo": {"nome": dispositivo, "id": id_dispositivo}, "funcionalidade": func, "parametros": parametros}
                resposta = enviar_e_receber(client_sock, mensagem)
                apresenta_status(resposta)

        elif acao == "status":
            mensagem = {"comando": "status", "dispositivo": {"nome": dispositivo, "id": id_dispositivo}}
            resposta = enviar_e_receber(client_sock, mensagem)
            apresenta_status(resposta)

        elif acao == "renomear":
            novo_id = input("Digite o novo ID para o dispositivo: ")
            mensagem = {"comando": "renomear", "dispositivo": {"nome": dispositivo, "id": id_dispositivo}, "novo_id": novo_id}
            resposta = enviar_e_receber(client_sock, mensagem)
            apresenta_status(resposta)

        else:
            print("Encerrando o programa...")
            break  # Sai do loop principal

    client_sock.close()


if __name__ == "__main__":
    main()
