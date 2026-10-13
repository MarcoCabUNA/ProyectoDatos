"""
Pruebas de --bench: Service/Cronometro.py, Service/BenchDatos.py, Service/ServicioBench.py y
DTO/ResultadoBenchDTO.py. Las mediciones se corren con tamaños CHICOS para que sean rápidas; los
tiempos no se comparan (dependen de la computadora), solo la forma de los resultados y los conteos.
"""
import dataclasses
import os
import shutil
import tempfile
import unittest

from DTO.ResultadoBenchDTO import ResultadoBenchDTO
from Service import BenchDatos, BenchInventario, BenchLogica
from Service.Cronometro import medir, mejor_y_mediana
from Service.ServicioBench import ServicioBench


class PruebasCronometro(unittest.TestCase):

    def test_mejor_y_mediana(self):
        self.assertEqual(mejor_y_mediana([3.0, 1.0, 2.0]), (1.0, 2.0))
        self.assertEqual(mejor_y_mediana([4.0, 1.0, 3.0, 2.0]), (1.0, 2.5))      # par: promedio de los del medio
        self.assertEqual(mejor_y_mediana([5.0]), (5.0, 5.0))
        with self.assertRaises(ValueError):
            mejor_y_mediana([])

    def test_medir_repite_y_calienta(self):
        llamadas = []
        mejor, mediana = medir(lambda: llamadas.append(1), repeticiones=4)
        self.assertEqual(len(llamadas), 5)                                        # 1 de calentamiento + 4
        self.assertTrue(0 <= mejor <= mediana)
        llamadas.clear()
        medir(lambda: llamadas.append(1), repeticiones=4, calentar=False)
        self.assertEqual(len(llamadas), 4)

    def test_preparar_se_pasa_a_la_funcion(self):
        recibidos = []
        contador = [0]

        def preparar():
            contador[0] += 1
            return contador[0]

        medir(recibidos.append, repeticiones=3, preparar=preparar, calentar=False)
        self.assertEqual(recibidos, [1, 2, 3])                                    # un estado nuevo por repetición

    def test_repeticiones_invalidas(self):
        for malo in (0, -1, True, 2.5):
            with self.assertRaises(ValueError):
                medir(lambda: None, repeticiones=malo)                            # type: ignore[arg-type]


