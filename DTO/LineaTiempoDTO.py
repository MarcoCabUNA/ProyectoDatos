"""
LineaTiempoDTO (Integrante 3, feature 004): la línea de tiempo tal como se GUARDA en el archivo de partida.

Contrato con el integrante 2 (Derek): specs/004-linea-tiempo/contracts/contrato-linea-tiempo.md §1.
PartidaGuardadaDTO recibe un campo nuevo AL FINAL, `linea: LineaTiempoGuardadaDTO | None = None`
(tarea T002, de Derek); este archivo define lo que va dentro.

LineaTiempoGuardadaDTO lleva exactamente cinco cosas (no hay marcadores de pergamino: tras un pergamino la
línea toma un punto de control nuevo, que se guarda como cualquier otro, research.md R4):
    k         cada cuántas acciones se toma un punto de control (>= 1)
    acciones  las acciones VIGENTES del jugador, cada una con el tiempo de su decisión (AccionGuardadaDTO)
    puntos    los puntos de control (PuntoControlGuardadoDTO): el estado completo tras N acciones
    cargas    el contenido inicial de cada sala que la partida ya cargó, con su ordinal (RegistroCargaGuardadoDTO)
    fichas    las fichas del catálogo que la partida ya pidió: enemigos, trampas y objetos, cada una una vez

Al LEER (desde_diccionario) se validan estas restricciones y se lanza ValueError si alguna falla:
    k >= 1; acciones en orden creciente de tiempo; puntos en orden estrictamente creciente de
    acciones_completadas, cada una entre 0 y la cantidad de acciones, y a lo sumo k acciones entre dos puntos
    consecutivos; el punto de partida.linea es siempre None (la línea no se anida dentro de sí misma).

a_diccionario / desde_diccionario sirven para comparar el JSON contra el binario (§4.10).

Regla de los DTOs: solo transportan datos. Las colecciones son arrays (list).
"""
from dataclasses import dataclass, field

from DTO.FichaEnemigoDTO import FichaEnemigoDTO
from DTO.FichaTrampaDTO import FichaTrampaDTO
from DTO.ObjetoDTO import ObjetoDTO, es_clase_objeto
from DTO.PartidaGuardadaDTO import PartidaGuardadaDTO, SalaGuardadaDTO
from DTO.SalaDTO import SalaDTO


@dataclass(frozen=True)
class AccionGuardadaDTO:
    """Una acción vigente: el tiempo de la decisión y la acción (los mismos campos de AccionDTO)."""
    tiempo: int
    tipo: str
    direccion: int | None = None
    objetivo: str | None = None
    objeto: str | None = None

    @classmethod
    def desde_diccionario(cls, d: dict) -> "AccionGuardadaDTO":
        return cls(d["tiempo"], d["tipo"], d.get("direccion"), d.get("objetivo"), d.get("objeto"))

    def a_diccionario(self) -> dict:
        return {"tiempo": self.tiempo, "tipo": self.tipo, "direccion": self.direccion,
                "objetivo": self.objetivo, "objeto": self.objeto}


@dataclass(frozen=True)
class PuntoControlGuardadoDTO:
    """Un punto de control: el estado global (con el azar) y un bloque por sala, tras N acciones."""
    acciones_completadas: int
    partida: PartidaGuardadaDTO            # con linea=None
    salas: list[SalaGuardadaDTO] = field(default_factory=list)

    @classmethod
    def desde_diccionario(cls, d: dict) -> "PuntoControlGuardadoDTO":
        return cls(d["acciones_completadas"], PartidaGuardadaDTO.desde_diccionario(d["partida"]),
                   [SalaGuardadaDTO.desde_diccionario(s) for s in d["salas"]])

    def a_diccionario(self) -> dict:
        return {"acciones_completadas": self.acciones_completadas, "partida": self.partida.a_diccionario(),
                "salas": [s.a_diccionario() for s in self.salas]}


