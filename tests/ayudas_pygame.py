"""
Ayudas para probar los controladores gráficos (no es una prueba). Necesitan pygame; las del backend, no
(esas están en ayudas_controladores.py).

Todo usa el paquete offline del repositorio y carpetas temporales: nada se escribe en cache/, logs/ ni saves/.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")       # pygame sin ventana
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")       # y sin dispositivo de audio
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402

from ayudas_controladores import crear_backend  # noqa: E402
from DTO.ElementoDTO import ElementoDTO  # noqa: E402

CTRL = pygame.KMOD_LCTRL
MAYUS = pygame.KMOD_LSHIFT


def crear_fabrica(carpeta: str, ruta_puntajes: str | None = None):
    """La función que ControladorPygame usa para crear un backend nuevo por partida (servicios reales, paquete offline)."""
    def fabrica(config):
        return crear_backend(carpeta, config, ruta_puntajes=ruta_puntajes)
    return fabrica


class VistaFalsa:
    """Cumple el contrato de la Vista (abrir, dibujar, cerrar y elemento_en) y recuerda lo que se le pidió.
    Las zonas donde 'hay' cosas las coloca cada prueba con zona(): devuelve un punto dentro de esa zona, para hacer
    clic ahí."""

    def __init__(self):
        self.abierta = False
        self.cerrada = False
        self.cuadros = []
        self.consultas = 0                  # cuántas veces el controlador preguntó 'qué hay aquí'
        self._zonas = []

    def abrir(self):
        self.abierta = True

    def dibujar(self, pantalla):
        self.cuadros.append(pantalla)

    def cerrar(self):
        self.cerrada = True

    def zona(self, elemento: ElementoDTO) -> tuple[int, int]:
        """Coloca 'elemento' en un rectángulo propio y devuelve su centro."""
        k = len(self._zonas)
        rectangulo = pygame.Rect(10 + 110 * (k % 10), 10 + 60 * (k // 10), 100, 50)
        self._zonas.append((rectangulo, elemento))
        return rectangulo.center

    def elemento_en(self, posicion):
        self.consultas += 1
        for rectangulo, elemento in self._zonas:
            if rectangulo.collidepoint(posicion):
                return elemento
        return None


class Reloj:
    """Un reloj que avanza solo cuando la prueba lo dice (para el doble clic)."""

    def __init__(self):
        self.ahora = 10_000

    def leer(self) -> int:
        return self.ahora


class Modificadores:
    """Las teclas modificadoras 'pulsadas' (los eventos del ratón no las traen)."""

    def __init__(self):
        self.valor = 0

    def leer(self) -> int:
        return self.valor


def tecla(codigo: int, mod: int = 0, caracter: str = ""):
    """Un evento de pygame: se pulsó una tecla."""
    return pygame.event.Event(pygame.KEYDOWN, key=codigo, mod=mod, unicode=caracter)


def letra(caracter: str):
    return tecla(ord(caracter.lower()), mod=MAYUS if caracter.isupper() else 0, caracter=caracter)


def clic(posicion, boton: int = 1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=posicion, button=boton)


def movimiento(posicion):
    return pygame.event.Event(pygame.MOUSEMOTION, pos=posicion, rel=(0, 0), buttons=(0, 0, 0))


def rueda(y: int):
    return pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=y)