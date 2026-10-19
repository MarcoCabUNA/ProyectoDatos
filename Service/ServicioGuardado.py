"""
ServicioGuardado (Servicios, Integrante 3): guarda y carga una partida en el archivo binario (§4.10).

Une tres piezas que no se conocen entre sí:
    Lógica   PartidaGuardada pasa el motor vivo a DTOs y vuelve a armar un motor con ellos.
    Datos    GuardadoBinario escribe y lee esos DTOs (formato propio, versionado).
    Datos    BitacoraReplayIO sigue el log de replay de la partida cargada.

    guardar(contexto, ruta)               escribe la partida; no cambia nada de la partida ni de su log
    cargar(ruta, nombre_jugador)          devuelve un ContextoPartida listo para seguir jugando

Se guarda y se carga cuando el control lo tiene el jugador, es decir, entre dos acciones.

Qué NO se guarda (decisiones del equipo):
    - El historial de retroceso: una partida cargada empieza sin nada que deshacer, hasta su primera acción.
    - Los mensajes en pantalla: el buffer empieza con el aviso de que se cargó la partida.
    - El nombre del jugador (el DTO no tiene ese campo): lo indica quien carga, para la tabla de puntajes.

No se continúa "a ciegas" con datos distintos. cargar() lanza ErrorCarga, sin armar nada, si la cripta o
el catálogo disponibles ahora son de otra versión que los de la partida: el estado guardado apuntaría a
otras salas y fichas. Si el archivo no existe, está dañado o es de otro formato, se propaga el ErrorGuardado
de Datos tal cual.

El replay de una partida cargada no se pierde: el guardado recuerda su log y cuántas acciones tenía.
Al cargar se crea un log NUEVO con el mismo encabezado y esas primeras acciones (el anterior no se toca) y se
sigue anexando ahí; reproducirlo da toda la partida, desde el principio. Es lo último que se hace al cargar,
para no dejar un log suelto si algo falla antes. Si el log anterior se borró o es de otra partida, la carga
falla con el ErrorBitacora de Datos: una partida que no se puede reproducir rompería la garantía del replay.
"""
from Data import GuardadoBinario
from Data.BitacoraReplayIO import BitacoraReplayIO
from DTO.ReplayDTO import EncabezadoReplayDTO
from Estructuras.BufferCircular import BufferCircular
from Logic.PartidaGuardada import PartidaGuardada
from Service.ContextoPartida import ContextoPartida
from Service.ServicioPartida import MENSAJES_EN_PANTALLA, ServicioPartida
from Service.SincronizadorUsos import SincronizadorUsos


class ErrorCarga(ValueError):
    """La partida guardada no se puede continuar fielmente. El mensaje dice por qué."""


class ServicioGuardado:

    def __init__(self, partida: ServicioPartida):
        self._partida = partida
        self._sincronizador = SincronizadorUsos()

    def guardar(self, contexto: ContextoPartida, ruta: str) -> int:
        """Escribe la partida en 'ruta' (reemplaza la anterior de forma segura). Devuelve los bytes escritos."""
        bitacora = contexto.bitacora
        partida, salas = PartidaGuardada.guardar(
            contexto.motor, contexto.cripta, contexto.resolvedor.version_catalogo(), contexto.semilla,
            None if bitacora is None else bitacora.ruta(),
            0 if bitacora is None else bitacora.acciones_escritas())
        return GuardadoBinario.guardar(ruta, partida, salas)

    def cargar(self, ruta: str, nombre_jugador: str) -> ContextoPartida:
        partida = GuardadoBinario.cargar(ruta)
        salas = GuardadoBinario.cargar_salas(ruta)
        cripta, resolvedor, esqueleto, contenido = self._partida.abrir_datos(partida.id_cripta)
        problemas = GuardadoBinario.comprobar_compatibilidad(partida, cripta.version, resolvedor.version_catalogo())
        if problemas:
            raise ErrorCarga("No se puede continuar esa partida: " + "; ".join(problemas) + ".")

        mensajes = BufferCircular(MENSAJES_EN_PANTALLA)
        motor = PartidaGuardada.cargar(partida, salas, cripta,
                                       [esqueleto.obtener_sala(i) for i in esqueleto.ids_salas()],
                                       resolvedor.ficha, mensajes.agregar)
        contexto = ContextoPartida(cripta=cripta, nombre_jugador=nombre_jugador, semilla=partida.semilla,
                                   fuente=self._partida.fuente(), resolvedor=resolvedor, esqueleto=esqueleto,
                                   contenido=contenido, mazmorra=motor.mazmorra, jugador=motor.jugador,
                                   inventario=motor.inventario, motor=motor, mensajes=mensajes)
        motor.mensaje(f"Partida cargada: estás en {motor.mazmorra.sala(motor.jugador.Sala_Actual).nombre}")
        self._sincronizador.sincronizar(contexto)
        contexto.bitacora = self._continuar_log(partida)             # lo último: lo único que crea un archivo
        return contexto

    # ---- interno ----

    def _continuar_log(self, partida):
        if partida.ruta_log is None:                                 # la partida guardada no tenía log
            return None
        encabezado = EncabezadoReplayDTO(partida.id_cripta, partida.version_cripta, partida.version_catalogo,
                                         partida.semilla)
        return BitacoraReplayIO.continuar_desde(partida.ruta_log, partida.acciones_en_log,
                                                self._partida.nueva_ruta_de_log(), encabezado)