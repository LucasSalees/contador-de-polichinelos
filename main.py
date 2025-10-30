# Importação das bibliotecas necessárias
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # Suprime avisos do TensorFlow
import cv2  # OpenCV para processamento de imagem e vídeo
import mediapipe as mp  # Framework do Google para detecção de poses
import time  # Para controle de tempo e timestamps
import math  # Para cálculos matemáticos
import tkinter as tk  # Para criar interface gráfica
from tkinter import filedialog  # Para diálogo de seleção de arquivo

# Inicialização dos módulos do MediaPipe
mp_desenho = mp.solutions.drawing_utils  # Utilitários para desenhar landmarks
mp_pose = mp.solutions.pose  # Módulo de detecção de pose

# Definição dos pontos de referência (landmarks) do corpo (índices do MediaPipe)
OMBRO_ESQUERDO = 11     # Ombro esquerdo
OMBRO_DIREITO = 12      # Ombro direito
PULSO_ESQUERDO = 15     # Pulso esquerdo
PULSO_DIREITO = 16      # Pulso direito
QUADRIL_ESQUERDO = 23   # Quadril esquerdo
QUADRIL_DIREITO = 24    # Quadril direito
TORNOZELO_ESQUERDO = 27 # Tornozelo esquerdo
TORNOZELO_DIREITO = 28  # Tornozelo direito

# Parâmetros de configuração para detecção
CONFIANCA_MIN_DETECCAO = 0.5        # Confiança mínima para detecção
CONFIANCA_MIN_RASTREAMENTO = 0.5    # Confiança mínima para tracking
RAZAO_TORNOZELO_QUADRIL_ABERTO = 1.5    # Razão para considerar pernas abertas
RAZAO_TORNOZELO_QUADRIL_FECHADO = 1.25  # Razão para considerar pernas fechadas
MARGEM_BRACO_ACIMA_OMBRO = 0.05       # Margem para braços acima do ombro

# === NOVA CONSTANTE ===
# Margem para considerar o pulso próximo ao quadril (15% da altura do recorte)
MARGEM_PULSO_QUADRIL = 0.05

# === NOVA CONSTANTE DE SIMETRIA ===
# Limite para simetria (ex: um pé não pode estar 2.5x mais longe do centro que o outro)
LIMITE_RAZAO_SIMETRIA = 2.5


def distancia_euclidiana(a, b):
    """
    Calcula a distância euclidiana entre dois pontos
    a, b: tuplas (x,y) representando coordenadas
    """
    return math.hypot(a[0] - b[0], a[1] - b[1])


