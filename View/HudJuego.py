"""
HudJuego (Vista): lo que rodea a la escena durante la partida (Etapa 7). Se dibuja DESPUÉS de la escena y de los velos de los
efectos, y ANTES del nombre del objeto bajo el ratón, que VistaPygame pide al final para que quede encima de todo.

Funciones puras (se prueban sin ventana):
    efectos_a_mostrar(efectos)          la línea de texto y el color del velo de cada efecto
    lineas_de_mensajes(mensajes)        las líneas que muestra el panel (las últimas 20, la más reciente al final)
    indices_equipados(inventario)       qué casillas llevan la marca de equipado (solo la primera con cada id)
    datos_del_objeto(objeto)            las líneas de detalle de un objeto
    casillas_del_inventario(cantidad)   el rectángulo de cada casilla de la ventana
    ventana_del_inventario(...)         desde qué casilla real se muestra la ventana de 15 que sigue al cursor
    criterio_a_texto(criterio)          "Orden: real / peso / valor / nombre"

Zonas de clic que registra: ELEMENTO_INVENTARIO (solo casillas ocupadas, índice en inventario.objetos) y ELEMENTO_BOTON 0
(Esperar). Todas las medidas están en View/Componentes.py (sección HUD).
"""
from dataclasses import dataclass

import pygame

from DTO.ElementoDTO import ELEMENTO_BOTON, ELEMENTO_INVENTARIO, ElementoDTO
from DTO.PantallaDTO import PantallaDTO
from View import Componentes as c

TEXTURA_CASILLA = "inventario"           # ui/inventario.png: la textura de las casillas
SIN_CRITERIO = "real"


# ============================================================================ funciones puras
@dataclass(frozen=True)
class EfectoVisible:
    texto: str                           # la línea: nombre del efecto y tiempo restante
    velo: tuple | None                   # RGBA del velo, o None (tipo desconocido, o velocidad sin valor)


def efectos_a_mostrar(efectos: list) -> list[EfectoVisible]:
    """Una línea y un velo por cada efecto, en el mismo orden. veneno: verde; velocidad > 0: azul; velocidad < 0: violeta;
    antorcha: naranja; cualquier otro tipo (o velocidad sin valor o 0): solo el texto."""
    visibles = []
    for efecto in efectos:
        if efecto.tipo == "veneno":
            nombre = "Veneno" if efecto.valor is None else f"Veneno (-{efecto.valor})"
            velo = c.VELO_VENENO
        elif efecto.tipo == "velocidad":
            valor = efecto.valor or 0
            nombre = "Velocidad" if efecto.valor is None else f"Velocidad {valor:+d}"
            velo = c.VELO_RAPIDO if valor > 0 else c.VELO_LENTO if valor < 0 else None
        elif efecto.tipo == "antorcha":
            nombre, velo = "Antorcha", c.VELO_ANTORCHA
        else:
            nombre, velo = str(efecto.tipo).capitalize(), None
        visibles.append(EfectoVisible(f"{nombre}: {efecto.restante}", velo))
    return visibles


def lineas_de_mensajes(mensajes: list[str], maximo: int = c.HUD_MENSAJES_LINEAS) -> list[str]:
    """Las últimas 'maximo' líneas, en orden cronológico (la más reciente es la última, abajo del panel)."""
    return list(mensajes[-maximo:]) if maximo > 0 else []


def indices_equipados(inventario) -> list[int]:
    """Las casillas con la marca de equipado. arma_equipada y armadura_equipada son ids, no instancias: con ids repetidos
    solo se marca el PRIMER objeto con ese id (limitación conocida del DTO)."""
    marcados = []
    for id_equipado in (inventario.arma_equipada, inventario.armadura_equipada):
        if id_equipado is None:
            continue
        for i, objeto in enumerate(inventario.objetos):
            if objeto.id == id_equipado:
                if i not in marcados:
                    marcados.append(i)
                break
    return marcados


def criterio_a_texto(criterio: str | None) -> str:
    return f"Orden: {SIN_CRITERIO if criterio is None else criterio}"


