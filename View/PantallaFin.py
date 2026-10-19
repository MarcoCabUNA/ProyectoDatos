"""
PantallaFin (Vista): las pantallas victoria y derrota.

Sus fondos (fondo_victoria y fondo_derrota) YA traen el mensaje en un recuadro central ("¡Victoria!" / "¡Derrota!" y su
frase): aquí no se dibuja ningún título ni mensaje, y NADA se pone sobre ese recuadro (RECUADRO). Lo que sí se dibuja
va en las franjas libres:

    izquierda   el puntaje de la partida (o "Puntaje no guardado" si no se pudo guardar)
    derecha     el reporte de datos que exige el enunciado (§5.1) y si fue offline
    abajo       los tres botones (cada uno registra su zona ELEMENTO_BOTON)
    arriba      el aviso, si lo hay (la ayuda va abajo del todo)

Qué texto se muestra lo deciden dos funciones puras (lineas_de_puntaje y lineas_de_reporte), que se prueban sin dibujar.
"""
import pygame

from DTO.ElementoDTO import ELEMENTO_BOTON, ElementoDTO
from DTO.PantallaDTO import PantallaDTO
from DTO.PuntajeDTO import PuntajeDTO
from DTO.ReporteDatosDTO import ReporteDatosDTO
from View import Componentes as c
from View.PantallaMenus import PantallaMenus
from View.ZonasClic import ZonasClic

PANTALLAS_FIN = ["victoria", "derrota"]
FONDOS_FIN = ["fondo_victoria", "fondo_derrota"]          # en el mismo orden que PANTALLAS_FIN

# El recuadro del mensaje de los fondos, con su brillo (medido: x 21-79 %, y 26-74 % de 1376x768)
RECUADRO = pygame.Rect(round(c.ANCHO * 0.21), round(c.ALTO * 0.26), round(c.ANCHO * 0.58), round(c.ALTO * 0.48))

_MARGEN_LATERAL = 14
_PANEL_IZQUIERDO = pygame.Rect(_MARGEN_LATERAL, RECUADRO.top, RECUADRO.left - 2 * _MARGEN_LATERAL - 2, RECUADRO.height)
_PANEL_DERECHO = pygame.Rect(RECUADRO.right + _MARGEN_LATERAL + 2, RECUADRO.top,
                             c.ANCHO - RECUADRO.right - 2 * _MARGEN_LATERAL - 2, RECUADRO.height)
_BOTON_FIN_ANCHO, _BOTON_FIN_ALTO, _BOTON_FIN_SEPARACION = 300, 44, 16
_BOTONES_Y = RECUADRO.bottom + 22

_RELLENO_X, _ENCABEZADO_Y, _FILA_Y0, _FILA_ALTO = 16, 14, 58, 56
_TEXTO_NO_GUARDADO = "Puntaje no guardado"


def lineas_de_puntaje(puntaje: PuntajeDTO | None) -> list[tuple[str, str]]:
    """(etiqueta, valor) de cada dato del puntaje, en el orden en que se muestran. Sin puntaje: el aviso de que no se
    guardó (con la etiqueta vacía)."""
    if puntaje is None:
        return [("", _TEXTO_NO_GUARDADO)]
    return [("Nombre", puntaje.nombre), ("Cripta", puntaje.mazmorra), ("Acciones", str(puntaje.acciones)),
            ("Enemigos derrotados", str(puntaje.enemigos_derrotados)), ("Tiempo final", str(puntaje.tiempo_final))]


def lineas_de_reporte(reporte: ReporteDatosDTO | None) -> list[tuple[str, str]]:
    """(etiqueta, valor) de lo que exige §5.1. El presupuesto desconocido (None) se muestra como "—"."""
    if reporte is None:
        return []
    presupuesto = "—" if reporte.presupuesto is None else str(reporte.presupuesto)
    return [("Solicitudes realizadas", str(reporte.solicitudes_realizadas)), ("Presupuesto", presupuesto),
            ("Aciertos de caché", str(reporte.aciertos_cache)), ("Fallos de caché", str(reporte.fallos_cache))]


