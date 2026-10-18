"""
VistaPygame (Vista): la ventana del juego. Cumple el contrato de cuatro métodos que usa ControladorPygame:

    abrir()              crea la ventana (aquí se inicia pygame, sin audio)
    dibujar(pantalla)    dibuja UN cuadro a partir de un PantallaDTO
    cerrar()             libera pygame; es seguro aunque abrir() no se haya llamado
    elemento_en(punto)   qué hay en ese punto de lo último que se dibujó (ElementoDTO) o None

Pantallas reales hasta ahora (Etapa 6): menu, criptas, nombre, pausa y puntajes (View/PantallaMenus.py), victoria y
derrota (View/PantallaFin.py), la escena de la partida (View/EscenaJuego.py) y su HUD (View/HudJuego.py: estadísticas,
mensajes, inventario, efectos, botón Esperar, aviso y ayuda).

Zonas de clic: dibujar() limpia las zonas al empezar y cada pantalla registra las suyas (View/ZonasClic.py);
elemento_en() consulta lo último que se dibujó.

La Vista no lee el teclado ni el ratón (eso es del Controlador) y solo importa pygame y DTO/.
Se dibuja en una resolución lógica fija; con pygame.SCALED la ventana se puede redimensionar.
"""
from pathlib import Path

import pygame

from DTO.ElementoDTO import ElementoDTO
from DTO.PantallaDTO import PantallaDTO
from View import Componentes as c
from View.AlmacenSprites import AlmacenSprites
from View.EfectosEscena import EfectosEscena
from View.EscenaJuego import EscenaJuego
from View.HudJuego import HudJuego
from View.PantallaFin import PANTALLAS_FIN, PantallaFin
from View.PantallaMenus import PantallaMenus
from View.ZonasClic import ZonasClic

TITULO_VENTANA = "Cripta"
PANTALLAS_CON_BOTONES = ["menu", "criptas", "nombre", "pausa", "puntajes"]
OLVIDAN_LA_SALA = ["menu", "criptas", "nombre", "victoria", "derrota", "puntajes"]    # la pausa no: la partida sigue
_RAIZ = Path(__file__).resolve().parent.parent


def _carpeta_de_recursos() -> str:
    """assets/ en la raíz del proyecto (no depende del directorio desde el que se ejecute)."""
    return str(_RAIZ / "assets")


class VistaPygame:

    def __init__(self, animaciones: bool = False, reloj=None, ruta_assets: str | None = None):
        """'animaciones' activa las animaciones de View/EfectosEscena.py (sin ellas la salida es la de siempre). 'reloj' es una
        función sin argumentos que da milisegundos (por omisión pygame.time.get_ticks): lo único que mueve las animaciones."""
        self._animaciones = animaciones
        self._reloj = reloj if reloj is not None else pygame.time.get_ticks
        self._efectos: EfectosEscena | None = None
        self._con_mano = False                # el cursor es la mano (solo con animaciones)
        self._ruta_assets = ruta_assets if ruta_assets is not None else _carpeta_de_recursos()
        self._superficie: pygame.Surface | None = None
        self._fuentes: c.Fuentes | None = None
        self._zonas = ZonasClic()
        self._menus: PantallaMenus | None = None
        self._fin: PantallaFin | None = None
        self._escena: EscenaJuego | None = None
        self._hud: HudJuego | None = None

    # ================================================================== contrato
    def abrir(self) -> None:
        pygame.display.init()                 # solo video y fuentes: así no se inicia el mezclador de audio
        pygame.font.init()
        self._superficie = pygame.display.set_mode((c.ANCHO, c.ALTO), pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption(TITULO_VENTANA)
        self._fuentes = c.Fuentes()
        almacen = AlmacenSprites(self._ruta_assets)
        self._efectos = EfectosEscena() if self._animaciones else None
        self._escena = EscenaJuego(almacen, self._fuentes, self._zonas, self._efectos)
        self._hud = HudJuego(almacen, self._fuentes, self._zonas)
        self._menus = PantallaMenus(almacen, self._fuentes, self._zonas, self._escena)
        self._fin = PantallaFin(almacen, self._fuentes, self._zonas, self._menus)

    def dibujar(self, pantalla: PantallaDTO) -> None:
        self._zonas.limpiar()                 # las zonas son las de ESTE cuadro, nunca las del anterior
        ahora = self._reloj()
        if pantalla.pantalla in OLVIDAN_LA_SALA:
            self._escena.olvidar_la_sala()    # la próxima partida no recuerda de qué sala se viene
        if self._efectos is not None:
            self._efectos.pantalla_vista(pantalla.pantalla, ahora)
        if pantalla.pantalla in PANTALLAS_CON_BOTONES:
            self._menus.dibujar(self._superficie, pantalla, ahora)
            self._fundir_pantalla(pantalla, ahora)
        elif pantalla.pantalla in PANTALLAS_FIN:
            self._fin.dibujar(self._superficie, pantalla)
            self._fundir_pantalla(pantalla, ahora)
        elif pantalla.estado is not None:
            self._escena.dibujar(self._superficie, pantalla.estado, pantalla.objetivo, con_nombre=False, ahora=ahora,
                                 elemento_bajo_el_raton=pantalla.elemento_bajo_el_raton)
            if self._efectos is not None:
                self._efectos.fundido_de_la_sala(self._superficie, ahora)   # sobre la escena, DEBAJO del HUD
            self._hud.dibujar(self._superficie, pantalla)         # velos, estadísticas, mensajes, inventario, botón, ayuda
            if self._efectos is not None:
                self._efectos.borde_rojo(self._superficie, ahora)   # el borde enrojecido cubre el HUD también
            self._escena.dibujar_nombre(self._superficie, pantalla.estado, pantalla.elemento_bajo_el_raton)    # encima de todo
        else:
            self._superficie.fill(c.NEGRO_TINTA)
        pygame.display.flip()
        self._poner_el_cursor(pantalla)

    def _poner_el_cursor(self, pantalla: PantallaDTO) -> None:
        """Con animaciones: una mano sobre lo que se puede pulsar en la partida, y la flecha en cualquier otro sitio. Solo se
        pide al sistema cuando cambia, y un fallo del sistema (sin cursor del sistema) no interrumpe nada."""
        if self._efectos is None:
            return
        mano = pantalla.elemento_bajo_el_raton is not None
        if mano == self._con_mano:
            return
        self._con_mano = mano
        try:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if mano else pygame.SYSTEM_CURSOR_ARROW)
        except pygame.error:
            pass

    def _fundir_pantalla(self, pantalla: PantallaDTO, ahora: int) -> None:
        """El fundido de entrada de una pantalla de menú (no de la pausa: ahí la escena sigue ahí detrás)."""
        if self._efectos is not None and pantalla.pantalla in c.PANTALLAS_CON_FUNDIDO:
            self._efectos.fundido_de_la_pantalla(self._superficie, ahora)

    def cerrar(self) -> None:
        self._superficie = None
        self._fuentes = None
        self._menus = None
        self._fin = None
        self._escena = None
        self._hud = None
        self._efectos = None
        self._con_mano = False
        pygame.quit()                         # seguro aunque nada se haya iniciado

    def elemento_en(self, posicion: tuple[int, int]) -> ElementoDTO | None:
        return self._zonas.buscar(posicion)
