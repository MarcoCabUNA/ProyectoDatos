"""
Pruebas del costo por salida en Logic/Mazmorra.py (feature 001, T004).

Cubre: el costo de SalidaViva y la igualación de los dos lados (FR-101), salidas_abiertas_con_costo
(FR-104) y costo_paso con varias salidas hacia la misma vecina (FR-119).

    python -m unittest tests.test_mazmorra_costos -v
"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.Direcciones import E, N, O, S  # noqa: E402
from Logic.Mazmorra import Mazmorra  # noqa: E402
from tests.ayudas_terreno import (mazmorra_con_costos, salida, salida_sin_vuelta,  # noqa: E402
                                  salidas_con_costos)


def costo_de(mazmorra: Mazmorra, id_sala: int, direccion: int) -> int:
    """El costo final de la cara 'direccion' de la sala 'id_sala'."""
    cara = mazmorra.salida(id_sala, direccion)
    assert cara is not None, f"la sala {id_sala} no tiene salida en la dirección {direccion}"
    return cara.costo


class TestIgualarCostos(unittest.TestCase):
    """FR-101: el costo es el mismo en los dos sentidos; si nadie lo declara, vale 100."""

    def test_fr101_los_dos_lados_declaran_el_mismo_costo(self):
        m = mazmorra_con_costos(2, [salida(1, E, 2, 250)])
        self.assertEqual(costo_de(m, 1, E), 250)
        self.assertEqual(costo_de(m, 2, O), 250)

    def test_fr101_solo_un_lado_declara_vale_para_los_dos(self):
        m = mazmorra_con_costos(2, [(1, E, 2, 250, None, False)])
        self.assertEqual(costo_de(m, 1, E), 250)
        self.assertEqual(costo_de(m, 2, O), 250)

    def test_fr101_solo_el_otro_lado_declara_vale_para_los_dos(self):
        m = mazmorra_con_costos(2, [(1, E, 2, None, 300, False)])
        self.assertEqual(costo_de(m, 1, E), 300)
        self.assertEqual(costo_de(m, 2, O), 300)

    def test_fr101_ningun_lado_declara_vale_100(self):
        m = mazmorra_con_costos(2, [salida(1, E, 2)])
        self.assertEqual(costo_de(m, 1, E), 100)
        self.assertEqual(costo_de(m, 2, O), 100)

    def test_fr101_salida_sin_vuelta_sin_costo_vale_100(self):
        m = mazmorra_con_costos(2, [salida_sin_vuelta(1, E, 2)])
        self.assertEqual(costo_de(m, 1, E), 100)

    def test_fr101_salida_sin_vuelta_con_costo(self):
        m = mazmorra_con_costos(2, [salida_sin_vuelta(1, E, 2, 40)])
        self.assertEqual(costo_de(m, 1, E), 40)

    def test_fr101_esqueleto_en_dos_llamadas_iguala_al_llegar_la_segunda(self):
        # Primero llega la sala 2, que no declara costo: mientras tanto vale 100.
        # Después llega la sala 1, que declara 250: la cara 2->1 pasa a valer 250.
        salas = salidas_con_costos(2, [(1, E, 2, 250, None, False)])
        m = Mazmorra(sala_salida=2, llave_salida="llave_final")
        m.cargar_esqueleto([salas[1]])
        self.assertEqual(costo_de(m, 2, O), 100)
        m.cargar_esqueleto([salas[0]])
        self.assertEqual(costo_de(m, 1, E), 250)
        self.assertEqual(costo_de(m, 2, O), 250)

    def test_fr101_esqueleto_en_dos_llamadas_en_el_otro_orden(self):
        salas = salidas_con_costos(2, [(1, E, 2, 250, None, False)])
        m = Mazmorra(sala_salida=2, llave_salida="llave_final")
        m.cargar_esqueleto([salas[0]])
        m.cargar_esqueleto([salas[1]])
        self.assertEqual(costo_de(m, 1, E), 250)
        self.assertEqual(costo_de(m, 2, O), 250)

    def test_fr101_sin_costos_todo_vale_100_como_en_p1(self):
        m = mazmorra_con_costos(3, [salida(1, E, 2), salida(2, S, 3, cerrada=True)])
        for id_sala in range(1, 4):
            for cara in m.sala(id_sala).salidas:
                if cara is not None:
                    self.assertEqual(cara.costo, 100)


class TestSalidasConCosto(unittest.TestCase):
    """FR-104 y FR-119: salidas abiertas con su costo, y el costo de un paso entre dos salas."""

    def setUp(self):
        # Dos salidas de 1 hacia 2 (E: 300, N: 120), una cerrada de 1 hacia 3 (S: 50) y 1 -> 4 (O: sin costo).
        self.m = mazmorra_con_costos(4, [
            salida(1, E, 2, 300),
            salida(1, N, 2, 120),
            salida(1, S, 3, 50, cerrada=True),
            salida(1, O, 4),
        ])

    def test_fr104_mismo_orden_y_longitud_que_salidas_abiertas(self):
        destinos = self.m.salidas_abiertas(1)
        con_costo = self.m.salidas_abiertas_con_costo(1)
        self.assertEqual(len(con_costo), len(destinos))
        for i in range(len(destinos)):
            self.assertEqual(con_costo[i][0], destinos[i])

    def test_fr104_trae_dos_salidas_hacia_la_misma_sala(self):
        # Orden de las direcciones: N, S, E, O. La S está cerrada.
        self.assertEqual(self.m.salidas_abiertas_con_costo(1), [(2, 120), (2, 300), (4, 100)])

    def test_fr104_no_trae_salidas_cerradas(self):
        for destino, _ in self.m.salidas_abiertas_con_costo(1):
            self.assertNotEqual(destino, 3)

    def test_fr119_costo_paso_es_el_menor_de_las_salidas_abiertas(self):
        self.assertEqual(self.m.costo_paso(1, 2), 120)

    def test_fr119_costo_paso_ignora_las_cerradas(self):
        # La salida más barata (N: 120) se cierra: queda la de 300.
        self.m.salida(1, N).cerrada = True
        self.assertEqual(self.m.costo_paso(1, 2), 300)

    def test_fr119_costo_paso_desde_el_otro_lado(self):
        self.assertEqual(self.m.costo_paso(2, 1), 120)
        self.assertEqual(self.m.costo_paso(4, 1), 100)


if __name__ == "__main__":
    unittest.main()
