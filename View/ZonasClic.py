"""
ZonasClic (Vista): las cosas clicables del último cuadro dibujado, como una lista de (rectángulo, ElementoDTO).

La Vista llama a limpiar() al inicio de cada dibujar() y a agregar() por cada cosa clicable, EN EL ORDEN en que la
dibuja (fondo -> escena -> panel -> botones). buscar() recorre de la última a la primera: gana lo que está dibujado
encima. Son dos listas paralelas (nada de dict, §7 del enunciado).
"""
import pygame

from DTO.ElementoDTO import ElementoDTO


class ZonasClic:

    def __init__(self):
        self._rectangulos: list[pygame.Rect] = []
        self._elementos: list[ElementoDTO] = []

    def limpiar(self) -> None:
        self._rectangulos = []
        self._elementos = []

    def agregar(self, rectangulo: pygame.Rect, elemento: ElementoDTO) -> None:
        self._rectangulos.append(pygame.Rect(rectangulo))
        self._elementos.append(elemento)

    def buscar(self, posicion: tuple[int, int]) -> ElementoDTO | None:
        for i in range(len(self._rectangulos) - 1, -1, -1):
            if self._rectangulos[i].collidepoint(posicion):
                return self._elementos[i]
        return None

    def cantidad(self) -> int:
        return len(self._rectangulos)
