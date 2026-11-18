"""
BusquedaBinaria (feature 004, línea de tiempo) — búsqueda binaria propia sobre un arreglo ordenado.

No usa `bisect` (prohibido, Principio II) y no importa ninguna capa.

    ultimo_menor_o_igual([0, 3, 6, 9], 7, clave)  ->  2     (la posición del 6)

Costos:
    tiempo   O(log n)
    espacio  O(1)
El arreglo debe estar ordenado de forma no decreciente por la clave. La línea de tiempo cumple eso
porque todo se agrega al final y todo recorte quita del final.
"""
from typing import Callable, Sequence, TypeVar

T = TypeVar("T")


def ultimo_menor_o_igual(arreglo: Sequence[T], clave: int, extraer_clave: Callable[[T], int]) -> int:
    """La posición del último elemento cuya clave es <= `clave`, o -1 si no hay ninguno.

    `extraer_clave(elemento)` devuelve la clave de ordenamiento de un elemento. Con claves repetidas
    devuelve la posición del último de ellas."""
    izquierda, derecha = 0, len(arreglo) - 1
    encontrado = -1
    while izquierda <= derecha:
        medio = (izquierda + derecha) // 2
        if extraer_clave(arreglo[medio]) <= clave:
            encontrado = medio                    # candidato; puede haber uno mejor más a la derecha
            izquierda = medio + 1
        else:
            derecha = medio - 1
    return encontrado
