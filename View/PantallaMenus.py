"""
PantallaMenus (Vista): las pantallas con botones: menu, criptas, nombre, pausa y puntajes.

Todas comparten el mismo esqueleto: fondo -> título -> contenido -> botones (cada uno registra su zona ELEMENTO_BOTON)
-> aviso destacado -> ayuda como pie. Los textos de opciones y ayuda llegan listos en el PantallaDTO y se dibujan tal cual.

    menu      fondo_menu tal cual. NO se dibuja pantalla.titulo: el fondo ya trae el título "Crypta" (§6.6 de la guía).
    criptas   fondo_menu con velo suave, título propio y una cuadrícula de botones (más pequeños, o en más columnas,
              si hay muchas criptas). El último botón (Volver) queda siempre aparte, abajo.
    nombre    campo de texto con cursor parpadeante y los botones Aceptar y Volver.
    pausa     la escena de la partida (pantalla.estado, sin zonas de clic) con un velo fuerte encima. Sin estado
              (solo en pruebas), fondo_menu.
    puntajes  tabla (nombre, cripta, acciones, enemigos derrotados, tiempo final) y el criterio de orden.
"""
import pygame

from DTO.ElementoDTO import ELEMENTO_BOTON, ElementoDTO
from DTO.PantallaDTO import PantallaDTO
from View import Componentes as c
from View.ZonasClic import ZonasClic

FONDO_MENU = "fondo_menu"
_PERIODO_CURSOR_MS = 500

