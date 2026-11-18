"""ServicioIrA (Servicios, feature 002): el viaje de «ir a», un paso «mover» a la vez por la línea de tiempo."""
from dataclasses import replace

from DTO.AccionDTO import AccionDTO
from DTO.ViajeDTO import INTERRUMPIDO, PASO_RECHAZADO, SIN_RUTA, TERMINADA, InicioViajeDTO, PasoViajeDTO, ViajeDTO
from Logic import ViajeAutomatico
from Logic.GrafoMapaConocido import GrafoMapaConocido
from Logic.MapaConocido import MapaConocido
from Service.ArmadorEstado import ArmadorEstado
from Service.ContextoPartida import ContextoPartida
from Service.ServicioLineaTiempo import ServicioLineaTiempo


class ServicioIrA:
    """Inicia un viaje y da sus pasos; guarda solo el grafo del viaje en curso."""

    def __init__(self) -> None:
        self._acciones = ServicioLineaTiempo()
        self._armador = ArmadorEstado()
        # Solo un caché: el grafo del viaje en curso y el mapa del que salió. El viaje en sí vive en el ViajeDTO.
        self._grafo: GrafoMapaConocido | None = None

    def iniciar(self, contexto: ContextoPartida, nombre: str) -> InicioViajeDTO:
        """Resuelve el destino por nombre y devuelve el viaje nuevo, o los motivos por los que no empieza."""
        self._grafo = None
        codigo, destino = ViajeAutomatico.resolver_destino(contexto.motor.mapa, nombre, contexto.jugador.Sala_Actual)
        if codigo != ViajeAutomatico.OK:
            return InicioViajeDTO(None, [codigo])
        nombre_real = contexto.mazmorra.sala(destino).nombre
        return InicioViajeDTO(ViajeDTO(destino, nombre_real, 0, contexto.jugador.acciones), [])

    def anotar(self, contexto: ContextoPartida, texto: str) -> None:
        """Agrega un mensaje del viaje con el reloj actual."""
        contexto.mensajes.agregar(f"[t={contexto.motor.reloj}] {texto}")

    def dar_paso(self, contexto: ContextoPartida, viaje: ViajeDTO) -> PasoViajeDTO:
        """Da un paso del viaje como una acción «mover» ordinaria y dice si el viaje sigue o por qué se detiene."""
        motor = contexto.motor
        jugador = contexto.jugador
        if jugador.acciones != viaje.acciones_esperadas:
            return self._parar(contexto, [INTERRUMPIDO])
        if motor.terminado:
            return self._parar(contexto, [TERMINADA])
        grafo = self._grafo_del_mapa(motor.mapa)
        paso = ViajeAutomatico.decidir_paso(grafo, motor.mapa, motor.mazmorra, jugador.Sala_Actual, viaje.destino)
        if paso is None:
            return self._parar(contexto, [SIN_RUTA])
        direccion = paso[0]
        acciones_antes = jugador.acciones
        danio_antes = jugador.danio_recibido
        estado = self._acciones.ejecutar(contexto, AccionDTO("mover", direccion=direccion))
        if jugador.acciones != acciones_antes + 1:
            return PasoViajeDTO(None, [PASO_RECHAZADO], estado)
        if viaje.pasos_dados == 0 and contexto.bitacora is not None:
            contexto.bitacora.anexar_comentario(f"ir a {viaje.nombre_destino}")
        motivos = ViajeAutomatico.motivos_de_parada(
            jugador.Sala_Actual, viaje.destino,
            len(motor.mazmorra.enemigos_vivos(jugador.Sala_Actual)) > 0,
            jugador.danio_recibido > danio_antes,
            motor.terminado)
        if len(motivos) > 0:
            return PasoViajeDTO(None, motivos, estado)
        return PasoViajeDTO(replace(viaje, pasos_dados=viaje.pasos_dados + 1, acciones_esperadas=jugador.acciones),
                            [], estado)

    def _grafo_del_mapa(self, mapa: MapaConocido) -> GrafoMapaConocido:
        """El grafo guardado si salió de este mapa; si no, uno nuevo."""
        if self._grafo is None or self._grafo.mapa is not mapa:
            self._grafo = GrafoMapaConocido(mapa)
        return self._grafo

    def _parar(self, contexto: ContextoPartida, motivos: list[str]) -> PasoViajeDTO:
        """Termina el viaje sin dar un paso, con los motivos y el estado actual."""
        return PasoViajeDTO(None, motivos, self._armador.armar_estado(contexto))
