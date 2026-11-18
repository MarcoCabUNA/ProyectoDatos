"""
ReporteResolubilidadDTO (Integrante 2, feature 003): el resultado de la verificación de resolubilidad, para la
interfaz (integrante 3). Contrato: specs/003-resolubilidad/contracts/contrato-reporte-resolubilidad.md.

Lo arma Lógica (VerificadorResolubilidad) o, si la verificación no concluyó, Servicios. La interfaz no calcula
nada: todas las listas llegan completas y ya ordenadas. Solo transporta datos.
Regla de cambios: un campo nuevo va AL FINAL de su clase y CON valor por defecto.
"""
from dataclasses import dataclass, field

from DTO.UbicacionLlaveDTO import UbicacionLlaveDTO

RESOLUBLE = "resoluble"
NO_RESOLUBLE = "no_resoluble"
NO_CONCLUYO = "no_concluyo"


@dataclass(frozen=True)
class PuertaLlaveDTO:
    """Una cara cerrada, vista desde la sala de la que sale. llave = None ⇒ «sin llave: no se puede abrir»."""
    sala_origen: int     # en la frontera: la sala alcanzable
    direccion: int       # índice en DTO/Direcciones.DIRECCIONES (0 N, 1 S, 2 E, 3 O)
    sala_destino: int
    llave: str | None    # la llave que pide ESA cara


@dataclass(frozen=True)
class LlaveNoObtenibleDTO:
    """Una llave no obtenible con todas sus ubicaciones distintas, en orden. Lista vacía ⇒ «sin ubicación»."""
    id: str
    ubicaciones: list[UbicacionLlaveDTO]


@dataclass(frozen=True)
class PasoCicloDTO:
    """«llave está en sala → la puerta X requiere la siguiente». puerta.llave = llave del paso siguiente."""
    llave: str
    ubicacion: UbicacionLlaveDTO   # la ubicación usada (menor nivel; si empatan, la primera de FR-309)
    puerta: PuertaLlaveDTO         # la única puerta que la bloquea (FR-310)


@dataclass(frozen=True)
class DependienteCicloDTO:
    """Una llave no obtenible que no está en el ciclo pero cuya cadena llega a él. depende_de es una llave del ciclo."""
    llave: str
    ubicacion: UbicacionLlaveDTO
    puerta: PuertaLlaveDTO
    depende_de: str


@dataclass(frozen=True)
class CicloLlavesDTO:
    """Un ciclo: empieza por la llave de menor id; una llave sola es un ciclo de un paso. Dependientes por id."""
    pasos: list[PasoCicloDTO]
    dependientes: list[DependienteCicloDTO]


@dataclass(frozen=True)
class ReporteResolubilidadDTO:
    """
    Veredicto y reporte. Con RESOLUBLE solo orden_llaves (campos 6 a 10 vacíos); con NO_RESOLUBLE las listas del
    reporte y, por FR-322, motivo; con NO_CONCLUYO solo mensaje (campos 5 a 9 vacíos: no hay veredicto).
    """
    id_cripta: str
    veredicto: str
    version_cripta: str | None = None
    llave_salida: str | None = None
    orden_llaves: list[str] = field(default_factory=list)
    llaves_no_obtenibles: list[LlaveNoObtenibleDTO] = field(default_factory=list)
    frontera: list[PuertaLlaveDTO] = field(default_factory=list)
    ciclos: list[CicloLlavesDTO] = field(default_factory=list)
    motivo: str | None = None
    mensaje: str | None = None
