"""
ServicioReplayHasta (Servicios, Integrante 3, feature 004, historia 2): `--replay partida.log --hasta t`.

Lee el log, crea la MISMA partida (misma cripta y semilla), reproduce TODAS sus acciones por
ServicioLineaTiempo.ejecutar (la línea se alimenta igual que en una partida en vivo) y consulta el instante t con
ServicioLineaTiempo.consultar_por_instante. Por construcción el resumen es el que mostraría `historia t` (FR-411).
No usa la Vista (Principio V): este módulo no importa pygame ni View/. No toca Service/ServicioReplay.py (la
reproducción completa de la primera parte). No verifica la resolubilidad (FR-301 de la 003). No escribe log nuevo
ni puntajes: no es una partida nueva.

    reproducir_hasta(ruta, t) -> ResumenHistoriaDTO

Reglas:
  - La validación de t (entero entre 0 y el reloj de la partida) es de Logic/LineaTiempo: aquí solo se propaga su
    ValueError, con el rango, SIN haber ejecutado nada de más (la partida se reproduce antes, porque el rango depende
    del reloj final).
  - FR-412: si la partida TERMINÓ y t es posterior a su final, el resumen es el del estado final (reloj del final) con
    `terminada_antes` verdadero e `instante_pedido` = t. Si la partida no terminó, un t posterior al reloj es
    un error (ValueError con el rango): no hay un «final» que mostrar.
  - Las líneas «# ir a <sala>» del log ya las ignora BitacoraReplayIO.leer (T071): no cambian el resultado.
  - Igual que ServicioReplay: ErrorReplay, sin ejecutar nada, si el log es de otra versión de cripta o de catálogo;
    ErrorReplay con el número de la acción si una acción ya no se puede hacer o sobran acciones tras el final.
    ErrorBitacora (log ilegible o inexistente) y ErrorRed se propagan para que el Controlador los muestre.
"""
import dataclasses

from Data.BitacoraReplayIO import BitacoraReplayIO, comprobar_compatibilidad
from DTO.ResumenHistoriaDTO import ResumenHistoriaDTO
from Service.ServicioLineaTiempo import ServicioLineaTiempo
from Service.ServicioPartida import ServicioPartida
from Service.ServicioReplay import NOMBRE_DEL_JUGADOR, ErrorReplay


class ServicioReplayHasta:

    def __init__(self, partida: ServicioPartida):
        self._partida = partida
        self._linea = ServicioLineaTiempo()

    def reproducir_hasta(self, ruta: str, t: int) -> ResumenHistoriaDTO:
        leido = BitacoraReplayIO.leer(ruta)
        encabezado = leido.encabezado
        contexto = self._partida.iniciar_partida(encabezado.id_cripta, NOMBRE_DEL_JUGADOR,
                                                 semilla=encabezado.semilla, registrar_bitacora=False)
        problemas = comprobar_compatibilidad(encabezado, contexto.cripta.version,
                                             contexto.resolvedor.version_catalogo())
        if problemas:
            raise ErrorReplay("No se puede garantizar una reproducción fiel: " + "; ".join(problemas) + ".")

        reproducidas = 0
        for accion in leido.acciones:
            if contexto.motor.terminado:
                raise ErrorReplay(f"El log trae la acción {reproducidas + 1} ({accion.a_linea()!r}) pero la "
                                  f"partida ya había terminado: no es la partida que se grabó.")
            estado = self._linea.ejecutar(contexto, accion)
            if estado.resultado is not None and not estado.terminado:
                raise ErrorReplay(f"La acción {reproducidas + 1} ({accion.a_linea()!r}) no se pudo hacer: "
                                  f"{estado.resultado} La partida ya no es la que se grabó.")
            reproducidas += 1

        final = contexto.motor.reloj
        if contexto.motor.terminado and isinstance(t, int) and not isinstance(t, bool) and t > final:
            resumen = self._linea.consultar_por_instante(contexto, final)             # FR-412: el estado final
            return dataclasses.replace(resumen, terminada_antes=True, instante_pedido=t)
        return self._linea.consultar_por_instante(contexto, t)                         # propaga el ValueError con el rango
