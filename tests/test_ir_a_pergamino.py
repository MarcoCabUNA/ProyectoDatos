"""
Pruebas del pergamino durante un viaje de «ir a» (feature 002, integrante 3): T109, H7-7 (Apéndice B, caso 6).

La partida es real (cuadrícula sin enemigos, con línea de tiempo y bitácora); el pergamino pasa por
ServicioLineaTiempo.ejecutar como cualquier otra acción.
"""
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.AccionDTO import AccionDTO  # noqa: E402
from DTO.Direcciones import E as ESTE  # noqa: E402
from DTO.ViajeDTO import INTERRUMPIDO  # noqa: E402
from Service.ServicioIrA import ServicioIrA  # noqa: E402
from Service.ServicioLineaTiempo import ServicioLineaTiempo  # noqa: E402
from tests.ayudas_ir_a import dar_pergaminos_a, servicio_partida_cuadricula  # noqa: E402
from tests.ayudas_mapa import estados  # noqa: E402


class PruebasPergaminoDuranteElViaje(unittest.TestCase):

    def test_h7_7_apendiceB_caso6_fr222_fr262_pergamino_revierte_solo_el_ultimo_paso(self):
        with tempfile.TemporaryDirectory() as carpeta:
            contexto = servicio_partida_cuadricula(carpeta).iniciar_partida("cuadricula", "Ana", semilla=11)
            dar_pergaminos_a(contexto, 1)
            lineas = ServicioLineaTiempo()
            for _ in range(4):                                                 # Sala 1 → Sala 5, a mano
                lineas.ejecutar(contexto, AccionDTO("mover", direccion=ESTE))
            acciones_a_mano = contexto.jugador.acciones
            servicio = ServicioIrA()
            viaje = servicio.iniciar(contexto, "Sala 1").viaje
            antes_del_tercero = None
            for numero in (1, 2, 3):
                if numero == 3:
                    antes_del_tercero = (contexto.motor.reloj, contexto.jugador.Sala_Actual, estados(contexto.motor.mapa))
                paso = servicio.dar_paso(contexto, viaje)
                self.assertEqual(paso.motivos, [])
                viaje = paso.viaje
            self.assertEqual(contexto.jugador.acciones, acciones_a_mano + 3)
            self.assertEqual(len(contexto.linea.acciones), acciones_a_mano + 3)

            lineas.ejecutar(contexto, AccionDTO("retroceder"))                 # el pergamino, tras el 3.er paso

            self.assertEqual(contexto.jugador.acciones, acciones_a_mano + 2)   # quedan dos pasos del viaje
            self.assertEqual(len(contexto.linea.acciones), acciones_a_mano + 2)
            despues = (contexto.motor.reloj, contexto.jugador.Sala_Actual, estados(contexto.motor.mapa))
            self.assertEqual(despues, antes_del_tercero)                       # posición, reloj y mapa de antes del 3.º

            paso = servicio.dar_paso(contexto, viaje)                          # el viaje no continúa
            self.assertEqual((paso.viaje, paso.motivos), (None, [INTERRUMPIDO]))
            self.assertEqual((contexto.motor.reloj, contexto.jugador.Sala_Actual, estados(contexto.motor.mapa)),
                             antes_del_tercero)
            self.assertEqual(contexto.jugador.acciones, acciones_a_mano + 2)


if __name__ == "__main__":
    unittest.main()
