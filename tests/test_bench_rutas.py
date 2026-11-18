"""
Pruebas de Logic/BenchRutas.py (feature 001, T042): cada medición corre sin vista con tamaños chicos y devuelve
ResultadoBenchDTO con el subsistema y el caso esperados (NFR-103, Principio V). BenchLogica.medir() las incluye.

    python -m unittest tests.test_bench_rutas -v
"""
import os
import random
import sys
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.Direcciones import E, N, O, S  # noqa: E402
from DTO.ResultadoBenchDTO import ResultadoBenchDTO  # noqa: E402
from Logic import BenchLogica  # noqa: E402
from Logic import BenchRutas as B  # noqa: E402
from Logic.BenchLogica import _cuadricula  # noqa: E402

OPUESTA = [S, N, O, E]


class TestCuadriculaConCostos(unittest.TestCase):

    def test_fr101_mismo_costo_en_las_dos_caras_y_mismas_vecinas(self):
        salas = B._cuadricula_con_costos(5, random.Random(7))
        base = _cuadricula(5)
        for sala, original in zip(salas, base):
            for direccion in range(4):
                cara = sala.salidas[direccion]
                if cara is None:
                    self.assertIsNone(original.salidas[direccion])
                    continue
                self.assertEqual(cara.sala_destino, original.salidas[direccion].sala_destino)
                self.assertTrue(1 <= cara.costo <= 300)
                vuelta = salas[cara.sala_destino - 1].salidas[OPUESTA[direccion]]
                self.assertEqual(vuelta.costo, cara.costo)
        for original in base:                           # _cuadricula no se modifica (Principio III)
            for cara in original.salidas:
                self.assertTrue(cara is None or cara.costo is None)

    def test_principio_viii_la_misma_semilla_da_la_misma_cripta(self):
        self.assertEqual(B._cuadricula_con_costos(6, random.Random(3)), B._cuadricula_con_costos(6, random.Random(3)))
        self.assertNotEqual(B._cuadricula_con_costos(6, random.Random(3)),
                            B._cuadricula_con_costos(6, random.Random(4)))


class TestMediciones(unittest.TestCase):
    """Cada función con tamaños chicos: subsistema, caso y tamaño esperados (NFR-103)."""

    def revisar(self, resultados, subsistema, casos):
        self.assertEqual([r.caso for r in resultados], casos)
        for r in resultados:
            self.assertIsInstance(r, ResultadoBenchDTO)
            self.assertTrue(r.subsistema.startswith(subsistema), r)
            self.assertTrue(0 <= r.mejor_ms <= r.mediana_ms, r)
            self.assertNotEqual(r.nota, "")

    def test_r1_cola_de_prioridad(self):
        resultados = B.medir_cola_prioridad((100, 400), repeticiones=1, tamano_max_array=100)
        self.revisar(resultados, "rutas del cazador", ["cola de prioridad: montículo (elegida)",
                                                       "cola de prioridad: recorrer un array (descartada)",
                                                       "cola de prioridad: montículo (elegida)"])
        self.assertEqual([r.tamano for r in resultados], [100, 100, 400])
        self.assertIn("el array no se mide", resultados[2].nota)

    def test_r2_un_cazador_frente_a_muchos(self):
        resultados = B.medir_compartida((1, 3), lado=10, ciclos=4, repeticiones=1)
        self.revisar(resultados, "rutas del cazador", [
            "1 cazadores: una búsqueda por cazador (descartada)", "1 cazadores: búsqueda compartida (elegida)",
            "3 cazadores: una búsqueda por cazador (descartada)", "3 cazadores: búsqueda compartida (elegida)"])
        self.assertIn("decisiones iguales a paso_desde_cero", resultados[3].nota)

    def test_r3_sc105_rango_pequeno_frente_a_grande(self):
        resultados = B.medir_rango(rangos=(200, 5000), tamanos=(100, 400), decisiones=10, repeticiones=1)
        self.revisar(resultados, "rutas del cazador", ["rango 200: tiempo por decisión"] * 2
                     + ["rango 5000: tiempo por decisión"] * 2)
        self.assertIn("SC-105 (≤ 2)", resultados[1].nota)            # el veredicto, solo con rango 200
        self.assertNotIn("SC-105", resultados[0].nota + resultados[3].nota)
        self.assertIn("1 decisiones", resultados[2].nota)           # rango > 600: una décima parte

    def test_r4_invalidacion_con_puertas_estables_e_inestables(self):
        resultados = B.medir_invalidacion(cazadores=4, lado=8, ciclos=10, repeticiones=1)
        casos = []
        for escenario in B.ESCENARIOS_PUERTAS:
            casos += [f"{escenario}: recalcular siempre (A)", f"{escenario}: descartar ante cualquier puerta (B)",
                      f"{escenario}: descarte preciso (C, elegida)"]
        self.revisar(resultados, "invalidación de rutas", casos)
        self.assertTrue(all(r.tamano == 4 for r in resultados))

    def test_nfr101_sc104_ciclo_con_cazadores(self):
        resultados = B.medir_ciclo_cazadores((3,), lado=8, otros=2, ciclos=5, ciclos_comprobados=5)
        self.revisar(resultados, "ciclo de eventos", ["con cazadores: el jugador espera",
                                                      "con cazadores: el jugador se mueve"])
        for r in resultados:
            self.assertRegex(r.nota, "límite 20 ms: (cumple|NO cumple)")

    def test_r6_agenda_con_costos_mismo_tiempo_y_cancelaciones(self):
        resultados = B.medir_agenda_con_costos((50,), lote=10, repeticiones=1)
        subsistemas = []
        for r in resultados:
            if r.subsistema not in subsistemas:
                subsistemas.append(r.subsistema)
        self.assertEqual(subsistemas, ["agenda de eventos (costos variables)",
                                       "agenda de eventos (mismo tiempo: 1 tiempo)",
                                       "agenda de eventos (mismo tiempo: 10 tiempos)",
                                       "agenda de eventos (50 % cancelados)", "agenda de eventos (90 % cancelados)"])
        self.assertEqual(len(resultados), 3 * 4 + 2 * 2)
        for r in resultados[-4:]:
            self.assertRegex(r.nota, r"descartó \d+ cancelados; arreglo de \d+ a \d+ entradas")

    def test_r6_historial_con_y_sin_la_busqueda(self):
        resultados = B.medir_historial(cazadores=3, lado=8, otros=2, ciclos=5)
        self.revisar(resultados, "historial de retroceso", [
            "el jugador espera: con la búsqueda registrada (elegida)", "el jugador espera: sin registrar la búsqueda",
            "el jugador se mueve: con la búsqueda registrada (elegida)", "el jugador se mueve: sin registrar la búsqueda"])
        self.assertIn("la búsqueda agrega", resultados[3].nota)


class TestBenchLogica(unittest.TestCase):

    def test_nfr103_bench_logica_incluye_las_mediciones_de_rutas(self):
        fila_rutas = ResultadoBenchDTO("rutas del cazador", "x", 1, 0.0, 0.0, "n")
        with mock.patch.object(BenchLogica, "medir_agenda", return_value=[]), \
                mock.patch.object(BenchLogica, "medir_ciclo", return_value=[]), \
                mock.patch.object(B, "medir", return_value=[fila_rutas]):
            self.assertEqual(BenchLogica.medir(), [fila_rutas])


if __name__ == "__main__":
    unittest.main()
