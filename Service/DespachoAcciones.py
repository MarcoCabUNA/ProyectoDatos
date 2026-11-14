"""
DespachoAcciones (Servicios, Integrante 3, feature 004): traduce un AccionDTO a la llamada del Motor.

Es la misma tabla de ServicioAccionJugador._ejecutar_en_el_motor, pero para RECONSTRUIR un estado pasado en un
Motor aparte (research.md R2). Por eso, a diferencia del servicio de acciones:
  - NO anexa nada a la bitácora (partida.log),
  - NO sincroniza los usos de la caché del catálogo,
  - NO le pide nada a Data: el contenido de una sala y las fichas salen del proveedor `contexto_datos`
    (que la línea de tiempo respalda con sus registros de carga y sus fichas, R3),
  - NO acepta `retroceder` ni usar un pergamino: la línea nunca contiene esas acciones (FR-413) y
    pedirlo es un error del que llama (ValueError).

No avanza el reloj hasta la siguiente decisión: quien reconstruye llama a `motor.avanzar_hasta_jugador()`
después de una acción aceptada ("ok"), como hace el servicio de acciones.

`contexto_datos` es cualquier objeto con dos métodos:
    ficha(id_ficha)  -> la ficha del catálogo (objeto, enemigo o trampa)
    sala(id_sala)    -> el SalaDTO con el contenido inicial de esa sala
El despacho repite la correspondencia acción -> método del motor a propósito (Principio III: no se refactoriza
ServicioAccionJugador); una prueba compara los dos para todas las acciones, así que una firma cambiada la rompe.
"""
from DTO.AccionDTO import AccionDTO
from Logic.motorJuego import Motor

CLASE_PERGAMINO = Motor.PERGAMINO


class DespachoAcciones:
    """Ejecuta una acción del jugador sobre un Motor sin tocar Data, la bitácora ni la caché viva."""

    def ejecutar(self, motor: Motor, contexto_datos: object, accion: AccionDTO) -> str:
        """Llama al método del motor que corresponde y devuelve su código ("ok", "sin_salida", ...).

        Lanza ValueError si la acción es `retroceder` o usar un pergamino."""
        tipo = accion.tipo
        if tipo == "mover":
            if not self._direccion_valida(accion.direccion):
                return "direccion_invalida"
            self._cargar_destino_si_falta(motor, contexto_datos, accion.direccion)
            return motor.mover_jugador(accion.direccion)
        if tipo == "abrir":
            if not self._direccion_valida(accion.direccion):
                return "direccion_invalida"
            return motor.abrir_puerta(accion.direccion, motor.inventario.tiene_objeto)
        if tipo == "atacar":
            if accion.objetivo is None:
                return "falta_objetivo"
            return motor.atacar_enemigo(accion.objetivo)
        if tipo == "esperar":
            return motor.esperar()
        if tipo == "retroceder":
            raise ValueError("la línea de tiempo no contiene la acción 'retroceder' (FR-413)")
        if tipo in ("recoger", "soltar", "equipar", "usar"):
            if accion.objeto is None:
                return "falta_objeto"
            if tipo == "recoger":
                return motor.recoger(accion.objeto, contexto_datos.ficha)
            if tipo == "soltar":
                return motor.soltar(accion.objeto)
            if tipo == "equipar":
                return motor.equipar(accion.objeto)
            if self._es_pergamino(motor, accion.objeto):
                raise ValueError("la línea de tiempo no contiene la lectura de un pergamino (FR-413)")
            return motor.usar(accion.objeto)
        return "accion_desconocida"

    @staticmethod
    def _direccion_valida(direccion: object) -> bool:
        """True si es un entero de 0 a 3 (N, S, E, O); un bool no cuenta."""
        return isinstance(direccion, int) and not isinstance(direccion, bool) and 0 <= direccion <= 3

    @staticmethod
    def _cargar_destino_si_falta(motor: Motor, contexto_datos: object, direccion: int) -> None:
        """El motor no deja entrar a una sala sin contenido: se lo da el proveedor (la línea), nunca Data."""
        salida = motor.mazmorra.salida(motor.jugador.Sala_Actual, direccion)
        if salida is None or salida.cerrada or motor.mazmorra.contenido_cargado(salida.destino):
            return
        motor.mazmorra.cargar_contenido(contexto_datos.sala(salida.destino), contexto_datos.ficha)

    @staticmethod
    def _es_pergamino(motor: Motor, id_objeto: str) -> bool:
        """True si el objeto del inventario con ese id es un pergamino de retroceso."""
        for objeto in motor.inventario.objetos():
            if objeto.id == id_objeto:
                return objeto.clase == CLASE_PERGAMINO
        return False
