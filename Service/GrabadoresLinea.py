"""
GrabadoresLinea (Servicios, Integrante 3, feature 004): los dos adaptadores que alimentan la línea de tiempo.

La línea tiene que poder reconstruir un estado pasado SIN pedirle nada a Data (Principio VII). Para eso guarda
lo que la partida viva ya pidió, al primer uso (research.md R3):

    ContenidoGrabador   envuelve `contexto.contenido` (GestorContenido). En `asegurar_sala(id)` guarda el
                        SalaDTO devuelto como REGISTRO DE CARGA, con el ordinal igual a `jugador.acciones` en
                        ese momento (hallazgo H-1: conserva el orden real de carga de las salas).
    ResolvedorGrabador  envuelve `contexto.resolvedor` (ResolvedorCatalogo). En `ficha(id)` guarda la ficha
                        devuelta, una sola vez por id.

Los dos delegan TODO lo demás al objeto original, incluidos `rechazo()` y `resolver_contenido()`; así se
comportan igual que el original y no agregan solicitudes. Si el original lanza ErrorDatos (o cualquier
error), el error sale igual y NO se registra nada. Se instalan en los dos únicos puntos donde se arma un
ContextoPartida (ServicioPartida.iniciar_partida y ServicioGuardado.cargar).
"""
from Logic.LineaTiempo import LineaTiempo
from Data.GestorContenido import GestorContenido
from Data.ResolvedorCatalogo import ResolvedorCatalogo
from DTO.SalaDTO import SalaDTO


class ContenidoGrabador:
    """Envuelve el GestorContenido y registra en la línea el contenido de cada sala que la partida carga."""

    def __init__(self, original: GestorContenido, linea: LineaTiempo, jugador: object) -> None:
        """`jugador` es quien lleva la cuenta `acciones` (el ordinal de cada registro de carga)."""
        self._original = original
        self._linea = linea
        self._jugador = jugador

    def asegurar_sala(self, id_sala: int) -> SalaDTO:
        """Pide la sala al original y, si la entregó, la registra (a lo sumo una vez por sala)."""
        sala = self._original.asegurar_sala(id_sala)       # si lanza ErrorDatos, no se registra nada
        self._linea.registrar_carga(self._jugador.acciones, sala)
        return sala

    def __getattr__(self, nombre: str):
        """Todo lo que no es asegurar_sala() es del objeto original."""
        if nombre.startswith("__") or nombre in ("_original", "_linea", "_jugador"):
            raise AttributeError(nombre)
        return getattr(self._original, nombre)


class ResolvedorGrabador:
    """Envuelve el ResolvedorCatalogo y registra en la línea cada ficha que la partida pide."""

    def __init__(self, original: ResolvedorCatalogo, linea: LineaTiempo) -> None:
        self._original = original
        self._linea = linea

    def ficha(self, id_ficha: str, contar_acierto: bool = True):
        """Pide la ficha al original (con los mismos argumentos) y la registra una sola vez por id."""
        ficha = self._original.ficha(id_ficha, contar_acierto)   # si lanza ErrorDatos, no se registra nada
        self._linea.registrar_ficha(ficha)
        return ficha

    def __getattr__(self, nombre: str):
        """Todo lo que no es ficha() (rechazo, resolver_contenido, versión, contadores...) es del original."""
        if nombre.startswith("__") or nombre in ("_original", "_linea"):
            raise AttributeError(nombre)
        return getattr(self._original, nombre)