def processar_lado(modelo_pose, recorte_bgr, deslocamento_x, estado):
    """
    Processa um lado da imagem para detectar e contar polichinelos

    Parâmetros:
    modelo_pose: modelo MediaPipe de detecção de pose
    recorte_bgr: imagem recortada para processar
    deslocamento_x: deslocamento horizontal para ajuste de coordenadas
    estado: dicionário com estado atual da contagem

    Retorna:
    - estado: dicionário atualizado com nova contagem/fase
    - pontos_para_desenhar: lista de pontos (x,y) em coordenadas do frame completo
    """

    # Obtém dimensões da imagem recortada
    altura, largura, _ = recorte_bgr.shape

    # Lista para pontos a desenhar (ajustada com deslocamento_x)
    pontos_para_desenhar = []

    # Converte imagem de BGR (formato OpenCV) para RGB (formato MediaPipe)
    imagem_rgb = cv2.cvtColor(recorte_bgr, cv2.COLOR_BGR2RGB)

    # Processa a imagem com MediaPipe para detectar poses
    resultados = modelo_pose.process(imagem_rgb)

    # Registra o momento atual para controle temporal
    agora = time.time()
    estado['ultimo_visto'] = agora

    # Se não detectou pessoa, retorna sem alterações
    if not resultados.pose_landmarks:
        return estado, pontos_para_desenhar

    marcos = resultados.pose_landmarks.landmark

    # calcular pontos em pixels relativos ao recorte
    def para_px(indice):
        return (int(marcos[indice].x * largura), int(marcos[indice].y * altura))

    ombro_esq = para_px(OMBRO_ESQUERDO)
    ombro_dir = para_px(OMBRO_DIREITO)
    pulso_esq = para_px(PULSO_ESQUERDO)
    pulso_dir = para_px(PULSO_DIREITO)
    quadril_esq = para_px(QUADRIL_ESQUERDO)
    quadril_dir = para_px(QUADRIL_DIREITO)
    tornozelo_esq = para_px(TORNOZELO_ESQUERDO)
    tornozelo_dir = para_px(TORNOZELO_DIREITO)

    # desenhar landmarks (retornar como deslocados para a imagem inteira)
    for p in (ombro_esq, ombro_dir, pulso_esq, pulso_dir, quadril_esq, quadril_dir, tornozelo_esq, tornozelo_dir):
        pontos_para_desenhar.append((p[0] + deslocamento_x, p[1]))

    # --- MÉTRICAS E LÓGICA DE CONTAGEM ATUALIZADA ---
    y_ombros = (ombro_esq[1] + ombro_dir[1]) / 2.0
    
    # === MÉTRICA 1: Posição ABERTA (Braços) ===
    # Braços estão "abertos" se os pulsos estiverem acima dos ombros
    pulso_acima = (pulso_esq[1] < y_ombros - MARGEM_BRACO_ACIMA_OMBRO * altura) and \
                  (pulso_dir[1] < y_ombros - MARGEM_BRACO_ACIMA_OMBRO * altura)

    # === MÉTRICA 2: Posição ABERTA (Pernas) ===
    distancia_quadril = distancia_euclidiana(quadril_esq, quadril_dir) + 1e-6
    distancia_tornozelos = distancia_euclidiana(tornozelo_esq, tornozelo_dir)
    razao_tornozelo_quadril = distancia_tornozelos / distancia_quadril
    pernas_abertas = razao_tornozelo_quadril >= RAZAO_TORNOZELO_QUADRIL_ABERTO

    # === MÉTRICA 3: Posição FECHADA (Braços) - LÓGICA APERFEIÇOADA ===
    # Braços "fechados" se os pulsos estiverem próximos ou abaixo da linha do quadril
    y_quadris = (quadril_esq[1] + quadril_dir[1]) / 2.0
    pulsos_perto_quadril = (pulso_esq[1] > y_quadris - (MARGEM_PULSO_QUADRIL * altura)) and \
                           (pulso_dir[1] > y_quadris - (MARGEM_PULSO_QUADRIL * altura))

    # === MÉTRICA 4: Posição FECHADA (Pernas) ===
    pernas_fechadas = razao_tornozelo_quadril <= RAZAO_TORNOZELO_QUADRIL_FECHADO

    # === MÉTRICA 5: SIMETRIA DAS PERNAS (Evitar "roubo" de 1 pé) ===
    # 1. Encontrar o centro horizontal do corpo (baseado nos quadris)
    centro_x_quadris = (quadril_esq[0] + quadril_dir[0]) / 2.0
    
    # 2. Calcular distância horizontal de cada tornozelo até esse centro
    dist_tornozelo_esq_centro = abs(tornozelo_esq[0] - centro_x_quadris)
    dist_tornozelo_dir_centro = abs(tornozelo_dir[0] - centro_x_quadris)

    # 3. Calcular a razão entre as distâncias (evita divisão por zero)
    if dist_tornozelo_dir_centro < 1e-6: # Evita divisão por zero
        # Se dir está no centro, esq tbm deve estar (ou ser < 1e-6)
        razao_simetria = 1.0 if dist_tornozelo_esq_centro < 1e-6 else 1000.0
    else:
        razao_simetria = dist_tornozelo_esq_centro / dist_tornozelo_dir_centro

    # 4. Validar se a razão está dentro dos limites de simetria
    # Se a razão for > LIMITE (ex: 2.5) ou < (1/LIMITE) (ex: 0.4), é assimétrico
    pernas_simetricas = (razao_simetria < LIMITE_RAZAO_SIMETRIA) and \
                        (razao_simetria > (1.0 / LIMITE_RAZAO_SIMETRIA))


    # Máquina de estado: fechado -> aberto -> fechado conta +1
    fase = estado.get('fase', 'fechado')

    if fase == 'fechado' or fase == 'desconhecido':
        # esperando abrir
        # === MUDANÇA: Adicionado "and pernas_simetricas" ===
        if pulso_acima and pernas_abertas and pernas_simetricas:
            estado['fase'] = 'aberto'
            estado['tempo_aberto'] = agora
            
    elif fase == 'aberto':
        # esperando fechar para contar
        # === MUDANÇA: Adicionado "and pernas_simetricas" ===
        if pulsos_perto_quadril and pernas_fechadas and pernas_simetricas:
            # transição aberto -> fechado completa um polichinelo
            estado['contagem'] = estado.get('contagem', 0) + 1
            estado['fase'] = 'fechado'
            estado['ultimo_tempo_contagem'] = agora

    return estado, pontos_para_desenhar


