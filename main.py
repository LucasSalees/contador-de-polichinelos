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

def draw_filled_transparent_rect(img, pt1, pt2, color=(0, 0, 0), alpha=0.65):
    overlay = img.copy()
    cv2.rectangle(overlay, pt1, pt2, color, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

def draw_gradient_rect(img, pt1, pt2, color1, color2):
    """Desenha retângulo com gradiente (usado nas telas de ranking)."""
    x1, y1 = pt1
    x2, y2 = pt2
    for i, y in enumerate(range(y1, y2)):
        ratio = (y - y1) / (y2 - y1)
        color = tuple(int(c1 * (1 - ratio) + c2 * ratio) for c1, c2 in zip(color1, color2))
        cv2.line(img, (x1, y), (x2, y), color, 1)

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

def draw_button(canvas, rect, color, label, label_color=(15, 18, 22),
                font=cv2.FONT_HERSHEY_SIMPLEX, scale=0.95, thickness=2):
    x1, y1, x2, y2 = rect
    overlay = canvas.copy()
    cv2.rectangle(overlay, (x1+4, y1+4), (x2+4, y2+4), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.35, canvas, 0.65, 0, canvas)
    overlay = canvas.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
    cv2.addWeighted(overlay, 0.88, canvas, 0.12, 0, canvas)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), (245, 245, 245), 2)
    (tw, th), _ = cv2.getTextSize(label, font, scale, thickness)
    tx = x1 + (x2 - x1 - tw) // 2
    ty = y1 + (y2 - y1 + th) // 2
    cv2.putText(canvas, label, (tx, ty), font, scale, label_color, thickness, cv2.LINE_AA)

def putText_outline(img, text, org, font, scale, color=(255,255,255), thickness=2,
                    outline_color=(0,0,0), outline_thickness=None):
    if outline_thickness is None:
        outline_thickness = max(1, thickness + 2)
    cv2.putText(img, text, org, font, scale, outline_color, outline_thickness, cv2.LINE_AA)
    cv2.putText(img, text, org, font, scale, color, thickness, cv2.LINE_AA)

# ============================================================================
# TELAS DE RANKING E CONFIRMAÇÃO
# ============================================================================
def handle_mouse_click_ranking(event, x, y, flags, param):
    """Callback para detectar cliques nos botões de exclusão do ranking."""
    global click_info
    if event == cv2.EVENT_LBUTTONDOWN:
        buttons = param['buttons']
        filename = param['file']
        for rect, entry_id in buttons:
            x1, y1, x2, y2 = rect
            if x1 <= x <= x2 and y1 <= y <= y2:
                click_info['clicked'] = True
                click_info['file'] = filename
                click_info['id'] = entry_id
                break