def datos_del_objeto(objeto) -> list[str]:
    """Nombre, clase, peso, valor y cada bonus que no sea None, una línea por dato."""
    lineas = [objeto.nombre, f"Clase: {objeto.clase}", f"Peso: {objeto.peso}   Valor: {objeto.valor}"]
    for etiqueta, valor, signo in (("Ataque", objeto.ataque_bonus, True), ("Defensa", objeto.defensa_bonus, True),
                                   ("Cura", objeto.cura, False), ("Velocidad", objeto.modificador_velocidad, True),
                                   ("Duración", objeto.duracion, False), ("Abre", objeto.abre, False)):
        if valor is not None:
            lineas.append(f"{etiqueta}: {valor:+d}" if signo and isinstance(valor, int) else f"{etiqueta}: {valor}")
    return lineas


def ventana_del_inventario(inicio: int, cursor: int, capacidad_maxima: int, tamano: int = c.INV_CASILLAS_MAX) -> int:
    """La primera casilla real que muestra la ventana de 'tamano' casillas. Parte de 'inicio' (la del cuadro anterior) y solo se
    desplaza lo justo para que el cursor quede dentro, así un clic sobre una casilla visible no mueve la ventana. Con
    capacidad_maxima <= tamano es siempre 0. El índice real de la casilla k de la ventana es inicio + k."""
    ultimo_inicio = max(0, capacidad_maxima - tamano)
    cursor = min(max(cursor, 0), max(capacidad_maxima - 1, 0))
    if cursor < inicio:
        inicio = cursor
    elif cursor >= inicio + tamano:
        inicio = cursor - tamano + 1
    return min(max(inicio, 0), ultimo_inicio)


def casillas_del_inventario(cantidad: int) -> list[pygame.Rect]:
    """El rectángulo de cada una de las 'cantidad' casillas de la ventana (como mucho INV_CASILLAS_MAX), en filas de
    INV_COLUMNAS."""
    panel = c.HUD_INVENTARIO
    rectangulos = []
    for i in range(min(max(0, cantidad), c.INV_CASILLAS_MAX)):
        fila, columna = divmod(i, c.INV_COLUMNAS)
        rectangulos.append(pygame.Rect(panel.x + c.HUD_RELLENO + 1 + columna * (c.INV_LADO + c.INV_HUECO),
                                       panel.y + c.INV_ARRIBA + fila * (c.INV_LADO + c.INV_HUECO),
                                       c.INV_LADO, c.INV_LADO))
    return rectangulos


