import tkinter as tk
from tkinter import simpledialog, messagebox
from cliente_pb import conectar, desconectar, enviar_e_receber
import mensagens_pb2

client_sock = None  # Variável global para o socket do cliente

def abrir_janela_funcoes(dispositivo, id_dispositivo):
    """
    Abre uma janela para selecionar uma funcionalidade e enviar os parâmetros, se necessário.
    """
    try:
        # Criar mensagem para solicitar funcionalidades
        comando = mensagens_pb2.ClienteC()
        comando.comando = "funcionalidades"
        comando.dispositivo.nome = dispositivo
        comando.dispositivo.id = id_dispositivo

        # Resposta esperada
        funcionalidades = mensagens_pb2.GatewayLF()
        funcionalidades = enviar_e_receber(client_sock, comando, funcionalidades)

        # Verificar se há funcionalidades disponíveis
        if not funcionalidades.funcionalidades:
            messagebox.showinfo("Erro", "Nenhuma funcionalidade disponível.")
            return

        # Janela para seleção de funcionalidade
        janela_funcoes = tk.Toplevel()
        janela_funcoes.title("Selecionar Funcionalidade")

        tk.Label(
            janela_funcoes,
            text=f"Dispositivo: {dispositivo}",
            font=("Arial", 12)
        ).pack(pady=10)

        tk.Label(
            janela_funcoes,
            text="Escolha uma funcionalidade:",
            font=("Arial", 10)
        ).pack(pady=5)

        funcionalidades_listbox = tk.Listbox(janela_funcoes, font=("Arial", 10), height=10, width=40)
        funcionalidades_listbox.pack(pady=5)

        # Adicionar funcionalidades à lista
        for func in funcionalidades.funcionalidades:
            descricao = f"{func.nome} - {'Requer parâmetros' if func.parametros else 'Sem parâmetros'}"
            funcionalidades_listbox.insert(tk.END, descricao)

        def executar_funcionalidade():
            """
            Executa a funcionalidade selecionada, pedindo parâmetros se necessário.
            """
            indice = funcionalidades_listbox.curselection()
            if not indice:
                messagebox.showinfo("Erro", "Selecione uma funcionalidade.")
                return

            funcionalidade_selecionada = funcionalidades.funcionalidades[indice[0]]

            # Checar se precisa de parâmetros
            parametros = []
            if funcionalidade_selecionada.parametros:
                entrada_parametros = simpledialog.askstring(
                    "Parâmetros",
                    f"Digite os parâmetros para '{funcionalidade_selecionada.nome}':"
                )
                if entrada_parametros is None:
                    return  # Cancelado pelo usuário
                parametros = [param.strip() for param in entrada_parametros.split(",")]

            # Criar mensagem para executar funcionalidade
            comando = mensagens_pb2.ClienteC()
            comando.comando = "função"
            comando.dispositivo.nome = dispositivo
            comando.dispositivo.id = id_dispositivo
            comando.funcionalidade = funcionalidade_selecionada.nome
            comando.parametrosEscolhidos.extend(parametros)

            # Resposta esperada
            resposta = mensagens_pb2.DispositivoS()
            resposta = enviar_e_receber(client_sock, comando, resposta)

            # Construir a mensagem de resposta para exibição
            informacoes = ""
            for item in resposta.status:
                informacoes += f"{item.nomeDoStatus}: {item.valorDoStatus}\n"

            # Exibir a resposta no MessageBox
            if informacoes:
                messagebox.showinfo("Resposta", f"Resposta do servidor:\n{informacoes}")
            else:
                messagebox.showinfo("Resposta", "O servidor não retornou nenhuma mensagem.")

            janela_funcoes.destroy()

        tk.Button(
            janela_funcoes,
            text="Executar",
            command=executar_funcionalidade,
            font=("Arial", 12)
        ).pack(pady=10)

        tk.Button(
            janela_funcoes,
            text="Cancelar",
            command=janela_funcoes.destroy,
            font=("Arial", 12)
        ).pack(pady=5)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir janela de funcionalidades: {e}")



