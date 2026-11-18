"""
Pruebas de Logic/BusquedaCostoMinimo.py y Logic/GrafoEsqueleto.py (feature 001, T017).

La búsqueda recibe el grafo como parámetro (contracts/busqueda-rutas.md), así que aquí se prueba con
grafos pequeños hechos en la propia prueba. FR-108 a FR-111 y FR-119.

    python -m unittest tests.test_busqueda_costo_minimo -v
"""
import os
import random
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.Direcciones import E, N, O, S  # noqa: E402
from Logic.BusquedaCostoMinimo import BusquedaCostoMinimo, paso_desde_cero  # noqa: E402
from Logic.GrafoEsqueleto import GrafoEsqueleto  # noqa: E402
from tests.ayudas_terreno import mazmorra_con_costos, salida, salida_sin_vuelta  # noqa: E402


class GrafoPrueba:
    """Grafo dirigido para las pruebas: aristas (origen, destino, costo), en el orden en que se agregan."""

    def __init__(self, cantidad: int, aristas: list[tuple[int, int, int]]):
        self.cantidad = cantidad
        self.aristas = list(aristas)

    def cantidad_salas(self) -> int:
        return self.cantidad

    def salidas(self, u: int) -> list[tuple[int, int]]:
        return [(v, c) for (o, v, c) in self.aristas if o == u]

    def entradas(self, x: int) -> list[tuple[int, int]]:
        return [(o, c) for (o, v, c) in self.aristas if v == x]


