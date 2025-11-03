import time
import cv2
import config
from utils import distancia_euclidiana

def processar_lado(modelo_pose, recorte_bgr, deslocamento_x, estado):
    """
    Mesma função processar_lado, isolada aqui. Retorna (estado, pontos_para_desenhar)
    """
    altura, largura, _ = recorte_bgr.shape
    pontos_para_desenhar = []

    imagem_rgb = cv2.cvtColor(recorte_bgr, cv2.COLOR_BGR2RGB)
    resultados = modelo_pose.process(imagem_rgb)
    agora = time.time()
    estado['ultimo_visto'] = agora

    if not resultados.pose_landmarks:
        return estado, pontos_para_desenhar

    marcos = resultados.pose_landmarks.landmark

    def para_px(indice):
        return (int(marcos[indice].x * largura), int(marcos[indice].y * altura))

    ombro_esq = para_px(config.OMBRO_ESQUERDO)
    ombro_dir = para_px(config.OMBRO_DIREITO)
    pulso_esq = para_px(config.PULSO_ESQUERDO)
    pulso_dir = para_px(config.PULSO_DIREITO)
    quadril_esq = para_px(config.QUADRIL_ESQUERDO)
    quadril_dir = para_px(config.QUADRIL_DIREITO)
    tornozelo_esq = para_px(config.TORNOZELO_ESQUERDO)
    tornozelo_dir = para_px(config.TORNOZELO_DIREITO)

    for p in (ombro_esq, ombro_dir, pulso_esq, pulso_dir, quadril_esq, quadril_dir, tornozelo_esq, tornozelo_dir):
        pontos_para_desenhar.append((p[0] + deslocamento_x, p[1]))

    y_ombros = (ombro_esq[1] + ombro_dir[1]) / 2.0

    pulso_acima = (pulso_esq[1] < y_ombros - config.MARGEM_BRACO_ACIMA_OMBRO * altura) and \
                  (pulso_dir[1] < y_ombros - config.MARGEM_BRACO_ACIMA_OMBRO * altura)

    distancia_quadril = distancia_euclidiana(quadril_esq, quadril_dir) + 1e-6
    distancia_tornozelos = distancia_euclidiana(tornozelo_esq, tornozelo_dir)
    razao_tornozelo_quadril = distancia_tornozelos / distancia_quadril
    pernas_abertas = razao_tornozelo_quadril >= config.RAZAO_TORNOZELO_QUADRIL_ABERTO

    y_quadris = (quadril_esq[1] + quadril_dir[1]) / 2.0
    pulsos_perto_quadril = (pulso_esq[1] > y_quadris - (config.MARGEM_PULSO_QUADRIL * altura)) and \
                           (pulso_dir[1] > y_quadris - (config.MARGEM_PULSO_QUADRIL * altura))

    pernas_fechadas = razao_tornozelo_quadril <= config.RAZAO_TORNOZELO_QUADRIL_FECHADO

    centro_x_quadris = (quadril_esq[0] + quadril_dir[0]) / 2.0
    dist_tornozelo_esq_centro = abs(tornozelo_esq[0] - centro_x_quadris)
    dist_tornozelo_dir_centro = abs(tornozelo_dir[0] - centro_x_quadris)

    if dist_tornozelo_dir_centro < 1e-6:
        razao_simetria = 1.0 if dist_tornozelo_esq_centro < 1e-6 else 1000.0
    else:
        razao_simetria = dist_tornozelo_esq_centro / dist_tornozelo_dir_centro

    pernas_simetricas = (razao_simetria < config.LIMITE_RAZAO_SIMETRIA) and \
                        (razao_simetria > (1.0 / config.LIMITE_RAZAO_SIMETRIA))

    fase = estado.get('fase', 'fechado')

    if fase == 'fechado' or fase == 'desconhecido':
        if pulso_acima and pernas_abertas and pernas_simetricas:
            estado['fase'] = 'aberto'
            estado['tempo_aberto'] = agora

    elif fase == 'aberto':
        if pulsos_perto_quadril and pernas_fechadas and pernas_simetricas:
            estado['contagem'] = estado.get('contagem', 0) + 1
            estado['fase'] = 'fechado'
            estado['ultimo_tempo_contagem'] = agora

    return estado, pontos_para_desenhar