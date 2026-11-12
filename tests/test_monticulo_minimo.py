"""
Pruebas de Estructuras/MonticuloMinimo.py (feature 001, T015): la cola de prioridad de la búsqueda
de costo mínimo del cazador (research R1; FR-108).

    python -m unittest tests.test_monticulo_minimo -v
"""
import os
import random
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from Estructuras.MonticuloMinimo import MonticuloMinimo  # noqa: E402


def vaciar_en_orden(monticulo: MonticuloMinimo) -> list[tuple[int, int]]:
    salida = []
    while not monticulo.esta_vacio():
        salida.append(monticulo.extraer_minimo())
    return salida


class TestMonticuloMinimo(unittest.TestCase):

    def test_fr108_extrae_en_orden_de_clave(self):
        m = MonticuloMinimo()
        for clave in [50, 10, 40, 30, 20]:
            m.insertar(clave, clave + 1)
        self.assertEqual([c for c, _ in vaciar_en_orden(m)], [10, 20, 30, 40, 50])

    def test_fr108_con_claves_iguales_desempata_por_valor(self):
        m = MonticuloMinimo()
        for valor in [7, 3, 9, 1]:
            m.insertar(100, valor)
        self.assertEqual(vaciar_en_orden(m), [(100, 1), (100, 3), (100, 7), (100, 9)])

    def test_fr108_admite_entradas_repetidas_de_la_misma_sala(self):
        # Borrado perezoso: la misma sala entra varias veces con distancias distintas.
        m = MonticuloMinimo()
        m.insertar(300, 5)
        m.insertar(120, 5)
        m.insertar(200, 5)
        self.assertEqual(vaciar_en_orden(m), [(120, 5), (200, 5), (300, 5)])

    def test_ver_minimo(self):
        m = MonticuloMinimo()
        self.assertIsNone(m.ver_minimo())
        m.insertar(5, 2)
        m.insertar(3, 9)
        self.assertEqual(m.ver_minimo(), (3, 9))
        self.assertEqual(m.tamano(), 2)                  # ver no extrae

    def test_tamano_esta_vacio_y_vaciar(self):
        m = MonticuloMinimo()
        self.assertTrue(m.esta_vacio())
        self.assertEqual(m.tamano(), 0)
        for i in range(10):
            m.insertar(i, i)
        self.assertFalse(m.esta_vacio())
        self.assertEqual(m.tamano(), 10)
        m.extraer_minimo()
        self.assertEqual(m.tamano(), 9)
        m.vaciar()
        self.assertTrue(m.esta_vacio())
        self.assertIsNone(m.ver_minimo())
        m.insertar(4, 4)                                 # sigue sirviendo después de vaciar
        self.assertEqual(m.extraer_minimo(), (4, 4))

    def test_extraer_de_vacio_lanza_error(self):
        with self.assertRaises(IndexError):
            MonticuloMinimo().extraer_minimo()

    def test_fr108_mil_inserciones_igual_que_una_referencia(self):
        azar = random.Random(7)
        m = MonticuloMinimo()
        entradas = []
        for _ in range(1000):
            entrada = (azar.randint(0, 300), azar.randint(0, 50))
            entradas.append(entrada)
            m.insertar(*entrada)
        # sorted() solo como oráculo de la prueba: en tests/ está permitido.
        self.assertEqual(vaciar_en_orden(m), sorted(entradas))

    def test_fr108_inserciones_y_extracciones_mezcladas(self):
        azar = random.Random(11)
        m = MonticuloMinimo()
        referencia = []
        for _ in range(2000):
            if referencia and azar.random() < 0.4:
                referencia.sort()                       # oráculo de la prueba
                self.assertEqual(m.extraer_minimo(), referencia.pop(0))
            else:
                entrada = (azar.randint(0, 1000), azar.randint(0, 100))
                referencia.append(entrada)
                m.insertar(*entrada)
            self.assertEqual(m.tamano(), len(referencia))


if __name__ == "__main__":
    unittest.main()