def doble(aristas: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    """Cada arista en los dos sentidos, con el mismo costo (como una salida con sus dos caras)."""
    resultado = []
    for u, v, c in aristas:
        resultado.append((u, v, c))
        resultado.append((v, u, c))
    return resultado


def dijkstra_referencia(grafo: GrafoPrueba, origen: int) -> list:
    """Distancia de cada sala HACIA 'origen', con un algoritmo O(S²) escrito en la prueba (oráculo)."""
    n = grafo.cantidad_salas()
    dist = [None] * n
    hecho = [False] * n
    dist[origen] = 0
    for _ in range(n):
        x = None
        for i in range(n):
            if not hecho[i] and dist[i] is not None and (x is None or dist[i] < dist[x]):
                x = i
        if x is None:
            break
        hecho[x] = True
        for u, c in grafo.entradas(x):
            if dist[u] is None or dist[x] + c < dist[u]:
                dist[u] = dist[x] + c
    return dist


class TestBusquedaCostoMinimo(unittest.TestCase):

    def test_fr108_distancias_con_costos_no_uniformes(self):
        # 0 -1(10)- 1 -(10)- 3 ; 0 -(50)- 2 -(1)- 3 ; 1 -(100)- 2
        grafo = GrafoPrueba(4, doble([(0, 1, 10), (1, 3, 10), (0, 2, 50), (2, 3, 1), (1, 2, 100)]))
        busqueda = BusquedaCostoMinimo(grafo)
        busqueda.reiniciar(3)
        self.assertEqual(busqueda.distancia_hasta(0, None), 20)
        self.assertEqual(busqueda.distancia_hasta(2, None), 1)
        self.assertEqual(busqueda.distancia_hasta(1, None), 10)

    def test_fr108_igual_que_una_referencia_en_grafos_al_azar(self):
        azar = random.Random(5)
        for _ in range(40):
            n = azar.randint(2, 25)
            aristas = []
            for _ in range(azar.randint(0, 3 * n)):
                u, v = azar.randint(0, n - 1), azar.randint(0, n - 1)
                if u != v:
                    aristas.append((u, v, azar.randint(1, 300)))
            grafo = GrafoPrueba(n, aristas)
            origen = azar.randint(0, n - 1)
            esperado = dijkstra_referencia(grafo, origen)
            busqueda = BusquedaCostoMinimo(grafo)
            busqueda.reiniciar(origen)
            for sala in range(n):
                self.assertEqual(busqueda.distancia_hasta(sala, None), esperado[sala])

    def test_fr109_sin_ruta_devuelve_none(self):
        grafo = GrafoPrueba(3, doble([(0, 1, 10)]))
        busqueda = BusquedaCostoMinimo(grafo)
        busqueda.reiniciar(0)
        self.assertIsNone(busqueda.distancia_hasta(2, None))

    def test_fr109_fr110_corte_en_el_limite(self):
        grafo = GrafoPrueba(3, doble([(0, 1, 400), (1, 2, 300)]))
        busqueda = BusquedaCostoMinimo(grafo)
        busqueda.reiniciar(0)
        self.assertIsNone(busqueda.distancia_hasta(2, 600))      # d = 700 > 600
        self.assertEqual(busqueda.distancia_hasta(2, 700), 700)  # d = límite: sí
        self.assertIsNone(busqueda.distancia_hasta(2, 699))      # ya resuelta, pero d > límite

    def test_la_busqueda_se_reanuda(self):
        grafo = GrafoPrueba(5, doble([(0, 1, 100), (1, 2, 100), (2, 3, 100), (3, 4, 100)]))
        reanudada = BusquedaCostoMinimo(grafo)
        reanudada.reiniciar(0)
        self.assertIsNone(reanudada.distancia_hasta(4, 100))
        resueltas_antes = reanudada.resueltas
        self.assertEqual(reanudada.distancia_hasta(4, 500), 400)
        de_una_vez = BusquedaCostoMinimo(grafo)
        de_una_vez.reiniciar(0)
        self.assertEqual(de_una_vez.distancia_hasta(4, 500), 400)
        # No se resuelve dos veces la misma sala: el total coincide con la búsqueda hecha de una vez.
        self.assertGreater(reanudada.resueltas, resueltas_antes)
        self.assertEqual(reanudada.resueltas, de_una_vez.resueltas)

    def test_reiniciar_cambia_la_generacion_y_no_filtra_distancias_viejas(self):
        grafo = GrafoPrueba(3, doble([(0, 1, 10), (1, 2, 10)]))
        busqueda = BusquedaCostoMinimo(grafo)
        busqueda.reiniciar(0)
        self.assertEqual(busqueda.distancia_hasta(2, None), 20)
        generacion = busqueda.generacion
        busqueda.reiniciar(2)
        self.assertEqual(busqueda.generacion, generacion + 1)
        self.assertFalse(busqueda.esta_resuelta(0))            # la sala 0 era resuelta en la búsqueda vieja
        self.assertEqual(busqueda.distancia_hasta(0, None), 20)
        self.assertEqual(busqueda.distancia_hasta(2, None), 0)

    def test_salida_sin_vuelta_se_recorre_al_reves(self):
        # Solo existe 0 -> 1 (sin vuelta). Desde 0 se llega a 1, pero no al revés.
        grafo = GrafoPrueba(2, [(0, 1, 30)])
        hacia_1 = BusquedaCostoMinimo(grafo)
        hacia_1.reiniciar(1)
        self.assertEqual(hacia_1.distancia_hasta(0, None), 30)
        hacia_0 = BusquedaCostoMinimo(grafo)
        hacia_0.reiniciar(0)
        self.assertIsNone(hacia_0.distancia_hasta(1, None))

    def test_fr111_paso_hacia_origen_escoge_la_vecina_de_menor_id(self):
        # Desde 1 hay dos rutas de costo 200 hacia 5: por 7 y por 4. La salida hacia 7 aparece primero.
        grafo = GrafoPrueba(8, doble([(1, 7, 100), (1, 4, 100), (7, 5, 100), (4, 5, 100)]))
        busqueda = BusquedaCostoMinimo(grafo)
        busqueda.reiniciar(5)
        d = busqueda.distancia_hasta(1, None)
        self.assertEqual(d, 200)
        self.assertEqual(busqueda.paso_hacia_origen(1, d), (4, 100))

    def test_fr119_dos_salidas_hacia_la_misma_vecina_usa_la_mas_barata(self):
        grafo = GrafoPrueba(3, doble([(0, 1, 300), (0, 1, 120), (1, 2, 100)]))
        busqueda = BusquedaCostoMinimo(grafo)
        busqueda.reiniciar(2)
        d = busqueda.distancia_hasta(0, None)
        self.assertEqual(d, 220)
        self.assertEqual(busqueda.paso_hacia_origen(0, d), (1, 120))

    def test_paso_desde_cero_igual_que_una_busqueda_nueva(self):
        grafo = GrafoPrueba(8, doble([(1, 7, 100), (1, 4, 100), (7, 5, 100), (4, 5, 100), (1, 5, 500)]))
        self.assertEqual(paso_desde_cero(grafo, 5, 1, None), (4, 100))
        self.assertEqual(paso_desde_cero(grafo, 5, 1, 200), (4, 100))
        self.assertIsNone(paso_desde_cero(grafo, 5, 1, 199))
        self.assertIsNone(paso_desde_cero(grafo, 5, 5, None))  # ya está en el origen: no hay paso
        self.assertIsNone(paso_desde_cero(GrafoPrueba(3, []), 0, 2, None))

    def test_fr111_desempate_al_azar_contra_la_referencia(self):
        azar = random.Random(9)
        for _ in range(40):
            n = azar.randint(3, 20)
            aristas = []
            for _ in range(azar.randint(n, 3 * n)):
                u, v = azar.randint(0, n - 1), azar.randint(0, n - 1)
                if u != v:
                    aristas.append((u, v, azar.choice([100, 100, 200])))   # muchos empates
            grafo = GrafoPrueba(n, doble(aristas))
            origen, u = azar.randint(0, n - 1), azar.randint(0, n - 1)
            dist = dijkstra_referencia(grafo, origen)
            paso = paso_desde_cero(grafo, origen, u, None)
            if u == origen or dist[u] is None:
                self.assertIsNone(paso)
                continue
            esperado = None
            for v, c in grafo.salidas(u):
                if dist[v] is not None and c + dist[v] == dist[u]:
                    if esperado is None or v < esperado[0] or (v == esperado[0] and c < esperado[1]):
                        esperado = (v, c)
            self.assertEqual(paso, esperado)


class TestGrafoEsqueleto(unittest.TestCase):
    """El grafo sobre la Mazmorra: salidas abiertas ahora, con el costo igualado (FR-112, FR-113)."""

    def setUp(self):
        self.m = mazmorra_con_costos(4, [salida(1, E, 2, 250), salida(2, S, 3, cerrada=True),
                                         salida_sin_vuelta(4, N, 1, 40)])
        self.grafo = GrafoEsqueleto(self.m)

    def test_cantidad_salas(self):
        self.assertEqual(self.grafo.cantidad_salas(), len(self.m.salas))

    def test_salidas_son_las_abiertas_con_costo(self):
        self.assertEqual(self.grafo.salidas(2), [(1, 250)])
        self.assertEqual(self.grafo.salidas(1), [(2, 250)])

    def test_entradas_son_las_salidas_abiertas_que_llegan(self):
        self.assertEqual(self.grafo.entradas(1), [(2, 250), (4, 40)])
        self.assertEqual(self.grafo.entradas(3), [])                 # la única que llega está cerrada

    def test_fr113_el_estado_de_la_puerta_se_lee_en_vivo(self):
        self.assertEqual(self.grafo.entradas(3), [])
        self.m.salida(2, S).cerrada = False
        self.assertEqual(self.grafo.entradas(3), [(2, 100)])
        self.assertEqual(self.grafo.entradas(2), [(1, 250)])         # la cara 3 -> 2 sigue cerrada
        self.m.salida(1, E).cerrada = True
        self.assertEqual(self.grafo.entradas(2), [])
        self.assertEqual(self.grafo.salidas(1), [])

    def test_fr112_busqueda_sobre_el_esqueleto(self):
        self.m.salida(2, S).cerrada = False
        self.m.salida(3, N).cerrada = False
        self.assertEqual(paso_desde_cero(self.grafo, 3, 4, None), (1, 40))
        self.assertEqual(paso_desde_cero(self.grafo, 3, 1, None), (2, 250))
        self.assertIsNone(paso_desde_cero(self.grafo, 4, 3, None))   # a la 4 no se puede volver


if __name__ == "__main__":
    unittest.main()