def show_confirmation_screen(window_title, message):
    """Mostra uma tela de confirmação e aguarda a resposta do usuário (S/N)."""
    confirm_window_name = f"Confirmar - {window_title}"
    while True:
        tela = np.ones((300, 700, 3), dtype=np.uint8) * 24
        draw_filled_transparent_rect(tela, (0, 0), (700, 80), (80, 40, 40), 0.9)
        putText_outline(tela, "CONFIRMACAO", (40, 55), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 100, 100), 2)
        
        putText_outline(tela, message, (40, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (230, 230, 230), 2)
        
        draw_button(tela, (100, 180, 300, 230), (0, 180, 0), "[S] Sim", label_color=(20, 22, 25))
        draw_button(tela, (400, 180, 600, 230), (200, 50, 50), "[N] Nao", label_color=(255, 255, 255))

        show_fullscreen(confirm_window_name, tela)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s') or key == ord('S'):
            cv2.destroyWindow(confirm_window_name)
            return True
        elif key == ord('n') or key == ord('N') or key == 27: # ESC
            cv2.destroyWindow(confirm_window_name)
            return False

def show_solo_ranking():
    """Exibe ranking detalhado do modo solo com a coluna de pontuação."""
    global click_info
    click_info = {'clicked': False, 'file': None, 'id': None}
    ranking_data = get_solo_ranking()
    window_name = "Ranking Solo"
    
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    y_offset = 160
    x_base = 40

    while True:
        delete_buttons = []
        tela = np.ones((700, 1100, 3), dtype=np.uint8) * 20
        draw_gradient_rect(tela, (0, 0), (1100, 120), (40, 60, 80), (20, 30, 40))
        putText_outline(tela, "RANKING - MODO SOLO", (40, 60), cv2.FONT_HERSHEY_DUPLEX, 1.5, (0, 255, 220), 4)
        putText_outline(tela, "TOP 5 MELHORES PONTUACOES", (40, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (180, 180, 180), 2)
        cv2.rectangle(tela, (40, 650), (1060, 680), (50, 50, 50), -1)
        putText_outline(tela, "Pressione ESC para voltar", (60, 670), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
        
        headers = [
            ("POS", 0, 60), ("JOGADOR", 80, 200), ("PONTOS", 300, 90), ("MOV.", 410, 80),
            ("TEMPO", 510, 100), ("DATA", 630, 120), ("EXCLUIR", 770, 100)
        ]
        
        for header, x_offset_h, width in headers:
            cv2.rectangle(tela, (x_base + x_offset_h, y_offset - 35), (x_base + x_offset_h + width, y_offset + 5), (60, 60, 60), -1)
            putText_outline(tela, header, (x_base + x_offset_h + 10, y_offset - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        
        y_offset_row = y_offset + 15
        cv2.line(tela, (x_base, y_offset_row), (x_base + 870, y_offset_row), (100, 100, 100), 2)
        y_offset_row += 30
        
        if not ranking_data:
            cv2.rectangle(tela, (x_base, y_offset_row), (x_base + 870, y_offset_row + 100), (40, 40, 40), -1)
            putText_outline(tela, "Nenhum registro encontrado", (x_base + 200, y_offset_row + 55), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (150, 150, 150), 2)
        else:
            for i, entry in enumerate(ranking_data):
                row_color = (35, 35, 35) if i % 2 == 0 else (28, 28, 28)
                cv2.rectangle(tela, (x_base, y_offset_row - 25), (x_base + 870, y_offset_row + 15), row_color, -1)
                
                pos_color = (200, 200, 200)
                if i == 0: pos_color = (0, 215, 255)
                elif i == 1: pos_color = (192, 192, 192)
                elif i == 2: pos_color = (205, 127, 50)
                
                data_str = entry.get("data_hora", "N/A").split(' ')[0]
                
                putText_outline(tela, f"{i+1}º", (x_base + 10, y_offset_row), cv2.FONT_HERSHEY_SIMPLEX, 0.7, pos_color, 2)
                putText_outline(tela, entry["nome"][:15], (x_base + 90, y_offset_row), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 220, 220), 1)
                putText_outline(tela, str(entry.get("pontuacao", "N/A")), (x_base + 310, y_offset_row), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
                putText_outline(tela, str(entry.get("movimentos_totais", "N/A")), (x_base + 420, y_offset_row), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
                tempo_seg = entry.get("tempo_total_segundos", 0)
                putText_outline(tela, f"{int(tempo_seg // 60):02d}:{int(tempo_seg % 60):02d}", (x_base + 520, y_offset_row), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
                putText_outline(tela, data_str, (x_base + 640, y_offset_row), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)
                
                btn_x, btn_y, btn_w, btn_h = x_base + 780, y_offset_row - 12, 35, 30
                cv2.rectangle(tela, (btn_x, btn_y), (btn_x + btn_w, btn_y + btn_h), (150, 50, 50), -1)
                putText_outline(tela, "X", (btn_x + 9, btn_y + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                delete_buttons.append(((btn_x, btn_y, btn_x + btn_w, btn_y + btn_h), entry.get('id')))
                y_offset_row += 50
        
        cv2.setMouseCallback(window_name, handle_mouse_click_ranking, param={'buttons': delete_buttons, 'file': RANKING_FILE_SOLO})
        cv2.imshow(window_name, tela)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            cv2.destroyWindow(window_name)
            break
        
        if click_info['clicked']:
            if show_confirmation_screen(window_name, "Excluir esta entrada do ranking?"):
                ranking_data = remove_ranking_entry(click_info['file'], click_info['id'])
            click_info = {'clicked': False, 'file': None, 'id': None}

def show_competicao_ranking():
    """Exibe ranking detalhado do modo competição com espaçamento corrigido."""
    global click_info
    click_info = {'clicked': False, 'file': None, 'id': None}
    ranking_data = get_competicao_ranking()
    window_name = "Ranking Competicao"

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    y_offset = 160
    x_base = 40

    while True:
        delete_buttons = []
        tela = np.ones((700, 1100, 3), dtype=np.uint8) * 20
        draw_gradient_rect(tela, (0, 0), (1100, 120), (80, 40, 60), (40, 20, 30))
        
        putText_outline(tela, "RANKING - MODO COMPETICAO", (40, 60), cv2.FONT_HERSHEY_DUPLEX, 1.5, (255, 100, 150), 4)
        putText_outline(tela, "TOP 5 BATALHAS EPICAS", (40, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (180, 180, 180), 2)
        cv2.rectangle(tela, (40, 650), (1060, 680), (50, 50, 50), -1)
        putText_outline(tela, "Pressione ESC para voltar", (60, 670), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
        
        headers = [
            ("POS", 0, 70), ("VENCEDOR", 90, 200), ("PONT.J1", 310, 90), ("PONT.J2", 410, 90),
            ("TEMPO", 510, 100), ("DATA", 620, 130), ("HORA", 780, 90), ("EXCLUIR", 890, 80)
        ]
        
        for header, x_offset_h, width in headers:
            cv2.rectangle(tela, (x_base + x_offset_h, y_offset - 35), (x_base + x_offset_h + width, y_offset + 5), (60, 60, 60), -1)
            putText_outline(tela, header, (x_base + x_offset_h + 10, y_offset - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        
        y_offset_row = y_offset + 15
        cv2.line(tela, (x_base, y_offset_row), (x_base + 970, y_offset_row), (100, 100, 100), 2)
        y_offset_row += 30
        
        if not ranking_data:
            cv2.rectangle(tela, (x_base, y_offset_row), (x_base + 970, y_offset_row + 100), (40, 40, 40), -1)
            putText_outline(tela, "Nenhuma competicao registrada ainda", (x_base + 200, y_offset_row + 55), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (150, 150, 150), 2)
        else:
            for i, entry in enumerate(ranking_data):
                row_color = (35, 35, 35) if i % 2 == 0 else (28, 28, 28)
                cv2.rectangle(tela, (x_base, y_offset_row - 25), (x_base + 970, y_offset_row + 15), row_color, -1)
                
                pos_color = (200, 200, 200)
                if i == 0: pos_color = (0, 215, 255)
                elif i == 1: pos_color = (192, 192, 192)
                elif i == 2: pos_color = (205, 127, 50)
                
                parts = entry.get("data_hora", "N/A N/A").split(' ')
                data_str = parts[0]; hora_str = parts[1] if len(parts) > 1 else "N/A"
                
                putText_outline(tela, f"{i+1}º", (x_base + 10, y_offset_row), cv2.FONT_HERSHEY_SIMPLEX, 0.7, pos_color, 2)
                
                vencedor_nome = entry["nome_vencedor"][:15]
                perdedor_nome = entry["nome_perdedor"][:15]
                putText_outline(tela, vencedor_nome, (x_base + 100, y_offset_row - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 100), 2)
                putText_outline(tela, perdedor_nome, (x_base + 100, y_offset_row + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 255), 1)
                
                putText_outline(tela, str(entry.get("pontuacao_jogador1", "N/A")), (x_base + 320, y_offset_row), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 255, 150), 2)
                putText_outline(tela, str(entry.get("pontuacao_jogador2", "N/A")), (x_base + 420, y_offset_row), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 140, 80), 2)
                tempo_seg = entry["tempo_total_segundos"]
                putText_outline(tela, f"{int(tempo_seg // 60):02d}:{int(tempo_seg % 60):02d}", (x_base + 510, y_offset_row), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
                putText_outline(tela, data_str, (x_base + 620, y_offset_row), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 180), 1)
                putText_outline(tela, hora_str, (x_base + 780, y_offset_row), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 180), 1)
                
                btn_x, btn_y, btn_w, btn_h = x_base + 890, y_offset_row - 12, 35, 30
                cv2.rectangle(tela, (btn_x, btn_y), (btn_x + btn_w, btn_y + btn_h), (150, 50, 50), -1)
                putText_outline(tela, "X", (btn_x + 9, btn_y + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                delete_buttons.append(((btn_x, btn_y, btn_x + btn_w, btn_y + btn_h), entry.get('id')))
                y_offset_row += 55
        
        cv2.setMouseCallback(window_name, handle_mouse_click_ranking, param={'buttons': delete_buttons, 'file': RANKING_FILE_COMPETICAO})
        cv2.imshow(window_name, tela)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            cv2.destroyWindow(window_name)
            break
        
        if click_info['clicked']:
            if show_confirmation_screen(window_name, "Excluir esta entrada do ranking?"):
                ranking_data = remove_ranking_entry(click_info['file'], click_info['id'])
            click_info = {'clicked': False, 'file': None, 'id': None}

def mostrar_resultado_analise(counter_final, tempo_total):
    """Mostra o resultado final da análise de vídeo."""
    window_name = "Resultado da Analise"
    while True:
        tela = np.ones((400, 800, 3), dtype=np.uint8) * 24
        draw_filled_transparent_rect(tela, (0, 0), (800, 100), (20, 22, 25), 0.9)
        putText_outline(tela, "ANALISE DE VIDEO CONCLUIDA", (50, 65), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 255, 220), 3)

        stats_text = f"Total de Polichinelos Detectados: {counter_final}"
        duration_text = f"Duracao Analisada: {int(tempo_total // 60):02d}m {int(tempo_total % 60):02d}s"

        putText_outline(tela, stats_text, (60, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        putText_outline(tela, duration_text, (60, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (230, 230, 230), 2)

        draw_button(tela, (250, 300, 550, 350), (200, 80, 80), "[ESC] VOLTAR AO MENU", label_color=(255, 255, 255), scale=0.9)
        
        show_fullscreen(window_name, tela)
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27: # ESC
            cv2.destroyWindow(window_name)
            break

# ============================================================================
# CLASSES DE LÓGICA DO JOGO (DO NOVO CÓDIGO)
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
        if self.vencedor: return # Impede contagem após um vencedor ser definido
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
    def __init__(self, nome_usuario, meta_polichinelos=20):
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
        if not stage_transition: return 0
        
        self.total_movimentos += 1
        
        score_up = (1.0 if arms_up else 0.5) + (1.0 if legs_open else 0.5)
        score_down = (1.0 if arms_down else 0.5) + (1.0 if legs_closed else 0.5)
        precisao = (score_up + score_down) / 4.0
        
        pontos = 50
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
        
        self.historico_precisao.append(precisao)
        return pontos

    def calcular_bonus(self):
        tempo_total = time.time() - self.tempo_inicio
        
        if tempo_total > 0 and self.total_movimentos > 0:
            ppm = (self.total_movimentos / tempo_total) * 60
            if ppm >= 30: self.bonus_velocidade = 50
            elif ppm >= 20: self.bonus_velocidade = 25
            else: self.bonus_velocidade = 0
        
        if len(self.historico_precisao) >= 5:
            consistencia = 1 - np.std(self.historico_precisao)
            if consistencia >= 0.9: self.bonus_consistencia = 100
            elif consistencia >= 0.8: self.bonus_consistencia = 50
            else: self.bonus_consistencia = 0

    def get_nota_final(self):
        if self.total_movimentos == 0:
            return "F", 0, "Nenhum movimento detectado"
        
        taxa_acerto = self.movimentos_corretos / self.total_movimentos
        pontos_base = taxa_acerto * 500
        
        self.calcular_bonus()
        pontos_bonus = self.bonus_velocidade + self.bonus_consistencia + (self.melhor_sequencia * 10)
        pontuacao_total = int(pontos_base + pontos_bonus)
        
        if pontuacao_total >= 650: nota, desc = "S+", "EXCEPCIONAL!"
        elif pontuacao_total >= 550: nota, desc = "S", "EXCELENTE!"
        elif pontuacao_total >= 450: nota, desc = "A", "MUITO BOM!"
        elif pontuacao_total >= 350: nota, desc = "B", "BOM!"
        elif pontuacao_total >= 250: nota, desc = "C", "REGULAR"
        elif pontuacao_total >= 150: nota, desc = "D", "PRECISA MELHORAR"
        else: nota, desc = "F", "TENTE NOVAMENTE"
        
        return nota, pontuacao_total, desc

# ============================================================================
# INTERFACE COM O USUÁRIO (DO NOVO CÓDIGO)
# ============================================================================

def obter_nome_estilizado(prompt_text, window_title, default_name):
    nome = ""
    max_chars = 15
    while True:
        tela = np.ones((400, 700, 3), dtype=np.uint8) * 24
        draw_filled_transparent_rect(tela, (0, 0), (700, 80), (20, 22, 25), 0.9)
        cv2.putText(tela, window_title, (40, 55), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 255, 220), 2, cv2.LINE_AA)
        cv2.putText(tela, prompt_text, (40, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (230, 230, 230), 2, cv2.LINE_AA)
        input_box_rect = (40, 170, 660, 230)
        cv2.rectangle(tela, (input_box_rect[0], input_box_rect[1]), (input_box_rect[2], input_box_rect[3]), (45, 45, 45), -1)
        cv2.rectangle(tela, (input_box_rect[0], input_box_rect[1]), (input_box_rect[2], input_box_rect[3]), (150, 150, 150), 2)
        (tw, th), _ = cv2.getTextSize(nome, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
        text_y = input_box_rect[1] + (input_box_rect[3] - input_box_rect[1] + th) // 2
        cursor = "|" if int(time.time() * 2) % 2 == 0 else ""
        cv2.putText(tela, nome + cursor, (input_box_rect[0] + 15, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3, cv2.LINE_AA)
        draw_label_box(tela, "Pressione ENTER para confirmar ou ESC para sair", (40, 350), font=cv2.FONT_HERSHEY_PLAIN, scale=1.2)
        
        show_fullscreen(window_title, tela)
        
        key = cv2.waitKey(50)
        if key == 13:
            cv2.destroyWindow(window_title)
            return nome.strip() if nome.strip() else default_name
        elif key == 27:
            cv2.destroyWindow(window_title)
            return None
        elif key == 8:
            nome = nome[:-1]
        elif key != -1 and len(nome) < max_chars and 32 <= key <= 126:
            nome += chr(key)

def obter_nome_usuario():
    return obter_nome_estilizado("Digite seu nome:", "Modo Solo", "Jogador")

def obter_nomes_jogadores():
    nome1 = obter_nome_estilizado("Digite o nome do JOGADOR 1:", "Modo Competicao", "Jogador1")
    if nome1 is None: return None, None
    nome2 = obter_nome_estilizado("Digite o nome do JOGADOR 2:", "Modo Competicao", "Jogador2")
    if nome2 is None: return nome1, None
    return nome1, nome2

def escolher_modo():
    """Menu principal com as opções de ranking adicionadas."""
    while True:
        tela = np.ones((500, 720, 3), dtype=np.uint8) * 24
        draw_filled_transparent_rect(tela, (0, 0), (720, 100), (20, 22, 25), 0.9)
        cv2.putText(tela, "CONTADOR DE POLICHINELOS", (40, 60), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 255, 220), 2, cv2.LINE_AA)
        cv2.putText(tela, "Escolha o modo de uso:", (40, 92), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (230, 230, 230), 2, cv2.LINE_AA)
        
        draw_button(tela, (80, 120, 640, 170), (80, 170, 255), "[1] MODO SOLO", label_color=(20, 22, 25))
        draw_button(tela, (80, 180, 640, 230), (255, 140, 80), "[2] MODO COMPETICAO", label_color=(20, 22, 25))
        draw_button(tela, (80, 240, 640, 290), (0, 210, 180), "[3] ANALISAR VIDEO", label_color=(20, 22, 25))
        draw_button(tela, (80, 300, 640, 350), (200, 200, 0), "[4] RANKING SOLO", label_color=(20, 22, 25))
        draw_button(tela, (80, 360, 640, 410), (0, 200, 200), "[5] RANKING COMPETICAO", label_color=(20, 22, 25))
        
        draw_label_box(tela, "Pressione 1-5 para selecionar ou ESC para sair", (40, 450), font=cv2.FONT_HERSHEY_PLAIN, scale=1.2)
        
        show_fullscreen("Selecao de Modo", tela)
        
        key = cv2.waitKey(1)
        if key == ord("1"): cv2.destroyWindow("Selecao de Modo"); return 0
        elif key == ord("2"): cv2.destroyWindow("Selecao de Modo"); return 1
        elif key == ord("3"): cv2.destroyWindow("Selecao de Modo"); return 2
        elif key == ord("4"): cv2.destroyWindow("Selecao de Modo"); return 3
        elif key == ord("5"): cv2.destroyWindow("Selecao de Modo"); return 4
        elif key == 27: cv2.destroyWindow("Selecao de Modo"); return None

def escolher_meta():
    while True:
        tela = np.ones((500, 650, 3), dtype=np.uint8) * 24
        draw_filled_transparent_rect(tela, (0, 0), (650, 100), (20, 22, 25), 0.9)
        cv2.putText(tela, "ESCOLHA A META", (50, 65), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 255, 220), 3, cv2.LINE_AA)
        draw_label_box(tela, "Pressione 1-4 para selecionar", (50, 130), scale=1.0, padding=8, alpha=0.8, text_color=(200, 200, 200))
        metas = [10, 20, 30, 50]
        descricoes = ["Iniciante", "Intermediario", "Avancado", "Expert"]
        cores = [(100, 255, 100), (80, 170, 255), (255, 140, 80), (255, 80, 120)]
        y_pos = 180
        for i, (meta, desc, cor) in enumerate(zip(metas, descricoes, cores)):
            draw_button(tela, (50, y_pos, 600, y_pos + 55), cor, f"[{i+1}] {meta} Polichinelos - {desc}", label_color=(20, 22, 25), scale=0.85)
            y_pos += 75
            
        show_fullscreen("Escolha da Meta", tela)
        
        key = cv2.waitKey(1)
        if key in [ord('1'), ord('2'), ord('3'), ord('4')]:
            cv2.destroyWindow("Escolha da Meta")
            return metas[key - ord('1')]
        elif key == 27:
            cv2.destroyWindow("Escolha da Meta")
            return None

# ============================================================================
# FUNÇÃO CORRIGIDA - mostrar_resultado_competicao
# ============================================================================
def mostrar_resultado_competicao(competition, counter1, counter2):
    """Tela de resultado da competição com salvamento no ranking."""
    tempo_total = int(competition.tempo_final) if competition.tempo_final else int(time.time() - competition.tempo_inicio)
    
    if competition.vencedor:
        vencedor_nome = competition.jogador1 if competition.vencedor == 1 else competition.jogador2
        perdedor_nome = competition.jogador2 if competition.vencedor == 1 else competition.jogador1
        vencedor_pts = counter1 if competition.vencedor == 1 else counter2
        perdedor_pts = counter2 if competition.vencedor == 1 else counter1
        # Chamada corrigida para incluir os pontos de J1 (counter1) e J2 (counter2)
        add_competicao_score(vencedor_nome, vencedor_pts, perdedor_nome, perdedor_pts, tempo_total, counter1, counter2)
    
    pontuacao1, pontuacao2 = counter1 * 50, counter2 * 50
    status1, status2 = "EM ANDAMENTO", "EM ANDAMENTO"
    if competition.vencedor == 1:
        pontuacao1 += 200; status1, status2 = "VENCEDOR", "2° LUGAR"
    elif competition.vencedor == 2:
        pontuacao2 += 200; status1, status2 = "2° LUGAR", "VENCEDOR"

    velocidade1 = (counter1 / tempo_total * 60) if tempo_total > 0 else 0
    velocidade2 = (counter2 / tempo_total * 60) if tempo_total > 0 else 0
    progresso1 = min((counter1 / competition.meta_polichinelos) * 100, 100)
    progresso2 = min((counter2 / competition.meta_polichinelos) * 100, 100)
    
    while True:
        tela = np.ones((750, 1000, 3), dtype=np.uint8) * 24
        draw_filled_transparent_rect(tela, (0, 0), (1000, 120), (20, 22, 25), 0.9)
        cv2.putText(tela, "RESULTADO DETALHADO DA COMPETICAO", (50, 70), cv2.FONT_HERSHEY_DUPLEX, 1.3, (0, 255, 220), 3)
        cv2.putText(tela, f"Duracao Total: {tempo_total//60}:{tempo_total%60:02d}", (50, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
        
        y_start, col1_x, col2_x = 180, 80, 520
        cv2.putText(tela, f"{competition.jogador1.upper()}", (col1_x, y_start), cv2.FONT_HERSHEY_DUPLEX, 1.2, (80, 170, 255), 3)
        cv2.putText(tela, status1, (col1_x, y_start + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (80, 170, 255), 2)
        stats1 = [ f"Pontuacao Final: {pontuacao1} pts", f"Polichinelos: {counter1}/{competition.meta_polichinelos}", f"Velocidade: {velocidade1:.1f}/min", f"Progresso: {progresso1:.1f}%", f"Meta Atingida: {'SIM' if counter1 >= competition.meta_polichinelos else 'NAO'}" ]
        y_pos = y_start + 80
        for i, stat in enumerate(stats1):
            color = (0, 255, 100) if i == 0 and competition.vencedor == 1 else (230, 230, 230)
            cv2.putText(tela, stat, (col1_x, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2); y_pos += 40
        barra_width, barra_height, barra_y = 300, 25, y_pos + 10
        cv2.rectangle(tela, (col1_x, barra_y), (col1_x + barra_width, barra_y + barra_height), (50, 50, 50), -1)
        cv2.rectangle(tela, (col1_x, barra_y), (col1_x + int(barra_width * progresso1/100), barra_y + barra_height), (80, 170, 255), -1)
        cv2.putText(tela, f"{progresso1:.0f}%", (col1_x + barra_width + 10, barra_y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.putText(tela, f"{competition.jogador2.upper()}", (col2_x, y_start), cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 140, 80), 3)
        cv2.putText(tela, status2, (col2_x, y_start + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 140, 80), 2)
        stats2 = [ f"Pontuacao Final: {pontuacao2} pts", f"Polichinelos: {counter2}/{competition.meta_polichinelos}", f"Velocidade: {velocidade2:.1f}/min", f"Progresso: {progresso2:.1f}%", f"Meta Atingida: {'SIM' if counter2 >= competition.meta_polichinelos else 'NAO'}" ]
        y_pos = y_start + 80
        for i, stat in enumerate(stats2):
            color = (0, 255, 100) if i == 0 and competition.vencedor == 2 else (230, 230, 230)
            cv2.putText(tela, stat, (col2_x, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2); y_pos += 40
        cv2.rectangle(tela, (col2_x, barra_y), (col2_x + barra_width, barra_y + barra_height), (50, 50, 50), -1)
        cv2.rectangle(tela, (col2_x, barra_y), (col2_x + int(barra_width * progresso2/100), barra_y + barra_height), (255, 140, 80), -1)
        cv2.putText(tela, f"{progresso2:.0f}%", (col2_x + barra_width + 10, barra_y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.line(tela, (500, y_start), (500, barra_y + barra_height + 20), (100, 100, 100), 2)
        
        if competition.vencedor:
            vencedor_nome = competition.jogador1 if competition.vencedor == 1 else competition.jogador2
            resultado_texto = f"PARABENS {vencedor_nome.upper()}! Resultado salvo no ranking."
            (rw, rh), _ = cv2.getTextSize(resultado_texto, cv2.FONT_HERSHEY_DUPLEX, 1.0, 3)
            cv2.putText(tela, resultado_texto, ((1000 - rw) // 2, barra_y + 80), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 255, 100), 3)
        
        draw_button(tela, (150, 650, 450, 700), (0, 200, 100), "[ENTER] NOVA PARTIDA", label_color=(20, 22, 25))
        draw_button(tela, (550, 650, 850, 700), (200, 80, 80), "[ESC] SAIR", label_color=(255, 255, 255))
        
        show_fullscreen("Resultado da Competicao", tela)
        key = cv2.waitKey(1)
        
        if key == 13:
            cv2.destroyWindow("Resultado da Competicao")
            return True
        elif key == 27:
            cv2.destroyWindow("Resultado da Competicao")
            return False

def mostrar_resultado_final(gamification, counter_final):
    """Tela de resultado do modo solo com salvamento no ranking."""
    nota, pontuacao, descricao = gamification.get_nota_final()
    tempo_total = time.time() - gamification.tempo_inicio
    
    add_solo_score(gamification.nome_usuario, pontuacao, gamification.total_movimentos, gamification.movimentos_corretos, tempo_total)
    
    while True:
        tela = np.ones((500, 850, 3), dtype=np.uint8) * 24
        draw_filled_transparent_rect(tela, (0, 0), (850, 100), (20, 22, 25), 0.9)
        cv2.putText(tela, "RELATORIO FINAL", (50, 65), cv2.FONT_HERSHEY_DUPLEX, 1.4, (0, 255, 220), 3)
        
        y_info = 150
        cv2.putText(tela, f"Jogador: {gamification.nome_usuario}", (60, y_info), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        y_info += 50
        
        stats = [
            f"Pontuacao Total: {pontuacao}",
            f"Polichinelos: {counter_final}/{gamification.meta_polichinelos}",
            f"Tempo: {int(tempo_total//60)}:{int(tempo_total%60):02d}"
        ]
        
        y_pos = y_info
        for stat in stats:
            cv2.putText(tela, stat, (60, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (230, 230, 230), 2)
            y_pos += 40
        
        cv2.putText(tela, "Resultado salvo no ranking!", (60, y_pos + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 100), 2)
        
        draw_button(tela, (80, 400, 380, 450), (0, 200, 100), "[ENTER] REINICIAR", label_color=(20, 22, 25), scale=0.9)
        draw_button(tela, (470, 400, 770, 450), (200, 80, 80), "[ESC] SAIR", label_color=(255, 255, 255), scale=0.9)
        
        show_fullscreen("Resultado Final", tela)
        key = cv2.waitKey(1)
        
        if key == 13:
            cv2.destroyWindow("Resultado Final")
            return True
        elif key == 27:
            cv2.destroyWindow("Resultado Final")
            return False

# ============================================================================
# DETECÇÃO E PROCESSAMENTO DE POSE
# ============================================================================

def detectar_multiplas_pessoas_corrigido(image, pose_model):
    h, w = image.shape[:2]
    meio_x = w // 2
    
    jogador1_landmarks, jogador2_landmarks = None, None
    jogador1_original, jogador2_original = None, None
    
    frame_esquerdo = image[:, :meio_x].copy()
    resultado_esquerda = pose_model.process(cv2.cvtColor(frame_esquerdo, cv2.COLOR_BGR2RGB))
    if resultado_esquerda.pose_landmarks:
        jogador1_landmarks = copy.deepcopy(resultado_esquerda.pose_landmarks)
        jogador1_original = copy.deepcopy(resultado_esquerda.pose_landmarks)
        for landmark in jogador1_landmarks.landmark:
            landmark.x = landmark.x * 0.5
    
    frame_direito = image[:, meio_x:].copy()
    resultado_direita = pose_model.process(cv2.cvtColor(frame_direito, cv2.COLOR_BGR2RGB))
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

# ========================================================================
# BLOCO PRINCIPAL DO PROGRAMA
# ========================================================================
if __name__ == "__main__":
    mp_drawing = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose

    WINDOW_NAME = "Contador de Polichinelos"
    while True:
        modo = escolher_modo()
        if modo is None:
            break
        if modo == 3:
            show_solo_ranking()
            continue
        if modo == 4:
            show_competicao_ranking()
            continue

        if modo == 0:  # SOLO
            nome_usuario = obter_nome_usuario()
            if not nome_usuario:
                continue
            meta = escolher_meta()
            if not meta:
                continue
            gamification = GamificationSystem(nome_usuario, meta)
            pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
            cap = cv2.VideoCapture(0)
            counter1 = 0
            stage1 = "down"
            open_frames1 = 0
            closed_frames1 = 0
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
                        if stage1 == "down" and open_frames1 >= 3 and arms_up and legs_open:
                            stage1 = "up"
                        elif stage1 == "up" and closed_frames1 >= 3 and arms_down and legs_closed:
                            stage1 = "down"
                            counter1 += 1
                            gamification.avaliar_movimento(arms_up, legs_open, arms_down, legs_closed, True)
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                putText_outline(image, f"Repeticoes: {counter1}", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255))
                putText_outline(image, f"Meta: {gamification.meta_polichinelos}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255))
                show_fullscreen(WINDOW_NAME, image)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or counter1 >= gamification.meta_polichinelos:
                    break
            cap.release()
            cv2.destroyAllWindows()
            mostrar_resultado_final(gamification, counter1)

        elif modo == 2:  # ANALISAR VIDEO
            Tk().withdraw()
            video_path = filedialog.askopenfilename(title="Selecione o vídeo para análise", filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
            if not video_path:
                continue
            pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
            cap = cv2.VideoCapture(video_path)
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
                        if stage1 == "down" and open_frames1 >= 3 and arms_up and legs_open:
                            stage1 = "up"
                        elif stage1 == "up" and closed_frames1 >= 3 and arms_down and legs_closed:
                            stage1 = "down"
                            counter1 += 1
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                putText_outline(image, "ANALISE DE VIDEO", (30, 40), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 220))
                putText_outline(image, f"Polichinelos: {counter1}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255))
                show_fullscreen(WINDOW_NAME, image)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
            cap.release()
            cv2.destroyAllWindows()
            tempo_total = time.time() - start_time
            mostrar_resultado_analise(counter1, tempo_total)

        elif modo == 1:  # COMPETICAO
            nome1, nome2 = obter_nomes_jogadores()
            if not nome1 or not nome2:
                continue
            meta = escolher_meta()
            if not meta:
                continue
            competition = CompetitionSystem(nome1, nome2, meta)
            pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
            cap = cv2.VideoCapture(0)
            counter1 = 0
            counter2 = 0
            stage1 = "down"
            stage2 = "down"
            open_frames1 = 0
            closed_frames1 = 0
            open_frames2 = 0
            closed_frames2 = 0
            flash_frames1 = 0
            flash_frames2 = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                h, w = frame.shape[:2]
                image = frame.copy()
                jogador1_landmarks, jogador2_landmarks, jogador1_original, jogador2_original, meio_x = detectar_multiplas_pessoas_corrigido(image, pose)
                
                cv2.line(image, (meio_x, 0), (meio_x, h), (100, 100, 100), 2)
                
                if jogador1_landmarks:
                    mp_drawing.draw_landmarks(image, jogador1_landmarks, mp_pose.POSE_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(80, 170, 255), thickness=2, circle_radius=2),
                        mp_drawing.DrawingSpec(color=(80, 170, 255), thickness=2))
                
                if jogador2_landmarks:
                    mp_drawing.draw_landmarks(image, jogador2_landmarks, mp_pose.POSE_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(255, 140, 80), thickness=2, circle_radius=2),
                        mp_drawing.DrawingSpec(color=(255, 140, 80), thickness=2))
                
                counter1, stage1, open_frames1, closed_frames1, flash_frames1, status1 = processar_jogador_competicao(
                    jogador1_landmarks, jogador1_original, meio_x, h, 1, counter1, stage1, open_frames1, closed_frames1, flash_frames1, competition, frame)
                counter2, stage2, open_frames2, closed_frames2, flash_frames2, status2 = processar_jogador_competicao(
                    jogador2_landmarks, jogador2_original, w - meio_x, h, 2, counter2, stage2, open_frames2, closed_frames2, flash_frames2, competition, frame)
                
                putText_outline(image, f"{nome1}: {counter1}", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (80,170,255))
                putText_outline(image, f"{nome2}: {counter2}", (w//2 + 30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,140,80))
                putText_outline(image, f"Meta: {meta}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255))
                show_fullscreen(WINDOW_NAME, image)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or competition.vencedor:
                    break
            cap.release()
            cv2.destroyAllWindows()
            mostrar_resultado_competicao(competition, counter1, counter2)