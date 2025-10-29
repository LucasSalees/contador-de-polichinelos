import cv2
import mediapipe as mp
import numpy as np
from tkinter import Tk, filedialog
from datetime import datetime
import time
import copy

# ============================================================================
# TEMA / DESIGN (TEMA CLARO)
# ============================================================================

THEME = {
    'COLORS': {
        'bg': (245, 245, 245),      # Fundo claro
        'accent': (0, 120, 230),       # Azul
        'accent_j2': (230, 120, 60),  # Laranja
        'text': (20, 20, 20),          # Texto principal (escuro)
        'text_secondary': (100, 100, 100),# Texto secundário (cinza)
        'warn': (220, 50, 50),       # Vermelho/Aviso
        'success': (0, 180, 80),      # Verde
        'box_bg': (255, 255, 255),    # Fundo de caixas (branco puro)
        'hud_bg': (255, 255, 255)     # Fundo do painel no jogo (branco)
    },
    'FONTS': {
        'title': cv2.FONT_HERSHEY_DUPLEX,
        'body': cv2.FONT_HERSHEY_SIMPLEX
    }
}

# Atalhos para facilitar o uso
COLORS = THEME['COLORS']
FONTS = THEME['FONTS']

# ============================================================================
# FUNÇÃO DE TELA CHEIA (Sem alteração)
# ============================================================================

def show_fullscreen(window_name, img):
    """Cria ou atualiza uma janela para ser exibida em tela cheia."""
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow(window_name, img)

# ============================================================================
# FUNÇÕES DE DESENHO (Sem alteração)
# ============================================================================

