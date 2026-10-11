"""
DTOs de la bitácora de partida para --replay (Integrante 2, enunciado §4.11).

EncabezadoReplayDTO -> lo que exige el encabezado del log: id de cripta, versión de cripta,
                       versión de catálogo y semilla.
PartidaReplayDTO    -> lo que devuelve BitacoraReplayIO.leer(): el encabezado y las acciones
                       en el orden en que se jugaron.

Cómo se llenan (Servicios, al empezar una partida):
    EncabezadoReplayDTO(id_cripta=cripta.id, version_cripta=cripta.version,
                        version_catalogo=resolvedor.version_catalogo(), semilla=semilla)

Regla de los DTOs: solo transportan datos.
"""
from dataclasses import dataclass

from DTO.AccionDTO import AccionDTO


@dataclass(frozen=True)
class EncabezadoReplayDTO:
    id_cripta: str
    version_cripta: str
    version_catalogo: str
    semilla: int


@dataclass(frozen=True)
class PartidaReplayDTO:
    encabezado: EncabezadoReplayDTO
    acciones: list[AccionDTO]             # array, en el orden en que se jugaron
    # True si la última línea del archivo estaba a medio escribir (el programa se cerró mientras
    # escribía) y por eso se descartó. Servicios puede avisarlo al reproducir.
    ultima_linea_descartada: bool = False