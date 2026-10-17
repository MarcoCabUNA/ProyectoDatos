"""
VistaPygame (Vista): la ventana del juego. Cumple el contrato de cuatro métodos que usa ControladorPygame:

    abrir()              crea la ventana (aquí se inicia pygame, sin audio)
    dibujar(pantalla)    dibuja UN cuadro a partir de un PantallaDTO
    cerrar()             libera pygame; es seguro aunque abrir() no se haya llamado
    elemento_en(punto)   qué hay en ese punto de lo último que se dibujó (ElementoDTO) o None

Pantallas reales hasta ahora (Etapa 4): menu, criptas, nombre, pausa y puntajes (View/PantallaMenus.py). Las demás
(juego, victoria, derrota) muestran todavía el contenido del PantallaDTO como texto de depuración; llegan en las
Etapas 5 a 7.

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
from View.PantallaMenus import PantallaMenus
from View.ZonasClic import ZonasClic

TITULO_VENTANA = "Cripta"
PANTALLAS_CON_BOTONES = ["menu", "criptas", "nombre", "pausa", "puntajes"]
MARGEN = 16

_RAIZ = Path(__file__).resolve().parent.parent


def _carpeta_de_recursos() -> str:
    """assets/ en la raíz del proyecto (no depende del directorio desde el que se ejecute)."""
    return str(_RAIZ / "assets")


class VistaPygame:

    def __init__(self, ruta_assets: str | None = None):
        self._ruta_assets = ruta_assets if ruta_assets is not None else _carpeta_de_recursos()
        self._superficie: pygame.Surface | None = None
        self._fuentes: c.Fuentes | None = None
        self._zonas = ZonasClic()
        self._menus: PantallaMenus | None = None

    # ================================================================== contrato
    def abrir(self) -> None:
        pygame.display.init()                 # solo video y fuentes: así no se inicia el mezclador de audio
        pygame.font.init()
        self._superficie = pygame.display.set_mode((c.ANCHO, c.ALTO), pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption(TITULO_VENTANA)
        self._fuentes = c.Fuentes()
        self._menus = PantallaMenus(AlmacenSprites(self._ruta_assets), self._fuentes, self._zonas)

    def dibujar(self, pantalla: PantallaDTO) -> None:
        self._zonas.limpiar()                 # las zonas son las de ESTE cuadro, nunca las del anterior
        if pantalla.pantalla in PANTALLAS_CON_BOTONES:
            self._menus.dibujar(self._superficie, pantalla, pygame.time.get_ticks())
        else:
            self._dibujar_depuracion(pantalla)
        pygame.display.flip()

    def cerrar(self) -> None:
        self._superficie = None
        self._fuentes = None
        self._menus = None
        pygame.quit()                         # seguro aunque nada se haya iniciado

    def elemento_en(self, posicion: tuple[int, int]) -> ElementoDTO | None:
        return self._zonas.buscar(posicion)

    # ================================================================== interno
    def _dibujar_depuracion(self, pantalla: PantallaDTO) -> None:
        """Provisional (Etapas 5 a 7): el contenido del PantallaDTO como texto."""
        self._superficie.fill(c.NEGRO_TINTA)
        y = MARGEN
        for texto, color in self._lineas_de_depuracion(pantalla):
            self._superficie.blit(self._fuentes.pie.render(texto, True, color), (MARGEN, y))
            y += self._fuentes.pie.get_linesize()
            if y > c.ALTO - MARGEN:
                break

    @staticmethod
    def _lineas_de_depuracion(pantalla: PantallaDTO) -> list[tuple[str, tuple[int, int, int]]]:
        """Todo lo que trae el PantallaDTO, una línea por dato, como (texto, color)."""
        lineas = [(f"[pantalla: {pantalla.pantalla}]  titulo: {pantalla.titulo!r}", c.ORO)]
        for i, opcion in enumerate(pantalla.opciones):
            marca = ">" if i == pantalla.seleccion else " "
            lineas.append((f"  {marca} boton {i}: {opcion}", c.TEXTO))
        if pantalla.pantalla == "nombre":
            lineas.append((f"  texto escrito: {pantalla.texto!r}", c.TEXTO))
        if pantalla.aviso:
            lineas.append((f"AVISO: {pantalla.aviso}", c.AVISO))
        estado = pantalla.estado
        if estado is not None:
            j = estado.jugador
            lineas.append((f"sala {estado.sala.id} '{estado.sala.nombre}' (inicial {estado.sala_inicial}, "
                           f"salida {estado.sala_salida})  reloj {estado.reloj}  resultado {estado.resultado}",
                           c.TEXTO))
            lineas.append((f"jugador {j.nombre}: vida {j.vida}/{j.vida_max} atq {j.ataque} def {j.defensa} "
                           f"vel {j.velocidad}", c.TEXTO))
            lineas.append((f"enemigos: {[e.nombre for e in estado.enemigos]}  objetivo: {pantalla.objetivo}",
                           c.TEXTO))
            lineas.append((f"suelo: {[o.nombre for o in estado.objetos_suelo]}  efectos: "
                           f"{[(f.tipo, f.restante) for f in estado.efectos]}", c.TEXTO))
            inv = estado.inventario
            lineas.append((f"inventario {inv.capacidad}/{inv.capacidad_maxima} cursor {inv.cursor} "
                           f"criterio {inv.criterio}: {[o.nombre for o in inv.objetos]}", c.TEXTO))
            lineas.extend((f"  {m}", c.TEXTO) for m in estado.mensajes)
        if pantalla.puntaje is not None:
            lineas.append((f"puntaje: {pantalla.puntaje}", c.TEXTO))
        if pantalla.reporte is not None:
            lineas.append((f"reporte: {pantalla.reporte}", c.TEXTO))
        if pantalla.pantalla == "puntajes":
            lineas.append((f"orden: {pantalla.criterio}  filas: {len(pantalla.puntajes)}", c.TEXTO))
            lineas.extend((f"  {p.nombre} {p.mazmorra} acc={p.acciones} ene={p.enemigos_derrotados} "
                           f"t={p.tiempo_final}", c.TEXTO) for p in pantalla.puntajes)
        lineas.extend((f"ayuda: {a}", c.TEXTO) for a in pantalla.ayuda)
        return lineas
