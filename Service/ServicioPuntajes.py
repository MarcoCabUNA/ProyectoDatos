"""
ServicioPuntajes (Servicios, Integrante 3): registra y muestra la tabla de puntajes local (§2.12).

Reparto acordado con Datos: AlmacenPuntajes solo guarda y lee las filas, en el orden en que se jugaron.
Ordenarlas con el Ordenador (§4.9) es de este servicio. La guía no lo listaba: se agrega porque el enunciado
pide la tabla y alguien tiene que ordenarla.

    registrar(puntaje)       anexa la fila de una partida terminada (PuntajeDTO viene de ServicioPartida.puntaje)
    tabla(criterio)          todas las filas ordenadas por un criterio:
        "enemigos"  más enemigos derrotados primero (el criterio por omisión)
        "tiempo"    menor tiempo final primero
        "acciones"  menos acciones primero
        "nombre"    alfabético, sin distinguir mayúsculas
    Los empates conservan el orden en que se jugaron (el ordenamiento es estable).

La fila no dice si la partida se ganó o se perdió (PuntajeDTO no tiene ese campo): por eso el criterio por
omisión es "enemigos" y no "acciones", que premiaría morir rápido. Una partida reproducida con --replay no
se registra: no es una partida nueva (quien llama decide cuándo registrar).
"""
from Data.AlmacenPuntajes import AlmacenPuntajes
from DTO.PuntajeDTO import PuntajeDTO
from Estructuras.Ordenador import Ordenador


def _por_enemigos(a, b) -> int:
    return Ordenador.comparar(b.enemigos_derrotados, a.enemigos_derrotados)      # al revés: más primero


def _por_tiempo(a, b) -> int:
    return Ordenador.comparar(a.tiempo_final, b.tiempo_final)


def _por_acciones(a, b) -> int:
    return Ordenador.comparar(a.acciones, b.acciones)


def _por_nombre(a, b) -> int:
    return Ordenador.comparar(a.nombre.casefold(), b.nombre.casefold())


class ServicioPuntajes:

    def __init__(self, almacen: AlmacenPuntajes | None = None):
        self._almacen = almacen if almacen is not None else AlmacenPuntajes()

    def registrar(self, puntaje: PuntajeDTO) -> None:
        self._almacen.agregar(puntaje)

    def tabla(self, criterio: str = "enemigos") -> list[PuntajeDTO]:
        """Las filas ordenadas por 'criterio'. Lanza ValueError si el criterio no existe."""
        if criterio == "enemigos":
            comparador = _por_enemigos
        elif criterio == "tiempo":
            comparador = _por_tiempo
        elif criterio == "acciones":
            comparador = _por_acciones
        elif criterio == "nombre":
            comparador = _por_nombre
        else:
            raise ValueError(f"criterio de orden desconocido: {criterio!r} "
                             f"(se esperaba enemigos, tiempo, acciones o nombre)")
        return Ordenador.ordenar(self._almacen.leer(), comparador)