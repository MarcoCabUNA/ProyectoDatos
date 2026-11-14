"""
ServicioLineaTiempo (Servicios, Integrante 3, feature 004): alimenta y consulta la línea de tiempo de la partida.

    ejecutar(contexto, accion)               hace la acción por ServicioAccionJugador y, según lo que pasó, la anota en
                                             la línea (FR-413) y toma un punto de control si toca (FR-416)
    tomar_punto(contexto)                    copia completa del estado vivo (PartidaGuardada.guardar) como punto de control
    consultar_por_instante(contexto, t)      ResumenHistoriaDTO del estado en el instante t     (`historia <t>`)
    consultar_por_accion(contexto, k)        ResumenHistoriaDTO justo antes de la acción k      (`historia #k`)

Cómo sabe `ejecutar` qué pasó, sin tocar ServicioAccionJugador: compara `jugador.acciones` antes y después.
    +1   la acción se hizo           -> agregar_accion(reloj de la decisión, acción) y, si toca, un punto de control
    sin cambio                        -> la acción fue rechazada: no se registra nada (FR-407)
    -1   se leyó un pergamino         -> se trata en T030 (fase 4); hasta entonces no se registra nada
Las consultas NO cambian la partida: no consumen tiempo, no cuentan como acción, no se anexan a partida.log y no
tocan el historial de retroceso (FR-407, FR-408). La validación del rango de t y de k es regla de negocio y vive en
Logic/LineaTiempo (ValueError con el rango válido); aquí solo se propaga.

Si el contexto no tiene línea (contexto armado a mano), `ejecutar` es igual a ServicioAccionJugador.ejecutar.
"""
from DTO.AccionDTO import AccionDTO
from DTO.EstadoJuegoDTO import EstadoJuegoDTO
from DTO.ResumenHistoriaDTO import ResumenHistoriaDTO
from Logic.LineaTiempo import PuntoControl
from Logic.PartidaGuardada import PartidaGuardada
from Service.ArmadorResumen import ArmadorResumen
from Service.ContextoPartida import ContextoPartida
from Service.ReconstructorEstado import ReconstructorEstado
from Service.ServicioAccionJugador import ServicioAccionJugador


class ServicioLineaTiempo:

    def __init__(self) -> None:
        self._acciones = ServicioAccionJugador()

    def ejecutar(self, contexto: ContextoPartida, accion: AccionDTO) -> EstadoJuegoDTO:
        """Ejecuta la acción (como ServicioAccionJugador) y mantiene la línea de tiempo al día."""
        linea = contexto.linea
        if linea is None:
            return self._acciones.ejecutar(contexto, accion)
        antes = contexto.jugador.acciones
        tiempo = contexto.motor.reloj                    # el reloj de la decisión: el estado "justo antes" de la acción
        estado = self._acciones.ejecutar(contexto, accion)
        despues = contexto.jugador.acciones
        if despues == antes + 1:
            linea.agregar_accion(tiempo, accion)
            if linea.necesita_punto(despues):
                self.tomar_punto(contexto)
        # despues == antes - 1: el pergamino (T030). Sin cambio: acción rechazada, nada que registrar.
        return estado

    @staticmethod
    def tomar_punto(contexto: ContextoPartida) -> None:
        """Agrega a la línea un punto de control: copia completa del estado vivo, hecha a mano (sin `copy`)."""
        partida, salas = PartidaGuardada.guardar(contexto.motor, contexto.cripta,
                                                 contexto.resolvedor.version_catalogo(), contexto.semilla)
        contexto.linea.agregar_punto(PuntoControl(contexto.jugador.acciones, partida, salas))

    def consultar_por_instante(self, contexto: ContextoPartida, t: int) -> ResumenHistoriaDTO:
        """`historia <t>`: el resumen del estado en el instante t. ValueError si t no está entre 0 y el reloj actual."""
        contexto.linea.validar_instante(t, contexto.motor.reloj)
        motor = ReconstructorEstado(contexto).hasta_instante(t)
        return ArmadorResumen.armar(motor, contexto.esqueleto, t, False, False, getattr(motor, "mapa_conocido", None))

    def consultar_por_accion(self, contexto: ContextoPartida, k: int) -> ResumenHistoriaDTO:
        """`historia #k`: el resumen justo antes de la acción k. ValueError si k no está entre 1 y las acciones hechas."""
        contexto.linea.validar_accion(k)
        motor = ReconstructorEstado(contexto).hasta_accion(k)
        return ArmadorResumen.armar(motor, contexto.esqueleto, k, True, False, getattr(motor, "mapa_conocido", None))
