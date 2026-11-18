"""
ArmadorResumen (Servicios, Integrante 3, feature 004): arma el ResumenHistoriaDTO de un Motor (FR-405, FR-406).

Solo LEE el motor (el reconstruido, o el vivo en las pruebas); no lo modifica. El resumen trae la sala, el jugador, el
inventario en su orden real (ids; SIN cursor), las armas y armaduras equipadas, los efectos del jugador y los enemigos
vivos de su sala. No trae mensajes (FR-406).

El `reloj` del resumen (FR-405):
    historia <t>    el instante pedido t
    historia #k     el instante de la decisión k: el reloj del motor, que está justo antes de ella
    si la partida terminó ANTES del instante pedido, el reloj del final

`mapa_conocido`: el MapaConocidoDTO del motor (`motor.mapa.a_dto()`), o None si quien arma no lo da. Es inmutable y
`a_dto()` arma uno nuevo en cada llamada, así que el resumen lo lleva tal cual, sin copiarlo.
"""
from DTO.ResumenHistoriaDTO import ResumenHistoriaDTO
from Logic.motorJuego import Motor


class ArmadorResumen:

    @staticmethod
    def armar(motor: Motor, esqueleto, instante_pedido: int, es_accion: bool, terminada_antes: bool,
              mapa_conocido: object | None = None) -> ResumenHistoriaDTO:
        """El resumen del estado del `motor`.

        `instante_pedido` es t, o el número k si `es_accion`. `terminada_antes` lo indica quien consulta
        (`--replay ... --hasta` con t posterior al final, FR-412). `mapa_conocido` es el del estado, si existe."""
        jugador = motor.jugador
        id_sala = jugador.Sala_Actual
        arma, armadura = motor.inventario.arma_equipada(), motor.inventario.armadura_equipada()
        return ResumenHistoriaDTO(
            reloj=ArmadorResumen._reloj(motor, instante_pedido, es_accion),
            sala_id=id_sala,
            sala_nombre=esqueleto.obtener_sala(id_sala).nombre,
            jugador=jugador.a_dto(),
            inventario=[objeto.id for objeto in motor.inventario.objetos()],
            arma_equipada=None if arma is None else arma.id,
            armadura_equipada=None if armadura is None else armadura.id,
            efectos=motor.efectos.visibles(jugador),
            enemigos=[enemigo.a_dto() for enemigo in motor.mazmorra.enemigos_vivos(id_sala)],
            mapa_conocido=mapa_conocido,
            terminada_antes=terminada_antes,
            instante_pedido=instante_pedido,
        )

    @staticmethod
    def _reloj(motor: Motor, instante_pedido: int, es_accion: bool) -> int:
        if es_accion:
            return motor.reloj                                  # el instante de la decisión k
        if motor.terminado and motor.reloj < instante_pedido:
            return motor.reloj                                  # la partida terminó antes: el reloj del final
        return instante_pedido
