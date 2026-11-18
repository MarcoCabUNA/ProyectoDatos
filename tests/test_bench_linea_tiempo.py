"""
Pruebas de Service/BenchLineaTiempo.py (feature 004, T058): cada medición corre sin vista con tamaños chicos
(por ejemplo, 50 acciones) y devuelve ResultadoBenchDTO con el subsistema y el caso esperados (NFR-401 a NFR-403,
Principio V). BenchInventario.medir() incluye el grupo de la línea de tiempo (T061).

    python -m unittest tests.test_bench_linea_tiempo -v
"""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.ResultadoBenchDTO import ResultadoBenchDTO  # noqa: E402
from Logic.LineaTiempo import LineaTiempo, PuntoControl  # noqa: E402
from Service import BenchInventario, BenchLineaTiempo as B  # noqa: E402

SUBSISTEMA = "línea de tiempo"
def tearDownModule():
    B._borrar_carpeta(B.CARPETA)                # las pruebas que arman partidas dejan su caché en saves/bench_tmp


ACCIONES = 50                       # tamaño chico para las pruebas
REP = 2                             # repeticiones chicas


def _revisar(resultados, cantidad):
    """La forma común de toda fila: DTO, subsistema, tiempos coherentes y una nota que explica la fila."""
    assert len(resultados) == cantidad, (len(resultados), cantidad)
    for r in resultados:
        assert isinstance(r, ResultadoBenchDTO), r
        assert r.subsistema == SUBSISTEMA, r
        assert 0 <= r.mejor_ms <= r.mediana_ms, r
        assert r.nota != "", r
    return resultados


class TestM1TiempoDeHistoria(unittest.TestCase):

    def test_bench_m1_tiempo_de_historia_fr401_nfr401(self):
        r = _revisar(B.medir_historia(acciones=ACCIONES, ks=(1, 5, 20), repeticiones=REP), 8)
        # por cada K (y al final «sin puntos de control»): `historia #k` y `historia <t>`
        casos = [x.caso for x in r]
        self.assertEqual(casos[0], "K=1: historia #k (peor caso del bloque)")
        self.assertEqual(casos[1], "K=1: historia <t> (peor caso del bloque)")
        self.assertEqual(casos[2], "K=5: historia #k (peor caso del bloque)")
        self.assertEqual(casos[6], "sin puntos de control (descartada): historia #k (peor caso del bloque)")
        self.assertEqual(casos[7], "sin puntos de control (descartada): historia <t> (peor caso del bloque)")
        for x in r:
            self.assertEqual(x.tamano, ACCIONES)

    def test_bench_m1_la_nota_dice_cuantas_acciones_se_reaplicaron_fr416(self):
        r = B.medir_historia(acciones=ACCIONES, ks=(5, 20), repeticiones=REP)
        for x in r:
            self.assertIn("re-simula", x.nota)
        # con K = 5 el peor caso re-simula K - 1 acciones; sin puntos, casi todas las de la historia
        self.assertIn("re-simula 4 acción", r[0].nota)
        self.assertNotIn("re-simula 4 acción", r[-1].nota)

    def test_bench_m1_nunca_se_reaplica_mas_de_k_acciones_fr416(self):
        contexto = B._partida_con(acciones=ACCIONES, k=7)
        self.assertEqual(contexto.jugador.acciones, ACCIONES)
        for numero in range(1, ACCIONES + 1):
            self.assertLessEqual(B._reaplicadas_por_accion(contexto, numero), 7, numero)


class TestM2Posicion(unittest.TestCase):

    def test_bench_m2_tiempo_segun_la_posicion_consultada_nfr401(self):
        r = _revisar(B.medir_posiciones(acciones=ACCIONES, ks=(5, 20), repeticiones=REP), 9)
        posiciones = ["inicio", "mitad", "final"]
        for i in range(9):
            self.assertIn(posiciones[i % 3], r[i].caso)
        self.assertIn("K=5", r[0].caso)
        self.assertIn("sin puntos de control", r[6].caso)


