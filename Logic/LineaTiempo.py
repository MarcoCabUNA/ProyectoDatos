"""
LineaTiempo (feature 004, Lógica): la historia de la partida tal como quedó.

Guarda lo necesario para reconstruir el estado de cualquier instante pasado hacia adelante:

    acciones   las acciones VIGENTES del jugador, cada una con el tiempo en que tomó la decisión
               (las revertidas con un pergamino dejan de existir, FR-413)
    puntos     copias completas del estado ("puntos de control"), una cada K acciones (FR-416)
    cargas     el contenido inicial de cada sala que la partida ya cargó, en el orden real (hallazgo H-1)
    fichas     las fichas del catálogo que la partida ya pidió, una por id

Todo se agrega AL FINAL y todo recorte quita DEL FINAL: los arreglos nacen ordenados y no hace falta
ordenar (por eso la búsqueda binaria propia de Estructuras/BusquedaBinaria.py basta). Son `list` usadas
como almacenamiento contiguo: sin `dict`, sin `set`, sin `copy`.

No hace I/O y no importa Data ni Service. Quien la alimenta y la consulta es Service. La validación de
rango de las consultas (FR-409) es regla de negocio y por eso vive aquí; Service solo propaga el error.

Costos: agregar_accion, agregar_punto y registrar_carga O(1) amortizado; ubicar_punto O(log P);
ubicar_accion_por_tiempo O(log A); registrar_ficha y ficha O(F), con F las fichas vistas (pocas).
(El recorte con el pergamino, retroceder_una, llega en la tarea T028.)
"""
from dataclasses import dataclass

from DTO.AccionDTO import AccionDTO
from DTO.PartidaGuardadaDTO import PartidaGuardadaDTO, SalaGuardadaDTO
from DTO.SalaDTO import SalaDTO
from Estructuras.BusquedaBinaria import ultimo_menor_o_igual


@dataclass
class AccionVigente:
    """Una acción del jugador que no fue revertida. Nunca es `retroceder` ni la lectura de un pergamino."""
    tiempo: int                      # reloj en que el jugador tomó la decisión (el estado "justo antes")
    accion: AccionDTO


@dataclass
class PuntoControl:
    """Copia completa del estado cuando el jugador tiene el control, tras `acciones_completadas` acciones."""
    acciones_completadas: int
    partida: PartidaGuardadaDTO      # estado global, con el estado del azar
    salas: list[SalaGuardadaDTO]     # un bloque por sala del esqueleto
    mapa_conocido: object | None = None   # copia del mapa conocido (spec 002); ausente hasta que exista


@dataclass
class RegistroCarga:
    """El contenido inicial que Data entregó para una sala, y cuántas acciones vigentes llevaba la partida."""
    ordinal: int
    sala: SalaDTO


def _es_entero(valor: object) -> bool:
    """True si es un entero de verdad (un bool no cuenta)."""
    return isinstance(valor, int) and not isinstance(valor, bool)


class LineaTiempo:
    """La historia vigente de una partida: acciones, puntos de control, registros de carga y fichas."""

    def __init__(self, k: int) -> None:
        """`k` es cada cuántas acciones se toma un punto de control (entero >= 1, FR-415)."""
        if not _es_entero(k) or k < 1:
            raise ValueError(f"K debe ser un entero mayor o igual que 1 (se recibió {k!r})")
        self.k: int = k
        self.acciones: list[AccionVigente] = []
        self.puntos: list[PuntoControl] = []
        self.cargas: list[RegistroCarga] = []
        self.fichas: list = []

    # ---------- Acciones

    def agregar_accion(self, tiempo: int, accion: AccionDTO) -> None:
        """Anexa la acción vigente número len(acciones) + 1. O(1) amortizado."""
        self.acciones.append(AccionVigente(tiempo, accion))

    def accion(self, numero: int) -> AccionVigente:
        """La acción número `numero` (desde 1). Se asume ya validada con validar_accion."""
        return self.acciones[numero - 1]

    def ubicar_accion_por_tiempo(self, t: int) -> int:
        """El número (desde 1) de la última acción con tiempo <= t, o 0 si ninguna. O(log A)."""
        return ultimo_menor_o_igual(self.acciones, t, lambda a: a.tiempo) + 1

    # ---------- Puntos de control

    def necesita_punto(self, acciones_completadas: int) -> bool:
        """True si hay que tomar un punto ahora: no hay ninguno, o pasaron K acciones desde el último. O(1).

        Así nunca hay más de K acciones entre dos puntos consecutivos (FR-416)."""
        if not self.puntos:
            return True
        return acciones_completadas - self.puntos[-1].acciones_completadas >= self.k

    def agregar_punto(self, punto: PuntoControl) -> None:
        """Anexa un punto de control al final. O(1) amortizado."""
        self.puntos.append(punto)

    def ubicar_punto(self, acciones: int) -> PuntoControl | None:
        """El último punto con acciones_completadas <= `acciones`, o None si no hay. O(log P)."""
        posicion = ultimo_menor_o_igual(self.puntos, acciones, lambda p: p.acciones_completadas)
        return self.puntos[posicion] if posicion >= 0 else None

    # ---------- Registros de carga y fichas (R3, hallazgo H-1)

    def registrar_carga(self, ordinal: int, sala: SalaDTO) -> None:
        """Anexa el registro de carga de la sala si todavía no estaba (a lo sumo uno por sala)."""
        for registro in self.cargas:
            if registro.sala.id == sala.id:
                return
        self.cargas.append(RegistroCarga(ordinal, sala))

    def registrar_ficha(self, ficha: object) -> None:
        """Guarda la ficha del catálogo si no había otra con el mismo id (búsqueda lineal: son pocas)."""
        if self.ficha(ficha.id) is None:
            self.fichas.append(ficha)

    def ficha(self, id_ficha: str) -> object | None:
        """La ficha guardada con ese id, o None."""
        for ficha in self.fichas:
            if ficha.id == id_ficha:
                return ficha
        return None

    # ---------- Validación de rango de las consultas (FR-409)

    def validar_instante(self, t: object, reloj_actual: int) -> None:
        """Lanza ValueError, con el motivo y el rango válido, si t no es un entero entre 0 y el reloj actual."""
        if not _es_entero(t):
            raise ValueError(f"El instante debe ser un entero entre 0 y {reloj_actual} (se recibió {t!r})")
        if t < 0:
            raise ValueError(f"El instante no puede ser negativo: debe estar entre 0 y {reloj_actual} (se pidió {t})")
        if t > reloj_actual:
            raise ValueError(f"El instante {t} es posterior al reloj actual: debe estar entre 0 y {reloj_actual}")

    def validar_accion(self, k: object) -> None:
        """Lanza ValueError, con el motivo y el rango válido, si k no es un entero entre 1 y las acciones vigentes."""
        cantidad = len(self.acciones)
        if cantidad == 0:
            raise ValueError("Todavía no hay acciones del jugador que consultar")
        if not _es_entero(k):
            raise ValueError(f"La acción debe ser un entero entre 1 y {cantidad} (se recibió {k!r})")
        if k < 1 or k > cantidad:
            raise ValueError(f"La acción {k} no existe: debe estar entre 1 y {cantidad}")
