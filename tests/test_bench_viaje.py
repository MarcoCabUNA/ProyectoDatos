"""
Pruebas de Logic/BenchViaje.py (feature 002, integrante 3, T119): el paso de «ir a» con tamaños chicos, sin vista
(Principio V). Los umbrales de tiempo se leen en la tabla de --bench (T122), no aquí: estas pruebas fijan que las cargas son
deterministas por semilla, que el paso cronometrado es el de decidir_paso y que medir() y ServicioBench devuelven las filas.

    python -m unittest tests.test_bench_viaje -v
"""
import os
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tests"))

from ayudas_resolubilidad import abierta, cripta, paquete_temporal, ubic  # noqa: E402
from DTO.Direcciones import E  # noqa: E402
from DTO.ResultadoBenchDTO import ResultadoBenchDTO  # noqa: E402
from Logic import BenchLogica, BenchMapaConocido, BenchViaje  # noqa: E402
from Logic.BusquedaCostoMinimo import paso_desde_cero  # noqa: E402
from Logic.GrafoMapaConocido import GrafoMapaConocido  # noqa: E402
from Logic.ViajeAutomatico import decidir_paso  # noqa: E402
from Service.ServicioBench import ServicioBench  # noqa: E402


def esqueleto(salas) -> list:
    filas = []
    for sala in salas:
        filas.append((sala.id, [None if s is None else (s.sala_destino, s.costo) for s in sala.salidas]))
    return filas


class PruebasCargasDelBench(unittest.TestCase):

    def test_nfr251_cuadriculas_deterministas_por_semilla(self):
        uno, otro = BenchViaje.armar_rectangulo(3, 4), BenchViaje.armar_rectangulo(3, 4)
        self.assertEqual(esqueleto(uno), esqueleto(otro))
        self.assertEqual(len(uno), 12)
        costos = []
        for sala in uno:
            for direccion in range(4):
                salida = sala.salidas[direccion]
                if salida is None:
                    continue
                self.assertTrue(1 <= salida.costo <= 300)
                vuelta = uno[salida.sala_destino - 1].salidas[BenchViaje.OPUESTA[direccion]]
                self.assertEqual((vuelta.sala_destino, vuelta.costo), (sala.id, salida.costo))   # igual en las dos caras
                costos.append(salida.costo)
        self.assertEqual(len(costos), 2 * (3 * 3 + 2 * 4))                     # 17 pares de salas vecinas, dos caras cada uno
        self.assertNotEqual(esqueleto(BenchViaje.armar_rectangulo(3, 4)), esqueleto(BenchViaje.armar_rectangulo(4, 3)))
        a, b = BenchMapaConocido.armar_cuadricula(5), BenchMapaConocido.armar_cuadricula(5)
        self.assertEqual(len(a.salas), 26)
        self.assertEqual([None if s is None else s.nombre for s in a.salas], [None if s is None else s.nombre for s in b.salas])

    def test_nfr251_medir_devuelve_tres_tamanos_y_el_de_referencia(self):
        resultados = BenchViaje.medir((4, 6), 2, 3, 4)
        for fila in resultados:
            self.assertIsInstance(fila, ResultadoBenchDTO)
            self.assertEqual(fila.subsistema, BenchViaje.SUBSISTEMA)
            self.assertGreater(fila.mediana_ms, 0)
            self.assertGreaterEqual(fila.mediana_ms, fila.mejor_ms)
        self.assertEqual([fila.tamano for fila in resultados], [16, 16, 16, 36, 36, 36, 12, 12, 12])
        self.assertEqual([fila.caso[:2] for fila in resultados], ["V1", "V2", "V3"] * 3)
        referencia = resultados[-1]
        self.assertIn("3 × 4 = 12 salas", referencia.nota)
        self.assertIn("cripta-06", referencia.nota)
        self.assertTrue("cumple" in referencia.nota or "NO cumple" in referencia.nota)
        self.assertIn("NFR-250", referencia.nota)
        self.assertNotIn("NFR-250", resultados[2].nota)                         # solo el de referencia lleva el criterio

    def test_h6_10_a32_nfr250_sc252_paso_medido_igual_a_decidir_paso(self):
        mazmorra = BenchViaje.mazmorra_de(BenchViaje.armar_rectangulo(4, 5))
        mapa = BenchMapaConocido.mapa_completo(mazmorra)
        destino = 20
        medido = BenchViaje.paso_completo(mapa, mazmorra, 1, destino)           # lo que cronometra V3
        fuera = decidir_paso(GrafoMapaConocido(mapa), mapa, mazmorra, 1, destino)
        self.assertEqual(medido, fuera)
        direccion, vecina, costo = medido
        self.assertEqual((vecina, costo), paso_desde_cero(GrafoMapaConocido(mapa), destino, 1, None))
        self.assertEqual(mazmorra.salida(1, direccion).destino, vecina)
        fila_v2 = BenchViaje.medir_en(mazmorra, 2, "prueba", False)[1]
        self.assertIn(f"decisión {medido}", fila_v2.nota)                        # la fila dice la decisión que cronometró

    def test_nfr251_servicio_bench_incluye_viaje_despues_de_mapa_conocido(self):
        mediciones = ServicioBench()._mediciones
        self.assertIn(BenchViaje.medir, mediciones)
        self.assertEqual(mediciones.index(BenchViaje.medir), mediciones.index(BenchMapaConocido.medir) + 1)
        self.assertGreater(mediciones.index(BenchViaje.medir), mediciones.index(BenchLogica.medir))


