"""
Pruebas de Logic/BenchResolubilidad.py (feature 003, integrante 2; research R7): el generador de criptas en cuadrícula
(T028; lo usan la prueba de recursión, T029, y las mediciones), y las mediciones B1 a B6 de --bench con el peine, las
variantes descartadas y la fila de la cripta del paquete de Service/ServicioBench.py (T059; NFR-301 a NFR-304).

cripta_en_cuadricula() se importa dentro de la prueba: hasta T030 cada prueba falla por su cuenta al importarlo.
"""
import contextlib
import dataclasses
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.CriptaDTO import ResumenCriptaDTO  # noqa: E402
from DTO.ReporteResolubilidadDTO import NO_RESOLUBLE, RESOLUBLE  # noqa: E402
from DTO.ResultadoBenchDTO import ResultadoBenchDTO  # noqa: E402
from Logic.GrafoLlaves import CERRADA_CON_LLAVE, GrafoLlaves  # noqa: E402
from Logic.RecorridoLlaves import RecorridoLlaves  # noqa: E402
from Logic.VerificadorResolubilidad import verificar  # noqa: E402
from tests.ayudas_resolubilidad import paquete_temporal  # noqa: E402


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


# ====================================================================== T059: mediciones B1 a B6 y fila del paquete
# Tamaños chicos: los umbrales de tiempo se leen en la tabla de T063, no en las pruebas. Los nombres nuevos de
# Logic/BenchResolubilidad.py se importan dentro de cada prueba: hasta T060 y T061 cada una falla por su cuenta.

def bench():
    """El módulo Logic/BenchResolubilidad.py."""
    from Logic import BenchResolubilidad
    return BenchResolubilidad


def peine(dientes, semilla):
    """cripta_en_peine(...). Hasta T061 no existe: es el fallo esperado."""
    return bench().cripta_en_peine(dientes, semilla)


def criptas_de_prueba():
    """(nombre, cripta) en cuadrículas resolubles y no resolubles y en peines."""
    criptas = []
    for filas, columnas, resoluble in ((2, 3, True), (10, 10, True), (3, 25, True), (4, 10, False), (4, 101, False),
                                       (2, 2, False)):
        criptas.append((f"cuadrícula {filas}×{columnas} {resoluble}", cuadricula(filas, columnas, 7, resoluble)))
    for dientes in (1, 2, 10, 57):
        criptas.append((f"peine {dientes}", peine(dientes, 7)))
    return criptas


@contextlib.contextmanager
def en_carpeta_temporal():
    """Cambia a una carpeta temporal vacía (para ver que no se crea partida.log) y la borra al salir."""
    anterior = os.getcwd()
    carpeta = tempfile.mkdtemp()
    os.chdir(carpeta)
    try:
        yield carpeta
    finally:
        os.chdir(anterior)
        shutil.rmtree(carpeta, ignore_errors=True)


def archivos_log(carpeta):
    """Rutas de los partida.log que haya dentro de 'carpeta'."""
    encontrados = []
    for raiz, _, archivos in os.walk(carpeta):
        for nombre in archivos:
            if nombre == "partida.log":
                encontrados.append(os.path.join(raiz, nombre))
    return encontrados


def paquete_con(carpeta, criptas):
    """Paquete temporal con varias criptas (en ese orden en criptas.json). criptas: [(dto, salas, ubicaciones o None)]."""
    for dto, salas, ubicaciones in criptas:
        paquete_temporal(carpeta, dto, salas, ubicaciones)
    with open(os.path.join(carpeta, "criptas.json"), "w", encoding="utf-8") as f:
        json.dump({"criptas": [ResumenCriptaDTO(dto.id, "Prueba", dto.salas_total, 1).a_diccionario()
                               for dto, _, _ in criptas]}, f)
    return carpeta


def con_id(datos, id_cripta):
    """La misma cripta sintética con otro id."""
    dto, salas, ubicaciones = datos
    return dataclasses.replace(dto, id=id_cripta), salas, ubicaciones


