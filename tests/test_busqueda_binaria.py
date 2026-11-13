"""
Pruebas de Estructuras/BusquedaBinaria.py (feature 004, FR-416 y §5.5: ubicar el punto de control).
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Estructuras.BusquedaBinaria import ultimo_menor_o_igual


def _identidad(elemento: int) -> int:
    return elemento


class PruebasBusquedaBinaria(unittest.TestCase):

    def test_busqueda_ultimo_menor_o_igual_fr416(self):
        arreglo = [0, 3, 6, 9, 12]
        self.assertEqual(ultimo_menor_o_igual(arreglo, 6, _identidad), 2)       # clave exacta
        self.assertEqual(ultimo_menor_o_igual(arreglo, 7, _identidad), 2)       # entre dos elementos
        self.assertEqual(ultimo_menor_o_igual(arreglo, 99, _identidad), 4)      # mayor que todas
        self.assertEqual(ultimo_menor_o_igual(arreglo, 0, _identidad), 0)       # exacta en el primero

    def test_busqueda_sin_menor_devuelve_menos_uno_fr416(self):
        self.assertEqual(ultimo_menor_o_igual([5, 8], 4, _identidad), -1)       # menor que todas
        self.assertEqual(ultimo_menor_o_igual([], 4, _identidad), -1)           # arreglo vacío

    def test_busqueda_con_extractor_de_clave_fr416(self):
        acciones = [(100, "a"), (250, "b"), (400, "c")]
        self.assertEqual(ultimo_menor_o_igual(acciones, 300, lambda par: par[0]), 1)
        self.assertEqual(ultimo_menor_o_igual(acciones, 99, lambda par: par[0]), -1)

    def test_busqueda_coincide_con_el_recorrido_lineal_fr416(self):
        arreglo = [2, 2, 5, 9, 9, 9, 14]                                        # con claves repetidas: el último
        for clave in range(0, 17):
            esperado = -1
            for i, valor in enumerate(arreglo):
                if valor <= clave:
                    esperado = i
            self.assertEqual(ultimo_menor_o_igual(arreglo, clave, _identidad), esperado)


if __name__ == "__main__":
    unittest.main()