class PantallaFin:

    def __init__(self, almacen, fuentes: c.Fuentes, zonas: ZonasClic, menus: PantallaMenus):
        self._almacen = almacen
        self._fuentes = fuentes
        self._zonas = zonas
        self._menus = menus                  # para dibujar el aviso y la ayuda como en el resto de las pantallas

    def dibujar(self, superficie: pygame.Surface, pantalla: PantallaDTO) -> None:
        fondo = FONDOS_FIN[0] if pantalla.pantalla == PANTALLAS_FIN[0] else FONDOS_FIN[1]
        superficie.blit(self._almacen.fondo(fondo, (c.ANCHO, c.ALTO)).fotogramas[0], (0, 0))
        self._panel_de_datos(superficie, _PANEL_IZQUIERDO, "Puntaje", lineas_de_puntaje(pantalla.puntaje),
                             pantalla.puntaje is None)
        self._panel_de_datos(superficie, _PANEL_DERECHO, "Reporte", lineas_de_reporte(pantalla.reporte), False)
        if pantalla.reporte is not None and pantalla.reporte.offline:
            self._nota_offline(superficie)
        self._botones(superficie, pantalla)
        self._menus.aviso_y_ayuda(superficie, pantalla, aviso_arriba=True)

    # ================================================================== piezas
    def _panel_de_datos(self, superficie, area: pygame.Rect, encabezado: str, lineas, es_aviso: bool) -> None:
        c.panel(superficie, area)
        ancho = area.width - 2 * _RELLENO_X
        c.texto_en(superficie, self._fuentes.boton, encabezado, c.ORO, (area.centerx, area.top + _ENCABEZADO_Y),
                   "midtop")
        pygame.draw.line(superficie, c.PANEL_BORDE, (area.left + 12, area.top + 44), (area.right - 12, area.top + 44), 2)
        y = area.top + _FILA_Y0
        for etiqueta, valor in lineas:
            if etiqueta:
                c.texto_en(superficie, self._fuentes.pie, etiqueta, c.TEXTO_SUAVE, (area.left + _RELLENO_X, y), "topleft")
            color = c.AVISO if es_aviso else c.TEXTO
            fuente = self._fuentes.texto if self._fuentes.texto.size(valor)[0] <= ancho else self._fuentes.pie
            c.texto_en(superficie, fuente, c.recortar_a_ancho(fuente, valor, ancho), color,
                       (area.left + _RELLENO_X, y + (18 if etiqueta else 0)), "topleft")
            y += _FILA_ALTO

    def _nota_offline(self, superficie) -> None:
        y = _PANEL_DERECHO.top + _FILA_Y0 + 4 * _FILA_ALTO
        c.texto_en(superficie, self._fuentes.pie, "Partida offline", c.ORO, (_PANEL_DERECHO.left + _RELLENO_X, y),
                   "topleft")
        texto = "Las lecturas locales no cuentan como solicitudes."
        for linea in c.ajustar_lineas(self._fuentes.pie, texto, _PANEL_DERECHO.width - 2 * _RELLENO_X):
            y += 20
            c.texto_en(superficie, self._fuentes.pie, linea, c.TEXTO_SUAVE, (_PANEL_DERECHO.left + _RELLENO_X, y),
                       "topleft")

    def _botones(self, superficie, pantalla: PantallaDTO) -> None:
        cantidad = len(pantalla.opciones)
        total = cantidad * _BOTON_FIN_ANCHO + (cantidad - 1) * _BOTON_FIN_SEPARACION
        x = (c.ANCHO - total) // 2
        for i in range(cantidad):
            rectangulo = pygame.Rect(x + i * (_BOTON_FIN_ANCHO + _BOTON_FIN_SEPARACION), _BOTONES_Y,
                                     _BOTON_FIN_ANCHO, _BOTON_FIN_ALTO)
            c.dibujar_boton(superficie, self._fuentes, rectangulo, pantalla.opciones[i], i == pantalla.seleccion)
            self._zonas.agregar(rectangulo, ElementoDTO(ELEMENTO_BOTON, i))
