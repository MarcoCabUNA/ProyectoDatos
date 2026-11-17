"""
MapaJuego (Vista, feature 002, FR-219): el panel del comando `mapa`. Solo recibe el MapaConocidoDTO y dibuja; no calcula nada
del juego. La única cuenta es la de la disposición en la pantalla: cada sala se pone junto a la que la nombra, hacia donde
apunta su salida (N arriba, S abajo, E a la derecha, O a la izquierda), a partir de la sala actual.

Funciones puras (se prueban sin ventana):
    disposicion(mapa, sala_actual)      las celdas (exploradas y «sin explorar») y las conexiones, en cuadrícula
    ventana(disposicion, cols, filas, sala_actual)   la parte de la cuadrícula que se dibuja cuando no cabe entera

Una salida con destino None es una sala avistada: se dibuja como una celda hueca «sin explorar», sin id y sin nombre (dos
salidas hacia la misma avistada son dos celdas, FR-204). El color de cada conexión es el estado RECORDADO de la puerta.
"""
from dataclasses import dataclass

import pygame

from DTO.MapaConocidoDTO import ABIERTA, CERRADA
from View import Componentes as c

CELDA_MAXIMA = 56
CELDA_MINIMA = 16
CELDA_CON_NOMBRE = 44                      # desde este lado se escriben los nombres y los costos
MOVIMIENTOS = ((0, -1), (0, 1), (1, 0), (-1, 0))     # N, S, E, O

EXPLORADA = "explorada"
ACTUAL = "actual"
SIN_EXPLORAR = "sin_explorar"

COLOR_ABIERTA = (84, 168, 72)
COLOR_CERRADA = (200, 52, 48)
COLOR_SIN_OBSERVAR = (140, 134, 128)
COLOR_EXPLORADA = (74, 60, 78)
COLOR_VACIA = (170, 160, 150)


@dataclass(frozen=True)
class Celda:
    x: int
    y: int
    tipo: str
    sala: int | None            # id de la sala explorada; None en «sin explorar»
    nombre: str


@dataclass(frozen=True)
class Conexion:
    x1: int
    y1: int
    x2: int
    y2: int
    estado_puerta: int
    costo: int


@dataclass(frozen=True)
class Disposicion:
    celdas: list[Celda]
    conexiones: list[Conexion]
    desplazadas: int            # salas que no cupieron junto a su vecina y se pusieron más lejos en la misma dirección


def disposicion(mapa, sala_actual: int) -> Disposicion:
    salas = mapa.salas
    if not salas:
        return Disposicion([], [], 0)
    ultimo = salas[len(salas) - 1].id
    por_id: list[int] = [-1] * (ultimo + 1)
    for i in range(len(salas)):
        por_id[salas[i].id] = i
    centro = 2 * len(salas) + 4
    lado = 2 * centro + 1
    ocupada = [[False] * lado for _ in range(lado)]
    posicion: list[tuple[int, int] | None] = [None] * len(salas)
    celdas: list[Celda] = []
    conexiones: list[Conexion] = []
    desplazadas = 0
    inicio = por_id[sala_actual] if 0 <= sala_actual <= ultimo and por_id[sala_actual] >= 0 else 0
    semillas = [inicio] + [i for i in range(len(salas)) if i != inicio]
    derecha = centro
    for semilla in semillas:
        if posicion[semilla] is not None:
            continue
        x0 = centro if semilla == inicio else derecha + 2
        posicion[semilla] = (x0, centro)
        ocupada[centro][x0] = True
        cola = [semilla]
        cabeza = 0
        while cabeza < len(cola):
            u = cola[cabeza]
            cabeza += 1
            ux, uy = posicion[u]
            derecha = max(derecha, ux)
            for d in range(4):
                salida = salas[u].salidas[d]
                if salida is None:
                    continue
                dx, dy = MOVIMIENTOS[d]
                if salida.destino is None:
                    sx, sy = ux + dx, uy + dy
                    if not ocupada[sy][sx]:
                        ocupada[sy][sx] = True
                        celdas.append(Celda(sx, sy, SIN_EXPLORAR, None, ""))
                    conexiones.append(Conexion(ux, uy, sx, sy, salida.estado_puerta, salida.costo))
                    continue
                v = por_id[salida.destino] if 0 <= salida.destino <= ultimo else -1
                if v < 0:
                    continue
                if posicion[v] is None:
                    vx, vy = ux + dx, uy + dy
                    while ocupada[vy][vx] and not _hueca(celdas, vx, vy) and 0 < vx < lado - 1 and 0 < vy < lado - 1:
                        vx, vy = vx + dx, vy + dy
                        desplazadas += 1
                    if _hueca(celdas, vx, vy):
                        celdas = _sin_celda(celdas, vx, vy)
                    posicion[v] = (vx, vy)
                    ocupada[vy][vx] = True
                    cola.append(v)
                vx, vy = posicion[v]
                conexiones.append(Conexion(ux, uy, vx, vy, salida.estado_puerta, salida.costo))
    for i in range(len(salas)):
        x, y = posicion[i]
        tipo = ACTUAL if salas[i].id == sala_actual else EXPLORADA
        celdas.append(Celda(x, y, tipo, salas[i].id, salas[i].nombre))
    return Disposicion(celdas, conexiones, desplazadas)