def principal(caminho_video=None, max_individuos=2):
    """
    Função principal que gerencia a captura e processamento do vídeo

    Parâmetros:
    caminho_video: caminho do arquivo de vídeo (None para usar webcam)
    max_individuos: número máximo de pessoas a detectar (1 ou 2)
    
    Retorna:
    'VOLTAR_MENU' - Indica que a execução terminou e o menu deve ser mostrado
    """
    if caminho_video:
        captura = cv2.VideoCapture(caminho_video)
    else:
        captura = cv2.VideoCapture(0)

    if not captura.isOpened():
        if caminho_video:
            print(f"Não foi possível abrir o arquivo de vídeo: {caminho_video}")
        else:
            print("Não foi possível abrir a câmera")
        return 'VOLTAR_MENU' # Retorna ao menu se a fonte falhar

    modelo_pose = mp_pose.Pose(min_detection_confidence=CONFIANCA_MIN_DETECCAO,
                               min_tracking_confidence=CONFIANCA_MIN_RASTREAMENTO)

    # estado para os indivíduos (1 ou 2)
    estados = []
    for _ in range(max_individuos):
        estados.append({'fase': 'fechado', 'contagem': 0, 'ultimo_visto': 0.0})

    modo_camera = (caminho_video is None)
    
    # Variáveis para cálculo de FPS
    tempo_anterior = time.time()
    contador_frames = 0
    fps = 0

    # Define o título da janela do OpenCV
    titulo_janela = 'Contador de Polichinelos - Pressione ESC para voltar'
    cv2.namedWindow(titulo_janela) # Cria a janela para poder verificar se foi fechada

    try:
        while True:
            ret, quadro = captura.read()
            
            # === LÓGICA DE SAÍDA ATUALIZADA ===
            # 1. Se o vídeo acabar (ret=False) E for modo vídeo (!modo_camera) -> volta ao menu
            # 2. Se a câmera falhar (ret=False) E for modo câmera (modo_camera) -> volta ao menu
            if not ret or quadro is None:
                if not modo_camera:
                    print("Vídeo terminou. Voltando ao menu.")
                else:
                    print("Falha na captura da câmera. Voltando ao menu.")
                break # Sai do loop

            # 3. Se o usuário fechar a janela no 'X' -> volta ao menu
            # WND_PROP_VISIBLE retorna 0 (ou < 1) se a janela foi fechada
            if cv2.getWindowProperty(titulo_janela, cv2.WND_PROP_VISIBLE) < 1:
                print("Janela fechada pelo usuário. Voltando ao menu.")
                break # Sai do loop

            # Se for modo WebCam, espelhar a imagem para ficar mais natural
            if modo_camera:
                quadro = cv2.flip(quadro, 1)

            altura, largura, _ = quadro.shape

            # Cálculo de FPS
            contador_frames += 1
            tempo_atual = time.time()
            tempo_decorrido = tempo_atual - tempo_anterior
            
            if tempo_decorrido >= 1.0:  # Atualiza FPS a cada segundo
                fps = contador_frames / tempo_decorrido
                contador_frames = 0
                tempo_anterior = tempo_atual

            # desenha linhas divisórias (somente se estiver em modo até 2 indivíduos)
            todos_pontos_para_desenhar = []
            meio = largura // 2
            if max_individuos == 2:
                cv2.line(quadro, (meio, 0), (meio, altura), (200, 200, 200), 2)
                metades = [
                    (0, 0, meio, altura),            # esquerda
                    (meio, 0, largura - meio, altura)   # direita
                ]
            else:
                # 1 indivíduo -> processa toda a imagem como única região
                metades = [
                    (0, 0, largura, altura)
                ]

            for i, (x, y, cw, ch) in enumerate(metades):
                recorte = quadro[y:y+ch, x:x+cw]
                if recorte.size == 0: # Evita erro se o recorte for inválido
                    continue
                    
                estado_atualizado, pontos_desenho = processar_lado(modelo_pose, recorte, x, estados[i])
                estados[i] = estado_atualizado
                if pontos_desenho:
                    todos_pontos_para_desenhar.extend(pontos_desenho)

                # retângulo de região (Cor sutil)
                cv2.rectangle(quadro, (x, y), (x + cw, y + ch), (70, 70, 70), 1)

                # --- EXIBIÇÃO DE CONTAGEM MELHORADA ---
                # Fundo semi-transparente para o texto
                overlay = quadro.copy()
                
                texto = f"PESSOA {i+1}: {estados[i].get('contagem', 0)}"
                if max_individuos == 1:
                    texto = f"TOTAL: {estados[i].get('contagem', 0)}"

                # Posição do texto (canto superior de cada região)
                (w, h), _ = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
                tx = x + 15
                ty = y + 35
                
                cv2.rectangle(overlay, (tx - 5, ty - h - 5), (tx + w + 5, ty + 8), (20, 20, 20), -1)
                cv2.putText(overlay, texto, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (57, 255, 20), 2) # Verde claro
                
                # Aplicar transparência (alpha=0.6)
                alpha = 0.6
                cv2.addWeighted(overlay, alpha, quadro, 1 - alpha, 0, quadro)


            # desenhar pontos detectados (Cor atualizada)
            for (px, py) in todos_pontos_para_desenhar:
                cv2.circle(quadro, (px, py), 5, (255, 200, 0), -1) # Azul claro

            # Exibir FPS no CENTRO superior da tela
            texto_fps = f"FPS: {fps:.1f}"
            (largura_texto, altura_texto), _ = cv2.getTextSize(texto_fps, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            pos_x_fps = (largura - largura_texto) // 2
            cv2.putText(quadro, texto_fps, (pos_x_fps, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2) # Amarelo

            # === MENSAGEM DE SAÍDA ATUALIZADA ===
            cv2.putText(quadro, "Pressione 'ESC' para voltar ao menu", (10, altura - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            cv2.imshow(titulo_janela, quadro)
            
            # === TECLA DE SAÍDA ATUALIZADA ===
            # 4. Se o usuário pressionar 'ESC' -> volta ao menu
            tecla = cv2.waitKey(1) & 0xFF
            if tecla == 27: # 27 é o código ASCII para 'ESC'
                print("Tecla ESC pressionada. Voltando ao menu.")
                break # Sai do loop

    finally:
        # Bloco 'finally' garante que a liberação de recursos ocorra
        # independentemente de como o loop 'while' foi interrompido
        captura.release()
        cv2.destroyAllWindows()
        modelo_pose.close()
        return 'VOLTAR_MENU'


def mostrar_menu():
    """
    Cria e exibe o menu principal da aplicação (com estilo atualizado)
    """
    resultado = {'modo': None, 'caminho': None, 'max_individuos': 2}
    caixa = tk.Tk()
    caixa.title("Contador de Polichinelos - Menu")

    # --- NOVO ESTILO ---
    BG_COLOR = "#2C3E50"      # Azul escuro
    FG_COLOR = "#ECF0F1"      # Branco "sujo"
    BTN_COLOR = "#1ABC9C"     # Verde água
    BTN_FG = "#2C3E50"        # Texto do botão (azul escuro)
    BTN_HOVER = "#16A085"     # Verde mais escuro (hover)
    RADIO_SELECT = "#1ABC9C"  # Cor de seleção do radio
    
    caixa.geometry("480x280")
    caixa.resizable(False, False)
    caixa.configure(bg=BG_COLOR)
    
    # Centralizar janela (mesma lógica de antes)
    largura_janela = 480
    altura_janela = 280
    largura_tela = caixa.winfo_screenwidth()
    altura_tela = caixa.winfo_screenheight()
    pos_x = (largura_tela - largura_janela) // 2
    pos_y = (altura_tela - altura_janela) // 2
    caixa.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
    
    # --- COMPONENTES COM ESTILO ---
    
    # Titulo Aplicação
    rotulo = tk.Label(caixa, text="CONTADOR DE POLICHINELOS", font=("Segoe UI", 16, "bold"), bg=BG_COLOR, fg=FG_COLOR)
    rotulo.pack(pady=(20, 5))

    descricao = tk.Label(caixa, text="Escolha o modo e a configuração de indivíduos.", font=("Segoe UI", 10), bg=BG_COLOR, fg=FG_COLOR)
    descricao.pack(pady=(0, 15))

    # Opção de número de indivíduos (radio)
    var_individuos = tk.IntVar(value=2)
    opcoes = tk.Frame(caixa, bg=BG_COLOR)
    opcoes.pack()
    
    tk.Label(opcoes, text="Detectar:", font=("Segoe UI", 10), bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, padx=5)
    
    # Usando ttk.Radiobutton para melhor estilo (embora o estilo do 'indicador' seja difícil de mudar no Tk)
    tk.Radiobutton(opcoes, text="1 Pessoa", variable=var_individuos, value=1, 
                   font=("Segoe UI", 10), bg=BG_COLOR, fg=FG_COLOR, 
                   selectcolor=BG_COLOR, # Cor do fundo do radio
                   activebackground=BG_COLOR, activeforeground=FG_COLOR,
                   indicatoron=1, borderwidth=0).pack(side=tk.LEFT, padx=10)
                   
    tk.Radiobutton(opcoes, text="Até 2 Pessoas", variable=var_individuos, value=2, 
                   font=("Segoe UI", 10), bg=BG_COLOR, fg=FG_COLOR,
                   selectcolor=BG_COLOR,
                   activebackground=BG_COLOR, activeforeground=FG_COLOR,
                   indicatoron=1, borderwidth=0).pack(side=tk.LEFT, padx=10)

    # --- Funções de Botão ---
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

    # --- Funções de Hover (Efeito visual) ---
    def on_enter(e):
        e.widget.config(bg=BTN_HOVER)

    def on_leave(e):
        e.widget.config(bg=BTN_COLOR)

    # --- Botões ---
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

    # --- LÓGICA DE SAÍDA DO MENU ---
    def ao_fechar():
        # Define o modo como None, para que o loop principal saiba que deve parar
        resultado['modo'] = None 
        caixa.destroy()

    # Se fechar no 'X', chama ao_fechar
    caixa.protocol("WM_DELETE_WINDOW", ao_fechar)
    
    # Se apertar 'ESC' no menu, chama ao_fechar
    caixa.bind('<Escape>', lambda e: ao_fechar())
    
    caixa.mainloop()
    return resultado['modo'], resultado['caminho'], resultado['max_individuos']

# Ponto de entrada do programa
if __name__ == "__main__":
    
    # === LOOP DE EXECUÇÃO PRINCIPAL ===
    # Este loop permite que o programa volte ao menu após a conclusão
    # da webcam/vídeo.
    
    while True:
        # 1. Mostra o menu e espera a seleção do usuário
        modo, caminho, max_inds = mostrar_menu()

        # 2. Verifica a seleção do menu:
        # Se 'modo' for None, significa que o usuário fechou o menu 
        # (pelo 'X' ou pressionando 'ESC'). O programa deve encerrar.
        if modo is None:
            print("Nenhuma opção selecionada. Encerrando.")
            break # Sai do loop 'while True' e termina o script

        # 3. Se um modo foi selecionado, executa a função 'principal'
        status = None
        if modo == 'camera':
            status = principal(None, max_individuos=max_inds)
        elif modo == 'video' and caminho:
            status = principal(caminho, max_individuos=max_inds)

        # 4. A função 'principal' SEMPRE retorna 'VOLTAR_MENU'
        # (seja por ESC, fim do vídeo ou 'X').
        # O 'continue' faz o loop 'while True' recomeçar,
        # chamando 'mostrar_menu()' novamente.
        if status == 'VOLTAR_MENU':
            continue
        else:
            # Caso algo inesperado aconteça
            break