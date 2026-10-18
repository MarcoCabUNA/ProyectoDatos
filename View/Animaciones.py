"""
Animaciones (Vista): funciones PURAS de las animaciones: tiempo en milisegundos -> valor. No dibujan, no guardan nada y no
leen ningún reloj: quien las llama pasa el instante. Las tablas y duraciones están en View/Componentes.py.

    fotograma(n, ms, fps)          qué fotograma de un bucle de n se ve en el instante ms
    bamboleo(ms, indice)           píxeles de subida del actor de un solo fotograma (con fase distinta por posición en la lista)
    alfa_aura(ms, indice, resaltado)   alfa del aura de un objeto del suelo (respira; brilla más con el ratón encima)
    alfa_parpadeo(ms)              alfa de la capa oscura que hace vacilar la luz del fondo de la sala
    progreso(inicio, ahora, duracion)  0.0 antes de empezar, 1.0 al terminar (o con duración 0)
    alfa_de_fundido(p)             255 al empezar (opaco) y 0 al terminar
    fotograma_unico(n, transcurrido, duracion)   fotograma de una animación que se reproduce una vez y se queda en el último
"""
import math

from View import Componentes as c


def fotograma(n: int, ms: int, fps: int) -> int:
    """El fotograma (0 a n-1) de un bucle de 'n' fotogramas a 'fps' fotogramas por segundo en el instante 'ms'."""
    if n <= 1 or fps <= 0:
        return 0
    return (ms * fps // 1000) % n


def _de_la_tabla(tabla: list, ms: int, periodo_ms: int, desfase: int = 0):
    """El valor de 'tabla' (un periodo de 'periodo_ms' repartido en partes iguales) en el instante 'ms', corrido 'desfase' pasos."""
    if not tabla:
        return 0
    if periodo_ms <= 0:
        return tabla[desfase % len(tabla)]
    return tabla[(ms * len(tabla) // periodo_ms + desfase) % len(tabla)]


def bamboleo(ms: int, indice: int) -> int:
    """Píxeles que sube el sprite en el instante 'ms'; 'indice' (la posición del actor en su lista) desfasa a unos de otros."""
    return _de_la_tabla(c.BAMBOLEO, ms, c.BAMBOLEO_PERIODO_MS, max(0, indice) * c.BAMBOLEO_FASE)


def alfa_aura(ms: int, indice: int, resaltado: bool) -> int:
    """El alfa (0-255) del aura del objeto número 'indice'; con 'resaltado' (el ratón encima) usa la tabla más clara."""
    desfase = max(0, indice) * c.AURA_FASE
    if resaltado:
        return _de_la_tabla(c.AURA_BRILLA, ms, c.AURA_BRILLA_PERIODO_MS, desfase)
    return _de_la_tabla(c.AURA_RESPIRA, ms, c.AURA_RESPIRA_PERIODO_MS, desfase)


def alfa_parpadeo(ms: int) -> int:
    return _de_la_tabla(c.PARPADEO, ms, c.PARPADEO_PERIODO_MS)


def progreso(inicio: int, ahora: int, duracion: int) -> float:
    """Qué parte de una animación que empezó en 'inicio' y dura 'duracion' ms ha pasado en 'ahora' (de 0.0 a 1.0)."""
    if duracion <= 0:
        return 1.0
    return min(1.0, max(0.0, (ahora - inicio) / duracion))


def alfa_de_fundido(p: float) -> int:
    """El alfa de un velo que se va aclarando: 255 (opaco) con p = 0 y 0 (transparente) con p = 1."""
    return round(255 * (1.0 - min(1.0, max(0.0, p))))


def fotograma_unico(n: int, transcurrido: int, duracion: int) -> int:
    """El fotograma (0 a n-1) de una animación de 'n' fotogramas que dura 'duracion' ms y se queda en el último."""
    if n <= 1:
        return 0
    if duracion <= 0 or transcurrido >= duracion:
        return n - 1
    return max(0, transcurrido) * n // duracion


# ---------------------------------------------------------------------------- feedback de combate (p: 0.0 al empezar, 1.0 al terminar)
def _limitar(p: float) -> float:
    return min(1.0, max(0.0, p))


def sube_numero(p: float) -> int:
    """Píxeles que ha subido un número flotante: rápido al principio y cada vez más despacio."""
    p = _limitar(p)
    return round(c.NUMERO_SUBE * (1.0 - (1.0 - p) * (1.0 - p)))


def alfa_numero(p: float) -> int:
    """Opaco durante NUMERO_FIJO del tiempo y luego se desvanece hasta 0."""
    p = _limitar(p)
    if p <= c.NUMERO_FIJO:
        return 255
    return round(255 * (1.0 - (p - c.NUMERO_FIJO) / (1.0 - c.NUMERO_FIJO)))


def alfa_destello(p: float) -> int:
    return round(c.DESTELLO_ALFA * (1.0 - _limitar(p)))


def alfa_borde(p: float) -> int:
    return round(c.BORDE_ALFA * (1.0 - _limitar(p)))


def alfa_velo_golpe(p: float) -> int:
    """El velo rojo del golpe: parpadea VELO_GOLPE_PARPADEOS veces mientras se va apagando."""
    p = _limitar(p)
    pulso = 0.5 + 0.5 * math.cos(2 * math.pi * c.VELO_GOLPE_PARPADEOS * p)
    return round(c.VELO_GOLPE_ALFA * (1.0 - p) * pulso)


def alfa_vineta(fraccion_vida: float, ms: int) -> int:
    """La viñeta de vida baja: 0 con la vida por encima de VINETA_UMBRAL; crece hasta VINETA_ALFA con la vida en 0 y late."""
    if fraccion_vida >= c.VINETA_UMBRAL:
        return 0
    gravedad = 1.0 - _limitar(fraccion_vida / c.VINETA_UMBRAL)
    latido = 0.8 + 0.2 * math.sin(2 * math.pi * ms / c.VINETA_PERIODO_MS)
    return round(c.VINETA_ALFA * gravedad * latido)


def escala_muerte(p: float) -> float:
    """El tamaño del enemigo que muere sin fotogramas propios: de 1.0 a MUERTE_ENCOGE."""
    return 1.0 - (1.0 - c.MUERTE_ENCOGE) * _limitar(p)


def alfa_muerte(p: float) -> int:
    """Opaco la primera mitad y luego se desvanece."""
    p = _limitar(p)
    return 255 if p <= 0.5 else round(255 * (1.0 - (p - 0.5) / 0.5))


def alfa_desvanece(p: float) -> int:
    return round(255 * (1.0 - _limitar(p)))


def sube_recogido(p: float) -> int:
    return round(c.RECOGIDO_SUBE * _limitar(p))


def alfa_calido(p: float) -> int:
    return round(c.PUERTA_CALIDO_ALFA * (1.0 - _limitar(p)))
