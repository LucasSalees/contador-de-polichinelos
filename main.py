# Importação das bibliotecas necessárias
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import cv2
import mediapipe as mp
import time

# Importar módulos novos
from detector import processar_lado
from gui import mostrar_menu
from utils import distancia_euclidiana  # se precisar em main
import config

def principal(caminho_video=None, max_individuos=2):
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

    modelo_pose = mp.solutions.pose.Pose(min_detection_confidence=config.CONFIANCA_MIN_DETECCAO,
                                         min_tracking_confidence=config.CONFIANCA_MIN_RASTREAMENTO)

    estados = []
    for _ in range(max_individuos):
        estados.append({'fase': 'fechado', 'contagem': 0, 'ultimo_visto': 0.0})

    modo_camera = (caminho_video is None)
    tempo_anterior = time.time()
    contador_frames = 0
    fps = 0
    titulo_janela = 'Contador de Polichinelos - Pressione ESC para voltar'
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

            contador_frames += 1
            tempo_atual = time.time()
            tempo_decorrido = tempo_atual - tempo_anterior

            if tempo_decorrido >= 1.0:
                fps = contador_frames / tempo_decorrido
                contador_frames = 0
                tempo_anterior = tempo_atual

            todos_pontos_para_desenhar = []
            meio = largura // 2
            if max_individuos == 2:
                cv2.line(quadro, (meio, 0), (meio, altura), (200, 200, 200), 2)
                metades = [
                    (0, 0, meio, altura),
                    (meio, 0, largura - meio, altura)
                ]
            else:
                metades = [(0, 0, largura, altura)]

            for i, (x, y, cw, ch) in enumerate(metades):
                recorte = quadro[y:y+ch, x:x+cw]
                if recorte.size == 0:
                    continue

                estado_atualizado, pontos_desenho = processar_lado(modelo_pose, recorte, x, estados[i])
                estados[i] = estado_atualizado
                if pontos_desenho:
                    todos_pontos_para_desenhar.extend(pontos_desenho)

                cv2.rectangle(quadro, (x, y), (x + cw, y + ch), (70, 70, 70), 1)

                overlay = quadro.copy()
                texto = f"PESSOA {i+1}: {estados[i].get('contagem', 0)}"
                if max_individuos == 1:
                    texto = f"TOTAL: {estados[i].get('contagem', 0)}"

                (w, h), _ = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
                tx = x + 15
                ty = y + 35

                cv2.rectangle(overlay, (tx - 5, ty - h - 5), (tx + w + 5, ty + 8), (20, 20, 20), -1)
                cv2.putText(overlay, texto, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (57, 255, 20), 2)
                alpha = 0.6
                cv2.addWeighted(overlay, alpha, quadro, 1 - alpha, 0, quadro)

            for (px, py) in todos_pontos_para_desenhar:
                cv2.circle(quadro, (px, py), 5, (255, 200, 0), -1)

            texto_fps = f"FPS: {fps:.1f}"
            (largura_texto, altura_texto), _ = cv2.getTextSize(texto_fps, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            pos_x_fps = (largura - largura_texto) // 2
            cv2.putText(quadro, texto_fps, (pos_x_fps, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

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

# Ponto de entrada do programa
if __name__ == "__main__":
    while True:
        modo, caminho, max_inds = mostrar_menu()
        if modo is None:
            print("Nenhuma opção selecionada. Encerrando.")
            break
        status = None
        if modo == 'camera':
            status = principal(None, max_individuos=max_inds)
        elif modo == 'video' and caminho:
            status = principal(caminho, max_individuos=max_inds)
        if status == 'VOLTAR_MENU':
            continue
        else:
            break