# ============================================================================ dibujo
class HudJuego:

    def __init__(self, almacen, fuentes: c.Fuentes, zonas):
        self._almacen = almacen
        self._fuentes = fuentes
        self._zonas = zonas
        self._colores_de_velo: list[tuple] = []      # un velo por color, creado la primera vez que hace falta
        self._velos: list[pygame.Surface] = []
        self._inicio = 0                             # la primera casilla real de la ventana del inventario

    def dibujar(self, superficie: pygame.Surface, pantalla: PantallaDTO) -> None:
        estado = pantalla.estado
        efectos = efectos_a_mostrar(estado.efectos)
        for efecto in efectos:
            if efecto.velo is not None:
                superficie.blit(self._velo(efecto.velo), (0, 0))          # debajo del HUD, encima de la escena
        self._estadisticas(superficie, estado)
        self._efectos(superficie, efectos)
        self._mensajes(superficie, estado.mensajes)
        self._inventario(superficie, estado.inventario)
        self._esperar(superficie, pantalla)
        self._aviso(superficie, pantalla.aviso)
        self._ayuda(superficie, pantalla.ayuda)

    def _velo(self, color: tuple) -> pygame.Surface:
        for i in range(len(self._colores_de_velo)):
            if self._colores_de_velo[i] == color:
                return self._velos[i]
        velo = pygame.Surface((c.ANCHO, c.ALTO), pygame.SRCALPHA)
        velo.fill(color)
        self._colores_de_velo.append(color)
        self._velos.append(velo)
        return velo

    # ------------------------------------------------------------------ paneles de la izquierda
    def _estadisticas(self, superficie, estado) -> None:
        marco = c.HUD_ESTADISTICAS
        c.panel(superficie, marco)
        jugador = estado.jugador
        c.barra_de_vida(superficie, self._fuentes, pygame.Rect(marco.x + c.HUD_RELLENO, marco.y + c.HUD_RELLENO,
                                                               marco.width - 2 * c.HUD_RELLENO, 22),
                        jugador.vida, jugador.vida_max)
        fuente = self._fuentes.pie
        izquierda, derecha = marco.x + c.HUD_RELLENO + 2, marco.x + c.HUD_STATS_COLUMNA
        filas = c.HUD_STATS_FILAS
        c.texto_en(superficie, fuente, f"Ataque: {jugador.ataque}", c.TEXTO, (izquierda, marco.y + filas[0]), "topleft")
        c.texto_en(superficie, fuente, f"Defensa: {jugador.defensa}", c.TEXTO, (derecha, marco.y + filas[0]), "topleft")
        c.texto_en(superficie, fuente, f"Velocidad: {jugador.velocidad}", c.TEXTO, (izquierda, marco.y + filas[1]),
                   "topleft")
        c.texto_en(superficie, fuente, f"Reloj: {estado.reloj}", c.ORO, (izquierda, marco.y + filas[2]), "topleft")

    def _efectos(self, superficie, efectos: list[EfectoVisible]) -> None:
        marco = c.HUD_EFECTOS
        c.panel(superficie, marco)
        c.texto_en(superficie, self._fuentes.chico, "Efectos", c.TEXTO_SUAVE, (marco.x + c.HUD_RELLENO + 2, marco.y + 8),
                   "topleft")
        if not efectos:
            c.texto_en(superficie, self._fuentes.pie, "Ninguno", c.TEXTO_SUAVE,
                       (marco.x + c.HUD_RELLENO + 2, marco.y + c.HUD_EFECTOS_ARRIBA), "topleft")
            return
        cabe = (marco.height - c.HUD_EFECTOS_ARRIBA - c.HUD_RELLENO) // c.HUD_EFECTOS_INTERLINEA
        ancho = marco.width - 2 * c.HUD_RELLENO - 4
        for i in range(min(len(efectos), cabe)):
            texto = efectos[i].texto
            if i == cabe - 1 and len(efectos) > cabe:
                texto = f"{texto}  (+{len(efectos) - cabe} más)"
            c.texto_en(superficie, self._fuentes.pie, c.recortar_a_ancho(self._fuentes.pie, texto, ancho), c.TEXTO,
                       (marco.x + c.HUD_RELLENO + 2, marco.y + c.HUD_EFECTOS_ARRIBA + i * c.HUD_EFECTOS_INTERLINEA),
                       "topleft")

    def _mensajes(self, superficie, mensajes: list[str]) -> None:
        marco = c.HUD_MENSAJES
        c.panel(superficie, marco)
        c.texto_en(superficie, self._fuentes.chico, "Mensajes", c.TEXTO_SUAVE, (marco.x + c.HUD_RELLENO + 2, marco.y + 4),
                   "topleft")
        lineas = lineas_de_mensajes(mensajes)
        ancho = marco.width - 2 * c.HUD_RELLENO
        for i, linea in enumerate(lineas):
            color = c.TEXTO if i == len(lineas) - 1 else c.TEXTO_SUAVE
            c.texto_en(superficie, self._fuentes.mensajes, c.recortar_a_ancho(self._fuentes.mensajes, linea, ancho), color,
                       (marco.x + c.HUD_RELLENO, marco.y + c.HUD_MENSAJES_ARRIBA + i * c.HUD_MENSAJES_INTERLINEA),
                       "topleft")

    # ------------------------------------------------------------------ inventario
    def _inventario(self, superficie, inventario) -> None:
        marco = c.HUD_INVENTARIO
        c.panel(superficie, marco)
        c.texto_en(superficie, self._fuentes.chico, criterio_a_texto(inventario.criterio), c.TEXTO_SUAVE,
                   (marco.x + c.HUD_RELLENO + 2, marco.y + 9), "topleft")
        c.texto_en(superficie, self._fuentes.pie, f"{inventario.capacidad}/{inventario.capacidad_maxima}", c.ORO,
                   (marco.right - c.HUD_RELLENO - 2, marco.y + 7), "topright")
        casillas = casillas_del_inventario(inventario.capacidad_maxima)
        self._inicio = ventana_del_inventario(self._inicio, inventario.cursor, inventario.capacidad_maxima)
        inicio = self._inicio
        marcados = indices_equipados(inventario)
        textura = self._almacen.ui(TEXTURA_CASILLA, c.INV_LADO / 64).fotogramas[0]
        for k, casilla in enumerate(casillas):
            i = inicio + k                           # el índice REAL: el de inventario.objetos
            ocupada = i < len(inventario.objetos)
            superficie.blit(textura, casilla)
            sombra = pygame.Surface(casilla.size, pygame.SRCALPHA)
            sombra.fill((0, 0, 0, 110 if ocupada else 190))
            superficie.blit(sombra, casilla)
            if i == inventario.cursor:
                pygame.draw.rect(superficie, c.ORO, casilla, 3, border_radius=3)
            else:
                pygame.draw.rect(superficie, c.PANEL_BORDE if ocupada else c.ORO_OSCURO, casilla, 1, border_radius=3)
            if not ocupada:
                continue
            objeto = inventario.objetos[i]
            sprite = self._almacen.objeto(objeto.id, objeto.clase, c.INV_SPRITE).fotogramas[0]
            superficie.blit(sprite, sprite.get_rect(center=casilla.center))
            if i in marcados:
                insignia = pygame.Rect(casilla.right - 16, casilla.top + 2, 14, 14)
                pygame.draw.rect(superficie, c.ORO, insignia, border_radius=3)
                c.texto_en(superficie, self._fuentes.chico, "E", c.NEGRO_TINTA, insignia.center)
            self._zonas.agregar(casilla, ElementoDTO(ELEMENTO_INVENTARIO, i))
        self._detalle(superficie, inventario, casillas)

    def _detalle(self, superficie, inventario, casillas) -> None:
        marco = c.HUD_INVENTARIO
        if not 0 <= inventario.cursor < len(inventario.objetos):
            return
        y = (casillas[-1].bottom if casillas else marco.y + c.INV_ARRIBA) + c.HUD_RELLENO + 4
        ancho = marco.width - 2 * c.HUD_RELLENO - 4
        lineas = datos_del_objeto(inventario.objetos[inventario.cursor])
        for i, linea in enumerate(lineas):
            fuente = self._fuentes.pie if i == 0 else self._fuentes.chico
            alto = fuente.get_linesize() + 2
            if y + alto > marco.bottom - c.HUD_RELLENO:
                break
            c.texto_en(superficie, fuente, c.recortar_a_ancho(fuente, linea, ancho), c.ORO if i == 0 else c.TEXTO,
                       (marco.x + c.HUD_RELLENO + 2, y), "topleft")
            y += alto

    # ------------------------------------------------------------------ botón, aviso y ayuda
    def _esperar(self, superficie, pantalla) -> None:
        if not pantalla.opciones:
            return
        c.dibujar_boton(superficie, self._fuentes, c.HUD_ESPERAR, pantalla.opciones[0], pantalla.seleccion == 0)
        self._zonas.agregar(c.HUD_ESPERAR, ElementoDTO(ELEMENTO_BOTON, 0))

    def _aviso(self, superficie, aviso: str | None) -> None:
        if not aviso:
            return
        marco = c.HUD_AVISO
        c.panel(superficie, marco, c.AVISO_FONDO, c.ROJO_VIVO, 2)
        fuente = self._fuentes.mensajes
        lineas = c.ajustar_lineas(fuente, aviso, marco.width - 2 * c.HUD_RELLENO)
        if len(lineas) > c.HUD_AVISO_LINEAS:
            lineas = lineas[:c.HUD_AVISO_LINEAS]
            lineas[-1] = c.recortar_a_ancho(fuente, lineas[-1] + " ...", marco.width - 2 * c.HUD_RELLENO)
        alto = len(lineas) * c.HUD_MENSAJES_INTERLINEA
        for i, linea in enumerate(lineas):
            c.texto_en(superficie, fuente, c.recortar_a_ancho(fuente, linea, marco.width - 2 * c.HUD_RELLENO), c.AVISO,
                       (marco.centerx, marco.centery - alto // 2 + i * c.HUD_MENSAJES_INTERLINEA), "midtop")

    def _ayuda(self, superficie, ayuda: list[str]) -> None:
        marco = c.HUD_AYUDA
        c.panel(superficie, marco)
        fuente = self._fuentes.ayuda_juego
        for i, linea in enumerate(ayuda):
            y = marco.y + c.HUD_RELLENO + i * c.HUD_AYUDA_INTERLINEA
            if y + c.HUD_AYUDA_INTERLINEA > marco.bottom:
                break
            c.texto_en(superficie, fuente, c.recortar_a_ancho(fuente, linea, marco.width - 2 * c.HUD_RELLENO),
                       c.TEXTO_SUAVE, (marco.x + c.HUD_RELLENO, y), "topleft")
