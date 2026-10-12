"""
ServicioReplay (Servicios, Integrante 3): reproduce una partida completa desde su log (§4.11, --replay).

Lee el log con BitacoraReplayIO, crea la MISMA partida (misma cripta y misma semilla) y ejecuta sus
acciones, una por una, con ServicioAccionJugador: el mismo camino que una partida en vivo, así que Lógica
no distingue entre jugar y reproducir. No usa la Vista: el que llama decide si mostrar el avance, con el
parámetro al_avanzar(numero, accion, estado), que se llama después de cada acción.

No reproduce "a ciegas" contra datos distintos (§4.11, Apéndice B). Lanza ErrorReplay, SIN ejecutar ninguna
acción, si el log fue grabado con otra versión de la cripta o del catálogo que la disponible en la fuente
de esta ejecución. Si la fuente es la red y el paquete de --offline tiene la versión del log, basta volver a
ejecutar con --offline: ese paquete es la "copia local compatible".

Si durante la reproducción una acción no se puede hacer (o el log trae acciones después de que la partida
terminó), la partida ya no es la que se grabó: también es ErrorReplay, con el número de la acción. En un log
bueno esto no ocurre: Servicios solo anota las acciones que sí se hicieron.

Otros errores se propagan tal cual para que el Controlador los muestre: ErrorBitacora (el log no se puede
leer) y ErrorRed (falló la red). Reproducir NO escribe un log nuevo ni registra puntajes: no es una partida nueva.
"""
from Data.BitacoraReplayIO import BitacoraReplayIO, comprobar_compatibilidad
from DTO.ResultadoReplayDTO import ResultadoReplayDTO
from Service.ServicioAccionJugador import ServicioAccionJugador
from Service.ServicioPartida import ServicioPartida

NOMBRE_DEL_JUGADOR = "Replay"


class ErrorReplay(ValueError):
    """El replay no se puede reproducir fielmente. El mensaje dice por qué."""


class ServicioReplay:

    def __init__(self, partida: ServicioPartida):
        self._partida = partida
        self._acciones = ServicioAccionJugador()

    def reproducir(self, ruta: str, al_avanzar=None) -> ResultadoReplayDTO:
        leido = BitacoraReplayIO.leer(ruta)
        encabezado = leido.encabezado
        contexto = self._partida.iniciar_partida(encabezado.id_cripta, NOMBRE_DEL_JUGADOR,
                                                 semilla=encabezado.semilla, registrar_bitacora=False)
        problemas = comprobar_compatibilidad(encabezado, contexto.cripta.version,
                                             contexto.resolvedor.version_catalogo())
        if problemas:
            raise ErrorReplay("No se puede garantizar una reproducción fiel: " + "; ".join(problemas) + ".")

        estado = self._partida.estado(contexto)
        reproducidas = 0
        for accion in leido.acciones:
            if contexto.motor.terminado:
                raise ErrorReplay(f"El log trae la acción {reproducidas + 1} ({accion.a_linea()!r}) pero la "
                                  f"partida ya había terminado: no es la partida que se grabó.")
            estado = self._acciones.ejecutar(contexto, accion)
            if estado.resultado is not None and not estado.terminado:
                raise ErrorReplay(f"La acción {reproducidas + 1} ({accion.a_linea()!r}) no se pudo hacer: "
                                  f"{estado.resultado} La partida ya no es la que se grabó.")
            reproducidas += 1
            if al_avanzar is not None:
                al_avanzar(reproducidas, accion, estado)
        return ResultadoReplayDTO(encabezado=encabezado, estado_final=estado, acciones_reproducidas=reproducidas,
                                  ultima_linea_descartada=leido.ultima_linea_descartada)