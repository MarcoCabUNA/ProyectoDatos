"""
Pruebas del núcleo de Logic/MapaConocido.py (feature 002, integrante 2): los dos arreglos, las consultas y las
dos únicas escrituras (_poner_estado / _poner_cara), que registran su reversión en el historial (research R1, R3).

Hasta T012 fallan al importar Logic.MapaConocido (dentro de mapa_de_prueba): es el fallo esperado.
"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from Logic.HistorialRetroceso import HistorialRetroceso  # noqa: E402
from tests.ayudas_mapa import (A, B, C, D, ESTE, NORTE, SUR, cripta_mapa, estados, mapa_de_prueba,  # noqa: E402
                               salida)

# Constantes del mapa con sus valores de data-model §1 (las pruebas no las importan para no depender de T011).
DESCONOCIDA, AVISTADA, EXPLORADA = 0, 1, 2
SIN_OBSERVAR, ABIERTA, CERRADA = 0, 1, 2


def cripta_chica():
    """A –E– B –S– C, y A –N– D. Cuatro salas: S = 5 (la posición 0 queda vacía)."""
    return cripta_mapa(4, [salida(A, ESTE, B), salida(B, SUR, C), salida(A, NORTE, D)])


class PruebasNucleoMapaConocido(unittest.TestCase):

    def setUp(self):
        self.mazmorra = cripta_chica()
        self.historial = HistorialRetroceso()
        self.mapa, self.jugador = mapa_de_prueba(self.mazmorra, A, self.historial)

    def test_fr201_fr206_mapa_nuevo_todo_desconocido(self):
        s = len(self.mazmorra.salas)
        estado, caras = estados(self.mapa)
        self.assertEqual(estado, [DESCONOCIDA] * s)
        self.assertEqual(caras, [SIN_OBSERVAR] * (4 * s))

    def test_nfr201_consultas_estado_sala_y_cara(self):
        self.mapa.estado[B] = AVISTADA
        self.mapa.caras[C * 4 + SUR] = CERRADA
        self.assertEqual(self.mapa.estado_sala(B), AVISTADA)
        self.assertEqual(self.mapa.estado_sala(C), DESCONOCIDA)
        self.assertEqual(self.mapa.estado_cara(C, SUR), CERRADA)
        self.assertEqual(self.mapa.estado_cara(C, NORTE), SIN_OBSERVAR)

    def test_fr222_poner_igual_no_registra(self):
        antes = estados(self.mapa)
        self.mapa._poner_estado(B, DESCONOCIDA)
        self.mapa._poner_cara(A * 4 + ESTE, SIN_OBSERVAR)
        self.historial.cerrar_intervalo()
        self.mapa.estado[B] = AVISTADA          # cambio sin registrar: deshacer no debe tocarlo
        self.historial.deshacer()
        self.assertEqual(self.mapa.estado_sala(B), AVISTADA)
        self.assertEqual(estados(self.mapa)[1], antes[1])

    def test_fr222_poner_distinto_registra_su_reversion(self):
        antes = estados(self.mapa)
        self.mapa._poner_estado(B, EXPLORADA)
        self.mapa._poner_cara(A * 4 + ESTE, ABIERTA)
        self.assertEqual(self.mapa.estado_sala(B), EXPLORADA)
        self.assertEqual(self.mapa.estado_cara(A, ESTE), ABIERTA)
        self.historial.cerrar_intervalo()
        self.assertTrue(self.historial.deshacer())
        self.assertEqual(estados(self.mapa), antes)

    def test_fr222_cambios_repetidos_vuelven_al_primer_valor(self):
        self.mapa._poner_estado(D, AVISTADA)
        self.mapa._poner_cara(B * 4 + SUR, ABIERTA)
        self.historial.cerrar_intervalo()
        antes = estados(self.mapa)
        self.mapa._poner_estado(C, AVISTADA)        # la misma casilla cambia dos veces en un intervalo
        self.mapa._poner_estado(C, EXPLORADA)
        self.mapa._poner_cara(B * 4 + SUR, CERRADA)
        self.mapa._poner_cara(B * 4 + SUR, ABIERTA)
        self.mapa._poner_cara(B * 4 + SUR, CERRADA)
        self.historial.cerrar_intervalo()
        self.historial.deshacer()
        self.assertEqual(estados(self.mapa), antes)
        self.historial.deshacer()                   # y el intervalo anterior también vuelve
        self.assertEqual(self.mapa.estado_sala(D), DESCONOCIDA)
        self.assertEqual(self.mapa.estado_cara(B, SUR), SIN_OBSERVAR)

    def test_nfr203_historial_none_no_registra(self):
        mapa, _ = mapa_de_prueba(self.mazmorra, A, None)
        mapa._poner_estado(B, EXPLORADA)
        mapa._poner_cara(A * 4 + ESTE, CERRADA)
        self.assertEqual(mapa.estado_sala(B), EXPLORADA)
        self.assertEqual(mapa.estado_cara(A, ESTE), CERRADA)


if __name__ == "__main__":
    unittest.main()
