"""
Componentes (Vista): el estilo del juego y los elementos reutilizables (botón, panel translúcido, texto).

TODA la paleta, los tamaños de fuente y las medidas fijas de la interfaz están en la sección ESTILO de este archivo:
es el único lugar donde se ajusta el aspecto. Paleta: oscura, con acentos rojos y dorados, como el arte del juego.

Las funciones dibujan sobre la superficie que reciben; no guardan estado ni llaman al Controlador.
"""
import pygame

# ============================================================================ ESTILO
ANCHO, ALTO = 1376, 768                      # resolución lógica (el tamaño nativo de los fondos)

# Colores (RGB; con una cuarta cifra, RGBA: translúcidos)
NEGRO_TINTA = (14, 10, 14)
VELO_SUAVE = (0, 0, 0, 232)                  # sobre fondo_menu en las pantallas que dibujan su propio título
VELO_FUERTE = (0, 0, 0, 215)                 # sobre la partida (o su sustituto) en la pausa
PANEL = (16, 11, 16, 205)                    # fondo de paneles y botones
PANEL_BORDE = (120, 28, 32)                  # rojo oscuro
ROJO = (190, 36, 42)
ROJO_VIVO = (226, 60, 56)
ORO = (232, 184, 84)
ORO_OSCURO = (150, 112, 48)
TEXTO = (236, 230, 218)
TEXTO_SUAVE = (170, 160, 150)
AVISO = (255, 128, 108)
AVISO_FONDO = (70, 14, 16, 230)

# Tamaños de fuente (pygame.font.Font(None, tamaño))
TAM_TITULO = 60
TAM_BOTON = 30
TAM_TEXTO = 28
TAM_PIE = 22

# Medidas de las pantallas con botones
BOTON_ALTO = 44
BOTON_ALTO_MENU = 36                         # el menú comparte espacio con el título del fondo
BOTON_ALTO_MINIMO = 30                       # por debajo de esto se pasa a otra columna
BOTON_SEPARACION = 8
BOTON_ANCHO = 420
RADIO = 8
TITULO_Y = 52
AVISO_MAX_LINEAS = 2                         # un aviso más largo se corta con "..." (no debe tapar los botones)
AVISO_INTERLINEA = 28
AVISO_ARRIBA_Y = 44                          # con el aviso arriba (victoria y derrota): su borde superior
AVISO_SEPARACION = 8                         # espacio entre el aviso y la primera línea de ayuda
PIE_BASE_Y = 760                             # las líneas de ayuda se apilan hacia arriba desde aquí
PIE_INTERLINEA = 20


class Fuentes:
    """Las fuentes del juego. Se crean al abrir la ventana (después de pygame.font.init())."""

    def __init__(self):
        self.titulo = pygame.font.Font(None, TAM_TITULO)
        self.boton = pygame.font.Font(None, TAM_BOTON)
        self.texto = pygame.font.Font(None, TAM_TEXTO)
        self.pie = pygame.font.Font(None, TAM_PIE)


# ============================================================================ texto
def texto_en(superficie, fuente, texto: str, color, posicion, ancla: str = "center") -> pygame.Rect:
    """Dibuja 'texto' con su 'ancla' (center, midtop, topleft, midbottom, ...) en 'posicion'. Devuelve su rectángulo."""
    imagen = fuente.render(texto, True, color)
    rectangulo = imagen.get_rect(**{ancla: posicion})
    superficie.blit(imagen, rectangulo)
    return rectangulo


def recortar_a_ancho(fuente, texto: str, ancho: int) -> str:
    """'texto' tal cual si cabe en 'ancho' píxeles; si no, lo corta y le pone '...'."""
    if fuente.size(texto)[0] <= ancho:
        return texto
    while texto and fuente.size(texto + "...")[0] > ancho:
        texto = texto[:-1]
    return texto + "..."


def ajustar_lineas(fuente, texto: str, ancho: int) -> list[str]:
    """Parte 'texto' en líneas que caben en 'ancho' píxeles, cortando entre palabras."""
    lineas: list[str] = []
    actual = ""
    for palabra in texto.split():
        prueba = palabra if not actual else f"{actual} {palabra}"
        if actual and fuente.size(prueba)[0] > ancho:
            lineas.append(actual)
            actual = palabra
        else:
            actual = prueba
    if actual:
        lineas.append(actual)
    return lineas or [""]


# ============================================================================ paneles y botones
def panel(superficie, rectangulo: pygame.Rect, relleno=PANEL, borde=PANEL_BORDE, grosor: int = 2) -> None:
    """Un rectángulo con esquinas redondeadas; el relleno puede ser translúcido (RGBA)."""
    capa = pygame.Surface(rectangulo.size, pygame.SRCALPHA)
    pygame.draw.rect(capa, relleno, capa.get_rect(), border_radius=RADIO)
    if borde is not None and grosor > 0:
        pygame.draw.rect(capa, borde, capa.get_rect(), width=grosor, border_radius=RADIO)
    superficie.blit(capa, rectangulo)


def dibujar_boton(superficie, fuentes: Fuentes, rectangulo: pygame.Rect, texto: str, resaltado: bool) -> None:
    """Un botón: normal (panel oscuro, borde rojo) o resaltado (relleno rojo, borde y texto dorados)."""
    if resaltado:
        panel(superficie, rectangulo, (ROJO[0], ROJO[1], ROJO[2], 235), ORO, 3)
        color = ORO
    else:
        panel(superficie, rectangulo)
        color = TEXTO
    texto_en(superficie, fuentes.boton, recortar_a_ancho(fuentes.boton, texto, rectangulo.width - 24), color,
             rectangulo.center)


def distribuir_botones(cantidad: int, area: pygame.Rect, alto: int = BOTON_ALTO, separacion: int = BOTON_SEPARACION,
                       alto_minimo: int = BOTON_ALTO_MINIMO) -> list[pygame.Rect]:
    """Rectángulos de 'cantidad' botones dentro de 'area', alineados arriba. Una columna de botones de 'alto'; si no
    caben, se achican hasta 'alto_minimo'; si aun así no caben, se reparten en más columnas."""
    if cantidad <= 0:
        return []
    columnas = 1
    while True:
        filas = -(-cantidad // columnas)
        alto_que_cabe = (area.height - (filas - 1) * separacion) // filas
        if alto_que_cabe >= alto_minimo or filas == 1:
            break
        columnas += 1
    alto_final = min(alto, max(1, alto_que_cabe))
    ancho = (area.width - (columnas - 1) * separacion) // columnas
    rectangulos = []
    for i in range(cantidad):
        columna, fila = divmod(i, filas)
        rectangulos.append(pygame.Rect(area.left + columna * (ancho + separacion),
                                       area.top + fila * (alto_final + separacion), ancho, alto_final))
    return rectangulos
