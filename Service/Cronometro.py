"""
Cronometro (Integrante 2, compartido por las mediciones de --bench): mide cuánto tarda una operación.

    mejor, mediana = medir(lambda: cache.contiene("itm_daga"))
    mejor, mediana = medir(insertar, preparar=crear_cache_llena)   # preparar NO se cronometra

Cómo mide:
  - time.perf_counter (el reloj de más resolución de Python).
  - Una ejecución de calentamiento sin cronometrar (la primera vez Python carga y prepara cosas).
  - N repeticiones; devuelve el MEJOR tiempo (el menos afectado por otros programas) y la MEDIANA
    (el caso típico). Las dos en milisegundos.
  - La mediana ordena los tiempos con el Ordenador del equipo (Estructuras/Ordenador.py), no con
    sorted() (§4.9).
"""
import time

from Estructuras.Ordenador import Ordenador

REPETICIONES_POR_DEFECTO = 15


def medir(funcion, repeticiones: int = REPETICIONES_POR_DEFECTO, preparar=None,
          calentar: bool = True) -> tuple[float, float]:
    """
    funcion:   lo que se cronometra. Sin argumentos, o con uno si se da 'preparar'.
    preparar:  opcional; se llama ANTES de cada repetición, fuera del cronómetro, y lo que devuelve
               se le pasa a 'funcion' (para operaciones que cambian el estado, como insertar).
    Devuelve (mejor_ms, mediana_ms).
    """
    if not isinstance(repeticiones, int) or isinstance(repeticiones, bool) or repeticiones < 1:
        raise ValueError(f"las repeticiones deben ser un entero >= 1 (llegó {repeticiones!r})")
    if calentar:
        _una_vez(funcion, preparar)
    tiempos: list[float] = []
    for _ in range(repeticiones):
        tiempos.append(_una_vez(funcion, preparar))
    return mejor_y_mediana(tiempos)


def mejor_y_mediana(tiempos: list[float]) -> tuple[float, float]:
    """(mínimo, mediana) de una lista no vacía. Con cantidad par, la mediana es el promedio de los dos del medio."""
    if not tiempos:
        raise ValueError("no hay tiempos")
    ordenados = Ordenador.ordenar(tiempos, Ordenador.comparar)
    n = len(ordenados)
    mitad = n // 2
    mediana = ordenados[mitad] if n % 2 == 1 else (ordenados[mitad - 1] + ordenados[mitad]) / 2
    return ordenados[0], mediana


def _una_vez(funcion, preparar) -> float:
    if preparar is None:
        inicio = time.perf_counter()
        funcion()
    else:
        argumento = preparar()
        inicio = time.perf_counter()
        funcion(argumento)
    return (time.perf_counter() - inicio) * 1000