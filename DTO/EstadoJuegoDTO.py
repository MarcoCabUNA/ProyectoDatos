"""
EstadoJuegoDTO (Integrante 3): to-do lo que la Vista necesita para mostrar un turno.

Lo arman ServicioAccionJugador y ServicioPartida después de cada acción, y lo imprime
VistaConsola.mostrar_estado(). No tiene métodos: solo se muestra.

Cruces con los DTO de los otros integrantes:
    sala          -> SalaDTO (integrante 2). Sus SalidaDTO traen el estado INICIAL de las
                     puertas; el estado vivo lo lleva Mazmorra en Lógica. Convención:
                     Servicios entrega aquí una copia de la sala (dataclasses.replace)
                     con las puertas en su estado actual.
    jugador       -> ActorDTO (integrante 1).
    enemigos      -> array de ActorDTO: los enemigos visibles.
    objetos_suelo -> array de ObjetoDTO (integrante 2). SalaDTO.objetos solo trae ids de
                     catálogo, así que Servicios los convierte en ObjetoDTO antes de armar
                     este DTO.
    efectos       -> array de EfectoDTO (integrante 1).
    inventario    -> InventarioDTO (integrante 3).

mensajes: los últimos 20, en orden cronológico. Se copian del buffer circular a un array;
la Vista no conoce el buffer.
resultado: "victoria", "derrota" o el mensaje de una acción rechazada; None si no aplica.
sala_inicial, sala_salida: ids de la sala de entrada y de la sala de salida de la cripta (CriptaDTO). La Vista los
compara con sala.id para elegir el fondo de la sala y la puerta final; None si no se conocen.
"""
from dataclasses import dataclass

from DTO.ActorDTO import ActorDTO
from DTO.EfectoDTO import EfectoDTO
from DTO.InventarioDTO import InventarioDTO
from DTO.ObjetoDTO import ObjetoDTO
from DTO.SalaDTO import SalaDTO


@dataclass(frozen=True)
class EstadoJuegoDTO:
    sala: SalaDTO
    jugador: ActorDTO
    enemigos: list[ActorDTO]
    objetos_suelo: list[ObjetoDTO]
    efectos: list[EfectoDTO]
    inventario: InventarioDTO
    mensajes: list[str]
    reloj: int
    terminado: bool = False
    resultado: str | None = None
    sala_inicial: int | None = None
    sala_salida: int | None = None