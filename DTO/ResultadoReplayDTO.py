"""
ResultadoReplayDTO (Integrante 3): lo que entrega ServicioReplay al terminar de reproducir un log.

    encabezado               con qué se jugó: cripta, versiones y semilla (EncabezadoReplayDTO, de Datos)
    estado_final             el EstadoJuegoDTO en que terminó la partida reproducida
    acciones_reproducidas    cuántas acciones del log se ejecutaron
    ultima_linea_descartada  True si la última línea del log estaba a medio escribir y se ignoró
                             (el programa se cerró mientras escribía): avisar al usuario

Regla de los DTOs: solo transportan datos.
"""
from dataclasses import dataclass

from DTO.EstadoJuegoDTO import EstadoJuegoDTO
from DTO.ReplayDTO import EncabezadoReplayDTO


@dataclass(frozen=True)
class ResultadoReplayDTO:
    encabezado: EncabezadoReplayDTO
    estado_final: EstadoJuegoDTO
    acciones_reproducidas: int
    ultima_linea_descartada: bool = False