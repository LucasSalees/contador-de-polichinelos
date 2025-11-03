import tkinter as tk
from tkinter import filedialog

def mostrar_menu():
    """
    Mesma função mostrar_menu, devolve (modo, caminho, max_individuos)
    """
    resultado = {'modo': None, 'caminho': None, 'max_individuos': 2}
    caixa = tk.Tk()
    caixa.title("Contador de Polichinelos - Menu")

    BG_COLOR = "#2C3E50"
    FG_COLOR = "#ECF0F1"
    BTN_COLOR = "#1ABC9C"
    BTN_FG = "#2C3E50"
    BTN_HOVER = "#16A085"

    caixa.geometry("480x280")
    caixa.resizable(False, False)
    caixa.configure(bg=BG_COLOR)

    largura_janela = 480
    altura_janela = 280
    largura_tela = caixa.winfo_screenwidth()
    altura_tela = caixa.winfo_screenheight()
    pos_x = (largura_tela - largura_janela) // 2
    pos_y = (altura_tela - altura_janela) // 2
    caixa.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")

    rotulo = tk.Label(caixa, text="CONTADOR DE POLICHINELOS", font=("Segoe UI", 16, "bold"), bg=BG_COLOR, fg=FG_COLOR)
    rotulo.pack(pady=(20, 5))

    descricao = tk.Label(caixa, text="Escolha o modo e a configuração de indivíduos.", font=("Segoe UI", 10), bg=BG_COLOR, fg=FG_COLOR)
    descricao.pack(pady=(0, 15))

    var_individuos = tk.IntVar(value=2)
    opcoes = tk.Frame(caixa, bg=BG_COLOR)
    opcoes.pack()

    tk.Label(opcoes, text="Detectar:", font=("Segoe UI", 10), bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, padx=5)

    tk.Radiobutton(opcoes, text="1 Pessoa", variable=var_individuos, value=1,
                   font=("Segoe UI", 10), bg=BG_COLOR, fg=FG_COLOR,
                   selectcolor=BG_COLOR, activebackground=BG_COLOR, activeforeground=FG_COLOR,
                   indicatoron=1, borderwidth=0).pack(side=tk.LEFT, padx=10)

    tk.Radiobutton(opcoes, text="Até 2 Pessoas", variable=var_individuos, value=2,
                   font=("Segoe UI", 10), bg=BG_COLOR, fg=FG_COLOR,
                   selectcolor=BG_COLOR, activebackground=BG_COLOR, activeforeground=FG_COLOR,
                   indicatoron=1, borderwidth=0).pack(side=tk.LEFT, padx=10)

    def iniciar_tempo_real():
        resultado['modo'] = 'camera'
        resultado['max_individuos'] = var_individuos.get()
        caixa.destroy()

    def iniciar_gravacao():
        tipos_arquivo = [("Arquivos de vídeo", ("*.mp4", "*.avi", "*.mov", "*.mkv")), ("Todos os arquivos", "*.*")]
        caminho = filedialog.askopenfilename(title="Selecione um arquivo de vídeo", filetypes=tipos_arquivo)
        if caminho:
            resultado['modo'] = 'video'
            resultado['caminho'] = caminho
            resultado['max_individuos'] = var_individuos.get()
            caixa.destroy()

    def on_enter(e):
        e.widget.config(bg=BTN_HOVER)

    def on_leave(e):
        e.widget.config(bg=BTN_COLOR)

    btn_tempo_real = tk.Button(caixa, text="▶ Iniciar WebCam",
                               font=("Segoe UI", 11, "bold"),
                               width=25, height=2, command=iniciar_tempo_real,
                               relief="flat", bg=BTN_COLOR, fg=BTN_FG,
                               activebackground=BTN_HOVER, activeforeground=BTN_FG)
    btn_tempo_real.pack(pady=(20, 6))
    btn_tempo_real.bind("<Enter>", on_enter)
    btn_tempo_real.bind("<Leave>", on_leave)

    btn_gravacao = tk.Button(caixa, text="📁 Abrir Vídeo (Gravação)",
                             font=("Segoe UI", 11, "bold"),
                             width=25, height=2, command=iniciar_gravacao,
                             relief="flat", bg=BTN_COLOR, fg=BTN_FG,
                             activebackground=BTN_HOVER, activeforeground=BTN_FG)
    btn_gravacao.pack(pady=(6, 6))
    btn_gravacao.bind("<Enter>", on_enter)
    btn_gravacao.bind("<Leave>", on_leave)

    def ao_fechar():
        resultado['modo'] = None
        caixa.destroy()

    caixa.protocol("WM_DELETE_WINDOW", ao_fechar)
    caixa.bind('<Escape>', lambda e: ao_fechar())
    caixa.mainloop()
    return resultado['modo'], resultado['caminho'], resultado['max_individuos']