class PruebasBench(unittest.TestCase):
    """T059: B1 a B6 (research R7), las variantes descartadas y la fila de la cripta del paquete (NFR-301 a NFR-304)."""

    def test_nfr304_peine_es_determinista_por_semilla(self):
        a = peine(20, 3)
        b = peine(20, 3)
        self.assertEqual(a, b)                                               # mismas salas, ubicaciones y orden
        otra = peine(20, 4)
        self.assertEqual(otra[1], a[1])                                      # el esqueleto no depende de la semilla
        self.assertNotEqual(otra[2], a[2])                                   # otro orden de la lista
        self.assertEqual(sala_de_cada_llave(otra[2]), sala_de_cada_llave(a[2]))   # las llaves en las mismas salas
        for dientes in (1, 5, 20):
            with self.subTest(dientes=dientes):
                dto, salas, ubicaciones = peine(dientes, 9)
                self.assertEqual((len(salas), dto.salas_total), (2 * dientes + 1, 2 * dientes + 1))
                self.assertEqual(len(ubicaciones), dientes + 1)              # una por diente más llave_salida
                reporte = verificar(dto, salas, ubicaciones)
                self.assertEqual(reporte.veredicto, RESOLUBLE)
                self.assertEqual(len(reporte.orden_llaves), dientes + 1)
                self.assertEqual(reporte.orden_llaves[-1], dto.llave_salida)
                grafo = GrafoLlaves(dto, salas, ubicaciones)
                recorrido = RecorridoLlaves(grafo)
                recorrido.recorrer()
                self.assertEqual(recorrido.oleada_llave[grafo.llave_salida], dientes)   # una llave por oleada
                frontera_inicial = 0                                         # todas las puertas a los dientes
                for c in range(len(grafo.tipo_cara)):
                    if grafo.tipo_cara[c] == CERRADA_CON_LLAVE and grafo.destino[c] > dientes \
                            and c // 4 <= dientes:
                        frontera_inicial += 1
                self.assertEqual(frontera_inicial, dientes)

    def test_nfr302_ingenua_da_el_mismo_orden_que_la_incremental(self):
        for nombre, (dto, salas, ubicaciones) in criptas_de_prueba():
            with self.subTest(cripta=nombre):
                grafo = GrafoLlaves(dto, salas, ubicaciones)
                recorrido = RecorridoLlaves(grafo)
                recorrido.recorrer()
                esperado = [grafo.ids[k] for k in recorrido.orden]
                resoluble, orden = bench().verificar_ingenua(dto, salas, ubicaciones)
                self.assertEqual(orden, esperado)                            # misma definición de oleada (R5)
                reporte = verificar(dto, salas, ubicaciones)
                self.assertEqual(resoluble, reporte.veredicto == RESOLUBLE)
                if resoluble:
                    self.assertEqual(orden, reporte.orden_llaves)

    def test_r3_indice_lineal_da_el_mismo_indice(self):
        for nombre, (dto, salas, ubicaciones) in criptas_de_prueba():
            with self.subTest(cripta=nombre):
                desordenadas = list(reversed(ubicaciones))                  # otro orden de entrada: mismo índice
                for entrada in (ubicaciones, desordenadas):
                    grafo, menciones = bench().menciones_de(dto, salas, entrada)
                    referencia = GrafoLlaves(dto, salas, entrada)
                    lineal = bench().indice_lineal(menciones, len(grafo.tipo_cara), len(entrada))
                    ordenando = bench().indice_ordenando(grafo, menciones, len(entrada))
                    self.assertEqual(lineal, ordenando)
                    ids, llave_cara, llave_de_entrada, llave_salida = lineal
                    self.assertEqual(ids, referencia.ids)
                    self.assertEqual(llave_cara, referencia.llave_cara)
                    self.assertEqual(llave_salida, referencia.llave_salida)
                    for i in range(len(entrada)):
                        self.assertEqual(ids[llave_de_entrada[i]], entrada[i].id)

    def test_r4_frontera_en_una_lista_da_el_mismo_resultado(self):
        for nombre, (dto, salas, ubicaciones) in criptas_de_prueba():
            with self.subTest(cripta=nombre):
                grafo = GrafoLlaves(dto, salas, ubicaciones)
                agrupada = RecorridoLlaves(grafo)
                agrupada.recorrer()
                unica = bench().RecorridoListaUnica(grafo)
                unica.recorrer()
                self.assertEqual(unica.orden, agrupada.orden)
                self.assertEqual(unica.oleada_llave, agrupada.oleada_llave)
                self.assertEqual(unica.alcanzable, agrupada.alcanzable)
                self.assertEqual(unica.caras_de_salida, agrupada.caras_de_salida)

    def test_nfr304_medir_devuelve_b1_a_b6(self):
        cuadriculas = ((2, 3), (3, 4), (4, 5))
        dientes = (3, 5, 8)
        resultados = bench().medir(cuadriculas=cuadriculas, desglose=(3, 4), dientes=dientes, repeticiones=2)
        casos = []
        for r in resultados:
            self.assertIsInstance(r, ResultadoBenchDTO)
            self.assertEqual(r.subsistema, "resolubilidad")
            self.assertTrue(0 <= r.mejor_ms <= r.mediana_ms, r)
            self.assertNotEqual(r.nota, "")
            casos.append(r.caso)
        for prefijo in ("B1 ", "B2 ", "B3 ", "B4 ", "B5 ", "B6 "):
            self.assertTrue(any(caso.startswith(prefijo) for caso in casos), prefijo)
        salas = [f * c for f, c in cuadriculas]
        salas_peine = [2 * d + 1 for d in dientes]

        def filas(prefijo):
            return [r for r in resultados if r.caso.startswith(prefijo)]

        for prefijo in ("B1 ", "B2 ", "B3 "):
            with self.subTest(medicion=prefijo):
                self.assertEqual([r.tamano for r in filas(prefijo)], salas)
                self.assertIn("×", filas(prefijo)[1].nota)                  # factor respecto del tamaño anterior
        self.assertEqual(len(filas("B4 ")), 4)                              # preparación, recorrido, ciclos, armado
        self.assertEqual({r.tamano for r in filas("B4 ")}, {12})
        self.assertEqual([r.tamano for r in filas("B5 ")], [s for s in salas for _ in range(2)])
        self.assertEqual([r.tamano for r in filas("B6 ")], [s for s in salas_peine for _ in range(2)])
        # las alternativas cuadráticas, en el tamaño mayor, con una sola repetición (y la nota lo dice)
        self.assertIn("1 repetición", filas("B2 ")[-1].nota)
        self.assertNotIn("1 repetición", filas("B1 ")[-1].nota)
        self.assertIn("1 repetición", [r for r in filas("B5 ") if "descartada" in r.caso][-1].nota)
        self.assertIn("1 repetición", [r for r in filas("B6 ") if "descartada" in r.caso][-1].nota)

    def test_nfr304_servicio_bench_incluye_resolubilidad_despues_de_logica(self):
        from Logic import BenchLogica
        from Service.ServicioBench import ServicioBench
        lista = ServicioBench()._mediciones
        self.assertIn(bench().medir, lista)
        self.assertEqual(lista.index(bench().medir), lista.index(BenchLogica.medir) + 1)

    def test_nfr301_sc306_bench_mide_la_cripta_con_mas_salas_del_paquete(self):
        from Data.ClienteHttp import ClienteHttp
        from Service.ServicioBench import ServicioBench
        chica = cuadricula(2, 3, 1, True)                                    # 6 salas
        grande = cuadricula(3, 5, 1, True)                                   # 15 salas
        prohibido = AssertionError("--bench no hace solicitudes de red")
        # en las dos combinaciones de id y de orden: la elección no sale del id ni de la posición en criptas.json
        for id_chica, id_grande, grande_primero in (("a-chica", "b-grande", False), ("b-chica", "a-grande", True),
                                                    ("b-chica", "a-grande", False), ("a-chica", "b-grande", True)):
            with self.subTest(grande=id_grande, primero=grande_primero), en_carpeta_temporal() as carpeta:
                datos = [con_id(chica, id_chica), con_id(grande, id_grande)]
                if grande_primero:
                    datos.reverse()
                ruta = paquete_con(os.path.join(carpeta, "paquete"), datos)
                with mock.patch.object(ClienteHttp, "get_json", side_effect=prohibido), \
                        mock.patch("requests.Session.request", side_effect=prohibido):
                    filas = ServicioBench(carpeta_paquete=ruta).medir_cripta_del_paquete(repeticiones=2)
                    # y dentro de ejecutar(), justo después de las filas de BenchResolubilidad
                    marca = ResultadoBenchDTO("resolubilidad", "B1 falsa", 1, 0.0, 0.0, "x")
                    with mock.patch.object(bench(), "medir", return_value=[marca]):
                        servicio = ServicioBench([lambda: [], bench().medir, lambda: []], carpeta_paquete=ruta)
                        todas = servicio.ejecutar()
                self.assertEqual(len(filas), 1)
                fila = filas[0]
                self.assertEqual(fila.subsistema, "resolubilidad")
                self.assertEqual(fila.tamano, 15)
                self.assertIn(id_grande, fila.nota)
                self.assertNotIn(id_chica, fila.nota)
                self.assertTrue(0 <= fila.mejor_ms <= fila.mediana_ms)
                self.assertEqual([r.caso for r in todas], ["B1 falsa", fila.caso])
                self.assertEqual(archivos_log(carpeta), [])                 # no inicia partidas
        # una cripta sin llaves.json no se elige aunque tenga más salas
        with en_carpeta_temporal() as carpeta:
            ruta = paquete_con(os.path.join(carpeta, "paquete"),
                               [con_id(chica, "con-llaves"), (con_id(grande, "sin-llaves")[0], grande[1], None)])
            filas = ServicioBench(carpeta_paquete=ruta).medir_cripta_del_paquete(repeticiones=2)
            self.assertEqual([(r.tamano, "con-llaves" in r.nota) for r in filas], [(6, True)])
        # sin criptas con llaves.json (o sin paquete): no hay medición y la nota dice por qué
        with en_carpeta_temporal() as carpeta:
            ruta = paquete_con(os.path.join(carpeta, "paquete"), [(chica[0], chica[1], None)])
            for carpeta_paquete in (ruta, os.path.join(carpeta, "no-existe")):
                with self.subTest(carpeta=carpeta_paquete):
                    filas = ServicioBench(carpeta_paquete=carpeta_paquete).medir_cripta_del_paquete(repeticiones=2)
                    self.assertEqual(len(filas), 1)
                    self.assertEqual((filas[0].tamano, filas[0].mejor_ms, filas[0].mediana_ms), (0, 0.0, 0.0))
                    self.assertIn("no se agregó", filas[0].nota)
                    self.assertIn("llaves.json", filas[0].nota)
            self.assertEqual(archivos_log(carpeta), [])


if __name__ == "__main__":
    unittest.main()
