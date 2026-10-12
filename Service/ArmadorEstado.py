"""
ArmadorEstado (Servicios, Integrante 3): convierte el estado vivo del juego en DTOs para la Vista.

Es la única pieza que sabe cómo se arma un EstadoJuegoDTO y un InventarioDTO. La Vista nunca ve
objetos vivos de Lógica (Actor, Inventario...), solo estos DTOs.

La sala que se entrega es una COPIA del esqueleto (SalaDTO) con el estado ACTUAL: las puertas con
su estado de ahora (el esqueleto trae el inicial) y los objetos que hay en el suelo ahora. Sus listas de
enemigos y trampas van vacías: lo vivo está en EstadoJuegoDTO.enemigos (ver _sala_con_estado_actual).
Las fichas del suelo se piden con contar_acierto=False: armar el estado ocurre en cada turno y solo MUESTRA,
así que no debe inflar los aciertos de caché del reporte (§5.1); un fallo sí cuenta, porque implica trabajo real.
El resultado de la acción es:
    - el mensaje de rechazo, si la acción no se pudo hacer (no consume tiempo);
    - "victoria" o "derrota" si la partida terminó;
    - None en cualquier otro caso.
"""
from dataclasses import replace

from DTO.EstadoJuegoDTO import EstadoJuegoDTO
from DTO.InventarioDTO import InventarioDTO


class ArmadorEstado:

    def armar_estado(self, contexto, resultado: str | None = None) -> EstadoJuegoDTO:
        motor = contexto.motor
        id_sala = contexto.jugador.Sala_Actual
        sala_viva = contexto.mazmorra.sala(id_sala)
        return EstadoJuegoDTO(
            sala=self._sala_con_estado_actual(contexto, id_sala),
            jugador=contexto.jugador.a_dto(),
            enemigos=[enemigo.a_dto() for enemigo in contexto.mazmorra.enemigos_vivos(id_sala)],
            objetos_suelo=[contexto.resolvedor.ficha(id_objeto, contar_acierto=False)
                           for id_objeto in sala_viva.objetos],
            efectos=motor.efectos.visibles(contexto.jugador),
            inventario=self.armar_inventario(contexto, contexto.criterio_vista),
            mensajes=contexto.mensajes.a_array(),
            reloj=motor.reloj,
            terminado=motor.terminado,
            resultado=self._resultado(motor, resultado),
        )

    def armar_inventario(self, contexto, criterio: str | None) -> InventarioDTO:
        """Foto del inventario: en su orden real (criterio None) o en una vista ordenada."""
        inventario = contexto.inventario
        objetos = inventario.vista_ordenada(criterio)
        if criterio is None:
            cursor = inventario.posicion_cursor()
        else:
            cursor = self._posicion_en(objetos, inventario.objeto_actual())
        arma, armadura = inventario.arma_equipada(), inventario.armadura_equipada()
        return InventarioDTO(
            objetos=objetos,
            cursor=cursor,
            capacidad=inventario.cantidad(),
            capacidad_maxima=inventario.capacidad_maxima(),
            arma_equipada=None if arma is None else arma.id,
            armadura_equipada=None if armadura is None else armadura.id,
            criterio=criterio,
        )

    # ---- interno ----

    def _sala_con_estado_actual(self, contexto, id_sala):
        base = contexto.esqueleto.obtener_sala(id_sala)
        viva = contexto.mazmorra.sala(id_sala)
        salidas = list(base.salidas)
        for direccion in range(len(salidas)):
            if salidas[direccion] is not None and viva.salidas[direccion] is not None:
                salidas[direccion] = replace(salidas[direccion], cerrada=viva.salidas[direccion].cerrada)
        # enemigos y trampas quedan VACÍOS a propósito: el SalaDTO del esqueleto puede traer el contenido INICIAL
        # (ratas con toda su vida, trampas armadas...), que ya no es cierto. Los enemigos vivos van aparte, en
        # EstadoJuegoDTO.enemigos, y las trampas no se muestran.
        return replace(base, salidas=salidas, objetos=list(viva.objetos), enemigos=[], trampas=[],
                       contenido_cargado=contexto.mazmorra.contenido_cargado(id_sala))

    @staticmethod
    def _resultado(motor, resultado):
        if resultado is not None:
            return resultado
        if motor.terminado:
            return "victoria" if motor.victoria else "derrota"
        return None

    @staticmethod
    def _posicion_en(objetos, actual) -> int:
        """Índice de 'actual' dentro de una vista ordenada (0 si no está o no hay objeto actual)."""
        for i in range(len(objetos)):
            if objetos[i] is actual:
                return i
        return 0