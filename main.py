# Importação das bibliotecas necessárias
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # Suprime avisos do TensorFlow
import cv2  # OpenCV para processamento de imagem e vídeo
import mediapipe as mp  # Framework do Google para detecção de poses
import time  # Para controle de tempo e timestamps
import math  # Para cálculos matemáticos
import numpy as np # Para criar a tela do menu
from tkinter import Tk, filedialog # Para a caixa de diálogo de seleção de arquivo

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

# Margem para considerar o pulso próximo ao quadril (15% da altura do recorte)
MARGEM_PULSO_QUADRIL = 0.05

# Limite para simetria (ex: um pé não pode estar 2.5x mais longe do centro que o outro)
LIMITE_RAZAO_SIMETRIA = 2.5

# ============================================================================
# FUNÇÕES DE DESENHO DA INTERFACE (Baseadas no seu exemplo)
# ============================================================================

def draw_filled_transparent_rect(img, pt1, pt2, color=(0, 0, 0), alpha=0.65):
    """Desenha um retângulo transparente preenchido."""
    overlay = img.copy()
    cv2.rectangle(overlay, pt1, pt2, color, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

def draw_label_box(img, text, org, font=cv2.FONT_HERSHEY_SIMPLEX, scale=0.9, thickness=2,
                   text_color=(255, 255, 255), bg_color=(20, 22, 25), alpha=0.7, padding=10):
    """Desenha uma caixa de texto com fundo."""
    (tw, th), base = cv2.getTextSize(text, font, scale, thickness)
    x, y = org
    x1 = max(x - padding, 0)
    y1 = max(int(y - th - padding), 0)
    x2 = min(int(x + tw + padding), img.shape[1] - 1)
    y2 = min(int(y + base + padding), img.shape[0] - 1)
    draw_filled_transparent_rect(img, (x1, y1), (x2, y2), bg_color, alpha)
    cv2.putText(img, text, (x, y), font, scale, text_color, thickness, cv2.LINE_AA)

def draw_button(canvas, rect, color, label, label_color=(15, 18, 22),
                font=cv2.FONT_HERSHEY_SIMPLEX, scale=0.95, thickness=2):
    """Desenha um botão estilizado no canvas do OpenCV."""
    x1, y1, x2, y2 = rect
    # Sombra
    overlay = canvas.copy()
    cv2.rectangle(overlay, (x1+4, y1+4), (x2+4, y2+4), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.35, canvas, 0.65, 0, canvas)
    # Botão principal
    overlay = canvas.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
    cv2.addWeighted(overlay, 0.88, canvas, 0.12, 0, canvas)
    # Borda
    cv2.rectangle(canvas, (x1, y1), (x2, y2), (245, 245, 245), 2)
    # Texto
    (tw, th), _ = cv2.getTextSize(label, font, scale, thickness)
    tx = x1 + (x2 - x1 - tw) // 2
    ty = y1 + (y2 - y1 + th) // 2
    cv2.putText(canvas, label, (tx, ty), font, scale, label_color, thickness, cv2.LINE_AA)

# ============================================================================
# LÓGICA DE DETECÇÃO (Seu código original, sem NENHUMA alteração)
# ============================================================================

def distancia_euclidiana(a, b):
    """
    Calcula a distância euclidiana entre dois pontos
    a, b: tuplas (x,y) representando coordenadas
    """
    return math.hypot(a[0] - b[0], a[1] - b[1])


def processar_lado(modelo_pose, recorte_bgr, deslocamento_x, estado):
    """
    Processa um lado da imagem para detectar e contar polichinelos
    (Esta é a sua lógica de simetria original)
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
    pulso_acima = (pulso_esq[1] < y_ombros - MARGEM_BRACO_ACIMA_OMBRO * altura) and \
                  (pulso_dir[1] < y_ombros - MARGEM_BRACO_ACIMA_OMBRO * altura)

    # === MÉTRICA 2: Posição ABERTA (Pernas) ===
    distancia_quadril = distancia_euclidiana(quadril_esq, quadril_dir) + 1e-6
    distancia_tornozelos = distancia_euclidiana(tornozelo_esq, tornozelo_dir)
    razao_tornozelo_quadril = distancia_tornozelos / distancia_quadril
    pernas_abertas = razao_tornozelo_quadril >= RAZAO_TORNOZELO_QUADRIL_ABERTO

    # === MÉTRICA 3: Posição FECHADA (Braços) - LÓGICA APERFEIÇOADA ===
    y_quadris = (quadril_esq[1] + quadril_dir[1]) / 2.0
    pulsos_perto_quadril = (pulso_esq[1] > y_quadris - (MARGEM_PULSO_QUADRIL * altura)) and \
                           (pulso_dir[1] > y_quadris - (MARGEM_PULSO_QUADRIL * altura))

    # === MÉTRICA 4: Posição FECHADA (Pernas) ===
    pernas_fechadas = razao_tornozelo_quadril <= RAZAO_TORNOZELO_QUADRIL_FECHADO

    # === MÉTRICA 5: SIMETRIA DAS PERNAS (Evitar "roubo" de 1 pé) ===
    centro_x_quadris = (quadril_esq[0] + quadril_dir[0]) / 2.0
    dist_tornozelo_esq_centro = abs(tornozelo_esq[0] - centro_x_quadris)
    dist_tornozelo_dir_centro = abs(tornozelo_dir[0] - centro_x_quadris)

    if dist_tornozelo_dir_centro < 1e-6:
        razao_simetria = 1.0 if dist_tornozelo_esq_centro < 1e-6 else 1000.0
    else:
        razao_simetria = dist_tornozelo_esq_centro / dist_tornozelo_dir_centro

    pernas_simetricas = (razao_simetria < LIMITE_RAZAO_SIMETRIA) and \
                        (razao_simetria > (1.0 / LIMITE_RAZAO_SIMETRIA))

    # Máquina de estado: fechado -> aberto -> fechado conta +1
    fase = estado.get('fase', 'fechado')

    if fase == 'fechado' or fase == 'desconhecido':
        # esperando abrir
        if pulso_acima and pernas_abertas and pernas_simetricas:
            estado['fase'] = 'aberto'
            estado['tempo_aberto'] = agora
            
    elif fase == 'aberto':
        # esperando fechar para contar
        if pulsos_perto_quadril and pernas_fechadas and pernas_simetricas:
            # transição aberto -> fechado completa um polichinelo
            estado['contagem'] = estado.get('contagem', 0) + 1
            estado['fase'] = 'fechado'
            estado['ultimo_tempo_contagem'] = agora

    return estado, pontos_para_desenhar

def principal(caminho_video=None, max_individuos=2):
    """
    Função principal que gerencia a captura e processamento do vídeo
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
        return 'VOLTAR_MENU' 

    modelo_pose = mp_pose.Pose(min_detection_confidence=CONFIANCA_MIN_DETECCAO,
                               min_tracking_confidence=CONFIANCA_MIN_RASTREAMENTO)

    # estado para os indivíduos (1 ou 2)
    estados = []
    for _ in range(max_individuos):
        estados.append({'fase': 'fechado', 'contagem': 0, 'ultimo_visto': 0.0})

    modo_camera = (caminho_video is None)

    # Define o título da janela do OpenCV
    titulo_janela = 'Contador de Polichinelos - ESC para voltar'
    cv2.namedWindow(titulo_janela) 

    try:
        while True:
            ret, quadro = captura.read()
            
            if not ret or quadro is None:
                if not modo_camera:
                    print("Vídeo terminou. Voltando ao menu.")
                else:
                    print("Falha na captura da câmera. Voltando ao menu.")
                break 

            if cv2.getWindowProperty(titulo_janela, cv2.WND_PROP_VISIBLE) < 1:
                print("Janela fechada pelo usuário. Voltando ao menu.")
                break 

            if modo_camera:
                quadro = cv2.flip(quadro, 1)

            altura, largura, _ = quadro.shape

            # desenha linhas divisórias (somente se estiver em modo até 2 indivíduos)
            todos_pontos_para_desenhar = []
            meio = largura // 2
            if max_individuos == 2:
                cv2.line(quadro, (meio, 0), (meio, altura), (200, 200, 200), 2)
                metades = [
                    (0, 0, meio, altura),            
                    (meio, 0, largura - meio, altura)   
                ]
            else:
                metades = [
                    (0, 0, largura, altura)
                ]

            for i, (x, y, cw, ch) in enumerate(metades):
                recorte = quadro[y:y+ch, x:x+cw]
                if recorte.size == 0: 
                    continue
                    
                estado_atualizado, pontos_desenho = processar_lado(modelo_pose, recorte, x, estados[i])
                estados[i] = estado_atualizado
                if pontos_desenho:
                    todos_pontos_para_desenhar.extend(pontos_desenho)

                cv2.rectangle(quadro, (x, y), (x + cw, y + ch), (70, 70, 70), 1)

                # --- EXIBIÇÃO DE CONTAGEM MELHORADA ---
                overlay = quadro.copy()
                
                texto = f"JOGADOR {i+1}: {estados[i].get('contagem', 0)}"
                if max_individuos == 1:
                    texto = f"REPETICOES: {estados[i].get('contagem', 0)}"

                (w, h), _ = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
                tx = x + 15
                ty = y + 35
                
                cv2.rectangle(overlay, (tx - 5, ty - h - 5), (tx + w + 5, ty + 8), (20, 20, 20), -1)
                cv2.putText(overlay, texto, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (57, 255, 20), 2) 
                
                alpha = 0.6
                cv2.addWeighted(overlay, alpha, quadro, 1 - alpha, 0, quadro)

            # desenhar pontos detectados
            for (px, py) in todos_pontos_para_desenhar:
                cv2.circle(quadro, (px, py), 5, (255, 200, 0), -1) 

            cv2.putText(quadro, "Pressione 'ESC' para voltar ao menu", (10, altura - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            cv2.imshow(titulo_janela, quadro)
            
            tecla = cv2.waitKey(1) & 0xFF
            if tecla == 27: 
                print("Tecla ESC pressionada. Voltando ao menu.")
                break 

    finally:
        captura.release()
        cv2.destroyAllWindows()
        modelo_pose.close()
        return 'VOLTAR_MENU'

# ============================================================================
# FUNÇÃO DE MENU
# ============================================================================

def mostrar_menu_cv2():
    """
    Cria e exibe o menu principal da aplicação (usando OpenCV).
    Implementa a lógica de desativar o botão de vídeo para 2 jogadores.
    """
    resultado = {'modo': None, 'caminho': None, 'max_individuos': 1} # Padrão para 1
    max_individuos = 1 # Estado atual da seleção
    
    # Novo Estilo
    BG_COLOR = (24, 24, 24)
    TITLE_COLOR = (0, 220, 220) # Ciano
    TEXT_COLOR = (230, 230, 230)
    
    BTN_SOLO_COLOR = (80, 80, 80)
    BTN_SOLO_SEL_COLOR = (150, 150, 150)
    BTN_DUPLA_COLOR = (80, 80, 80)
    BTN_DUPLA_SEL_COLOR = (150, 150, 150)
    
    BTN_WEBCAM_COLOR = (0, 100, 150) # Azul
    BTN_VIDEO_COLOR = (100, 150, 0) # Verde
    BTN_VIDEO_DISABLED_COLOR = (60, 60, 60) # Cinza escuro
    
    BTN_TEXT_COLOR = (255, 255, 255)
    BTN_TEXT_DARK = (20, 20, 20)

    window_name = "Menu Principal - Analisador de Movimento"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 720, 500)

    while True:
        # Cria a tela do menu
        tela = np.ones((500, 720, 3), dtype=np.uint8) * 24
        
        # Título
        draw_filled_transparent_rect(tela, (0, 0), (720, 80), (15, 15, 15), 0.9)
        cv2.putText(tela, "ANALISADOR DE MOVIMENTO", (40, 55), cv2.FONT_HERSHEY_DUPLEX, 1.0, TITLE_COLOR, 2, cv2.LINE_AA)

        # --- 1. Seleção de Modo (1 ou 2) ---
        cv2.putText(tela, "1. Escolha o Modo de Deteccao:", (40, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, TEXT_COLOR, 2, cv2.LINE_AA)
        
        # Botão 1 - Individual
        cor_solo = BTN_SOLO_SEL_COLOR if max_individuos == 1 else BTN_SOLO_COLOR
        label_cor_solo = BTN_TEXT_DARK if max_individuos == 1 else BTN_TEXT_COLOR
        draw_button(tela, (80, 150, 340, 200), cor_solo, "[1] Individual", label_color=label_cor_solo)

        # Botão 2 - Dupla
        cor_dupla = BTN_DUPLA_SEL_COLOR if max_individuos == 2 else BTN_DUPLA_COLOR
        label_cor_dupla = BTN_TEXT_DARK if max_individuos == 2 else BTN_TEXT_COLOR
        draw_button(tela, (380, 150, 640, 200), cor_dupla, "[2] Dupla", label_color=label_cor_dupla)

        # --- 2. Seleção de Fonte (Webcam ou Video) ---
        cv2.putText(tela, "2. Escolha a Fonte de Video:", (40, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, TEXT_COLOR, 2, cv2.LINE_AA)

        # Botão C - Webcam
        draw_button(tela, (80, 280, 640, 330), BTN_WEBCAM_COLOR, "[C] Iniciar Camera Ao Vivo", label_color=BTN_TEXT_COLOR)

        # Botão V - Carregar Arquivo (com lógica de desativar)
        cor_video = BTN_VIDEO_COLOR
        texto_video = "[V] Carregar Arquivo de Video"
        if max_individuos == 2:
            # Lógica para desativar o botão
            cor_video = BTN_VIDEO_DISABLED_COLOR
            texto_video = "[V] Carregar (Apenas Individual)"
            
        draw_button(tela, (80, 350, 640, 400), cor_video, texto_video, label_color=BTN_TEXT_COLOR)
        
        # --- Instruções ---
        draw_label_box(tela, "Use 1 e 2 para trocar o modo. Pressione C ou V para iniciar.", (40, 450), font=cv2.FONT_HERSHEY_PLAIN, scale=1.2)
        cv2.putText(tela, "ESC para Sair", (500, 480), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1, cv2.LINE_AA)
        
        cv2.imshow(window_name, tela)
        
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            # Verifica se o usuário fechou a janela do menu no 'X'
            resultado['modo'] = None
            break

        key = cv2.waitKey(1) & 0xFF

        if key == 27: # ESC
            resultado['modo'] = None
            break
        
        elif key == ord('1'):
            max_individuos = 1
            resultado['max_individuos'] = 1
        
        elif key == ord('2'):
            max_individuos = 2
            resultado['max_individuos'] = 2
            
        elif key == ord('c'): # Iniciar Webcam
            resultado['modo'] = 'camera'
            break
            
        elif key == ord('v'): # Carregar Video
            if max_individuos == 2:
                # Botão está desativado, não faz nada
                pass 
            else:
                # Usar Tkinter escondido para abrir o seletor de arquivo
                root = Tk()
                root.withdraw() # Esconde a janela principal do Tkinter
                caminho = filedialog.askopenfilename(title="Selecione um arquivo de vídeo", filetypes=[("Arquivos de vídeo", ("*.mp4", "*.avi", "*.mov", "*.mkv")), ("Todos os arquivos", "*.*")])
                root.destroy()
                if caminho:
                    resultado['modo'] = 'video'
                    resultado['caminho'] = caminho
                    break
                else:
                    # O usuário cancelou a seleção, continua no menu
                    pass 
                    
    cv2.destroyWindow(window_name)
    return resultado['modo'], resultado['caminho'], resultado['max_individuos']

# Ponto de entrada do programa
if __name__ == "__main__":
    
    # === LOOP DE EXECUÇÃO PRINCIPAL ===
    # Este loop permite que o programa volte ao menu após a conclusão
    # da webcam/vídeo.
    
    while True:
        # 1. Mostra o novo menu CV2 e espera a seleção do usuário
        modo, caminho, max_inds = mostrar_menu_cv2()

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
            # A lógica no menu já impede que isso seja chamado com max_inds == 2
            status = principal(caminho, max_individuos=max_inds)

        # 4. A função 'principal' SEMPRE retorna 'VOLTAR_MENU'
        # (seja por ESC, fim do vídeo ou 'X').
        # O 'continue' faz o loop 'while True' recomeçar,
        # chamando 'mostrar_menu_cv2()' novamente.
        if status == 'VOLTAR_MENU':
            continue
        else:
            # Caso algo inesperado aconteça
            break