def draw_filled_transparent_rect(img, pt1, pt2, color, alpha=0.85):
    """Função de desenho base"""
    overlay = img.copy()
    cv2.rectangle(overlay, pt1, pt2, color, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

def draw_gradient_rect(img, pt1, pt2, color1, color2):
    """(Sem alteração de lógica)"""
    x1, y1 = pt1
    x2, y2 = pt2
    for i, y in enumerate(range(y1, y2)):
        ratio = (y - y1) / (y2 - y1)
        color = tuple(int(c1 * (1 - ratio) + c2 * ratio) for c1, c2 in zip(color1, color2))
        cv2.line(img, (x1, y), (x2, y), color, 1)

def draw_label_box(img, text, org, font=FONTS['body'], scale=0.7, thickness=2,
                   text_color=COLORS['text'], bg_color=COLORS['hud_bg'], alpha=0.7, padding=10):
    """Função de caixa de texto"""
    (tw, th), base = cv2.getTextSize(text, font, scale, thickness)
    x, y = org
    x1 = max(x - padding, 0)
    y1 = max(int(y - th - padding), 0)
    x2 = min(int(x + tw + padding), img.shape[1] - 1)
    y2 = min(int(y + base + padding), img.shape[0] - 1)
    draw_filled_transparent_rect(img, (x1, y1), (x2, y2), bg_color, alpha)
    cv2.putText(img, text, (x, y), font, scale, text_color, thickness, cv2.LINE_AA)

def draw_modern_button(canvas, rect, color, label, label_color=COLORS['bg'],
                       font=FONTS['body'], scale=0.9, thickness=2):
    """Função de botão redesenhada para tema claro"""
    x1, y1, x2, y2 = rect
    
    # Sombra leve
    draw_filled_transparent_rect(canvas, (x1+4, y1+4), (x2+4, y2+4), (0, 0, 0), alpha=0.1)

    # Botão principal
    cv2.rectangle(canvas, (x1, y1), (x2, y2), color, -1)
    # Borda (sutil)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), COLORS['text_secondary'], 1) 
    
    (tw, th), _ = cv2.getTextSize(label, font, scale, thickness)
    tx = x1 + (x2 - x1 - tw) // 2
    ty = y1 + (y2 - y1 + th) // 2
    
    # Texto do botão
    cv2.putText(canvas, label, (tx, ty), font, scale, label_color, thickness, cv2.LINE_AA)

def putText_outline(img, text, org, font, scale, color, thickness=2,
                    outline_color=COLORS['bg'], outline_thickness=None):
    """Contorno atualizado para tema claro"""
    if outline_thickness is None:
        outline_thickness = max(1, thickness + 1)
    cv2.putText(img, text, org, font, scale, outline_color, outline_thickness, cv2.LINE_AA)
    cv2.putText(img, text, org, font, scale, color, thickness, cv2.LINE_AA)

# ============================================================================
# TELA DE RESULTADO (ANÁLISE DE VÍDEO) - (Sem alteração)
# ============================================================================
def mostrar_resultado_analise(counter_final, tempo_total):
    """Mostra o resultado final da análise de vídeo."""
    window_name = "Resultado da Analise"
    while True:
        tela = np.ones((400, 800, 3), dtype=np.uint8) * COLORS['bg'][0]
        
        # Cabeçalho
        draw_filled_transparent_rect(tela, (0, 0), (800, 80), COLORS['box_bg'], 0.9)
        cv2.putText(tela, "ANALISE CONCLUIDA", (40, 55), FONTS['title'], 1.0, COLORS['accent'], 2, cv2.LINE_AA)

        # Stats
        stats_text = f"Total de Polichinelos: {counter_final}"
        duration_text = f"Duracao Analisada: {int(tempo_total // 60):02d}m {int(tempo_total % 60):02d}s"

        cv2.putText(tela, stats_text, (60, 150), FONTS['body'], 1.0, COLORS['text'], 2, cv2.LINE_AA)
        cv2.putText(tela, duration_text, (60, 200), FONTS['body'], 0.9, COLORS['text_secondary'], 2, cv2.LINE_AA)

        # Botão
        draw_modern_button(tela, (250, 300, 550, 350), COLORS['warn'], "[ESC] VOLTAR AO MENU")
        
        show_fullscreen(window_name, tela)
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27: # ESC
            cv2.destroyWindow(window_name)
            break # Volta ao menu principal

# ============================================================================
# CLASSES DE LÓGICA DO JOGO (Sem alteração)
# ============================================================================

class CompetitionSystem:
    def __init__(self, jogador1, jogador2, meta_polichinelos=20):
        self.jogador1 = jogador1
        self.jogador2 = jogador2
        self.meta_polichinelos = meta_polichinelos
        self.tempo_inicio = time.time()
        self.contador1 = 0
        self.contador2 = 0
        self.vencedor = None
        self.tempo_final = None

    def registrar_polichinelo(self, jogador):
        if self.vencedor: return
        if jogador == 1:
            self.contador1 += 1
            if self.contador1 >= self.meta_polichinelos:
                self.vencedor = 1
                self.tempo_final = time.time() - self.tempo_inicio
        else:
            self.contador2 += 1
            if self.contador2 >= self.meta_polichinelos:
                self.vencedor = 2
                self.tempo_final = time.time() - self.tempo_inicio

    def get_stats(self):
        return self.contador1, self.contador2

# ============================================================================
# INTERFACE COM O USUÁRIO (Sem alteração)
# ============================================================================

def obter_nome_estilizado(prompt_text, window_title, default_name):
    # (Função mantida para o Modo Competição)
    nome = ""
    max_chars = 15
    window_name = f"Input - {window_title}"
    while True:
        tela = np.ones((400, 700, 3), dtype=np.uint8) * COLORS['bg'][0]
        
        # Cabeçalho
        draw_filled_transparent_rect(tela, (0, 0), (700, 80), COLORS['box_bg'], 0.9)
        cv2.putText(tela, window_title, (40, 55), FONTS['title'], 1.0, COLORS['accent'], 2, cv2.LINE_AA)
        
        # Prompt
        cv2.putText(tela, prompt_text, (40, 130), FONTS['body'], 0.8, COLORS['text_secondary'], 2, cv2.LINE_AA)
        
        # Caixa de Input
        input_box_rect = (40, 170, 660, 230)
        cv2.rectangle(tela, (input_box_rect[0], input_box_rect[1]), (input_box_rect[2], input_box_rect[3]), COLORS['box_bg'], -1)
        cv2.rectangle(tela, (input_box_rect[0], input_box_rect[1]), (input_box_rect[2], input_box_rect[3]), COLORS['text_secondary'], 2)
        
        # Texto e Cursor
        (tw, th), _ = cv2.getTextSize(nome, FONTS['body'], 1.2, 3)
        text_y = input_box_rect[1] + (input_box_rect[3] - input_box_rect[1] + th) // 2
        cursor = "|" if int(time.time() * 2) % 2 == 0 else " " # Cursor pisca
        cv2.putText(tela, nome + cursor, (input_box_rect[0] + 15, text_y), FONTS['body'], 1.2, COLORS['text'], 3, cv2.LINE_AA)
        
        # Helper
        cv2.putText(tela, "Pressione ENTER para confirmar ou ESC para voltar", (40, 350), FONTS['body'], 0.7, COLORS['text_secondary'], 1, cv2.LINE_AA)
        
        show_fullscreen(window_name, tela)
        
        key = cv2.waitKey(50)
        if key == 13:
            cv2.destroyWindow(window_name)
            return nome.strip() if nome.strip() else default_name
        elif key == 27:
            cv2.destroyWindow(window_name)
            return None # Volta ao menu
        elif key == 8:
            nome = nome[:-1]
        elif key != -1 and len(nome) < max_chars and 32 <= key <= 126:
            nome += chr(key)

def obter_nomes_jogadores():
    nome1 = obter_nome_estilizado("Digite o nome do JOGADOR 1:", "Modo Competicao", "Jogador1")
    if nome1 is None: return None, None # Volta ao menu
    nome2 = obter_nome_estilizado("Digite o nome do JOGADOR 2:", "Modo Competicao", "Jogador2")
    if nome2 is None: return nome1, None # Volta ao menu
    return nome1, nome2

def escolher_modo():
    """Menu principal (Sem alteração)"""
    window_name = "Selecao de Modo"
    while True:
        tela = np.ones((500, 720, 3), dtype=np.uint8) * COLORS['bg'][0]
        
        # Cabeçalho
        draw_filled_transparent_rect(tela, (0, 0), (720, 100), COLORS['box_bg'], 0.9)
        cv2.putText(tela, "CONTADOR DE POLICHINELOS", (40, 50), FONTS['title'], 1.2, COLORS['text'], 2, cv2.LINE_AA)
        cv2.putText(tela, "Selecione um modo com as teclas 1-3", (40, 80), FONTS['body'], 0.7, COLORS['text_secondary'], 1, cv2.LINE_AA)
        
        # Botões
        draw_modern_button(tela, (80, 120, 640, 170), COLORS['accent'], "[1] MODO SOLO")
        draw_modern_button(tela, (80, 190, 640, 240), COLORS['accent_j2'], "[2] MODO COMPETICAO")
        draw_modern_button(tela, (80, 260, 640, 310), COLORS['text_secondary'], "[3] ANALISAR VIDEO", label_color=COLORS['bg']) 
        
        # Helper
        cv2.putText(tela, "Pressione [ESC] para FECHAR O APLICATIVO", (40, 450), FONTS['body'], 0.7, COLORS['warn'], 1, cv2.LINE_AA)
        
        show_fullscreen(window_name, tela)
        
        key = cv2.waitKey(1)
        if key == ord("1"): cv2.destroyWindow(window_name); return 0
        elif key == ord("2"): cv2.destroyWindow(window_name); return 1
        elif key == ord("3"): cv2.destroyWindow(window_name); return 2
        elif key == 27: cv2.destroyWindow(window_name); return None # Sai do aplicativo

def escolher_meta():
    """Tela de meta (Sem alteração)"""
    window_name = "Escolha da Meta"
    while True:
        tela = np.ones((500, 650, 3), dtype=np.uint8) * COLORS['bg'][0]
        
        # Cabeçalho
        draw_filled_transparent_rect(tela, (0, 0), (650, 80), COLORS['box_bg'], 0.9)
        cv2.putText(tela, "ESCOLHA A META DE REPETICOES", (40, 55), FONTS['title'], 1.0, COLORS['accent'], 2, cv2.LINE_AA)
        
        metas = [10, 20, 30, 50]
        descricoes = ["Iniciante", "Intermediario", "Avancado", "Expert"]
        
        y_pos = 120
        for i, (meta, desc) in enumerate(zip(metas, descricoes)):
            draw_modern_button(tela, (80, y_pos, 570, y_pos + 55), COLORS['accent'], f"[{i+1}] {meta} Repeticoes ({desc})")
            y_pos += 75
        
        # Helper
        cv2.putText(tela, "Pressione 1-4 para selecionar ou ESC para voltar ao menu", (40, 450), FONTS['body'], 0.7, COLORS['text_secondary'], 1, cv2.LINE_AA)
            
        show_fullscreen(window_name, tela)
        
        key = cv2.waitKey(1)
        if key in [ord('1'), ord('2'), ord('3'), ord('4')]:
            cv2.destroyWindow(window_name)
            return metas[key - ord('1')]
        elif key == 27:
            cv2.destroyWindow(window_name)
            return None # Volta ao menu principal

# ============================================================================
# TELAS DE RESULTADO (Sem alteração)
# ============================================================================

def mostrar_resultado_solo_simples(nome_usuario, counter_final, meta, tempo_total):
    """Mostra o resultado final do modo solo"""
    window_name = "Resultado Final"
    while True:
        tela = np.ones((450, 800, 3), dtype=np.uint8) * COLORS['bg'][0]
        
        # Cabeçalho
        draw_filled_transparent_rect(tela, (0, 0), (800, 80), COLORS['box_bg'], 0.9)
        cv2.putText(tela, "EXERCICIO CONCLUIDO", (40, 55), FONTS['title'], 1.0, COLORS['accent'], 2, cv2.LINE_AA)

        # Stats
        cv2.putText(tela, f"Jogador: {nome_usuario}", (60, 140), FONTS['body'], 1.0, COLORS['text'], 2, cv2.LINE_AA)
        cv2.putText(tela, f"Polichinelos: {counter_final} / {meta}", (60, 190), FONTS['body'], 0.9, COLORS['text_secondary'], 2, cv2.LINE_AA)
        cv2.putText(tela, f"Tempo Total: {int(tempo_total // 60):02d}m {int(tempo_total % 60):02d}s", (60, 230), FONTS['body'], 0.9, COLORS['text_secondary'], 2, cv2.LINE_AA)

        # Botões
        draw_modern_button(tela, (80, 320, 380, 370), COLORS['success'], "[ENTER] REINICIAR")
        draw_modern_button(tela, (420, 320, 720, 370), COLORS['warn'], "[ESC] MENU PRINCIPAL")
        
        show_fullscreen(window_name, tela)
        key = cv2.waitKey(1) & 0xFF
        if key == 13:
            cv2.destroyWindow(window_name)
            return True # Reiniciar
        elif key == 27:
            cv2.destroyWindow(window_name)
            return False # Sair para o menu

def mostrar_resultado_competicao_simples(competition, counter1, counter2):
    """Tela de resultado da competição"""
    window_name = "Resultado da Competicao"
    tempo_total = int(competition.tempo_final) if competition.tempo_final else int(time.time() - competition.tempo_inicio)
    
    vencedor_nome = "Ninguem"
    if competition.vencedor:
        vencedor_nome = competition.jogador1 if competition.vencedor == 1 else competition.jogador2
    
    while True:
        tela = np.ones((600, 900, 3), dtype=np.uint8) * COLORS['bg'][0]
        
        # Cabeçalho
        draw_filled_transparent_rect(tela, (0, 0), (900, 80), COLORS['box_bg'], 0.9)
        cv2.putText(tela, "COMPETICAO FINALIZADA", (40, 55), FONTS['title'], 1.0, COLORS['accent'], 2, cv2.LINE_AA)
        
        # Vencedor
        if competition.vencedor:
            resultado_texto = f"VENCEDOR: {vencedor_nome.upper()}!"
            cv2.putText(tela, resultado_texto, (40, 140), FONTS['title'], 1.2, COLORS['success'], 3, cv2.LINE_AA)
        else:
            cv2.putText(tela, "A competicao terminou sem um vencedor.", (40, 140), FONTS['body'], 1.0, COLORS['text_secondary'], 2, cv2.LINE_AA)

        col1_x, col2_x = 80, 480
        
        # Jogador 1
        cv2.putText(tela, f"{competition.jogador1.upper()}", (col1_x, 220), FONTS['body'], 1.1, COLORS['accent'], 2, cv2.LINE_AA)
        cv2.putText(tela, f"Polichinelos: {counter1} / {competition.meta_polichinelos}", (col1_x, 260), FONTS['body'], 0.9, COLORS['text'], 2, cv2.LINE_AA)

        # Jogador 2
        cv2.putText(tela, f"{competition.jogador2.upper()}", (col2_x, 220), FONTS['body'], 1.1, COLORS['accent_j2'], 2, cv2.LINE_AA)
        cv2.putText(tela, f"Polichinelos: {counter2} / {competition.meta_polichinelos}", (col2_x, 260), FONTS['body'], 0.9, COLORS['text'], 2, cv2.LINE_AA)

        # Tempo
        cv2.line(tela, (40, 320), (860, 320), COLORS['text_secondary'], 1)
        cv2.putText(tela, f"Tempo Total: {tempo_total//60:02d}m {tempo_total%60:02d}s", (40, 360), FONTS['body'], 0.9, COLORS['text_secondary'], 2, cv2.LINE_AA)

        # Botões
        draw_modern_button(tela, (100, 450, 400, 500), COLORS['success'], "[ENTER] NOVA PARTIDA")
        draw_modern_button(tela, (500, 450, 800, 500), COLORS['warn'], "[ESC] MENU PRINCIPAL")
        
        show_fullscreen(window_name, tela)
        key = cv2.waitKey(1)
        
        if key == 13:
            cv2.destroyWindow(window_name)
            return True # Reiniciar
        elif key == 27:
            cv2.destroyWindow(window_name)
            return False # Sair para o menu

# ============================================================================
# DETECÇÃO E PROCESSAMENTO DE POSE (Sem alteração)
# ============================================================================

def detectar_multiplas_pessoas_corrigido(image, pose_model_j1, pose_model_j2):
    h, w = image.shape[:2]
    meio_x = w // 2
    
    jogador1_landmarks, jogador2_landmarks = None, None
    jogador1_original, jogador2_original = None, None
    
    frame_esquerdo = image[:, :meio_x].copy()
    resultado_esquerda = pose_model_j1.process(cv2.cvtColor(frame_esquerdo, cv2.COLOR_BGR2RGB))
    if resultado_esquerda.pose_landmarks:
        jogador1_landmarks = copy.deepcopy(resultado_esquerda.pose_landmarks)
        jogador1_original = copy.deepcopy(resultado_esquerda.pose_landmarks)
        for landmark in jogador1_landmarks.landmark:
            landmark.x = landmark.x * 0.5
    
    frame_direito = image[:, meio_x:].copy()
    resultado_direita = pose_model_j2.process(cv2.cvtColor(frame_direito, cv2.COLOR_BGR2RGB))
    if resultado_direita.pose_landmarks:
        jogador2_landmarks = copy.deepcopy(resultado_direita.pose_landmarks)
        jogador2_original = copy.deepcopy(resultado_direita.pose_landmarks)
        for landmark in jogador2_landmarks.landmark:
            landmark.x = (landmark.x * 0.5) + 0.5
    
    return jogador1_landmarks, jogador2_landmarks, jogador1_original, jogador2_original, meio_x

def validar_pose_melhorada(landmarks):
    if not landmarks: return False, 0.0
    
    pontos_criticos = [11, 12, 23, 24, 15, 16, 27, 28]
    visibilidades = [landmarks.landmark[idx].visibility for idx in pontos_criticos if idx < len(landmarks.landmark)]
    
    if not visibilidades: return False, 0.0
    
    vis_media = sum(visibilidades) / len(visibilidades)
    vis_minima = min(visibilidades)
    return vis_media >= 0.35 and vis_minima >= 0.25, vis_media

def detectar_postura_polichinelo_competicao(landmarks, w, h):
    def pt(lm_id): return (landmarks.landmark[lm_id].x * w, landmarks.landmark[lm_id].y * h, landmarks.landmark[lm_id].visibility)
    
    l_sh_x, l_sh_y, l_sh_vis = pt(11); r_sh_x, r_sh_y, r_sh_vis = pt(12)
    l_hp_x, l_hp_y, l_hp_vis = pt(23); r_hp_x, r_hp_y, r_hp_vis = pt(24)
    l_wr_x, l_wr_y, l_wr_vis = pt(15); r_wr_x, r_wr_y, r_wr_vis = pt(16)
    l_an_x, l_an_y, l_an_vis = pt(27); r_an_x, r_an_y, r_an_vis = pt(28)
    l_el_x, l_el_y, l_el_vis = pt(13); r_el_x, r_el_y, r_el_vis = pt(14)
    
    shoulder_mid_y = (l_sh_y + r_sh_y) / 2.0; hip_mid_y = (l_hp_y + r_hp_y) / 2.0
    shoulder_width = abs(r_sh_x - l_sh_x); body_height = abs(hip_mid_y - shoulder_mid_y)
    wrist_mid_y = (l_wr_y + r_wr_y) / 2.0; elbow_mid_y = (l_el_y + r_el_y) / 2.0
    
    tolerance_up, tolerance_down = 0.15 * body_height, 0.10 * body_height
    
    arms_up = (wrist_mid_y < shoulder_mid_y + tolerance_up and elbow_mid_y < shoulder_mid_y + tolerance_up)
    arms_down = (wrist_mid_y > hip_mid_y - tolerance_down)
    normalized_distance = abs(r_an_x - l_an_x) / shoulder_width if shoulder_width > 20 else 0
    
    legs_open = (normalized_distance > 1.3 and l_an_vis > 0.3 and r_an_vis > 0.3)
    legs_closed = (normalized_distance < 1.5 and l_an_vis > 0.3 and r_an_vis > 0.3)
    
    return arms_up, legs_open, arms_down, legs_closed

def processar_jogador_competicao(landmarks, landmarks_original, w, h, jogador_num, counter, stage, open_frames, closed_frames, flash_frames, competition, frame_atual):
    # (Lógica de contagem original mantida - threshold 2)
    if not landmarks: return counter, stage, max(0, open_frames - 2), max(0, closed_frames - 2), flash_frames, "Pessoa nao detectada"
    
    pose_valida, vis_media = validar_pose_melhorada(landmarks_original or landmarks)
    if not pose_valida: return counter, stage, max(0, open_frames - 1), max(0, closed_frames - 1), flash_frames, f"Pose invalida (vis: {vis_media:.2f})"
    
    arms_up, legs_open, arms_down, legs_closed = detectar_postura_polichinelo_competicao(landmarks_original or landmarks, w, h)
    
    status = ""
    if arms_up and legs_open:
        open_frames = min(open_frames + 1, 15)
        closed_frames = max(0, closed_frames - 1)
    elif arms_down and legs_closed:
        closed_frames = min(closed_frames + 1, 15)
        open_frames = max(0, open_frames - 1)
    else:
        open_frames, closed_frames = max(0, open_frames - 1), max(0, closed_frames - 1)

    threshold = 2
    
    if stage == "down" and open_frames >= threshold:
        stage = "up"
        closed_frames = 0
    elif stage == "up" and closed_frames >= threshold:
        stage = "down"
        counter += 1
        competition.registrar_polichinelo(jogador_num)
        open_frames = 0
        flash_frames = 15
    
    return counter, stage, open_frames, closed_frames, flash_frames, status

def detectar_postura_polichinelo(landmarks, w, h):
    # (Lógica original do Modo Solo/Análise - Sem alteração)
    def pt(lm_id): return (landmarks[lm_id].x * w, landmarks[lm_id].y * h)
    
    l_sh_x, l_sh_y = pt(11); r_sh_x, r_sh_y = pt(12)
    l_hp_x, l_hp_y = pt(23); r_hp_x, r_hp_y = pt(24)
    l_wr_x, l_wr_y = pt(15); r_wr_x, r_wr_y = pt(16)
    l_an_x, l_an_y = pt(27); r_an_x, r_an_y = pt(28)
    l_el_y = pt(13)[1]; r_el_y = pt(14)[1]
    
    shoulder_mid_y = (l_sh_y + r_sh_y) / 2.0
    hip_mid_y = (l_hp_y + r_hp_y) / 2.0
    body_width = max(abs(r_sh_x - l_sh_x), 1)
    body_height = abs(hip_mid_y - shoulder_mid_y)
    wrist_mid_y = (l_wr_y + r_wr_y) / 2.0
    elbow_mid_y = (l_el_y + r_el_y) / 2.0

    tolerance_up = 0.15 * body_height
    tolerance_down = 0.10 * body_height

    arms_up = (wrist_mid_y < shoulder_mid_y + tolerance_up and elbow_mid_y < shoulder_mid_y + tolerance_up)
    arms_down = (wrist_mid_y > hip_mid_y - tolerance_down)
    normalized_distance = abs(r_an_x - l_an_x) / body_width if body_width > 20 else 0

    legs_open = (normalized_distance > 1.3)
    legs_closed = (normalized_distance < 1.5)

    return arms_up, legs_open, arms_down, legs_closed

# ============================================================================
# LOOP PRINCIPAL (MODO 2 REVERTIDO)
# ============================================================================

if __name__ == "__main__":
    mp_drawing = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose

    WINDOW_NAME = "Contador de Polichinelos"
    
    # --- Loop Principal da Aplicação ---
    while True:
        modo = escolher_modo()
        if modo is None:
            break # UNICA SAÍDA DO PROGRAMA
        
        if modo == 0: # Modo Solo
            # (Sem alteração)
            nome_usuario = "Jogador" 
            meta = escolher_meta()
            if not meta:
                continue 
            
            while True:
                pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
                cap = cv2.VideoCapture(0)
                counter1 = 0
                stage1 = "down"
                open_frames1 = 0
                closed_frames1 = 0
                start_time = time.time()
                
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    h, w = frame.shape[:2]
                    image = frame.copy()
                    results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    
                    if results.pose_landmarks:
                        pose_valida, _ = validar_pose_melhorada(results.pose_landmarks)
                        if pose_valida:
                            arms_up, legs_open, arms_down, legs_closed = detectar_postura_polichinelo(results.pose_landmarks.landmark, w, h)
                            if arms_up and legs_open:
                                open_frames1 = min(open_frames1 + 1, 15)
                                closed_frames1 = max(0, closed_frames1 - 1)
                            elif arms_down and legs_closed:
                                closed_frames1 = min(closed_frames1 + 1, 15)
                                open_frames1 = max(0, open_frames1 - 1)
                            else:
                                open_frames1 = max(0, open_frames1 - 1)
                                closed_frames1 = max(0, closed_frames1 - 1)
                                
                            if stage1 == "down" and open_frames1 >= 2 and arms_up and legs_open: # threshold 2
                                stage1 = "up"
                            elif stage1 == "up" and closed_frames1 >= 2 and arms_down and legs_closed: # threshold 2
                                stage1 = "down"
                                counter1 += 1
                                
                        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                    
                    # --- HUD (MODO SOLO) ---
                    draw_filled_transparent_rect(image, (0, 0), (w, 80), COLORS['hud_bg'], 0.8)
                    cv2.putText(image, "MODO SOLO", (20, 30), FONTS['title'], 0.8, COLORS['accent'], 2, cv2.LINE_AA)
                    cv2.putText(image, f"REPETICOES: {counter1}", (20, 65), FONTS['body'], 1.0, COLORS['text'], 2, cv2.LINE_AA)
                    
                    draw_filled_transparent_rect(image, (0, h - 50), (w, h), COLORS['hud_bg'], 0.8)
                    cv2.putText(image, f"META: {meta}", (20, h - 20), FONTS['body'], 0.8, COLORS['text_secondary'], 2, cv2.LINE_AA)
                    
                    q_text = "Pressione 'Q' para Sair"
                    (tw_q, _), _ = cv2.getTextSize(q_text, FONTS['body'], 0.6, 1)
                    cv2.putText(image, q_text, (w - tw_q - 20, h - 20), FONTS['body'], 0.6, COLORS['text_secondary'], 1, cv2.LINE_AA)
                    # --- FIM DO HUD ---

                    show_fullscreen(WINDOW_NAME, image)
                    
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or counter1 >= meta:
                        break
                        
                tempo_total = time.time() - start_time
                cap.release()
                cv2.destroyAllWindows()
                
                reiniciar = mostrar_resultado_solo_simples(nome_usuario, counter1, meta, tempo_total)
                if not reiniciar:
                    break 

        # --- MUDANÇA AQUI: MODO 2 REVERTIDO ---
        # --- MUDANÇA AQUI: MODO 2 COM FRAME SKIPPING SIMPLES ---
        elif modo == 2: # Modo Análise de Vídeo
            Tk().withdraw()
            video_path = filedialog.askopenfilename(title="Selecione o vídeo para análise", filetypes=[("MP4 files", ".mp4"), ("All files", ".*")])
            if not video_path:
                continue 
            
            pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
            cap = cv2.VideoCapture(video_path)
            
            # --- NOVAS VARIÁVEIS PARA PULAR QUADROS ---
            # Ajuste: Analisar 1 quadro a cada X. (Use 2 ou 3 para mais rápido)
            PROCESSAR_A_CADA_N_FRAMES = 3 
            frame_count = 0
            last_valid_landmarks = None # Para desenhar o último esqueleto válido
            # --- FIM DAS NOVAS VARIÁVEIS ---

            counter1 = 0
            stage1 = "down"
            open_frames1 = 0
            closed_frames1 = 0
            start_time = time.time()
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                h, w = frame.shape[:2]
                image = frame.copy()
                frame_count += 1
                
                # --- LÓGICA DE PULAR QUADROS ---
                if frame_count % PROCESSAR_A_CADA_N_FRAMES == 0:
                    # Processa este quadro
                    results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    if results.pose_landmarks:
                        last_valid_landmarks = results.pose_landmarks # Salva o último esqueleto válido
                        
                        # --- LÓGICA DE CONTAGEM (SÓ RODA QUANDO PROCESSA) ---
                        pose_valida, _ = validar_pose_melhorada(results.pose_landmarks)
                        if pose_valida:
                            arms_up, legs_open, arms_down, legs_closed = detectar_postura_polichinelo(results.pose_landmarks.landmark, w, h)
                            if arms_up and legs_open:
                                open_frames1 = min(open_frames1 + 1, 15)
                                closed_frames1 = max(0, closed_frames1 - 1)
                            elif arms_down and legs_closed:
                                closed_frames1 = min(closed_frames1 + 1, 15)
                                open_frames1 = max(0, open_frames1 - 1)
                            else:
                                open_frames1 = max(0, open_frames1 - 1)
                                closed_frames1 = max(0, closed_frames1 - 1)
                            
                            # threshold 2 para contagem rápida
                            if stage1 == "down" and open_frames1 >= 2 and arms_up and legs_open: 
                                stage1 = "up"
                            elif stage1 == "up" and closed_frames1 >= 2 and arms_down and legs_closed: 
                                stage1 = "down"
                                counter1 += 1
                        # --- FIM DA LÓGICA DE CONTAGEM ---
                
                # --- DESENHO (SEMPRE RODA) ---
                if last_valid_landmarks:
                    # Desenha o último esqueleto válido (mesmo em quadros pulados)
                    mp_drawing.draw_landmarks(image, last_valid_landmarks, mp_pose.POSE_CONNECTIONS)
                
                # HUD (Sempre desenha)
                draw_filled_transparent_rect(image, (0, 0), (w, 80), COLORS['hud_bg'], 0.8)
                cv2.putText(image, "MODO ANALISE", (20, 30), FONTS['title'], 0.8, COLORS['accent'], 2, cv2.LINE_AA)
                cv2.putText(image, f"POLICHINELOS: {counter1}", (20, 65), FONTS['body'], 1.0, COLORS['text'], 2, cv2.LINE_AA)
                
                draw_filled_transparent_rect(image, (0, h - 50), (w, h), COLORS['hud_bg'], 0.8)
                q_text = "Pressione 'Q' para Sair"
                (tw_q, _), _ = cv2.getTextSize(q_text, FONTS['body'], 0.6, 1)
                cv2.putText(image, q_text, (w - tw_q - 20, h - 20), FONTS['body'], 0.6, COLORS['text_secondary'], 1, cv2.LINE_AA)
                # --- FIM DO HUD ---
                
                show_fullscreen(WINDOW_NAME, image)

                # --- MANTIDO: waitKey(1) ---
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
                    
            cap.release()
            cv2.destroyAllWindows()
            tempo_total = time.time() - start_time
            mostrar_resultado_analise(counter1, tempo_total)
        # --- FIM DA ALTERAÇÃO DO MODO 2 ---

        elif modo == 1: # Modo Competição
            # (Sem alteração)
            nome1, nome2 = obter_nomes_jogadores()
            if not nome1 or not nome2:
                continue 
            meta = escolher_meta()
            if not meta:
                continue 
            
            while True: 
                competition = CompetitionSystem(nome1, nome2, meta)
                
                pose_j1 = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
                pose_j2 = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

                cap = cv2.VideoCapture(0)
                counter1 = 0; counter2 = 0
                stage1 = "down"; stage2 = "down"
                open_frames1 = 0; closed_frames1 = 0
                open_frames2 = 0; closed_frames2 = 0
                flash_frames1 = 0; flash_frames2 = 0
                
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    h, w = frame.shape[:2]
                    image = frame.copy()
                    
                    jogador1_landmarks, jogador2_landmarks, jogador1_original, jogador2_original, meio_x = detectar_multiplas_pessoas_corrigido(image, pose_j1, pose_j2)
                    
                    # Linha divisória
                    cv2.line(image, (meio_x, 0), (meio_x, h), COLORS['text_secondary'], 2)
                    
                    # Esqueletos
                    if jogador1_landmarks:
                        mp_drawing.draw_landmarks(image, jogador1_landmarks, mp_pose.POSE_CONNECTIONS,
                            mp_drawing.DrawingSpec(color=COLORS['accent'], thickness=2, circle_radius=2),
                            mp_drawing.DrawingSpec(color=COLORS['accent'], thickness=2))
                    if jogador2_landmarks:
                        mp_drawing.draw_landmarks(image, jogador2_landmarks, mp_pose.POSE_CONNECTIONS,
                            mp_drawing.DrawingSpec(color=COLORS['accent_j2'], thickness=2, circle_radius=2),
                            mp_drawing.DrawingSpec(color=COLORS['accent_j2'], thickness=2))
                    
                    # Lógica (LÓGICA ORIGINAL)
                    counter1, stage1, open_frames1, closed_frames1, flash_frames1, status1 = processar_jogador_competicao(
                        jogador1_landmarks, jogador1_original, meio_x, h, 1, counter1, stage1, open_frames1, closed_frames1, flash_frames1, competition, frame)
                    counter2, stage2, open_frames2, closed_frames2, flash_frames2, status2 = processar_jogador_competicao(
                        jogador2_landmarks, jogador2_original, w - meio_x, h, 2, counter2, stage2, open_frames2, closed_frames2, flash_frames2, competition, frame)
                    
                    # --- HUD (MODO COMPETIÇÃO) ---
                    # Barra Superior
                    draw_filled_transparent_rect(image, (0, 0), (w, 80), COLORS['hud_bg'], 0.8)
                    
                    # Jogador 1 (Esquerda)
                    cv2.putText(image, f"{nome1.upper()}", (20, 30), FONTS['title'], 0.8, COLORS['accent'], 2, cv2.LINE_AA)
                    cv2.putText(image, f"REPETICOES: {counter1}", (20, 65), FONTS['body'], 1.0, COLORS['text'], 2, cv2.LINE_AA)
                    
                    # Jogador 2 (Direita)
                    cv2.putText(image, f"{nome2.upper()}", (meio_x + 20, 30), FONTS['title'], 0.8, COLORS['accent_j2'], 2, cv2.LINE_AA)
                    cv2.putText(image, f"REPETICOES: {counter2}", (meio_x + 20, 65), FONTS['body'], 1.0, COLORS['text'], 2, cv2.LINE_AA)
                    
                    # Barra Inferior
                    draw_filled_transparent_rect(image, (0, h - 50), (w, h), COLORS['hud_bg'], 0.8)
                    cv2.putText(image, f"META: {meta}", (20, h - 20), FONTS['body'], 0.8, COLORS['text_secondary'], 2, cv2.LINE_AA)
                    
                    q_text = "Pressione 'Q' para Sair"
                    (tw_q, _), _ = cv2.getTextSize(q_text, FONTS['body'], 0.6, 1)
                    cv2.putText(image, q_text, (w - tw_q - 20, h - 20), FONTS['body'], 0.6, COLORS['text_secondary'], 1, cv2.LINE_AA)
                    # --- FIM DO HUD ---

                    show_fullscreen(WINDOW_NAME, image)
                    
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or competition.vencedor:
                        break
                        
                cap.release()
                cv2.destroyAllWindows()
                
                reiniciar = mostrar_resultado_competicao_simples(competition, counter1, counter2)
                if not reiniciar:
                    break 
    
    cv2.destroyAllWindows()