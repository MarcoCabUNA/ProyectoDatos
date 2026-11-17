"""
Pruebas del H-2, opción A (feature 002, T115; FR-204, FR-217, SC-202): el EstadoJuegoDTO no revela el id de una sala que
el jugador no ha explorado. ArmadorEstado pone SIN_EXPLORAR (-1) en `sala.salidas[d].sala_destino` hacia salas no
exploradas y deja `sala_salida` en None hasta que la sala de salida esté explorada. La vista no cambia.

La partida es real: una cuadrícula de 5 × 5 salas sin enemigos (Sala 1 = esquina, Sala 25 = la salida).
"""
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.AccionDTO import AccionDTO  # noqa: E402
from DTO.Direcciones import E as ESTE, S as SUR  # noqa: E402
from DTO.EstadoJuegoDTO import SIN_EXPLORAR  # noqa: E402
from Logic.Efectos import Antorcha  # noqa: E402
from Service.ArmadorEstado import ArmadorEstado  # noqa: E402
from Service.ServicioLineaTiempo import ServicioLineaTiempo  # noqa: E402
from tests.ayudas_ir_a import LADO_REAL, servicio_partida_cuadricula  # noqa: E402

SALA_SALIDA = LADO_REAL * LADO_REAL


def revisar(prueba, contexto, estado):
    mapa = contexto.motor.mapa
    for salida in estado.sala.salidas:
        if salida is None:
            continue
        if mapa.es_explorada(salida.sala_destino):
            continue
        prueba.assertEqual(salida.sala_destino, SIN_EXPLORAR)
    if estado.sala_salida is not None:
        prueba.assertTrue(mapa.es_explorada(estado.sala_salida))


class PruebasEstadoSinFiltrar(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(self.carpeta.cleanup)
        self.contexto = servicio_partida_cuadricula(self.carpeta.name).iniciar_partida("cuadricula", "Ana", semilla=3)
        self.servicio = ServicioLineaTiempo()
        self.armador = ArmadorEstado()

    def mover(self, direccion):
        estado = self.servicio.ejecutar(self.contexto, AccionDTO("mover", direccion=direccion))
        self.assertIsNone(estado.resultado)
        return estado

    def test_sc202_h2_doscientas_acciones_sin_ids_de_no_exploradas(self):
        contexto, x = self.contexto, 3
        inicial = self.armador.armar_estado(contexto)
        revisar(self, contexto, inicial)
        hechas, antorcha = 0, [False, False]
        while hechas < 200:
            if hechas == 100:                                                 # la segunda mitad, con la antorcha
                contexto.motor.efectos.aplicar(Antorcha(contexto.jugador, 10 ** 7))
            antorcha[contexto.motor.efectos.tiene(contexto.jugador, "antorcha")] = True
            estado = self.armador.armar_estado(contexto)
            abiertas = [d for d in range(4) if estado.sala.salidas[d] is not None]
            x = (x * 1103515245 + 12345) % (1 << 32)
            direccion = abiertas[(x >> 16) % len(abiertas)]
            nuevo = self.mover(direccion)
            revisar(self, contexto, nuevo)
            hechas += 1
        self.assertEqual(antorcha, [True, True])

    def test_salida_a_sala_no_explorada_sale_con_sin_explorar(self):
        estado = self.armador.armar_estado(self.contexto)
        self.assertEqual(SIN_EXPLORAR, -1)
        self.assertEqual(estado.sala.salidas[ESTE].sala_destino, SIN_EXPLORAR)    # la Sala 2 solo está avistada
        self.assertEqual(estado.sala.salidas[SUR].sala_destino, SIN_EXPLORAR)     # y la Sala 6
        self.assertTrue(self.contexto.motor.mapa.estado_sala(2) == 1)
        self.assertTrue(estado.sala.salidas[ESTE].costo is not None)              # el resto de la salida no cambia

    def test_fr204_fr217_h2_salidas_a_exploradas_y_sala_inicial_sin_cambios(self):
        self.mover(ESTE)                                                           # Sala 1 → Sala 2
        estado = self.armador.armar_estado(self.contexto)
        self.assertEqual(estado.sala.id, 2)
        oeste = estado.sala.salidas[3]
        self.assertEqual(oeste.sala_destino, 1)                                    # la Sala 1 ya está explorada
        self.assertEqual(estado.sala.salidas[ESTE].sala_destino, SIN_EXPLORAR)
        self.assertEqual(estado.sala_inicial, 1)                                   # la inicial siempre se conoce
        self.assertEqual(estado.reloj, self.contexto.motor.reloj)
        self.assertEqual(estado.jugador, self.contexto.jugador.a_dto())

    def test_sala_salida_es_none_hasta_que_se_explora_y_despues_vuelve_a_su_id(self):
        estado = self.armador.armar_estado(self.contexto)
        self.assertEqual((estado.sala_salida, self.contexto.cripta.sala_salida), (None, SALA_SALIDA))
        for _ in range(LADO_REAL - 1):
            estado = self.mover(ESTE)
        for _ in range(LADO_REAL - 2):                                             # hasta la Sala 20: la 25 solo avistada
            estado = self.mover(SUR)
        self.assertEqual(estado.sala.id, SALA_SALIDA - LADO_REAL)
        self.assertEqual(estado.sala.salidas[SUR].sala_destino, SIN_EXPLORAR)
        self.assertIsNone(estado.sala_salida)
        estado = self.mover(SUR)                                                    # entra a la Sala 25
        self.assertEqual((estado.sala.id, estado.sala_salida), (SALA_SALIDA, SALA_SALIDA))
        estado = self.mover(3)                                                      # sale: sigue explorada
        self.assertEqual(estado.sala_salida, SALA_SALIDA)
        self.assertEqual(estado.sala.salidas[ESTE].sala_destino, SALA_SALIDA)       # y las salidas hacia ella la nombran


if __name__ == "__main__":
    unittest.main()
