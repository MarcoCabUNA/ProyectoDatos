"""
VistaPygame (Vista): la ventana del juego. Cumple el contrato de cuatro métodos que usa ControladorPygame:

    abrir()              crea la ventana (aquí se inicia pygame, sin audio)
    dibujar(pantalla)    dibuja UN cuadro a partir de un PantallaDTO
    cerrar()             libera pygame; es seguro aunque abrir() no se haya llamado
    elemento_en(punto)   qué hay en ese punto de lo último que se dibujó (ElementoDTO) o None

ETAPA 2 (esqueleto): dibujar() muestra el contenido del PantallaDTO como texto de depuración, para comprobar que
llega todo. Las zonas de clic, los sprites y las pantallas reales llegan en las etapas siguientes.

La Vista no lee el teclado ni el ratón (eso es del Controlador) y solo importa pygame y DTO/.
Se dibuja en una resolución lógica fija; con pygame.SCALED la ventana se puede redimensionar.
"""
from pathlib import Path

import pygame

from DTO.ElementoDTO import ElementoDTO
from DTO.PantallaDTO import PantallaDTO

ANCHO, ALTO = 1376, 768                 # tamaño nativo de los fondos
TITULO_VENTANA = "Cripta"
COLOR_FONDO = (18, 14, 22)
COLOR_TEXTO = (225, 220, 210)
COLOR_TITULO = (240, 190, 90)
COLOR_AVISO = (240, 110, 100)
TAMANO_FUENTE = 22
MARGEN = 16

_RAIZ = Path(__file__).resolve().parent.parent


def _carpeta_de_recursos() -> str:
    """assets/ en la raíz del proyecto (no depende del directorio desde el que se ejecute)."""
    return str(_RAIZ / "assets")


class VistaPygame:

    def __init__(self, ruta_assets: str | None = None):
        self._ruta_assets = ruta_assets if ruta_assets is not None else _carpeta_de_recursos()
        self._superficie: pygame.Surface | None = None
        self._fuente: pygame.font.Font | None = None

    # ================================================================== contrato
    def abrir(self) -> None:
        pygame.display.init()                 # solo video y fuentes: así no se inicia el mezclador de audio
        pygame.font.init()
        self._superficie = pygame.display.set_mode((ANCHO, ALTO), pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption(TITULO_VENTANA)
        self._fuente = pygame.font.Font(None, TAMANO_FUENTE)

    def dibujar(self, pantalla: PantallaDTO) -> None:
        self._superficie.fill(COLOR_FONDO)
        y = MARGEN
        for texto, color in self._lineas_de_depuracion(pantalla):
            imagen = self._fuente.render(texto, True, color)
            self._superficie.blit(imagen, (MARGEN, y))
            y += self._fuente.get_linesize()
            if y > ALTO - MARGEN:
                break
        pygame.display.flip()

    def cerrar(self) -> None:
        self._superficie = None
        self._fuente = None
        pygame.quit()                         # seguro aunque nada se haya iniciado

    def elemento_en(self, posicion: tuple[int, int]) -> ElementoDTO | None:
        return None                           # todavía no hay zonas de clic (Etapa 4)

    # ================================================================== interno
    @staticmethod
    def _lineas_de_depuracion(pantalla: PantallaDTO) -> list[tuple[str, tuple[int, int, int]]]:
        """Todo lo que trae el PantallaDTO, una línea por dato, como (texto, color)."""
        lineas = [(f"[pantalla: {pantalla.pantalla}]  titulo: {pantalla.titulo!r}", COLOR_TITULO)]
        for i, opcion in enumerate(pantalla.opciones):
            marca = ">" if i == pantalla.seleccion else " "
            lineas.append((f"  {marca} boton {i}: {opcion}", COLOR_TEXTO))
        if pantalla.pantalla == "nombre":
            lineas.append((f"  texto escrito: {pantalla.texto!r}", COLOR_TEXTO))
        if pantalla.aviso:
            lineas.append((f"AVISO: {pantalla.aviso}", COLOR_AVISO))
        estado = pantalla.estado
        if estado is not None:
            j = estado.jugador
            lineas.append((f"sala {estado.sala.id} '{estado.sala.nombre}' (inicial {estado.sala_inicial}, "
                           f"salida {estado.sala_salida})  reloj {estado.reloj}  resultado {estado.resultado}",
                           COLOR_TEXTO))
            lineas.append((f"jugador {j.nombre}: vida {j.vida}/{j.vida_max} atq {j.ataque} def {j.defensa} "
                           f"vel {j.velocidad}", COLOR_TEXTO))
            lineas.append((f"enemigos: {[e.nombre for e in estado.enemigos]}  objetivo: {pantalla.objetivo}",
                           COLOR_TEXTO))
            lineas.append((f"suelo: {[o.nombre for o in estado.objetos_suelo]}  efectos: "
                           f"{[(f.tipo, f.restante) for f in estado.efectos]}", COLOR_TEXTO))
            inv = estado.inventario
            lineas.append((f"inventario {inv.capacidad}/{inv.capacidad_maxima} cursor {inv.cursor} "
                           f"criterio {inv.criterio}: {[o.nombre for o in inv.objetos]}", COLOR_TEXTO))
            lineas.extend((f"  {m}", COLOR_TEXTO) for m in estado.mensajes)
        if pantalla.puntaje is not None:
            lineas.append((f"puntaje: {pantalla.puntaje}", COLOR_TEXTO))
        if pantalla.reporte is not None:
            lineas.append((f"reporte: {pantalla.reporte}", COLOR_TEXTO))
        if pantalla.pantalla == "puntajes":
            lineas.append((f"orden: {pantalla.criterio}  filas: {len(pantalla.puntajes)}", COLOR_TEXTO))
            lineas.extend((f"  {p.nombre} {p.mazmorra} acc={p.acciones} ene={p.enemigos_derrotados} "
                           f"t={p.tiempo_final}", COLOR_TEXTO) for p in pantalla.puntajes)
        lineas.extend((f"ayuda: {a}", COLOR_TEXTO) for a in pantalla.ayuda)
        return lineas
