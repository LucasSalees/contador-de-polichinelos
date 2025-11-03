import math

def distancia_euclidiana(a, b):
    """Calcula distância euclidiana entre tuplas (x,y)."""
    return math.hypot(a[0] - b[0], a[1] - b[1])