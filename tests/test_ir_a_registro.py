"""
Pruebas del registro de «ir a» (feature 002, integrante 3): T110, H7-8 (A36) y H7-9 (A37), FR-261, FR-263 y SC-253.

La partida es real (cuadrícula sin enemigos, con bitácora y línea de tiempo en una carpeta temporal). El log se lee como
texto y con BitacoraReplayIO.leer; el replay se hace como ServicioReplay: la misma semilla y las mismas acciones.
"""
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from Data.BitacoraReplayIO import BitacoraReplayIO  # noqa: E402
from DTO.AccionDTO import AccionDTO  # noqa: E402
from DTO.Direcciones import E as ESTE, O as OESTE  # noqa: E402
from DTO.ViajeDTO import DESTINO_INVALIDO, SIN_RUTA  # noqa: E402
from Service.ServicioAccionJugador import ServicioAccionJugador  # noqa: E402
from Service.ServicioIrA import ServicioIrA  # noqa: E402
from Service.ServicioLineaTiempo import ServicioLineaTiempo  # noqa: E402
from Service.ServicioReplay import ServicioReplay  # noqa: E402
from tests.ayudas_ir_a import BitacoraPrueba, contexto_de_prueba, servicio_partida_cuadricula  # noqa: E402
from tests.ayudas_mapa import A, B, D, E, ESTE as ESTE_MAPA, OESTE as OESTE_MAPA, SUR, estados, salida  # noqa: E402

SEMILLA = 21


def lineas_del_log(contexto):
    with open(contexto.bitacora.ruta(), encoding="utf-8", newline="") as archivo:
        return archivo.read().split("\n")[:-1]


