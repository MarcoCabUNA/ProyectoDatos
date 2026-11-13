"""
ResumenHistoriaDTO (Integrante 3, feature 004): lo que muestra una consulta de la línea de tiempo.

Es la vista de SOLO LECTURA del estado de la partida en un instante pasado (FR-405). La arma
Service/ArmadorResumen.py sobre un Motor aparte; la partida viva no se toca.

    reloj               el reloj del resumen, según FR-405: el instante pedido; para `historia #k`, el instante de
                        la decisión k; si la partida terminó antes, el reloj del final
    sala_id, sala_nombre   la sala del jugador
    jugador             ActorDTO con vida, vida máxima, ataque, defensa y velocidad
    inventario          ids de los objetos en el orden real. SIN cursor (FR-406)
    arma_equipada, armadura_equipada   id equipado, o None
    efectos             efectos activos del jugador (EfectoDTO: tipo y duración restante)
    enemigos            los enemigos de esa sala (ActorDTO), con su vida
    mapa_conocido       el mapa conocido (spec 002), o None si todavía no existe
    terminada_antes     True si `--replay ... --hasta` pidió un instante posterior al final (FR-412)
    instante_pedido     el t pedido, o la acción k, según la consulta

No hay campo de mensajes (FR-406).

Regla de los DTOs: solo transportan datos.
"""
from dataclasses import dataclass

from DTO.ActorDTO import ActorDTO
from DTO.EfectoDTO import EfectoDTO


@dataclass(frozen=True)
class ResumenHistoriaDTO:
    reloj: int
    sala_id: int
    sala_nombre: str
    jugador: ActorDTO
    inventario: list[str]
    arma_equipada: str | None
    armadura_equipada: str | None
    efectos: list[EfectoDTO]
    enemigos: list[ActorDTO]
    mapa_conocido: object | None = None
    terminada_antes: bool = False
    instante_pedido: int | None = None
