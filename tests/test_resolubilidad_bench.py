"""
Pruebas del generador de criptas en cuadrícula de Logic/BenchResolubilidad.py (feature 003, integrante 2; research R7):
lo usan la prueba de recursión (T029) y, en la fase 9, las mediciones de --bench (NFR-303, NFR-304).

cripta_en_cuadricula() se importa dentro de la prueba: hasta T030 cada prueba falla por su cuenta al importarlo.
"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.ReporteResolubilidadDTO import NO_RESOLUBLE, RESOLUBLE  # noqa: E402
from Logic.VerificadorResolubilidad import verificar  # noqa: E402


def cuadricula(filas, columnas, semilla, resoluble):
    """cripta_en_cuadricula(...). Hasta T030 no existe: es el fallo esperado."""
    from Logic.BenchResolubilidad import cripta_en_cuadricula
    return cripta_en_cuadricula(filas, columnas, semilla, resoluble)


def sala_de_cada_llave(ubicaciones):
    """(id, sala) de cada ubicación, en orden de id (sorted solo en la prueba, para comparar)."""
    return sorted((u.id, u.sala) for u in ubicaciones)


class PruebasCuadricula(unittest.TestCase):
    """T028: el generador de cuadrícula es determinista, exige dos filas y produce la cripta esperada."""

    def test_nfr304_cuadricula_es_determinista_por_semilla(self):
        for resoluble in (True, False):
            with self.subTest(resoluble=resoluble):
                a = cuadricula(10, 10, 3, resoluble)
                b = cuadricula(10, 10, 3, resoluble)
                self.assertEqual(a, b)                                       # mismas salas, ubicaciones y orden
                otra = cuadricula(10, 10, 4, resoluble)
                self.assertEqual(otra[1], a[1])                              # el esqueleto no depende de la semilla
                self.assertNotEqual(otra[2], a[2])                           # otro orden de la lista
                self.assertNotEqual(sala_de_cada_llave(otra[2]), sala_de_cada_llave(a[2]))   # otras filas

    def test_nfr304_cuadricula_exige_dos_filas(self):
        for filas in (1, 0, -3):
            with self.assertRaises(ValueError):
                cuadricula(filas, 10, 1, True)

    def test_nfr304_cuadricula_resoluble(self):
        for filas, columnas in ((2, 3), (10, 10), (3, 25)):
            with self.subTest(filas=filas, columnas=columnas):
                dto, salas, ubicaciones = cuadricula(filas, columnas, 11, True)
                self.assertEqual((len(salas), dto.salas_total), (filas * columnas, filas * columnas))
                self.assertEqual(len(ubicaciones), columnas)                 # columnas − 1 llaves más llave_salida
                reporte = verificar(dto, salas, ubicaciones)
                self.assertEqual(reporte.veredicto, RESOLUBLE)
                self.assertEqual(len(reporte.orden_llaves), columnas)
                self.assertEqual(reporte.orden_llaves[-1], dto.llave_salida)

    def test_nfr303_cuadricula_no_resoluble_un_ciclo_y_una_cadena(self):
        for columnas in (10, 101):
            with self.subTest(columnas=columnas):
                dto, salas, ubicaciones = cuadricula(4, columnas, 5, False)
                reporte = verificar(dto, salas, ubicaciones)
                self.assertEqual(reporte.veredicto, NO_RESOLUBLE)
                m = (columnas - 1) // 2
                self.assertEqual(len(reporte.ciclos), 1)
                ciclo = reporte.ciclos[0]
                self.assertEqual(len(ciclo.pasos), 1)                        # un ciclo de un paso: m → m
                self.assertEqual(ciclo.pasos[0].puerta.llave, ciclo.pasos[0].llave)
                self.assertEqual(len(ciclo.dependientes), columnas - m - 1)  # unas K/2, todas de m
                for dep in ciclo.dependientes:
                    self.assertEqual(dep.depende_de, ciclo.pasos[0].llave)
                self.assertEqual(len(reporte.orden_llaves), 0)
                self.assertEqual(len(reporte.llaves_no_obtenibles), columnas - m)


if __name__ == "__main__":
    unittest.main()