class PruebasCriptaDeReferenciaEnElPaquete(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.carpeta, True)

    def test_sin_cripta_06_en_el_paquete_una_fila_lo_dice(self):
        paquete = paquete_temporal(self.carpeta, *cripta(3, [abierta(1, E, 2), abierta(2, E, 3)], [ubic("S", 3)],
                                                         sala_salida=3, id_cripta="otra"))
        filas = ServicioBench(carpeta_paquete=paquete).medir_viaje_en_la_cripta_de_referencia()
        self.assertEqual(len(filas), 1)
        self.assertIn("(no medida)", filas[0].caso)
        self.assertEqual((filas[0].tamano, filas[0].mediana_ms), (0, 0.0))
        self.assertIn("cripta-06 no está en el paquete", filas[0].nota)
        self.assertIn("sintética de 300 salas", filas[0].nota)

    def test_con_cripta_06_en_el_paquete_se_mide_esa_cripta(self):
        dto, salas, ubicaciones = cripta(4, [abierta(1, E, 2), abierta(2, E, 3), abierta(3, E, 4)], [ubic("S", 4)],
                                         sala_salida=4, id_cripta="cripta-06")
        paquete = paquete_temporal(self.carpeta, dto, salas, ubicaciones)
        filas = ServicioBench(carpeta_paquete=paquete).medir_viaje_en_la_cripta_de_referencia(2)
        self.assertEqual([fila.caso[:2] for fila in filas], ["V1", "V2", "V3"])
        self.assertEqual([fila.tamano for fila in filas], [4, 4, 4])
        self.assertIn("cripta-06 versión v1 del paquete", filas[2].nota)
        self.assertIn("NFR-250", filas[2].nota)
        self.assertIn("decisión (2, 2, 100)", filas[1].nota)                     # un paso: de la 1 hacia la 2, por el este

    def test_ejecutar_agrega_la_fila_de_referencia_justo_despues_de_las_de_viaje(self):
        original = BenchViaje.medir
        BenchViaje.medir = lambda: BenchViaje.medir_en(BenchViaje.mazmorra_de(BenchViaje.armar_rectangulo(2, 3)), 1, "chica",
                                                       False)
        self.addCleanup(setattr, BenchViaje, "medir", original)
        marca = ResultadoBenchDTO("otro", "x", 1, 0.0, 0.0)
        paquete = paquete_temporal(self.carpeta, *cripta(3, [abierta(1, E, 2)], [ubic("S", 3)], sala_salida=3,
                                                         id_cripta="otra"))
        servicio = ServicioBench([lambda: [marca], BenchViaje.medir, lambda: [marca]], paquete)
        casos = [fila.caso[:2] for fila in servicio.ejecutar()]
        self.assertEqual(casos, ["x", "V1", "V2", "V3", "cr", "x"])              # «cr»: la fila «cripta-06 … (no medida)»


if __name__ == "__main__":
    unittest.main()
