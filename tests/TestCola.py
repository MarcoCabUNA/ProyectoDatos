"""
Pruebas de Estructuras/Cola.py (cola FIFO compartida del equipo).
"""
import time
import unittest

from Estructuras.Cola import Cola


class PruebasCola(unittest.TestCase):

    def test_nueva_esta_vacia(self):
        c = Cola()
        self.assertTrue(c.esta_vacia())
        self.assertEqual((c.tamano(), len(c)), (0, 0))

    def test_orden_fifo(self):
        c = Cola()
        for x in (5, 10, 15):
            c.encolar(x)
        self.assertEqual(c.tamano(), 3)
        self.assertEqual(c.ver_frente(), 5)
        self.assertEqual([c.desencolar(), c.desencolar(), c.desencolar()], [5, 10, 15])
        self.assertTrue(c.esta_vacia())

    def test_un_solo_elemento_y_reutilizar_despues_de_vaciar(self):
        c = Cola()
        c.encolar("a")
        self.assertEqual(c.desencolar(), "a")
        self.assertTrue(c.esta_vacia())
        c.encolar("b")                    # 'final' se reinició bien al vaciarse
        self.assertEqual((c.ver_frente(), c.tamano()), ("b", 1))

    def test_alternar_encolar_y_desencolar(self):
        c = Cola()
        c.encolar(1)
        c.encolar(2)
        self.assertEqual(c.desencolar(), 1)
        c.encolar(3)
        self.assertEqual([c.desencolar(), c.desencolar()], [2, 3])

    def test_repetidos_y_none(self):
        c = Cola()
        for x in (7, 7, None, 7):
            c.encolar(x)
        self.assertEqual([c.desencolar() for _ in range(4)], [7, 7, None, 7])

    def test_vacia_lanza_IndexError(self):
        c = Cola()
        with self.assertRaises(IndexError):
            c.desencolar()
        with self.assertRaises(IndexError):
            c.ver_frente()

    def test_muchos_elementos(self):
        c = Cola()
        for i in range(100_000):
            c.encolar(i)
        for i in range(100_000):
            self.assertEqual(c.desencolar(), i)
        self.assertTrue(c.esta_vacia())

    def test_costo_constante_por_operacion(self):
        """Si fuera O(n), pasar de 1.000 a 200.000 elementos haría cada operación ~200 veces más lenta."""
        def ns_por_operacion(n):
            c = Cola()
            inicio = time.perf_counter()
            for i in range(n):
                c.encolar(i)
            for _ in range(n):
                c.desencolar()
            return (time.perf_counter() - inicio) / (2 * n)
        pequeno, grande = ns_por_operacion(1_000), ns_por_operacion(200_000)
        self.assertLess(grande, pequeno * 10)


if __name__ == "__main__":
    unittest.main()