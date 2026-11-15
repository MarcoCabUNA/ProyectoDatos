"""
Pruebas de la historia 4 en Logic (feature 002, integrante 2): con el HistorialRetroceso real, el pergamino deja el
mapa exactamente como antes de la acción (FR-222, NFR-203), sin copiar el mapa.

Excepción documentada al «falla primero» (Principio X, T023): estos escenarios usan código que ya llegó en T012 (la
reversión por casilla), T015 y T021, así que pueden pasar desde que se escriben.

T031: la variante con el motor (leer un pergamino); falla hasta T033. El guardado (H4-3) y la línea de tiempo (H4-4)
llegan en la fase 9.
"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.ObjetoDTO import ObjetoDTO  # noqa: E402
from Logic.HistorialRetroceso import HistorialRetroceso  # noqa: E402
from tests.ayudas_mapa import (A, B, C, D, E, ESTE, NORTE, SUR, cripta_mapa, entrar_a, estados,  # noqa: E402
                               mapa_de_prueba, motor_con_inventario, salida)

# Constantes del mapa con sus valores de data-model §1.
DESCONOCIDA, AVISTADA, EXPLORADA = 0, 1, 2
SIN_OBSERVAR, ABIERTA, CERRADA = 0, 1, 2


def cripta_h4():
    """A –E– B, A –S– D, B –S– C, B –N– D, C –E– E. Salas 1..5."""
    return cripta_mapa(5, [salida(A, ESTE, B), salida(A, SUR, D), salida(B, SUR, C), salida(B, NORTE, D),
                           salida(C, ESTE, E)])


class PruebasPergamino(unittest.TestCase):

    def setUp(self):
        self.mazmorra = cripta_h4()
        self.historial = HistorialRetroceso()
        self.mapa, self.jugador = mapa_de_prueba(self.mazmorra, A, self.historial)
        self.mapa.iniciar(A)
        self.historial.descartar_intervalo_abierto()       # como la preparación del motor

    def test_h4_1_apendiceB_caso5_fr222_pergamino_revierte_entrada_con_antorcha(self):
        self.assertEqual(self.mapa.estado_sala(B), AVISTADA)
        self.assertEqual(self.mapa.estado_sala(C), DESCONOCIDA)
        self.assertEqual(self.mapa.estado_sala(D), AVISTADA)
        antes = estados(self.mapa)
        entrar_a(self.mapa, self.jugador, B, True)
        for sala in (B, C, D):
            self.assertEqual(self.mapa.estado_sala(sala), EXPLORADA)
        self.historial.cerrar_intervalo()
        self.assertTrue(self.historial.deshacer())
        self.assertEqual(self.mapa.estado_sala(B), AVISTADA)
        self.assertEqual(self.mapa.estado_sala(C), DESCONOCIDA)
        self.assertEqual(self.mapa.estado_sala(D), AVISTADA)
        self.assertEqual(estados(self.mapa), antes)

    def test_h4_2_a8_fr222_pergamino_revierte_la_observacion(self):
        entrar_a(self.mapa, self.jugador, B)
        self.historial.cerrar_intervalo()
        entrar_a(self.mapa, self.jugador, A)
        self.historial.cerrar_intervalo()
        self.assertEqual(self.mapa.estado_cara(B, SUR), ABIERTA)
        self.mazmorra.salida(B, SUR).cerrada = True             # se cierra lejos del jugador
        self.mazmorra.salida(C, NORTE).cerrada = True
        entrar_a(self.mapa, self.jugador, B)
        self.assertEqual(self.mapa.estado_cara(B, SUR), CERRADA)
        self.historial.cerrar_intervalo()
        self.historial.deshacer()
        self.assertEqual(self.mapa.estado_cara(B, SUR), ABIERTA)
        self.assertEqual(self.mapa.estado_cara(C, NORTE), ABIERTA)

    def test_fr222_pergaminos_seguidos(self):
        inicial = estados(self.mapa)
        entrar_a(self.mapa, self.jugador, B)
        self.historial.cerrar_intervalo()
        despues_de_b = estados(self.mapa)
        entrar_a(self.mapa, self.jugador, C, True)
        self.historial.cerrar_intervalo()
        self.assertEqual(self.mapa.estado_sala(E), EXPLORADA)
        self.historial.deshacer()
        self.assertEqual(estados(self.mapa), despues_de_b)
        self.historial.deshacer()
        self.assertEqual(estados(self.mapa), inicial)

    def test_fr222_pergamino_sin_cambios_del_mapa(self):
        entrar_a(self.mapa, self.jugador, B)
        self.historial.cerrar_intervalo()
        entrar_a(self.mapa, self.jugador, A)                   # ya explorada y puertas iguales: no cambia nada
        self.historial.cerrar_intervalo()
        antes = estados(self.mapa)
        self.assertTrue(self.historial.deshacer())
        self.assertEqual(estados(self.mapa), antes)

    def test_fr222_iniciar_no_se_deshace(self):
        self.assertFalse(self.historial.deshacer())             # el conocimiento inicial se descartó
        self.assertEqual(self.mapa.estado_sala(A), EXPLORADA)
        entrar_a(self.mapa, self.jugador, B)
        self.historial.cerrar_intervalo()
        self.assertTrue(self.historial.deshacer())
        self.assertFalse(self.historial.deshacer())
        self.assertEqual(self.mapa.estado_sala(A), EXPLORADA)
        self.assertEqual(self.mapa.estado_sala(B), AVISTADA)
        self.assertEqual(self.mapa.estado_cara(A, ESTE), ABIERTA)
        self.assertEqual(self.mapa.estado_sala(C), DESCONOCIDA)


ANTORCHA, PERGAMINO = "itm_antorcha", "itm_pergamino"


class PruebasPergaminoConMotor(unittest.TestCase):
    """T031, historia 4 con el motor: leer un pergamino revierte el mapa junto con la posición y el reloj."""

    def test_h4_1_apendiceB_caso5_fr222_motor_leer_pergamino(self):
        objetos = [ObjetoDTO(ANTORCHA, "Antorcha", "antorcha", 1, 5, duracion=1000),
                   ObjetoDTO(PERGAMINO, "Pergamino", "pergamino_retroceso", 1, 5)]
        motor, _ = motor_con_inventario(cripta_h4(), A, objetos)
        motor.iniciar()
        motor.avanzar_hasta_jugador()
        self.assertEqual(motor.usar(ANTORCHA), "ok")
        motor.avanzar_hasta_jugador()
        antes = (estados(motor.mapa), motor.jugador.Sala_Actual, motor.reloj)
        self.assertEqual(motor.mapa.estado_sala(C), DESCONOCIDA)
        self.assertEqual(motor.mover_jugador(ESTE), "ok")        # entra a B con la antorcha encendida
        motor.avanzar_hasta_jugador()
        for sala in (B, C, D):
            self.assertEqual(motor.mapa.estado_sala(sala), EXPLORADA, f"sala {sala}")
        self.assertEqual(motor.usar(PERGAMINO), "ok")
        self.assertEqual((estados(motor.mapa), motor.jugador.Sala_Actual, motor.reloj), antes)
        self.assertEqual(motor.mapa.estado_sala(B), AVISTADA)
        self.assertEqual(motor.mapa.estado_sala(C), DESCONOCIDA)


if __name__ == "__main__":
    unittest.main()
