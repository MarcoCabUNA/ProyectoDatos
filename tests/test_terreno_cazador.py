"""
Pruebas de la feature 001: terreno con costo por salida y enemigo cazador.

Una prueba por escenario de aceptación de spec.md, con el escenario y el FR en el nombre (Principio X).

    python -m unittest tests.test_terreno_cazador -v
"""
import os
import random
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.Direcciones import E, N, O, S  # noqa: E402
from DTO.ObjetoDTO import ObjetoDTO  # noqa: E402
from Logic.Comportamientos import Errante  # noqa: E402
from Logic.Inventario import Inventario  # noqa: E402
from tests.ayudas_terreno import (ficha_errante, ficha_rastreador, mazmorra_con_costos,  # noqa: E402
                                  motor_con, poner_enemigo, salida)


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


class TestTerrenoComportamientos(unittest.TestCase):
    """FR-102 y FR-104: errantes, rastreadores y guardianes deciden como en P1 y pagan el costo de la salida."""

    def _sala_con_dos_salidas_a_la_misma_vecina(self):
        # Sala 1: N -> 2 (costo 300), E -> 2 (costo 100), S -> 3 (sin costo). El jugador queda aislado en la 4.
        return mazmorra_con_costos(4, [salida(1, N, 2, 300), salida(1, E, 2, 100), salida(1, S, 3)])

    def test_fr104_errante_sortea_por_salida_igual_que_p1(self):
        for semilla in range(1, 30):
            motor_p1, _ = motor_con(self._sala_con_dos_salidas_a_la_misma_vecina(), 4, semilla)
            motor_nuevo, _ = motor_con(self._sala_con_dos_salidas_a_la_misma_vecina(), 4, semilla)
            errante_p1 = poner_enemigo(motor_p1, 1, ficha_errante())
            errante_nuevo = poner_enemigo(motor_nuevo, 1, ficha_errante())
            destino = Errante().decidir(errante_p1, motor_p1)
            paso = Errante().decidir_paso(errante_nuevo, motor_nuevo)
            # Mismo índice sorteado, mismo destino y el generador queda en el mismo estado (Principio IV).
            opciones = motor_nuevo.mazmorra.salidas_abiertas_con_costo(1)
            indice = random.Random(semilla).randint(0, len(opciones) - 1)
            self.assertEqual(paso, opciones[indice])
            self.assertEqual(paso[0], destino)
            self.assertEqual(motor_nuevo.azar.getstate(), motor_p1.azar.getstate())

    def test_fr104_errante_paga_el_costo_de_la_salida_sorteada(self):
        costos_vistos = []
        for semilla in range(1, 30):
            motor, _ = motor_con(self._sala_con_dos_salidas_a_la_misma_vecina(), 4, semilla)
            errante = poner_enemigo(motor, 1, ficha_errante())
            opciones = motor.mazmorra.salidas_abiertas_con_costo(1)
            destino, costo = opciones[random.Random(semilla).randint(0, len(opciones) - 1)]
            motor.turno_enemigo(errante)
            self.assertEqual(errante.Sala_Actual, destino)
            self.assertEqual(siguiente_accion(errante), costo)
            costos_vistos.append(costo)
        # Con 29 semillas salen las dos salidas hacia la sala 2 (100 y 300), no solo la más barata.
        self.assertIn(100, costos_vistos)
        self.assertIn(300, costos_vistos)

    def test_fr104_rastreador_usa_la_salida_mas_barata(self):
        # Dos salidas de 1 a 2 (costos 300 y 120); el rastro de la sala 2 está fresco.
        motor, _ = motor_con(mazmorra_con_costos(4, [salida(1, N, 2, 300), salida(1, E, 2, 120)]), 4)
        rastreador = poner_enemigo(motor, 1, ficha_rastreador())
        motor.rastro.marcar(2, 0)
        motor.turno_enemigo(rastreador)
        self.assertEqual(rastreador.Sala_Actual, 2)
        self.assertEqual(siguiente_accion(rastreador), 120)

    def test_fr104_guardian_no_se_mueve(self):
        motor, _ = motor_con(mazmorra_con_costos(3, [salida(1, E, 2, 250)]), 3)
        guardian = poner_enemigo(motor, 1, ficha_errante(comportamiento="guardián", id="guardian"))
        self.assertIsNone(guardian.estrategia.decidir_paso(guardian, motor))
        motor.turno_enemigo(guardian)
        self.assertEqual(guardian.Sala_Actual, 1)
        self.assertEqual(siguiente_accion(guardian), 100)        # esperar cuesta 100 (FR-103)

    def test_fr102_enemigo_programa_con_costo_de_salida(self):
        # Errante de velocidad 50 por la única salida (costo 250): max(1, 250 * 100 // 50) = 500.
        motor, _ = motor_con(mazmorra_con_costos(3, [salida(1, E, 2, 250)]), 3)
        errante = poner_enemigo(motor, 1, ficha_errante(velocidad=50))
        motor.turno_enemigo(errante)
        self.assertEqual(errante.Sala_Actual, 2)
        self.assertEqual(siguiente_accion(errante), 500)


if __name__ == "__main__":
    unittest.main()