@dataclass(frozen=True)
class RegistroCargaGuardadoDTO:
    """El contenido inicial que Data entregó para una sala y las acciones vigentes que llevaba la partida."""
    ordinal: int
    sala: SalaDTO

    @classmethod
    def desde_diccionario(cls, d: dict) -> "RegistroCargaGuardadoDTO":
        return cls(d["ordinal"], SalaDTO.desde_persistido(d["sala"]))

    def a_diccionario(self) -> dict:
        return {"ordinal": self.ordinal, "sala": self.sala.a_diccionario()}


def _ficha_desde_diccionario(d: dict):
    """Elige el DTO del catálogo según 'clase' (lo mismo que hace Data, sin importar Data)."""
    clase = d["clase"]
    if clase == "enemigo":
        return FichaEnemigoDTO.desde_diccionario(d)
    if clase == "trampa":
        return FichaTrampaDTO.desde_diccionario(d)
    if es_clase_objeto(clase):
        return ObjetoDTO.desde_diccionario(d)
    raise ValueError(f"clase de ficha desconocida en la línea de tiempo: {clase!r}")


def _es_entero(valor: object) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


@dataclass(frozen=True)
class LineaTiempoGuardadaDTO:
    k: int
    acciones: list[AccionGuardadaDTO] = field(default_factory=list)
    puntos: list[PuntoControlGuardadoDTO] = field(default_factory=list)
    cargas: list[RegistroCargaGuardadoDTO] = field(default_factory=list)
    fichas: list = field(default_factory=list)       # FichaEnemigoDTO, FichaTrampaDTO u ObjetoDTO

    def validar(self) -> None:
        """Lanza ValueError si no se cumple alguna restricción de la línea guardada (ver el encabezado)."""
        if not _es_entero(self.k) or self.k < 1:
            raise ValueError(f"línea de tiempo: k debe ser un entero >= 1 (se leyó {self.k!r})")
        for anterior, siguiente in zip(self.acciones, self.acciones[1:]):
            if siguiente.tiempo <= anterior.tiempo:
                raise ValueError("línea de tiempo: las acciones deben estar en orden creciente de tiempo")
        cantidad = len(self.acciones)
        previo: int | None = None
        for punto in self.puntos:
            hechas = punto.acciones_completadas
            if not _es_entero(hechas) or hechas < 0 or hechas > cantidad:
                raise ValueError(f"línea de tiempo: un punto de control tiene {hechas!r} acciones completadas, "
                                 f"fuera del rango 0 a {cantidad}")
            if previo is not None:
                if hechas <= previo:
                    raise ValueError("línea de tiempo: los puntos deben estar en orden estrictamente creciente "
                                     "de acciones completadas")
                if hechas - previo > self.k:
                    raise ValueError(f"línea de tiempo: hay más de k = {self.k} acciones entre dos puntos "
                                     f"consecutivos ({previo} y {hechas})")
            previo = hechas
            if getattr(punto.partida, "linea", None) is not None:
                raise ValueError("línea de tiempo: el estado de un punto de control no puede traer otra línea")

    @classmethod
    def desde_diccionario(cls, d: dict) -> "LineaTiempoGuardadaDTO":
        linea = cls(d["k"],
                    [AccionGuardadaDTO.desde_diccionario(a) for a in d["acciones"]],
                    [PuntoControlGuardadoDTO.desde_diccionario(p) for p in d["puntos"]],
                    [RegistroCargaGuardadoDTO.desde_diccionario(c) for c in d["cargas"]],
                    [_ficha_desde_diccionario(f) for f in d["fichas"]])
        linea.validar()
        return linea

    def a_diccionario(self) -> dict:
        return {"k": self.k,
                "acciones": [a.a_diccionario() for a in self.acciones],
                "puntos": [p.a_diccionario() for p in self.puntos],
                "cargas": [c.a_diccionario() for c in self.cargas],
                "fichas": [f.a_diccionario() for f in self.fichas]}
