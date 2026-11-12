"""
Pruebas de la feature 001: terreno con costo por salida y enemigo cazador.

Una prueba por escenario de aceptación de spec.md, con el escenario y el FR en el nombre (Principio X).

    python -m unittest tests.test_terreno_cazador -v
"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.Direcciones import E, O  # noqa: E402
from DTO.ObjetoDTO import ObjetoDTO  # noqa: E402
from Logic.Inventario import Inventario  # noqa: E402
from tests.ayudas_terreno import (ficha_errante, mazmorra_con_costos, motor_con,  # noqa: E402
                                  poner_enemigo, salida)


def turno_del_jugador(motor):
    """Inicia la partida y avanza hasta el primer turno del jugador (t = 0)."""
    motor.iniciar()
    motor.avanzar_hasta_jugador()
    return motor


def siguiente_accion(actor) -> int:
    """El instante de la siguiente acción programada del actor."""
    assert actor.Evento_pendiente is not None
    return actor.Evento_pendiente.tiempo


class TestTerreno(unittest.TestCase):
    """Historia 1: el terreno cuesta distinto (escenarios H1-1 a H1-8)."""

    def test_h1_1_fr102_salida_costo_250(self):
        motor, _ = motor_con(mazmorra_con_costos(2, [salida(1, E, 2, 250)]), 1)
        turno_del_jugador(motor)
        self.assertEqual(motor.mover_jugador(E), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 250)

    def test_h1_2_fr101_salida_sin_costo_vale_100(self):
        motor, _ = motor_con(mazmorra_con_costos(2, [salida(1, E, 2)]), 1)
        turno_del_jugador(motor)
        self.assertEqual(motor.mover_jugador(E), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 100)

    def test_h1_3_fr101_mismo_costo_en_ambos_sentidos(self):
        motor, _ = motor_con(mazmorra_con_costos(2, [salida(1, E, 2, 250)]), 2)
        turno_del_jugador(motor)
        self.assertEqual(motor.mover_jugador(O), "ok")
        self.assertEqual(motor.jugador.Sala_Actual, 1)
        self.assertEqual(siguiente_accion(motor.jugador), 250)

    def test_h1_4_apendiceB_caso6_fr102_intervalo_minimo_1(self):
        motor, _ = motor_con(mazmorra_con_costos(2, [salida(1, E, 2, 1)]), 1)
        motor.jugador.velocidad = 300
        turno_del_jugador(motor)
        self.assertEqual(motor.mover_jugador(E), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 1)     # max(1, 1 * 100 // 300) = 1, nunca 0

    def test_h1_5_apendiceB_caso7_fr105_cambio_de_velocidad(self):
        motor, _ = motor_con(mazmorra_con_costos(2, [salida(1, E, 2, 400)]), 1)
        turno_del_jugador(motor)
        self.assertEqual(motor.mover_jugador(E), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 400)
        motor.reloj = 100                                        # el reloj llega a t = 100 (P1 §2.3)
        motor.cambiar_velocidad(motor.jugador, 200)
        # max(1, (400 - 100) * 100 // 200) = 150 -> t = 250
        self.assertEqual(siguiente_accion(motor.jugador), 250)

    def test_h1_6_fr103_otras_acciones_conservan_costo(self):
        salidas_caras = [salida(1, E, 2, 400), (1, O, 3, 300, 300, False)]

        motor, _ = motor_con(mazmorra_con_costos(3, salidas_caras), 1)
        poner_enemigo(motor, 1, ficha_errante(comportamiento="guardián", id="guardian", vida_max=50))
        turno_del_jugador(motor)
        self.assertEqual(motor.atacar_enemigo("e-1"), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 100)

        motor, _ = motor_con(mazmorra_con_costos(3, salidas_caras), 1)
        turno_del_jugador(motor)
        self.assertEqual(motor.esperar(), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 100)

        motor, _ = motor_con(mazmorra_con_costos(3, salidas_caras), 1)
        motor.inventario = Inventario(5)
        motor.inventario.historial = motor.historial
        motor.inventario.recoger(ObjetoDTO("pocion", "Poción", "pocion", 1, 1, cura=5))
        turno_del_jugador(motor)
        self.assertEqual(motor.usar("pocion"), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 50)

    def test_h1_7_fr104_errante_paga_la_salida_sorteada(self):
        # La única salida abierta de la sala 1 cuesta 300; el jugador está lejos, en la sala 3 (aislada).
        motor, _ = motor_con(mazmorra_con_costos(3, [salida(1, E, 2, 300)]), 3)
        errante = poner_enemigo(motor, 1, ficha_errante())
        motor.turno_enemigo(errante)                             # en t = 0
        self.assertEqual(errante.Sala_Actual, 2)
        self.assertEqual(siguiente_accion(errante), 300)

    def test_h1_8_fr101_costo_declarado_en_un_solo_lado(self):
        # Solo el lado de la sala 1 declara 250; el jugador va de 2 a 1.
        motor, _ = motor_con(mazmorra_con_costos(2, [(1, E, 2, 250, None, False)]), 2)
        turno_del_jugador(motor)
        self.assertEqual(motor.mover_jugador(O), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 250)


if __name__ == "__main__":
    unittest.main()