def interagir_com_dispositivo():
    dispositivo_selecionado = dispositivos_listbox.get(tk.ACTIVE)

    if not dispositivo_selecionado:
        status_label.config(text="Nenhum dispositivo selecionado", fg="red")
        return

    dispositivo, id_dispositivo = dispositivo_selecionado.split(" - ID:")

    def abrir_opcoes():
        """
        Abre uma janela para selecionar e executar a ação desejada.
        """
        def executar_acao(acao):
            if acao == "Função":
                abrir_janela_funcoes(dispositivo, id_dispositivo)

            elif acao == "Status":
                try:
                    # Construir o comando usando Protocol Buffers
                    comando = mensagens_pb2.ClienteC()
                    comando.comando = "status"
                    comando.dispositivo.nome = dispositivo
                    comando.dispositivo.id = id_dispositivo

                    # Objeto de resposta esperado
                    resposta = mensagens_pb2.DispositivoS()

                    # Enviar e receber a mensagem usando enviar_e_receber()
                    resposta = enviar_e_receber(client_sock, comando, resposta)

                    # Construir a mensagem de status para exibição
                    informacoes = ""
                    for item in resposta.status:
                        informacoes += f"{item.nomeDoStatus}: {item.valorDoStatus}\n"

                    # Exibir as informações no MessageBox
                    if informacoes:
                        messagebox.showinfo("Status", f"Status do dispositivo:\n{informacoes}")
                    else:
                        messagebox.showinfo("Status", "Nenhum status disponível para o dispositivo.")
                except Exception as e:
                    status_label.config(text=f"Erro ao obter status: {e}", fg="red")

            elif acao == "Renomear":
                try:
                    # Solicitar novo ID ao usuário
                    novo_id = simpledialog.askstring("Renomear", "Digite o novo ID para o dispositivo:")

                    if not novo_id:
                        messagebox.showinfo("Renomear", "Nenhum ID foi fornecido.")
                        return

                    # Criar a mensagem usando Protocol Buffers
                    comando = mensagens_pb2.ClienteC()
                    comando.comando = "renomear"
                    comando.dispositivo.nome = dispositivo
                    comando.dispositivo.id = id_dispositivo
                    comando.novo_id = novo_id

                    # Objeto de resposta esperado
                    resposta = mensagens_pb2.DispositivoS()

                    # Enviar e receber a mensagem
                    resposta = enviar_e_receber(client_sock, comando, resposta)

                    # Construir a mensagem de resposta para exibição
                    informacoes = ""
                    for item in resposta.status:
                        informacoes += f"{item.nomeDoStatus}: {item.valorDoStatus}\n"

                    # Exibir a resposta no MessageBox
                    if informacoes:
                        messagebox.showinfo("Resposta", f"Resposta do servidor:\n{informacoes}")
                    else:
                        messagebox.showinfo("Resposta", "O servidor não retornou nenhuma mensagem.")
                except Exception as e:
                    status_label.config(text=f"Erro ao renomear dispositivo: {e}", fg="red")

            janela_opcoes.destroy()

        # Janela para escolher a ação
        janela_opcoes = tk.Toplevel()
        janela_opcoes.title("Escolher Ação")

        tk.Label(janela_opcoes, text=f"Dispositivo: {dispositivo}", font=("Arial", 12)).pack(pady=10)

        botoes = ["Função", "Status", "Renomear"]
        for botao in botoes:
            tk.Button(
                janela_opcoes, text=botao, command=lambda b=botao: executar_acao(b), font=("Arial", 12)
            ).pack(pady=5)

    abrir_opcoes()

def conectar_ou_desconectar():
    global client_sock
    if conectar_button.config('text')[-1] == "Conectar":
        client_sock = conectar()
        if client_sock:
            status_label.config(text="Conectado ao servidor", fg="green")
            conectar_button.config(text="Desconectar")
        else:
            status_label.config(text="Falha na conexão", fg="red")
    else:
        desconectar(client_sock)
        client_sock = None
        status_label.config(text="Desconectado", fg="red")
        conectar_button.config(text="Conectar")


def atualizar_lista():
    if not client_sock:
        status_label.config(text="Conecte-se ao servidor primeiro!", fg="red")
        return

    dispositivos_listbox.delete(0, tk.END)  # Sempre limpar a listbox antes de atualizar

    try:
        # Criar a mensagem de comando
        comando = mensagens_pb2.ClienteC()
        comando.comando = "dispositivos"

        # Criar o objeto de resposta esperado
        dispositivos_resposta = mensagens_pb2.GatewayLD()

        # Enviar e receber a resposta usando Protocol Buffers
        dispositivos_resposta = enviar_e_receber(client_sock, comando, dispositivos_resposta)

        # Obter a lista de dispositivos
        dispositivos = getattr(dispositivos_resposta, "dispositivos", [])

        # Verificar se todos os dispositivos possuem id e nome como "vazia"
        if all(dispositivo.id == "vazia" and dispositivo.nome == "vazia" for dispositivo in dispositivos):
            status_label.config(text="Nenhum dispositivo encontrado", fg="orange")
            return  # Finaliza a função sem adicionar nada à listbox

        # Inserir dispositivos válidos na listbox
        for dispositivo in dispositivos:
            if dispositivo.nome and dispositivo.id and dispositivo.nome != "vazia" and dispositivo.id != "vazia":
                dispositivos_listbox.insert(tk.END, f"{dispositivo.nome} - ID:{dispositivo.id}")

        status_label.config(text="Lista de dispositivos atualizada", fg="green")

    except Exception as e:
        status_label.config(text=f"Erro ao atualizar lista: {e}", fg="red")


# Configuração da interface gráfica
janela = tk.Tk()
janela.title("Smart Home")

tk.Label(janela, text="Smart Home", font=("Arial", 16)).pack(pady=10)

conectar_button = tk.Button(janela, text="Conectar", command=conectar_ou_desconectar, font=("Arial", 12))
conectar_button.pack(pady=5)

status_label = tk.Label(janela, text="Desconectado", fg="red", font=("Arial", 12))
status_label.pack(pady=5)

tk.Label(janela, text="Dispositivos Disponíveis:", font=("Arial", 12)).pack(pady=5)

dispositivos_listbox = tk.Listbox(janela, height=10, width=40, font=("Arial", 12))
dispositivos_listbox.pack(pady=5)

tk.Button(janela, text="Atualizar Lista", command=atualizar_lista, font=("Arial", 12)).pack(pady=5)

tk.Button(janela, text="Interagir", command=interagir_com_dispositivo, font=("Arial", 12)).pack(pady=5)

janela.mainloop()