"""
Pruebas de Logic/BenchMapaConocido.py (feature 002, integrante 2, T051): B1 a B11 con tamaños chicos, sin vista
(Principio V). Los umbrales de tiempo se leen en la tabla de --bench (T056), no aquí: estas pruebas fijan que las
cargas son deterministas por semilla, que cada alternativa descartada da el mismo mapa que la decisión y que medir()
devuelve los once casos.

Fallan al importar Logic.BenchMapaConocido hasta T052; la de ServicioBench, hasta T055.

    python -m unittest tests.test_bench_mapa -v
"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.ResultadoBenchDTO import ResultadoBenchDTO  # noqa: E402
from Logic.BusquedaCostoMinimo import paso_desde_cero  # noqa: E402
from tests.ayudas_mapa import estados  # noqa: E402
from tests.test_grafo_mapa_conocido import GrafoFiltradoAMano  # noqa: E402

DESCONOCIDA, AVISTADA, EXPLORADA = 0, 1, 2


def bench():
    from Logic import BenchMapaConocido      # hasta T052 no existe: es el fallo esperado
    return BenchMapaConocido


def esqueleto(mazmorra) -> list:
    """Nombre, destinos, costos y estado de cada salida de cada sala, para comparar dos criptas."""
    filas = []
    for sala in mazmorra.salas:
        if sala is None:
            filas.append(None)
            continue
        salidas = []
        for s in sala.salidas:
            salidas.append(None if s is None else (s.destino, s.costo, s.cerrada))
        filas.append((sala.id, sala.nombre, salidas))
    return filas


class PruebasCargasDelBench(unittest.TestCase):

    def test_nfr204_cuadriculas_deterministas_por_semilla(self):
        B = bench()
        uno, otro = B.armar_cuadricula(6), B.armar_cuadricula(6)
        self.assertEqual(esqueleto(uno), esqueleto(otro))
        self.assertEqual(len(uno.salas), 37)                     # 6 × 6 salas, ids 1..36
        self.assertEqual(estados(B.mapa_por_tercios(uno)), estados(B.mapa_por_tercios(otro)))
        estado = B.mapa_por_tercios(uno).estado
        for valor in (DESCONOCIDA, AVISTADA, EXPLORADA):         # un tercio de las salas en cada estado
            self.assertEqual(estado[1:].count(valor), 12)
        self.assertEqual(estados(B.mapa_para_antorcha(uno, 6)[0]), estados(B.mapa_para_antorcha(otro, 6)[0]))
        self.assertEqual(estados(B.mapa_completo(uno)), estados(B.mapa_completo(otro)))

    def test_r1_lista_de_exploradas_da_el_mismo_estado(self):
        B = bench()
        mapa = B.mapa_por_tercios(B.armar_cuadricula(6))
        exploradas, avistadas = B.listas_de_ids(mapa)
        for sala in range(len(mapa.estado)):
            self.assertEqual(B.estado_por_lista(exploradas, avistadas, sala), mapa.estado_sala(sala), f"sala {sala}")

    def test_r2_recalcular_avistadas_da_el_mismo_mapa(self):
        B = bench()
        mapa, historial, jugador, centro = B.mapa_para_antorcha(B.armar_cuadricula(6), 6)
        self.assertEqual(B.recalcular_avistadas(mapa), mapa.estado)
        B.entrar_con_antorcha(mapa, jugador, centro)
        self.assertEqual(mapa.estado_sala(centro), EXPLORADA)
        self.assertEqual(B.recalcular_avistadas(mapa), mapa.estado)

    def test_r3_copiar_y_restaurar_da_el_mismo_mapa(self):
        B = bench()
        mapa, _, jugador, centro = B.mapa_para_antorcha(B.armar_cuadricula(6), 6, con_historial=False)
        antes = estados(mapa)
        B.copiar_entrar_y_restaurar(mapa, jugador, centro)
        self.assertEqual(estados(mapa), antes)

    def test_nfr203_b6_vuelve_al_mapa_de_antes(self):
        B = bench()
        mapa, historial, jugador, centro = B.mapa_para_antorcha(B.armar_cuadricula(6), 6)
        antes = estados(mapa)
        B.entrar_con_antorcha(mapa, jugador, centro)
        self.assertNotEqual(estados(mapa), antes)                # la entrada sí cambió casillas
        historial.cerrar_intervalo()
        self.assertTrue(historial.deshacer())
        self.assertEqual(estados(mapa), antes)
        B.entrar_cerrar_y_deshacer(mapa, historial, jugador, centro)   # lo que cronometra B6
        self.assertEqual(estados(mapa), antes)

    def test_nfr205_b8_mapa_igual_al_de_un_motor_de_control(self):
        B = bench()
        for con_puertas in (False, True):
            with self.subTest(con_puertas=con_puertas):
                comparaciones, caras_cambiadas = B.comprobar_contra_control(lado=6, cazadores=3, otros=2, ciclos=12,
                                                                            con_puertas=con_puertas)
                self.assertEqual(comparaciones, 12)
                if con_puertas:                                  # el aviso llegó al mapa por el repartidor
                    self.assertGreater(caras_cambiadas, 0)
                else:
                    self.assertEqual(caras_cambiadas, 0)

    def test_r5_b11_paso_igual_al_de_un_grafo_filtrado_a_mano(self):
        B = bench()
        for lado in (4, 6, 7):
            mazmorra = B.armar_cuadricula(lado)
            for mapa in (B.mapa_completo(mazmorra), B.mapa_por_tercios(mazmorra)):
                with self.subTest(lado=lado, explorado=mapa.estado.count(EXPLORADA)):
                    esperado = paso_desde_cero(GrafoFiltradoAMano(mapa, mazmorra), lado * lado, 1, None)
                    self.assertEqual(B.paso_b11(mapa, lado), esperado)
            self.assertIsNotNone(B.paso_b11(B.mapa_completo(mazmorra), lado))   # con el mapa completo hay ruta


class PruebasMediciones(unittest.TestCase):

    def test_nfr204_medir_devuelve_b1_a_b11(self):
        B = bench()
        resultados = B.medir(lados=(4, 6), repeticiones=2, consultas=200, consultas_lista=20, lado_ciclo=6,
                             cazadores=3, otros=2, ciclos=4)
        casos = []
        for r in resultados:
            self.assertIsInstance(r, ResultadoBenchDTO)
            self.assertEqual(r.subsistema, "mapa conocido")
            self.assertTrue(0 <= r.mejor_ms <= r.mediana_ms, r)
            self.assertNotEqual(r.nota, "")
            prefijo = r.caso.split(" ")[0]
            if not casos or casos[-1] != prefijo:
                casos.append(prefijo)
        self.assertEqual(casos, [f"B{i}" for i in range(1, 12)])
        tamanos_b1 = [r.tamano for r in resultados if r.caso.startswith("B1 ")]
        self.assertEqual(tamanos_b1, [16, 36])
        self.assertIn("cumple", [r for r in resultados if r.caso.startswith("B8 ")][0].nota)

    def test_nfr204_servicio_bench_incluye_mapa_conocido(self):
        from Logic import BenchLogica
        from Service.ServicioBench import ServicioBench
        B = bench()
        mediciones = ServicioBench()._mediciones
        self.assertIn(B.medir, mediciones)
        self.assertGreater(mediciones.index(B.medir), mediciones.index(BenchLogica.medir))


if __name__ == "__main__":
    unittest.main()
