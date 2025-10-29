import cv2
import mediapipe as mp
import numpy as np
from tkinter import Tk, filedialog
from datetime import datetime
import time
import copy
import json
import os

# ============================================================================
# FUNÇÃO DE TELA CHEIA
# ============================================================================

def show_fullscreen(window_name, img):
    """Cria ou atualiza uma janela para ser exibida em tela cheia."""
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow(window_name, img)

# ============================================================================
# SISTEMA DE RANKING - ARMAZENAMENTO E GESTÃO (INTEGRADO)
# ============================================================================

RANKING_FILE_SOLO = 'ranking_solo.json'
RANKING_FILE_COMPETICAO = 'ranking_competicao.json'
MAX_RANKING_ENTRIES = 5

# Variável global para comunicação entre o callback do mouse e o loop principal
click_info = {'clicked': False, 'file': None, 'id': None}

def _load_ranking(filename):
    """Carrega dados do ranking de um arquivo JSON."""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def _save_ranking(filename, ranking_data):
    """Salva dados do ranking em um arquivo JSON."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(ranking_data, f, indent=4, ensure_ascii=False)

def add_solo_score(nome_usuario, pontuacao, movimentos_totais, movimentos_corretos, tempo_total):
    """Adiciona pontuação do modo solo ao ranking com um ID único."""
    ranking = _load_ranking(RANKING_FILE_SOLO)
    ranking.append({
        'id': time.time(), # Adiciona um ID único
        'nome': nome_usuario,
        'pontuacao': pontuacao,
        'movimentos_totais': movimentos_totais,
        'movimentos_corretos': movimentos_corretos,
        'tempo_total_segundos': tempo_total,
        'taxa_acerto': round((movimentos_corretos / movimentos_totais * 100) if movimentos_totais > 0 else 0, 1),
        'data_hora': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    })
    ranking.sort(key=lambda x: x['pontuacao'], reverse=True)
    ranking = ranking[:MAX_RANKING_ENTRIES]
    _save_ranking(RANKING_FILE_SOLO, ranking)

def get_solo_ranking():
    """Retorna o ranking do modo solo."""
    return _load_ranking(RANKING_FILE_SOLO)

# ============================================================================
# FUNÇÃO CORRIGIDA - add_competicao_score
# ============================================================================
def add_competicao_score(nome_vencedor, pontuacao_vencedor, nome_perdedor, pontuacao_perdedor, tempo_total_segundos, pontuacao_j1, pontuacao_j2):
    """Adiciona resultado da competição ao ranking com um ID único."""
    ranking = _load_ranking(RANKING_FILE_COMPETICAO)
    ranking.append({
        'id': time.time(), # Adiciona um ID único
        'nome_vencedor': nome_vencedor,
        'pontuacao_vencedor': pontuacao_vencedor,
        'nome_perdedor': nome_perdedor,
        'pontuacao_perdedor': pontuacao_perdedor,
        'pontuacao_jogador1': pontuacao_j1,  # Adicionado para salvar pontos do J1
        'pontuacao_jogador2': pontuacao_j2,  # Adicionado para salvar pontos do J2
        'tempo_total_segundos': tempo_total_segundos,
        'diferenca': pontuacao_vencedor - pontuacao_perdedor,
        'data_hora': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    })
    ranking.sort(key=lambda x: (x['pontuacao_vencedor'], -x['tempo_total_segundos']), reverse=True)
    ranking = ranking[:MAX_RANKING_ENTRIES]
    _save_ranking(RANKING_FILE_COMPETICAO, ranking)

def get_competicao_ranking():
    """Retorna o ranking do modo competição."""
    return _load_ranking(RANKING_FILE_COMPETICAO)

def clear_ranking(filename):
    """Apaga o arquivo de ranking especificado."""
    if os.path.exists(filename):
        try:
            os.remove(filename)
            print(f"Ranking '{filename}' foi limpo com sucesso.")
        except OSError as e:
            print(f"Erro ao limpar o ranking '{filename}': {e}")

def remove_ranking_entry(filename, entry_id):
    """Remove uma entrada específica do ranking pelo seu ID."""
    ranking_data = _load_ranking(filename)
    updated_ranking = [entry for entry in ranking_data if entry.get('id') != entry_id]
    _save_ranking(filename, updated_ranking)
    return updated_ranking

# ============================================================================
# FUNÇÕES DE DESENHO (DO NOVO CÓDIGO + GRADIENTE DO RANKING)
# ============================================================================

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

def draw_label_box(img, text, org, font=cv2.FONT_HERSHEY_SIMPLEX, scale=0.9, thickness=2,
                   text_color=(255, 255, 255), bg_color=(20, 22, 25), alpha=0.7, padding=10):
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

def putText_outline(img, text, org, font, scale, color=(255,255,255), thickness=2,
                   outline_color=(0,0,0), outline_thickness=None):
    if outline_thickness is None:
        outline_thickness = max(1, thickness + 1)
    cv2.putText(img, text, org, font, scale, outline_color, outline_thickness, cv2.LINE_AA)
    cv2.putText(img, text, org, font, scale, color, thickness, cv2.LINE_AA)

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
        """Registra um polichinelo para o jogador especificado"""
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

class GamificationSystem:
    def _init_(self, nome_usuario, meta_polichinelos=20):
        self.nome_usuario = nome_usuario
        self.meta_polichinelos = meta_polichinelos
        self.reset_stats()

    def reset_stats(self):
        self.total_movimentos = 0
        self.movimentos_corretos = 0
        self.movimentos_imperfeitos = 0
        self.tempo_inicio = time.time()
        self.historico_precisao = []
        self.melhor_sequencia = 0
        self.sequencia_atual = 0
        self.bonus_velocidade = 0
        self.bonus_consistencia = 0

    def avaliar_movimento(self, arms_up, legs_open, arms_down, legs_closed, stage_transition=False):
        if not stage_transition:
            return 0
        
        self.total_movimentos += 1
        
        score_up = (1.0 if arms_up else 0.5) + (1.0 if legs_open else 0.5)
        score_down = (1.0 if arms_down else 0.5) + (1.0 if legs_closed else 0.5)
        precisao = (score_up + score_down) / 4.0
        
        if precisao >= 0.90:
            self.movimentos_corretos += 1
            self.sequencia_atual += 1
            self.melhor_sequencia = max(self.melhor_sequencia, self.sequencia_atual)
            pontos = 100
        elif precisao >= 0.75:
            self.movimentos_imperfeitos += 1
            self.sequencia_atual = 0
            pontos = 75
        else:
            self.sequencia_atual = 0
            pontos = 50
        
        self.historico_precisao.append(precisao)
        return pontos

    def calcular_bonus(self):
        tempo_total = time.time() - self.tempo_inicio
        
        if tempo_total > 0 and self.total_movimentos > 0:
            ppm = (self.total_movimentos / tempo_total) * 60
            if ppm >= 30: 
                self.bonus_velocidade = 50
            elif ppm >= 20: 
                self.bonus_velocidade = 25
            else:
                self.bonus_velocidade = 0
        
        if len(self.historico_precisao) >= 5:
            consistencia = 1 - np.std(self.historico_precisao)
            if consistencia >= 0.9: 
                self.bonus_consistencia = 100
            elif consistencia >= 0.8: 
                self.bonus_consistencia = 50
            else:
                self.bonus_consistencia = 0

    def get_nota_final(self):
        if self.total_movimentos == 0:
            return "F", 0, "Nenhum movimento detectado"
        
        taxa_acerto = self.movimentos_corretos / self.total_movimentos
        pontos_base = taxa_acerto * 500
        
        self.calcular_bonus()
        pontos_bonus = self.bonus_velocidade + self.bonus_consistencia + (self.melhor_sequencia * 10)
        
        pontuacao_total = int(pontos_base + pontos_bonus)
        
        if pontuacao_total >= 650: 
            nota, desc = "S+", "EXCEPCIONAL!"
        elif pontuacao_total >= 550: 
            nota, desc = "S", "EXCELENTE!"
        elif pontuacao_total >= 450: 
            nota, desc = "A", "MUITO BOM!"
        elif pontuacao_total >= 350: 
            nota, desc = "B", "BOM!"
        elif pontuacao_total >= 250: 
            nota, desc = "C", "REGULAR"
        elif pontuacao_total >= 150: 
            nota, desc = "D", "PRECISA MELHORAR"
        else: 
            nota, desc = "F", "TENTE NOVAMENTE"
        
        return nota, pontuacao_total, desc

def obter_nome_estilizado(prompt_text, window_title, default_name):
    nome = ""
    max_chars = 15
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
        cursor = "|" if int(time.time() * 2) % 2 == 0 else ""
        cv2.putText(tela, nome + cursor, (input_box_rect[0] + 15, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3, cv2.LINE_AA)
        draw_label_box(tela, "Pressione ENTER para confirmar ou ESC para sair", (40, 350), font=cv2.FONT_HERSHEY_PLAIN, scale=1.2)
        cv2.imshow(window_title, tela)
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
    while True:
        tela = np.ones((400, 720, 3), dtype=np.uint8) * 24
        draw_filled_transparent_rect(tela, (0, 0), (720, 100), (20, 22, 25), 0.9)
        cv2.putText(tela, "CONTADOR DE POLICHINELOS", (40, 60), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 255, 220), 2, cv2.LINE_AA)
        cv2.putText(tela, "Escolha o modo de uso:", (40, 92), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (230, 230, 230), 2, cv2.LINE_AA)
        draw_button(tela, (80, 140, 640, 190), (80, 170, 255), "[1] MODO SOLO", label_color=(20, 22, 25))
        draw_button(tela, (80, 210, 640, 260), (255, 140, 80), "[2] MODO COMPETICAO (SIMULTANEO)", label_color=(20, 22, 25))
        draw_button(tela, (80, 280, 640, 330), (0, 210, 180), "[3] CARREGAR VIDEO", label_color=(20, 22, 25))
        draw_label_box(tela, "Pressione 1, 2 ou 3 para selecionar", (40, 370), font=cv2.FONT_HERSHEY_PLAIN, scale=1.2)
        cv2.imshow("Selecao de Modo", tela)
        key = cv2.waitKey(1)
        if key == ord("1"): cv2.destroyWindow("Selecao de Modo"); return 0
        elif key == ord("2"): cv2.destroyWindow("Selecao de Modo"); return 1
        elif key == ord("3"): cv2.destroyWindow("Selecao de Modo"); return 2
        elif key == 27: cv2.destroyWindow("Selecao de Modo"); return None

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
        cv2.imshow("Escolha da Meta", tela)
        key = cv2.waitKey(1)
        if key in [ord('1'), ord('2'), ord('3'), ord('4')]:
            cv2.destroyWindow(window_name)
            return metas[key - ord('1')]
        elif key == 27:
            cv2.destroyWindow("Escolha da Meta")
            return None

def mostrar_resultado_competicao(competition, counter1, counter2):
    tempo_total = int(competition.tempo_final) if competition.tempo_final else int(time.time() - competition.tempo_inicio)
    
    pontuacao1 = counter1 * 50
    pontuacao2 = counter2 * 50
    
    if competition.vencedor == 1:
        pontuacao1 += 200
        status1 = "VENCEDOR"
        status2 = "2° LUGAR"
    elif competition.vencedor == 2:
        pontuacao2 += 200  
        status1 = "2° LUGAR"
        status2 = "VENCEDOR"
    else:
        status1 = "EM ANDAMENTO"
        status2 = "EM ANDAMENTO"
    
    velocidade1 = (counter1 / tempo_total * 60) if tempo_total > 0 else 0
    velocidade2 = (counter2 / tempo_total * 60) if tempo_total > 0 else 0
    
    progresso1 = min((counter1 / competition.meta_polichinelos) * 100, 100)
    progresso2 = min((counter2 / competition.meta_polichinelos) * 100, 100)
    
    while True:
        tela = np.ones((750, 1000, 3), dtype=np.uint8) * 24
        draw_filled_transparent_rect(tela, (0, 0), (1000, 120), (20, 22, 25), 0.9)
        cv2.putText(tela, "RESULTADO DETALHADO DA COMPETICAO", (50, 70), cv2.FONT_HERSHEY_DUPLEX, 1.3, (0, 255, 220), 3)
        cv2.putText(tela, f"Duracao Total: {tempo_total//60}:{tempo_total%60:02d}", (50, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
        
        y_start = 180
        col1_x = 80
        col2_x = 520
        
        cv2.putText(tela, f"{competition.jogador1.upper()}", (col1_x, y_start), cv2.FONT_HERSHEY_DUPLEX, 1.2, (80, 170, 255), 3)
        cv2.putText(tela, status1, (col1_x, y_start + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (80, 170, 255), 2)
        
        stats1 = [
            f"Pontuacao Final: {pontuacao1} pts",
            f"Polichinelos: {counter1}/{competition.meta_polichinelos}",
            f"Velocidade: {velocidade1:.1f}/min",
            f"Progresso: {progresso1:.1f}%",
            f"Meta Atingida: {'SIM' if counter1 >= competition.meta_polichinelos else 'NAO'}"
        ]
        
        y_pos = y_start + 80
        for i, stat in enumerate(stats1):
            color = (0, 255, 100) if i == 0 and competition.vencedor == 1 else (230, 230, 230)
            cv2.putText(tela, stat, (col1_x, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            y_pos += 40
        
        barra_width = 300
        barra_height = 25
        barra_y = y_pos + 10
        cv2.rectangle(tela, (col1_x, barra_y), (col1_x + barra_width, barra_y + barra_height), (50, 50, 50), -1)
        cv2.rectangle(tela, (col1_x, barra_y), (col1_x + int(barra_width * progresso1/100), barra_y + barra_height), (80, 170, 255), -1)
        cv2.putText(tela, f"{progresso1:.0f}%", (col1_x + barra_width + 10, barra_y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.putText(tela, f"{competition.jogador2.upper()}", (col2_x, y_start), cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 140, 80), 3)
        cv2.putText(tela, status2, (col2_x, y_start + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 140, 80), 2)
        
        stats2 = [
            f"Pontuacao Final: {pontuacao2} pts",
            f"Polichinelos: {counter2}/{competition.meta_polichinelos}",
            f"Velocidade: {velocidade2:.1f}/min",
            f"Progresso: {progresso2:.1f}%",
            f"Meta Atingida: {'SIM' if counter2 >= competition.meta_polichinelos else 'NAO'}"
        ]
        
        y_pos = y_start + 80
        for i, stat in enumerate(stats2):
            color = (0, 255, 100) if i == 0 and competition.vencedor == 2 else (230, 230, 230)
            cv2.putText(tela, stat, (col2_x, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            y_pos += 40
        
        cv2.rectangle(tela, (col2_x, barra_y), (col2_x + barra_width, barra_y + barra_height), (50, 50, 50), -1)
        cv2.rectangle(tela, (col2_x, barra_y), (col2_x + int(barra_width * progresso2/100), barra_y + barra_height), (255, 140, 80), -1)
        cv2.putText(tela, f"{progresso2:.0f}%", (col2_x + barra_width + 10, barra_y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.line(tela, (500, y_start), (500, barra_y + barra_height + 20), (100, 100, 100), 2)
        
        if competition.vencedor:
            vencedor_nome = competition.jogador1 if competition.vencedor == 1 else competition.jogador2
            resultado_texto = f"PARABENS {vencedor_nome.upper()}!"
            (rw, rh), _ = cv2.getTextSize(resultado_texto, cv2.FONT_HERSHEY_DUPLEX, 1.0, 3)
            resultado_x = (1000 - rw) // 2
            cv2.putText(tela, resultado_texto, (resultado_x, barra_y + 80), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 255, 100), 3)
        
        draw_button(tela, (150, 650, 450, 700), (0, 200, 100), "NOVA COMPETICAO", label_color=(20, 22, 25))
        draw_button(tela, (550, 650, 850, 700), (200, 80, 80), "SAIR", label_color=(255, 255, 255))
        
        cv2.putText(tela, "Pressione ENTER para nova competicao ou ESC para sair", (200, 730), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 2)
        
        cv2.imshow("Resultado da Competicao", tela)
        key = cv2.waitKey(1)
        
        if key == 13:
            cv2.destroyWindow("Resultado da Competicao")
            return True
        elif key == 27:
            cv2.destroyWindow("Resultado da Competicao")
            return False

def mostrar_resultado_final(gamification, counter_final):
    nota, pontuacao, descricao = gamification.get_nota_final()
    tempo_total = int(time.time() - gamification.tempo_inicio)
    
    while True:
        tela = np.ones((500, 850, 3), dtype=np.uint8) * 24
        draw_filled_transparent_rect(tela, (0, 0), (850, 100), (20, 22, 25), 0.9)
        cv2.putText(tela, "RELATORIO FINAL", (50, 65), cv2.FONT_HERSHEY_DUPLEX, 1.4, (0, 255, 220), 3)
        
        y_info = 180
        cv2.putText(tela, f"Jogador: {gamification.nome_usuario}", (60, y_info), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        y_info += 60
        
        stats = [
            f"Pontuacao Total: {pontuacao}",
            f"Polichinelos: {counter_final}/{gamification.meta_polichinelos}",
            f"Tempo: {tempo_total//60}:{tempo_total%60:02d}"
        ]
        
        y_pos = y_info
        for stat in stats:
            cv2.putText(tela, stat, (60, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (230, 230, 230), 2)
            y_pos += 50
        
        draw_button(tela, (80, 400, 380, 450), (0, 200, 100), "REINICIAR", label_color=(20, 22, 25), scale=0.9)
        draw_button(tela, (470, 400, 770, 450), (200, 80, 80), "SAIR", label_color=(255, 255, 255), scale=0.9)
        
        cv2.imshow("Resultado Final", tela)
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

def detectar_multiplas_pessoas_corrigido(image, pose_model):
    """
    Versão corrigida da detecção de múltiplas pessoas
    """
    h, w = image.shape[:2]
    meio_x = w // 2
    
    jogador1_landmarks = None
    jogador2_landmarks = None
    jogador1_original = None
    jogador2_original = None
    
    # LADO ESQUERDO (Jogador 1)
    img_esquerda = image[:, :meio_x]
    rgb_esquerda = cv2.cvtColor(img_esquerda, cv2.COLOR_BGR2RGB)
    resultado_esquerda = pose_model.process(rgb_esquerda)
    
    if resultado_esquerda.pose_landmarks:
        nose = resultado_esquerda.pose_landmarks.landmark[0]
        left_shoulder = resultado_esquerda.pose_landmarks.landmark[11]
        right_shoulder = resultado_esquerda.pose_landmarks.landmark[12]
        
        centro_x = (nose.x + left_shoulder.x + right_shoulder.x) / 3.0
        
        if centro_x < 0.75:
            jogador1_original = resultado_esquerda.pose_landmarks
            jogador1_landmarks = resultado_esquerda.pose_landmarks
    
    # LADO DIREITO (Jogador 2)
    img_direita = image[:, meio_x:]
    rgb_direita = cv2.cvtColor(img_direita, cv2.COLOR_BGR2RGB)
    resultado_direita = pose_model.process(rgb_direita)
    
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

def processar_jogador_competicao(landmarks, landmarks_original, w, h, jogador_num, 
                                 counter, stage, open_frames, closed_frames, 
                                 flash_frames, competition, frame_atual):
    """
    Processa detecção e contagem para um jogador específico
    """
    
    if not landmarks:
        return (counter, stage, max(0, open_frames - 2), max(0, closed_frames - 2), 
                flash_frames, "Pessoa nao detectada")
    
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
        open_frames = max(0, open_frames - 1)
        closed_frames = max(0, closed_frames - 1)
        status = f"TRANSICAO (A:{arms_up} P:{legs_open} / a:{arms_down} p:{legs_closed})"
    
    threshold = 4
    
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
    """
    Função original para detecção de postura (modo solo e vídeo)
    """
    def pt(lm_id): 
        return (landmarks[lm_id].x * w, landmarks[lm_id].y * h)
    
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
    
    body_height = abs(hip_mid_y - shoulder_mid_y)
    tolerance_y = max(0.08 * body_height, 15)
    
    arms_up = (wrist_mid_y < shoulder_mid_y + tolerance_y and 
               elbow_mid_y < shoulder_mid_y + tolerance_y)
    
    arms_down = wrist_mid_y > hip_mid_y - tolerance_y
    
    ankle_distance = abs(r_an_x - l_an_x)
    normalized_ankle_distance = ankle_distance / body_width
    
    legs_open = normalized_ankle_distance > 1.0
    
    legs_closed = normalized_ankle_distance < 1.2
    
    return arms_up, legs_open, arms_down, legs_closed

def main():
    while True:
        modo = escolher_modo()
        if modo is None:
            return

        cap = None
        gamification = None
        competition = None
        
        try:
            if modo == 0:
                nome_usuario = obter_nome_usuario()
                if nome_usuario is None: continue
                meta_polichinelos = escolher_meta()
                if meta_polichinelos is None: continue
                gamification = GamificationSystem(nome_usuario, meta_polichinelos)
                cap = cv2.VideoCapture(0)
                wait_delay = 10
                ambiente = "Casa"

            elif modo == 1:
                jogador1, jogador2 = obter_nomes_jogadores()
                if jogador1 is None or jogador2 is None: continue
                meta_polichinelos = escolher_meta()
                if meta_polichinelos is None: continue
                competition = CompetitionSystem(jogador1, jogador2, meta_polichinelos)
                cap = cv2.VideoCapture(0)
                wait_delay = 10
                ambiente = "Competicao"
                
            else:
                root = Tk()
                root.withdraw()
                video_path = filedialog.askopenfilename(
                    title="Selecione o video", 
                    filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv")]
                )
                root.destroy()
                if not video_path: 
                    continue
                cap = cv2.VideoCapture(video_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                wait_delay = max(1, int(1000 / (fps or 30)))
                ambiente = "Video"

            if not cap or not cap.isOpened():
                print("Erro ao abrir a câmera ou vídeo.")
                continue

            mp_pose = mp.solutions.pose
            mp_drawing = mp.solutions.drawing_utils
            
            counter1, stage1, open_frames1, closed_frames1, flash_frames1 = 0, "down", 0, 0, 0
            counter2, stage2, open_frames2, closed_frames2, flash_frames2 = 0, "down", 0, 0, 0
            last_points = 0
            
            WINDOW_NAME = 'Contador de Polichinelos'
            cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
            cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

            with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=1) as pose:
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret: break

                    h, w, _ = frame.shape
                    image = frame.copy()

                    if competition:
                        # MODO COMPETIÇÃO CORRIGIDO
                        jogador1_pose, jogador2_pose, j1_original, j2_original, meio_x = detectar_multiplas_pessoas_corrigido(image, pose)
                        
                        frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) if cap else 0
                        
                        # PROCESSAR JOGADOR 1
                        counter1, stage1, open_frames1, closed_frames1, flash_frames1, status1 = processar_jogador_competicao(
                            jogador1_pose, j1_original, meio_x, h, 1,
                            counter1, stage1, open_frames1, closed_frames1, flash_frames1,
                            competition, frame_num
                        )
                        
                        # Desenhar landmarks Jogador 1
                        if j1_original:
                            for connection in mp_pose.POSE_CONNECTIONS:
                                start_idx = connection[0]
                                end_idx = connection[1]
                                
                                start = j1_original.landmark[start_idx]
                                end = j1_original.landmark[end_idx]
                                
                                start_point = (int(start.x * meio_x), int(start.y * h))
                                end_point = (int(end.x * meio_x), int(end.y * h))
                                
                                cv2.line(image, start_point, end_point, (255, 100, 190), 2)
                            
                            for landmark in j1_original.landmark:
                                x = int(landmark.x * meio_x)
                                y = int(landmark.y * h)
                                cv2.circle(image, (x, y), 3, (80, 170, 255), -1)
                        
                        # PROCESSAR JOGADOR 2
                        counter2, stage2, open_frames2, closed_frames2, flash_frames2, status2 = processar_jogador_competicao(
                            jogador2_pose, j2_original, w - meio_x, h, 2,
                            counter2, stage2, open_frames2, closed_frames2, flash_frames2,
                            competition, frame_num
                        )
                        
                        # Desenhar landmarks Jogador 2
                        if j2_original:
                            for connection in mp_pose.POSE_CONNECTIONS:
                                start_idx = connection[0]
                                end_idx = connection[1]
                                
                                start = j2_original.landmark[start_idx]
                                end = j2_original.landmark[end_idx]
                                
                                start_point = (int(start.x * (w - meio_x) + meio_x), int(start.y * h))
                                end_point = (int(end.x * (w - meio_x) + meio_x), int(end.y * h))
                                
                                cv2.line(image, start_point, end_point, (255, 100, 190), 2)
                            
                            for landmark in j2_original.landmark:
                                x = int(landmark.x * (w - meio_x) + meio_x)
                                y = int(landmark.y * h)
                                cv2.circle(image, (x, y), 3, (255, 140, 80), -1)
                        
                        # INTERFACE
                        cv2.line(image, (meio_x, 0), (meio_x, h), (255, 255, 255), 3)
                        
                        putText_outline(image, competition.jogador1, (20, 50), cv2.FONT_HERSHEY_DUPLEX, 1.2, 
                                       color=(80, 170, 255), thickness=2)
                        putText_outline(image, f"Contagem: {counter1}", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                                       color=(255, 255, 255), thickness=2)
                        putText_outline(image, f"Estado: {stage1.upper()}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                       color=(200, 200, 200), thickness=1)
                        
                        putText_outline(image, competition.jogador2, (meio_x + 20, 50), cv2.FONT_HERSHEY_DUPLEX, 1.2,
                                       color=(255, 140, 80), thickness=2)
                        putText_outline(image, f"Contagem: {counter2}", (meio_x + 20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                                       color=(255, 255, 255), thickness=2)
                        putText_outline(image, f"Estado: {stage2.upper()}", (meio_x + 20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                       color=(200, 200, 200), thickness=1)
                        
                        placar = f"{counter1}  x  {counter2}"
                        (pw, ph), _ = cv2.getTextSize(placar, cv2.FONT_HERSHEY_DUPLEX, 2.5, 3)
                        placar_x = (w - pw) // 2
                        putText_outline(image, placar, (placar_x, h - 60), cv2.FONT_HERSHEY_DUPLEX, 2.5,
                                       color=(0, 255, 220), thickness=3)
                        
                        # DEBUG
                        putText_outline(image, status1[:40], (20, h - 100), cv2.FONT_HERSHEY_PLAIN, 1.0,
                                       color=(150, 150, 150), thickness=1)
                        putText_outline(image, status2[:40], (meio_x + 20, h - 100), cv2.FONT_HERSHEY_PLAIN, 1.0,
                                       color=(150, 150, 150), thickness=1)
                        
                        if flash_frames1 > 0:
                            putText_outline(image, "+1!", (meio_x // 2 - 30, 200), cv2.FONT_HERSHEY_DUPLEX, 2.0,
                                           color=(0, 255, 100), thickness=3)
                            flash_frames1 -= 1
                        
                        if flash_frames2 > 0:
                            putText_outline(image, "+1!", (meio_x + (w - meio_x) // 2 - 30, 200), cv2.FONT_HERSHEY_DUPLEX, 2.0,
                                           color=(0, 255, 100), thickness=3)
                            flash_frames2 -= 1

                    else:
                        # MODO SOLO
                        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        results = pose.process(image_rgb)
                        image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

                        if results.pose_landmarks:
                            landmarks = results.pose_landmarks.landmark
                            
                            ids = [11, 12, 23, 24, 15, 16, 27, 28]
                            
                            visibilities = []
                            for i in ids:
                                if i < len(landmarks):
                                    visibilities.append(landmarks[i].visibility)
                                else:
                                    visibilities.append(0.0)
                            
                            min_vis = min(visibilities) if visibilities else 0
                            avg_vis = sum(visibilities) / len(visibilities) if visibilities else 0
                            
                            pose_valida = min_vis >= 0.3 and avg_vis >= 0.4
                            
                            if pose_valida:
                                arms_up, legs_open, arms_down, legs_closed = detectar_postura_polichinelo(landmarks, w, h)

                                if arms_up and legs_open:
                                    open_frames1 += 1
                                    closed_frames1 = max(0, closed_frames1 - 1)
                                elif arms_down and legs_closed:
                                    closed_frames1 += 1
                                    open_frames1 = max(0, open_frames1 - 1)
                                else:
                                    open_frames1 = max(0, open_frames1 - 1)
                                    closed_frames1 = max(0, closed_frames1 - 1)

                                open_frames1 = min(open_frames1, 15)
                                closed_frames1 = min(closed_frames1, 15)

                                if stage1 == "down" and open_frames1 >= 3:
                                    stage1 = "up"
                                    closed_frames1 = 0
                                elif stage1 == "up" and closed_frames1 >= 3:
                                    stage1 = "down"
                                    counter1 += 1
                                    open_frames1 = 0
                                    flash_frames1 = 10
                                    
                                    if gamification:
                                        last_points = gamification.avaliar_movimento(arms_up, legs_open, arms_down, legs_closed, True)
                                    
                                    print(f"POLICHINELO #{counter1} DETECTADO! Visibilidade: {avg_vis:.2f}")
                            else:
                                open_frames1 = max(0, open_frames1 - 2)
                                closed_frames1 = max(0, closed_frames1 - 2)

                            if pose_valida:
                                landmark_color = (0, 255, 220)
                                connection_color = (255, 100, 190)
                            else:
                                landmark_color = (0, 150, 255)
                                connection_color = (150, 150, 150)
                            
                            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                                      mp_drawing.DrawingSpec(color=landmark_color, thickness=2, circle_radius=2),
                                                      mp_drawing.DrawingSpec(color=connection_color, thickness=2, circle_radius=2))
                        else:
                            open_frames1 = max(0, open_frames1 - 3)
                            closed_frames1 = max(0, closed_frames1 - 3)

                    y_pos, y_step, x_pos = 40, 45, 30
                    TEXT_COLOR, OUTLINE_COLOR = (255, 255, 255), (0, 0, 0)
                    instrucao = "Pressione Q para sair"

                    if not competition:
                        if gamification:
                            titulo = f'DESAFIO DE {gamification.nome_usuario.upper()}'
                            putText_outline(image, titulo, (x_pos, y_pos), cv2.FONT_HERSHEY_DUPLEX, 0.9, color=(0, 255, 220), outline_color=OUTLINE_COLOR, thickness=2)
                            y_pos += y_step

                            progresso_text = f'Progresso: {counter1}/{gamification.meta_polichinelos}'
                            cor_progresso = (0, 255, 0) if counter1 >= gamification.meta_polichinelos else (255, 255, 255)
                            putText_outline(image, progresso_text, (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color=cor_progresso, outline_color=OUTLINE_COLOR, thickness=2)
                            
                            stage_text = f'Estagio: {stage1.upper()}'
                            putText_outline(image, stage_text, (x_pos + 300, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color=TEXT_COLOR, outline_color=OUTLINE_COLOR, thickness=2)
                            y_pos += y_step
                            
                            if ambiente == "Video":
                                if cap:
                                    current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                                    fps = cap.get(cv2.CAP_PROP_FPS)
                                    
                                    if total_frames > 0 and fps > 0:
                                        current_time = current_frame / fps
                                        total_time = total_frames / fps
                                        progress_percent = (current_frame / total_frames) * 100
                                        
                                        time_text = f'Tempo: {int(current_time//60):02d}:{int(current_time%60):02d} / {int(total_time//60):02d}:{int(total_time%60):02d} ({progress_percent:.1f}%)'
                                        putText_outline(image, time_text, (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color=(200, 200, 200), outline_color=OUTLINE_COLOR, thickness=1)
                                        y_pos += 30

                            if counter1 >= gamification.meta_polichinelos:
                                instrucao = "META ATINGIDA! Pressione Q para ver resultado"
                                bar_width = 400
                                bar_height = 20
                                bar_x = x_pos
                                bar_y = y_pos + 10
                                
                                cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
                                progress_width = int((counter1 / gamification.meta_polichinelos) * bar_width)
                                cv2.rectangle(image, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), (0, 255, 100), -1)
                                cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 2)
                        
                        else:
                            titulo = 'CONTADOR DE POLICHINELOS'
                            if ambiente == "Video":
                                titulo += ' - ANALISE DE VIDEO'
                            
                            putText_outline(image, titulo, (x_pos, y_pos), cv2.FONT_HERSHEY_DUPLEX, 1.0, color=TEXT_COLOR, outline_color=OUTLINE_COLOR, thickness=2)
                            y_pos += y_step
                            
                            rep_text = f'Repeticoes: {counter1}'
                            putText_outline(image, rep_text, (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color=TEXT_COLOR, outline_color=OUTLINE_COLOR, thickness=2)
                            stage_text = f'Estagio: {stage1.upper()}'
                            putText_outline(image, stage_text, (x_pos + 300, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color=TEXT_COLOR, outline_color=OUTLINE_COLOR, thickness=2)
                            y_pos += y_step
                            putText_outline(image, f'Ambiente: {ambiente}', (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color=TEXT_COLOR, outline_color=OUTLINE_COLOR, thickness=2)
                            
                            if ambiente == "Video" and cap:
                                y_pos += 30
                                current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                                fps = cap.get(cv2.CAP_PROP_FPS)
                                
                                if total_frames > 0 and fps > 0:
                                    current_time = current_frame / fps
                                    total_time = total_frames / fps
                                    
                                    time_text = f'Video: {int(current_time//60):02d}:{int(current_time%60):02d} / {int(total_time//60):02d}:{int(total_time%60):02d}'
                                    putText_outline(image, time_text, (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color=(200, 200, 200), outline_color=OUTLINE_COLOR, thickness=1)

                        putText_outline(image, instrucao, (x_pos, h - 25), cv2.FONT_HERSHEY_PLAIN, 1.4, color=TEXT_COLOR, outline_color=OUTLINE_COLOR, thickness=1)
                    else:
                        # Instruções para modo competição
                        instrucao = "Pressione Q para ver resultado" if competition.vencedor else "Pressione Q para sair"
                        putText_outline(image, instrucao, (w//2 - 200, h - 25), cv2.FONT_HERSHEY_PLAIN, 1.4, color=TEXT_COLOR, outline_color=OUTLINE_COLOR, thickness=1)

                        if flash_frames1 > 0:
                            if gamification and last_points > 0:
                                cor_pontos = (0, 255, 120) if last_points >= 90 else (0, 200, 255) if last_points >= 75 else (255, 200, 0)
                                putText_outline(image, f"+{last_points}pt", (w - 120, 60), cv2.FONT_HERSHEY_DUPLEX, 1.0, color=cor_pontos, outline_color=(0,0,0), thickness=2)
                            else:
                                putText_outline(image, "+1", (w - 90, 60), cv2.FONT_HERSHEY_DUPLEX, 1.2, color=(0, 255, 120), outline_color=(0,0,0), thickness=2)
                            flash_frames1 -= 1
                    
                    cv2.imshow(WINDOW_NAME, image)
                    
                    should_exit = False
                    key = cv2.waitKey(wait_delay) & 0xFF
                    
                    if key == ord('q'):
                        should_exit = True
                    elif gamification and counter1 >= gamification.meta_polichinelos:
                        time.sleep(0.5)
                        should_exit = True
                    elif competition and competition.vencedor:
                        time.sleep(0.5)
                        should_exit = True
                        
                    if should_exit:
                        break

        except Exception as e:
            print(f"Erro durante execução: {e}")
        
        finally:
            if cap:
                cap.release()
            cv2.destroyAllWindows()
        
        continuar = True
        if gamification:
            continuar = mostrar_resultado_final(gamification, counter1)
        elif competition:
            continuar = mostrar_resultado_competicao(competition, competition.contador1, competition.contador2)
        
        if not continuar:
            break

if __name__ == "__main__":
    main()