class TestM3Memoria(unittest.TestCase):

    def test_bench_m3_memoria_nfr402(self):
        r = _revisar(B.medir_memoria(tamanos=(10, 30), ks=(1, 5)), 6)       # (2 K + sin puntos) x 2 tamaños
        for x in r:
            self.assertIn("bytes", x.nota)
            self.assertIn("puntos", x.nota)
            self.assertEqual(x.mejor_ms, 0.0)                               # memoria: la columna de ms no aplica
        self.assertEqual([x.tamano for x in r], [10, 30] * 3)

    def test_bench_m3_con_menos_puntos_se_guarda_menos_nfr402(self):
        r = B.medir_memoria(tamanos=(30,), ks=(1, 5))
        k1, k5, sin = (B._bytes_de_la_nota(x.nota) for x in r)
        self.assertGreater(k1, k5)
        self.assertGreater(k5, sin)

    def test_bench_m3_cuenta_los_elementos_guardados_nfr402(self):
        contexto = B._partida_con(acciones=20, k=5)
        cuenta = B._contar_elementos(contexto.linea)
        self.assertEqual(cuenta[0], 20)                                      # acciones vigentes
        self.assertEqual(cuenta[1], len(contexto.linea.puntos))              # puntos de control
        self.assertEqual(len(contexto.linea.puntos), 1 + 20 // 5)            # el 0 y uno cada K


class TestM4UbicarPunto(unittest.TestCase):

    def test_bench_m4_ubicar_punto_nfr401(self):
        r = _revisar(B.medir_ubicar_punto(cantidades=(10, 100), repeticiones=REP), 4)
        self.assertEqual(r[0].caso, "búsqueda binaria: ubicar el punto de control")
        self.assertEqual(r[1].caso, "recorrido lineal (descartada): ubicar el punto de control")
        self.assertEqual([x.tamano for x in r], [10, 10, 100, 100])

    def test_bench_m4_las_dos_busquedas_dan_el_mismo_punto_nfr401(self):
        linea = B._linea_con_puntos(37, k=3)
        for acciones in (0, 1, 2, 3, 50, 110, 111, 500):
            binario = linea.ubicar_punto(acciones)
            lineal = B._ubicar_lineal(linea.puntos, acciones)
            self.assertIs(binario, lineal, acciones)


class TestM5CostoDeUnaCopia(unittest.TestCase):

    def test_bench_m5_costo_de_una_copia_nfr401(self):
        r = _revisar(B.medir_copia(salas=(6, 50), enemigos=(0, 10), repeticiones=REP), 4)
        self.assertEqual([x.tamano for x in r], [6, 6, 50, 50])
        for x in r:
            self.assertIn("enemigos", x.nota)
            self.assertIn("PartidaGuardada.guardar", x.caso)

    def test_bench_m5_el_motor_sintetico_tiene_las_salas_y_los_enemigos_pedidos(self):
        motor = B._motor_con(salas=25, enemigos=10)
        self.assertEqual(len([s for s in motor.mazmorra.salas if s is not None]), 25)
        vivos = 0
        for sala in motor.mazmorra.salas:
            if sala is not None:
                vivos += len(sala.enemigos)
        self.assertEqual(vivos, 10)


class TestM6Recorte(unittest.TestCase):

    def test_bench_m6_recorte_nfr403(self):
        r = _revisar(B.medir_recorte(historias=(20, 60), repeticiones=REP), 2)
        self.assertEqual([x.tamano for x in r], [20, 60])
        for x in r:
            self.assertEqual(x.caso, "pergamino: recorte + copia del punto de control")

    def test_bench_m6_la_prueba_deja_la_linea_en_el_estado_esperado_nfr403(self):
        linea, motor = B._linea_y_motor_para_recorte(historia=40, k=5)
        B._leer_pergamino(linea, motor)
        self.assertEqual(len(linea.acciones), 39)
        self.assertEqual(linea.puntos[-1].acciones_completadas, 39)
        self.assertEqual(motor.jugador.acciones, 39)


class TestCostoPorAccion(unittest.TestCase):

    def test_bench_costo_por_accion_con_y_sin_linea_nfr401(self):
        r = _revisar(B.medir_costo_por_accion(acciones=30, repeticiones=REP), 2)
        self.assertEqual(r[0].caso, "ServicioLineaTiempo.ejecutar con línea activa")
        self.assertEqual(r[1].caso, "ServicioLineaTiempo.ejecutar sin línea (descartada)")
        for x in r:
            self.assertIn("µs por acción", x.nota)


class TestPartidaSintetica(unittest.TestCase):

    def test_la_partida_sintetica_llega_a_las_acciones_pedidas_y_es_repetible(self):
        a = B._partida_con(acciones=ACCIONES, k=5)
        b = B._partida_con(acciones=ACCIONES, k=5)
        self.assertEqual(a.jugador.acciones, ACCIONES)
        self.assertFalse(a.motor.terminado)
        self.assertEqual(a.motor.reloj, b.motor.reloj)                      # determinista por semilla
        self.assertEqual(len(a.linea.acciones), ACCIONES)

    def test_sin_puntos_de_control_solo_queda_el_punto_cero(self):
        contexto = B._partida_con(acciones=ACCIONES, k=B.SIN_PUNTOS)
        self.assertEqual(len(contexto.linea.puntos), 1)


class TestMedirYBenchInventario(unittest.TestCase):

    def test_medir_junta_los_grupos_en_orden(self):
        nombres = ["medir_historia", "medir_posiciones", "medir_memoria", "medir_ubicar_punto",
                   "medir_copia", "medir_recorte", "medir_costo_por_accion"]
        filas = [ResultadoBenchDTO(SUBSISTEMA, f"caso {i}", i, 0.1, 0.2, "n") for i in range(len(nombres))]
        parches = [mock.patch.object(B, nombres[i], return_value=[filas[i]]) for i in range(len(nombres))]
        for p in parches:
            p.start()
        try:
            self.assertEqual(B.medir(), filas)
        finally:
            for p in parches:
                p.stop()

    def test_bench_inventario_medir_incluye_la_linea_de_tiempo_nfr401(self):
        fila = ResultadoBenchDTO(SUBSISTEMA, "caso", 1, 0.1, 0.2, "n")
        vacio = mock.Mock(return_value=[])
        with mock.patch.object(BenchInventario, "medir_estructura", vacio), \
                mock.patch.object(BenchInventario, "medir_inventario", vacio), \
                mock.patch.object(BenchInventario, "medir_historial", vacio), \
                mock.patch.object(BenchInventario, "medir_buffer", vacio), \
                mock.patch.object(BenchInventario, "medir_ordenamiento", vacio), \
                mock.patch.object(BenchInventario.BenchLineaTiempo, "medir", return_value=[fila]):
            self.assertEqual(BenchInventario.medir(), [fila])

    def test_bench_no_usa_lo_prohibido_por_el_enunciado(self):
        texto = (Path(RAIZ) / "Service" / "BenchLineaTiempo.py").read_text(encoding="utf-8")
        for prohibido in ("sorted(", ".sort(", "heapq", "bisect", "import copy", "from copy", "collections",
                          "tracemalloc", "deque", "random.seed(", "random.randint("):
            self.assertNotIn(prohibido, texto, prohibido)

    def test_la_linea_de_prueba_es_una_linea_valida(self):
        linea = B._linea_con_puntos(10, k=3)
        self.assertIsInstance(linea, LineaTiempo)
        self.assertIsInstance(linea.puntos[0], PuntoControl)
        self.assertEqual(len(linea.acciones), 10)


if __name__ == "__main__":
    unittest.main()