class PruebasBenchDatos(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.mkdtemp()
        self.carpeta = os.path.join(self.temp, "bench_tmp")

    def tearDown(self):
        shutil.rmtree(self.temp)

    def revisar(self, resultados, subsistema, cantidad):
        self.assertEqual(len(resultados), cantidad)
        for r in resultados:
            self.assertIsInstance(r, ResultadoBenchDTO)
            self.assertEqual(r.subsistema, subsistema)
            self.assertTrue(0 <= r.mejor_ms <= r.mediana_ms, r)

    def test_cache_mide_la_alternativa_descartada(self):
        r = BenchDatos.medir_cache(tamanos=(5, 50), consultas=20, repeticiones=2)
        self.revisar(r, "caché", 4)
        self.assertEqual([x.tamano for x in r], [5, 5, 50, 50])
        self.assertEqual([x.caso for x in r[:2]], ["búsqueda binaria (CacheCatalogo)", "búsqueda lineal (descartada)"])

    def test_busqueda_lineal_correcta(self):
        ids = ["a", "b", "c"]
        self.assertTrue(BenchDatos._contiene_lineal(ids, "c"))
        self.assertFalse(BenchDatos._contiene_lineal(ids, "z"))
        self.assertFalse(BenchDatos._contiene_lineal([], "a"))

    def test_fichas_liberadas_y_borra_la_carpeta(self):
        r = BenchDatos.medir_fichas_liberadas(cantidad=15, repeticiones=2, carpeta=self.carpeta)
        self.revisar(r, "fichas liberadas", 2)
        self.assertIn("2 solicitudes", r[0].nota)                                # 15 fichas = 2 lotes de 10
        self.assertFalse(os.path.exists(self.carpeta))

    def test_precarga_hace_menos_solicitudes_que_una_por_sala(self):
        r = BenchDatos.medir_precarga(lados=(5,), pasos=20, repeticiones=2)
        self.revisar(r, "precarga", 1)
        self.assertEqual(r[0].tamano, 25)
        self.assertIn("20 salas recorridas", r[0].nota)
        solicitudes = int(r[0].nota.split(": ")[1].split(" ")[0])
        self.assertLess(solicitudes, 20)

    def test_zigzag_recorre_salas_vecinas(self):
        self.assertEqual(BenchDatos._zigzag(3, 9), [1, 2, 3, 6, 5, 4, 7, 8, 9])
        self.assertEqual(BenchDatos._zigzag(3, 4), [1, 2, 3, 6])

    def test_guardado_y_borra_la_carpeta(self):
        r = BenchDatos.medir_guardado(tamanos=(3, 10), repeticiones=2, carpeta=self.carpeta)
        self.revisar(r, "guardado", 12)                                           # 6 casos por tamaño
        self.assertIn("binario", r[0].nota)
        self.assertIn("JSON", r[0].nota)
        self.assertFalse(os.path.exists(self.carpeta))

    def test_bitacora_y_borra_la_carpeta(self):
        r = BenchDatos.medir_bitacora(tamanos=(5, 30), anexos=3, repeticiones=2, carpeta=self.carpeta)
        self.revisar(r, "bitácora", 4)
        self.assertEqual([x.caso for x in r[:2]], ["leer el log completo", "anexar 1 acción"])
        self.assertFalse(os.path.exists(self.carpeta))

    def test_si_falla_igual_borra_la_carpeta(self):
        os.makedirs(os.path.join(self.carpeta, "sobra", "adentro"))               # basura de una corrida anterior
        with self.assertRaises(ValueError):
            BenchDatos.medir_fichas_liberadas(cantidad=3, repeticiones=0, carpeta=self.carpeta)
        self.assertFalse(os.path.exists(self.carpeta))


class PruebasServicioBench(unittest.TestCase):

    def test_junta_en_orden_y_avisa_el_avance(self):
        a = ResultadoBenchDTO("x", "a", 1, 0.1, 0.2)
        b = ResultadoBenchDTO("y", "b", 2, 0.3, 0.4, "nota")
        avances = []
        servicio = ServicioBench([lambda: [a], lambda: [], lambda: [b]])
        self.assertEqual(servicio.ejecutar(lambda i, n: avances.append((i, n))), [a, b])
        self.assertEqual(avances, [(1, 3), (2, 3), (3, 3)])

    def test_por_defecto_usa_los_tres_archivos(self):
        servicio = ServicioBench()
        self.assertEqual(servicio._mediciones, [BenchDatos.medir, BenchLogica.medir, BenchInventario.medir])
        self.assertEqual((BenchLogica.medir(), BenchInventario.medir()), ([], []))   # pendientes de Marco y Kristel

    def test_tabla_texto(self):
        resultados = [ResultadoBenchDTO("caché", "búsqueda binaria", 25, 0.3, 0.32, "500 consultas"),
                      ResultadoBenchDTO("guardado", "cargar 1 sala: binario", 2000, 0.034, 0.035)]
        texto = ServicioBench.tabla_texto(resultados)
        lineas = texto.split("\n")
        self.assertEqual(len(lineas), 4)                                          # encabezado, separador y 2 filas
        for columna in ("subsistema", "caso", "tamaño", "mejor ms", "mediana ms", "nota"):
            self.assertIn(columna, lineas[0])
        self.assertIn("0.300", lineas[2])
        self.assertIn("500 consultas", lineas[2])
        self.assertEqual(lineas[2].index("|"), lineas[3].index("|"))              # columnas alineadas
        self.assertEqual(ServicioBench.tabla_texto([]).count("\n"), 1)

    def test_dto_inmutable(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            setattr(ResultadoBenchDTO("x", "y", 1, 0.0, 0.0), "tamano", 2)


if __name__ == "__main__":
    unittest.main()