class PruebasRegistro(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(self.carpeta.cleanup)
        self.partida = servicio_partida_cuadricula(self.carpeta.name)
        self.contexto = self.partida.iniciar_partida("cuadricula", "Ana", semilla=SEMILLA)
        self.lineas = ServicioLineaTiempo()

    def a_mano(self, cantidad, direccion=ESTE):
        for _ in range(cantidad):
            self.lineas.ejecutar(self.contexto, AccionDTO("mover", direccion=direccion))

    def viajar(self, nombre):
        servicio = ServicioIrA()
        viaje = servicio.iniciar(self.contexto, nombre).viaje
        pasos = []
        while viaje is not None:
            paso = servicio.dar_paso(self.contexto, viaje)
            pasos.append(paso)
            viaje = paso.viaje
        return pasos

    def test_h7_8_a36_fr261_log_con_tres_movimientos_y_un_comentario(self):
        self.a_mano(3)                                                          # Sala 1 → Sala 4
        antes = lineas_del_log(self.contexto)
        pasos = self.viajar("Sala 1")
        self.assertEqual(len(pasos), 3)
        nuevas = lineas_del_log(self.contexto)[len(antes):]
        mover_oeste = AccionDTO("mover", direccion=OESTE).a_linea()
        self.assertEqual(nuevas, [mover_oeste, "# ir a Sala 1", mover_oeste, mover_oeste])   # entre el 1.º y el 2.º
        self.assertEqual(sum(1 for linea in lineas_del_log(self.contexto) if linea.startswith("# ")), 1)
        leido = BitacoraReplayIO.leer(self.contexto.bitacora.ruta())
        self.assertEqual(len(leido.acciones), 6)                               # el comentario no es una acción
        self.assertEqual(self.contexto.bitacora.acciones_escritas(), 6)
        a_mano = self.partida.iniciar_partida("cuadricula", "Ana", semilla=SEMILLA)    # los mismos 6 movimientos a mano
        for accion in leido.acciones:
            self.lineas.ejecutar(a_mano, accion)
        self.assertEqual(estados(a_mano.motor.mapa), estados(self.contexto.motor.mapa))
        self.assertEqual(a_mano.motor.reloj, self.contexto.motor.reloj)

    def test_h7_8_a36_fr261_sc253_replay_da_la_misma_partida_y_el_mismo_mapa(self):
        self.a_mano(4)
        self.viajar("Sala 2")
        vivo = (self.contexto.motor.reloj, self.contexto.jugador.Sala_Actual, estados(self.contexto.motor.mapa),
                self.contexto.jugador.a_dto())
        ruta = self.contexto.bitacora.ruta()
        resultado = ServicioReplay(self.partida).reproducir(ruta)
        self.assertEqual(resultado.acciones_reproducidas, 4 + 3)
        self.assertEqual((resultado.estado_final.reloj, resultado.estado_final.sala.id), (vivo[0], vivo[1]))
        replay = self.partida.iniciar_partida("cuadricula", "Replay", semilla=SEMILLA, registrar_bitacora=False)
        servicio = ServicioAccionJugador()
        for accion in BitacoraReplayIO.leer(ruta).acciones:
            servicio.ejecutar(replay, accion)
        self.assertEqual((replay.motor.reloj, replay.jugador.Sala_Actual, estados(replay.motor.mapa),
                          replay.jugador.a_dto()), vivo)
        self.assertEqual(BitacoraReplayIO.leer(ruta).acciones[-3:], [AccionDTO("mover", direccion=OESTE)] * 3)

    def test_fr261_orden_sin_pasos_no_se_registra(self):
        self.a_mano(1)
        antes = lineas_del_log(self.contexto)
        servicio = ServicioIrA()
        self.assertEqual(servicio.iniciar(self.contexto, "Sala 25").motivos, [DESTINO_INVALIDO])   # desconocida
        self.assertEqual(lineas_del_log(self.contexto), antes)
        salidas = [salida(A, ESTE_MAPA, B, 100), salida(B, SUR, D, 100), salida(D, ESTE_MAPA, E, 100)]
        bitacora = BitacoraPrueba()
        contexto = contexto_de_prueba(5, salidas, A, [B, D], bitacora)
        contexto.mazmorra.salida(A, ESTE_MAPA).cerrada = True                  # la puerta de A hacia B está cerrada…
        contexto.mazmorra.salida(B, OESTE_MAPA).cerrada = True
        contexto.motor.mapa.caras[A * 4 + ESTE_MAPA] = 2                        # …y A ya la recuerda cerrada: sin ruta
        viaje = servicio.iniciar(contexto, "Sala 4").viaje
        paso = servicio.dar_paso(contexto, viaje)
        self.assertEqual(paso.motivos, [SIN_RUTA])
        self.assertEqual(bitacora.lineas, [])

    def test_el_comentario_se_escribe_una_sola_vez_por_orden(self):
        self.a_mano(4)
        self.viajar("Sala 1")
        comentarios = [linea for linea in lineas_del_log(self.contexto) if linea.startswith("# ")]
        self.assertEqual(comentarios, ["# ir a Sala 1"])
        self.viajar("Sala 5")
        comentarios = [linea for linea in lineas_del_log(self.contexto) if linea.startswith("# ")]
        self.assertEqual(comentarios, ["# ir a Sala 1", "# ir a Sala 5"])      # uno por orden, no por paso

    def test_h7_9_a37_fr263_sc253_tres_acciones_en_la_linea_y_la_orden_no_cuenta(self):
        self.a_mano(3)
        antes = (self.contexto.jugador.acciones, len(self.contexto.linea.acciones))
        previos = []
        servicio = ServicioIrA()
        viaje = servicio.iniciar(self.contexto, "Sala 1").viaje
        self.assertEqual((self.contexto.jugador.acciones, len(self.contexto.linea.acciones)), antes)  # la orden no cuenta
        while viaje is not None:
            previos.append((self.contexto.motor.reloj, self.contexto.jugador.Sala_Actual))
            viaje = servicio.dar_paso(self.contexto, viaje).viaje
        self.assertEqual((self.contexto.jugador.acciones, len(self.contexto.linea.acciones)),
                         (antes[0] + 3, antes[1] + 3))
        for numero, (reloj, sala) in enumerate(previos, start=antes[0] + 1):
            resumen = self.lineas.consultar_por_accion(self.contexto, numero)  # `historia #k`
            self.assertEqual((resumen.reloj, resumen.sala_id), (reloj, sala), numero)
            self.assertEqual(self.contexto.linea.accion(numero).accion, AccionDTO("mover", direccion=OESTE))


if __name__ == "__main__":
    unittest.main()