def _hueca(celdas, x: int, y: int) -> bool:
    for celda in celdas:
        if celda.x == x and celda.y == y:
            return celda.tipo == SIN_EXPLORAR
    return False


def _sin_celda(celdas, x: int, y: int):
    resto = []
    for celda in celdas:
        if not (celda.x == x and celda.y == y and celda.tipo == SIN_EXPLORAR):
            resto.append(celda)
    return resto


def limites(disp: Disposicion) -> tuple[int, int, int, int]:
    xs = [celda.x for celda in disp.celdas]
    ys = [celda.y for celda in disp.celdas]
    return min(xs), min(ys), max(xs), max(ys)


def ventana(disp: Disposicion, columnas: int, filas: int, sala_actual: int) -> tuple[int, int]:
    minx, miny, maxx, maxy = limites(disp)
    ancho, alto = maxx - minx + 1, maxy - miny + 1
    if ancho <= columnas and alto <= filas:
        return minx, miny
    actual = (minx, miny)
    for celda in disp.celdas:
        if celda.tipo == ACTUAL:
            actual = (celda.x, celda.y)
    x0 = min(max(actual[0] - columnas // 2, minx), max(minx, maxx - columnas + 1))
    y0 = min(max(actual[1] - filas // 2, miny), max(miny, maxy - filas + 1))
    return x0, y0


def lado_de_celda(disp: Disposicion, ancho: int, alto: int) -> int:
    minx, miny, maxx, maxy = limites(disp)
    columnas, filas = maxx - minx + 1, maxy - miny + 1
    return max(CELDA_MINIMA, min(CELDA_MAXIMA, ancho // columnas, alto // filas))


def color_de_puerta(estado_puerta: int) -> tuple:
    if estado_puerta == ABIERTA:
        return COLOR_ABIERTA
    if estado_puerta == CERRADA:
        return COLOR_CERRADA
    return COLOR_SIN_OBSERVAR


class PanelMapa:

    def __init__(self, fuentes: c.Fuentes) -> None:
        self._fuentes = fuentes
        self._mapa = None                    # el DTO con que se calculó la disposición (se compara por identidad)
        self._sala = None
        self._disp: Disposicion | None = None

    def dibujar(self, superficie: pygame.Surface, mapa, sala_actual: int, marco=None, cierre=None) -> None:
        marco = c.HUD_MAPA if marco is None else marco       # marco y cierre: el panel de historia usa el mismo dibujo (FR-223)
        c.panel(superficie, marco, c.PANEL, c.ORO, 2)
        fuente = self._fuentes.chico
        c.texto_en(superficie, fuente, f"Mapa conocido: {len(mapa.salas)} salas exploradas", c.ORO,
                   (marco.x + c.HUD_RELLENO + 2, marco.y + 6), "topleft")
        c.texto_en(superficie, fuente, "Esc o `mapa`: cerrar" if cierre is None else cierre, c.TEXTO_SUAVE,
                   (marco.right - c.HUD_RELLENO - 2, marco.y + 6), "topright")
        if self._mapa is not mapa or self._sala != sala_actual:
            self._mapa, self._sala = mapa, sala_actual
            self._disp = disposicion(mapa, sala_actual)
        disp = self._disp
        area = pygame.Rect(marco.x + c.HUD_RELLENO, marco.y + 28, marco.width - 2 * c.HUD_RELLENO,
                           marco.height - 28 - 44)
        if not disp.celdas:
            return
        lado = lado_de_celda(disp, area.width, area.height)
        columnas, filas = area.width // lado, area.height // lado
        x0, y0 = ventana(disp, columnas, filas, sala_actual)
        minx, miny, maxx, maxy = limites(disp)
        recortado = (maxx - minx + 1) > columnas or (maxy - miny + 1) > filas
        sobrante_x = (area.width - min(columnas, maxx - minx + 1) * lado) // 2
        sobrante_y = (area.height - min(filas, maxy - miny + 1) * lado) // 2

        def centro(x: int, y: int) -> tuple[int, int]:
            return (area.x + sobrante_x + (x - x0) * lado + lado // 2, area.y + sobrante_y + (y - y0) * lado + lado // 2)

        def visible(x: int, y: int) -> bool:
            return 0 <= x - x0 < columnas and 0 <= y - y0 < filas

        for conexion in disp.conexiones:
            if visible(conexion.x1, conexion.y1) and visible(conexion.x2, conexion.y2):
                pygame.draw.line(superficie, color_de_puerta(conexion.estado_puerta), centro(conexion.x1, conexion.y1),
                                 centro(conexion.x2, conexion.y2), 3)
        mitad = max(4, lado * 3 // 10)
        nombre_actual = ""
        for celda in disp.celdas:
            if not visible(celda.x, celda.y):
                continue
            cx, cy = centro(celda.x, celda.y)
            caja = pygame.Rect(cx - mitad, cy - mitad, 2 * mitad, 2 * mitad)
            if celda.tipo == SIN_EXPLORAR:
                pygame.draw.rect(superficie, COLOR_VACIA, caja, 1)
                continue
            pygame.draw.rect(superficie, c.ORO if celda.tipo == ACTUAL else COLOR_EXPLORADA, caja)
            pygame.draw.rect(superficie, c.ORO if celda.tipo == ACTUAL else c.TEXTO_SUAVE, caja, 1)
            if celda.tipo == ACTUAL:
                nombre_actual = celda.nombre
            if lado >= CELDA_CON_NOMBRE:
                c.texto_en(superficie, fuente, c.recortar_a_ancho(fuente, celda.nombre, lado), c.TEXTO,
                           (cx, caja.bottom + 1), "midtop")
        if lado >= CELDA_CON_NOMBRE:
            for conexion in disp.conexiones:
                if visible(conexion.x1, conexion.y1) and visible(conexion.x2, conexion.y2):
                    ax, ay = centro(conexion.x1, conexion.y1)
                    bx, by = centro(conexion.x2, conexion.y2)
                    c.texto_en(superficie, fuente, str(conexion.costo), c.TEXTO_SUAVE, ((ax + bx) // 2, (ay + by) // 2))
        self._pie(superficie, marco, fuente, nombre_actual, recortado, len(mapa.salas))

    def _pie(self, superficie, marco, fuente, nombre_actual: str, recortado: bool, total: int) -> None:
        y = marco.bottom - 40
        ancho = marco.width - 2 * c.HUD_RELLENO
        izquierda = marco.x + c.HUD_RELLENO + 2
        c.texto_en(superficie, fuente, c.recortar_a_ancho(fuente, f"Estás en: {nombre_actual}", ancho), c.ORO,
                   (izquierda, y), "topleft")
        x = izquierda
        for color, texto in ((COLOR_ABIERTA, "puerta abierta"), (COLOR_CERRADA, "cerrada"),
                             (COLOR_SIN_OBSERVAR, "sin observar"), (COLOR_VACIA, "hueco: sala sin explorar")):
            pygame.draw.line(superficie, color, (x, y + 24), (x + 16, y + 24), 3)
            x += 22
            x = c.texto_en(superficie, fuente, texto, c.TEXTO_SUAVE, (x, y + 24), "midleft").right + 14
        if recortado:
            c.texto_en(superficie, fuente, "Recortado: se muestra el entorno de la sala actual", c.AVISO,
                       (marco.right - c.HUD_RELLENO - 2, y), "topright")
