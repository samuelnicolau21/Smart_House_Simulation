import tkinter as tk
from tkinter import simpledialog, messagebox
from cliente import conectar, desconectar, enviar_e_receber

client_sock = None  # Variável global para o socket do cliente

def abrir_janela_funcoes(dispositivo, id_dispositivo):
    """
    Abre uma janela para selecionar uma funcionalidade e enviar os parâmetros, se necessário.
    """
    funcionalidades = enviar_e_receber(client_sock, {
        "comando": "funcionalidades",
        "dispositivo": {"nome": dispositivo, "id": id_dispositivo}
    })

    if not funcionalidades or "funcionalidades" not in funcionalidades:
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
    for funcionalidade in funcionalidades["funcionalidades"]:
        funcionalidades_listbox.insert(
            tk.END,
            f"{funcionalidade['nome']} - {'Requer parâmetros' if funcionalidade['parametros'] else 'Sem parâmetros'}"
        )

    def executar_funcionalidade():
        """
        Executa a funcionalidade selecionada, pedindo parâmetros se necessário.
        """
        indice = funcionalidades_listbox.curselection()
        if not indice:
            messagebox.showinfo("Erro", "Selecione uma funcionalidade.")
            return

        funcionalidade_selecionada = funcionalidades["funcionalidades"][indice[0]]

        # Checar se precisa de parâmetros
        if funcionalidade_selecionada["parametros"]:
            parametros = simpledialog.askstring(
                "Parâmetros",
                f"Digite os parâmetros para '{funcionalidade_selecionada['nome']}'"
            )
            print(f"Parâmetro capturado: {parametros}")
            if parametros is None:
                return  # Cancelado pelo usuário
            parametros = [parametros.strip()] 
        else:
            parametros = None

        # Enviar mensagem ao servidor
        mensagem = {
            "comando": "função",
            "dispositivo": {"nome": dispositivo, "id": id_dispositivo},
            "funcionalidade": funcionalidade_selecionada["nome"],
            "parametros": parametros
        }

        resposta = enviar_e_receber(client_sock, mensagem)
        informacoes = ""
        for item in resposta['status']:
            for chave, valor in item.items():
                informacoes += f"{chave}: {valor}\n"

        # Exibindo a mensagem no MessageBox
        messagebox.showinfo("Resposta", f"Resposta do servidor:\n{informacoes}")
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
                mensagem = {"comando": "status", "dispositivo": {"nome": dispositivo, "id": id_dispositivo}}
                resposta = enviar_e_receber(client_sock, mensagem)

                informacoes = ""
                for item in resposta['status']:
                    for chave, valor in item.items():
                        informacoes += f"{chave}: {valor}\n"

                # Exibindo a mensagem no MessageBox
                messagebox.showinfo("Status", f"Status do dispositivo:\n{informacoes}")

            elif acao == "Renomear":
                novo_id = simpledialog.askstring("Renomear", "Digite o novo ID para o dispositivo:")

                if novo_id:
                    mensagem = {
                        "comando": "renomear",
                        "dispositivo": {"nome": dispositivo, "id": id_dispositivo},
                        "novo_id": novo_id
                    }
                    resposta = enviar_e_receber(client_sock, mensagem)
                    informacoes = ""
                    for item in resposta['status']:
                        for chave, valor in item.items():
                            informacoes += f"{chave}: {valor}\n"

                    # Exibindo a mensagem no MessageBox
                    messagebox.showinfo("Resposta", f"Resposta do servidor:\n{informacoes}")

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

    dispositivos_listbox.delete(0, tk.END)
    try:
        resposta = enviar_e_receber(client_sock, {"comando": "dispositivos"})
        dispositivos = resposta.get("dispositivos", [])

        if not dispositivos:
            status_label.config(text="Nenhum dispositivo encontrado", fg="orange")
        else:
            for dispositivo in dispositivos:
                dispositivos_listbox.insert(tk.END, f"{dispositivo['nome']} - ID:{dispositivo['id']}")
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