_AREA_MENU = pygame.Rect((c.ANCHO - c.BOTON_ANCHO) // 2, 452, c.BOTON_ANCHO, 204)
_AREA_CRIPTAS = pygame.Rect(188, 126, c.ANCHO - 376, 424)
_AREA_VOLVER = pygame.Rect((c.ANCHO - 260) // 2, 562, 260, c.BOTON_ALTO)
_AREA_PAUSA = pygame.Rect((c.ANCHO - c.BOTON_ANCHO) // 2, 190, c.BOTON_ANCHO, 4 * (c.BOTON_ALTO + c.BOTON_SEPARACION))
_CAMPO_NOMBRE = pygame.Rect((c.ANCHO - 520) // 2, 190, 520, 64)
_AREA_NOMBRE = pygame.Rect((c.ANCHO - c.BOTON_ANCHO) // 2, 286, c.BOTON_ANCHO, 2 * (c.BOTON_ALTO + c.BOTON_SEPARACION))
_TABLA = pygame.Rect(118, 118, c.ANCHO - 236, 392)
_AREA_PUNTAJES = pygame.Rect((c.ANCHO - c.BOTON_ANCHO) // 2, 530, c.BOTON_ANCHO, 2 * (c.BOTON_ALTO + c.BOTON_SEPARACION))

# Columnas de la tabla de puntajes: (encabezado, criterio de orden que la resalta o None, x relativa a la tabla)
_COLUMNAS = [("Nombre", "nombre", 24), ("Cripta", None, 250), ("Acciones", "acciones", 620),
             ("Enemigos derrotados", "enemigos", 760), ("Tiempo final", "tiempo", 990)]
_FILA_Y0, _FILA_ALTO = 56, 28

# Criterios de orden que manda el Controlador y cómo se muestran (listas paralelas)
_CRITERIOS = ["enemigos", "tiempo", "acciones", "nombre"]
_ETIQUETAS = ["enemigos derrotados", "tiempo final", "acciones", "nombre"]


class PantallaMenus:

    def __init__(self, almacen, fuentes: c.Fuentes, zonas: ZonasClic, escena=None):
        self._almacen = almacen
        self._escena = escena
        self._fuentes = fuentes
        self._zonas = zonas
        self._velo_suave = self._crear_velo(c.VELO_SUAVE)
        self._velo_fuerte = self._crear_velo(c.VELO_FUERTE)

    def dibujar(self, superficie: pygame.Surface, pantalla: PantallaDTO, ms: int) -> None:
        """Dibuja una de las cinco pantallas. 'ms' es el reloj en milisegundos (solo para el cursor parpadeante)."""
        nombre = pantalla.pantalla
        if nombre == "pausa" and pantalla.estado is not None and self._escena is not None:
            self._escena.dibujar(superficie, pantalla.estado, None, con_zonas=False)
        else:
            superficie.blit(self._almacen.fondo(FONDO_MENU, (c.ANCHO, c.ALTO)).fotogramas[0], (0, 0))
        if nombre == "menu":
            self._botones(superficie, pantalla, c.distribuir_botones(len(pantalla.opciones), _AREA_MENU,
                                                                      c.BOTON_ALTO_MENU, 6))
        elif nombre == "criptas":
            self._criptas(superficie, pantalla)
        elif nombre == "nombre":
            self._nombre(superficie, pantalla, ms)
        elif nombre == "pausa":
            superficie.blit(self._velo_fuerte, (0, 0))
            self._titulo(superficie, pantalla.titulo)
            self._botones(superficie, pantalla, c.distribuir_botones(len(pantalla.opciones), _AREA_PAUSA))
        elif nombre == "puntajes":
            self._puntajes(superficie, pantalla)
        self.aviso_y_ayuda(superficie, pantalla)

    # ================================================================== cada pantalla
    def _criptas(self, superficie, pantalla):
        superficie.blit(self._velo_suave, (0, 0))
        self._titulo(superficie, pantalla.titulo)
        cantidad = len(pantalla.opciones)
        rectangulos = c.distribuir_botones(cantidad - 1, _AREA_CRIPTAS) + [_AREA_VOLVER]   # Volver, siempre aparte
        self._botones(superficie, pantalla, rectangulos)

    def _nombre(self, superficie, pantalla, ms):
        superficie.blit(self._velo_suave, (0, 0))
        self._titulo(superficie, pantalla.titulo)
        c.panel(superficie, _CAMPO_NOMBRE, c.PANEL, c.ORO, 2)
        cursor = "|" if (ms // _PERIODO_CURSOR_MS) % 2 == 0 else " "
        c.texto_en(superficie, self._fuentes.titulo, pantalla.texto + cursor, c.TEXTO, _CAMPO_NOMBRE.center)
        self._botones(superficie, pantalla, c.distribuir_botones(len(pantalla.opciones), _AREA_NOMBRE))

    def _puntajes(self, superficie, pantalla):
        superficie.blit(self._velo_suave, (0, 0))
        self._titulo(superficie, pantalla.titulo)
        c.panel(superficie, _TABLA)
        for encabezado, criterio, x in _COLUMNAS:
            color = c.ORO if criterio == pantalla.criterio else c.TEXTO_SUAVE
            c.texto_en(superficie, self._fuentes.texto, encabezado, color, (_TABLA.left + x, _TABLA.top + 14), "topleft")
        pygame.draw.line(superficie, c.PANEL_BORDE, (_TABLA.left + 12, _TABLA.top + 46),
                         (_TABLA.right - 12, _TABLA.top + 46), 2)
        filas_que_caben = (_TABLA.height - _FILA_Y0 - 36) // _FILA_ALTO
        if not pantalla.puntajes:
            c.texto_en(superficie, self._fuentes.texto, "Aún no hay puntajes", c.TEXTO_SUAVE,
                       (_TABLA.centerx, _TABLA.centery), "center")
        for i, p in enumerate(pantalla.puntajes[:filas_que_caben]):
            y = _TABLA.top + _FILA_Y0 + i * _FILA_ALTO
            celdas = [p.nombre, f"{p.mazmorra}  v.{p.version[:7]}", str(p.acciones), str(p.enemigos_derrotados),
                      str(p.tiempo_final)]
            for (_, _, x), celda in zip(_COLUMNAS, celdas):
                c.texto_en(superficie, self._fuentes.texto, celda, c.TEXTO, (_TABLA.left + x, y), "topleft")
        restantes = len(pantalla.puntajes) - filas_que_caben
        etiqueta = self._etiqueta_de(pantalla.criterio)
        pie_tabla = f"Orden: {etiqueta}" + (f"   (y {restantes} más)" if restantes > 0 else "")
        c.texto_en(superficie, self._fuentes.pie, pie_tabla, c.ORO_OSCURO, (_TABLA.right - 20, _TABLA.bottom - 12),
                   "bottomright")
        self._botones(superficie, pantalla, c.distribuir_botones(len(pantalla.opciones), _AREA_PUNTAJES))

    # ================================================================== piezas comunes
    def _titulo(self, superficie, texto: str):
        c.texto_en(superficie, self._fuentes.titulo, texto, c.ORO, (c.ANCHO // 2, c.TITULO_Y))

    def _botones(self, superficie, pantalla, rectangulos):
        """Dibuja un botón por opción y registra su zona (en el orden en que se dibujan)."""
        for i, rectangulo in enumerate(rectangulos):
            c.dibujar_boton(superficie, self._fuentes, rectangulo, pantalla.opciones[i], i == pantalla.seleccion)
            self._zonas.agregar(rectangulo, ElementoDTO(ELEMENTO_BOTON, i))

    def caja_del_aviso(self, pantalla, arriba: bool = False) -> tuple[pygame.Rect | None, list[str]]:
        """El rectángulo del aviso y sus líneas (como mucho AVISO_MAX_LINEAS). Va justo encima de la ayuda y crece hacia
        arriba; con 'arriba' va pegado al borde superior (victoria y derrota, donde abajo están los botones).
        Sin aviso devuelve (None, [])."""
        if not pantalla.aviso:
            return None, []
        ancho_texto = c.ANCHO - 240
        lineas = c.ajustar_lineas(self._fuentes.texto, pantalla.aviso, ancho_texto)
        if len(lineas) > c.AVISO_MAX_LINEAS:
            lineas = lineas[:c.AVISO_MAX_LINEAS]
            lineas[-1] = c.recortar_a_ancho(self._fuentes.texto, lineas[-1] + "...", ancho_texto)
        caja = pygame.Rect(0, 0, c.ANCHO - 200, 14 + c.AVISO_INTERLINEA * len(lineas))
        if arriba:
            caja.midtop = (c.ANCHO // 2, c.AVISO_ARRIBA_Y)
        else:
            caja.midbottom = (c.ANCHO // 2, self.tope_de_la_ayuda(pantalla) - c.AVISO_SEPARACION)
        return caja, lineas

    def tope_de_la_ayuda(self, pantalla) -> int:
        """La coordenada y más alta que ocupa el texto de ayuda (o el borde de abajo si no hay ayuda)."""
        if not pantalla.ayuda:
            return c.PIE_BASE_Y
        return c.PIE_BASE_Y - c.PIE_INTERLINEA * (len(pantalla.ayuda) - 1) - self._fuentes.pie.get_height()

    def aviso_y_ayuda(self, superficie, pantalla, aviso_arriba: bool = False):
        caja, lineas = self.caja_del_aviso(pantalla, aviso_arriba)
        if caja is not None:
            c.panel(superficie, caja, c.AVISO_FONDO, c.ROJO_VIVO, 2)
            for i, linea in enumerate(lineas):
                c.texto_en(superficie, self._fuentes.texto, linea, c.AVISO,
                           (caja.centerx, caja.top + 21 + c.AVISO_INTERLINEA * i))
        y = c.PIE_BASE_Y
        for linea in reversed(pantalla.ayuda):
            c.texto_en(superficie, self._fuentes.pie, linea, c.TEXTO_SUAVE, (c.ANCHO // 2, y), "midbottom")
            y -= c.PIE_INTERLINEA

    @staticmethod
    def _etiqueta_de(criterio) -> str:
        for i in range(len(_CRITERIOS)):
            if _CRITERIOS[i] == criterio:
                return _ETIQUETAS[i]
        return str(criterio)

    @staticmethod
    def _crear_velo(color) -> pygame.Surface:
        velo = pygame.Surface((c.ANCHO, c.ALTO), pygame.SRCALPHA)
        velo.fill(color)
        return velo
