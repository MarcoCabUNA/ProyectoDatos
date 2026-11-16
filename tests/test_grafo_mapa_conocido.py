"""
Pruebas del contrato del mapa conocido para «ir a» (feature 002, integrante 2; contracts/contrato-mapa-conocido.md,
(a) y (c), confirmado por el integrante 3 en T005): GrafoMapaConocido con la interfaz de la búsqueda de la 001,
MapaConocido.buscar_exploradas y MapaConocido.es_explorada. Estas pruebas fijan el contrato: si cambian, se avisa
antes al integrante 3.

GrafoMapaConocido se importa dentro de grafo_de(): hasta T027 cada prueba del grafo falla por su cuenta al importarlo,
y las de buscar_exploradas y es_explorada fallan hasta T028.
"""
import os
import random
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from Logic.BusquedaCostoMinimo import paso_desde_cero  # noqa: E402
from Logic.HistorialRetroceso import HistorialRetroceso  # noqa: E402
from Logic.Mazmorra import Mazmorra  # noqa: E402
from tests.ayudas_mapa import (A, B, C, D, E, ESTE, F, NORTE, OESTE, SUR, cara_cerrada_sin_llave,  # noqa: E402
                               cripta_mapa, entrar_a, estados, mapa_de_prueba, salida, salida_sin_vuelta)
from tests.ayudas_terreno import salidas_con_costos  # noqa: E402

# Constantes del mapa con sus valores de data-model §1.
DESCONOCIDA, AVISTADA, EXPLORADA = 0, 1, 2
SIN_OBSERVAR, ABIERTA, CERRADA = 0, 1, 2


def grafo_de(mapa):
    """GrafoMapaConocido(mapa). Hasta T027 no existe: es el fallo esperado."""
    from Logic.GrafoMapaConocido import GrafoMapaConocido
    return GrafoMapaConocido(mapa)


class GrafoFiltradoAMano:
    """
    Referencia: el grafo de las salidas utilizables armado a mano, de una vez, recorriendo toda la cripta
    (u y v exploradas y la cara de u recordada abierta; costo = SalidaViva.costo).
    """

    def __init__(self, mapa, mazmorra):
        salas = mazmorra.salas
        self.total = len(salas)
        self._salidas = [[] for _ in range(self.total)]
        self._entradas = [[] for _ in range(self.total)]
        for u in range(self.total):
            if salas[u] is None or mapa.estado[u] != EXPLORADA:
                continue
            for d in range(4):
                s = salas[u].salidas[d]
                if s is None or s.destino >= self.total or salas[s.destino] is None:
                    continue
                if mapa.estado[s.destino] == EXPLORADA and mapa.caras[u * 4 + d] == ABIERTA:
                    self._salidas[u].append((s.destino, s.costo))
                    self._entradas[s.destino].append((u, s.costo))

    def cantidad_salas(self):
        return self.total

    def salidas(self, u):
        return self._salidas[u]

    def entradas(self, x):
        return self._entradas[x]


def cripta_h2_5():
    """
    A –E– B (solo la cara de B declara costo 150), A –S– C, A –N– D, B –S– E, E –E– C. Salas 1..5.
    El jugador empieza en B; entra a E con la antorcha (explora C) y vuelve a B con la antorcha (explora A).
    """
    return cripta_mapa(5, [(A, ESTE, B, None, 150, False, True), salida(A, SUR, C), salida(A, NORTE, D),
                           salida(B, SUR, E), salida(E, ESTE, C)])


def mapa_h2_5():
    mazmorra = cripta_h2_5()
    mapa, jugador = mapa_de_prueba(mazmorra, B, HistorialRetroceso())
    mapa.iniciar(B)
    entrar_a(mapa, jugador, E, True)
    entrar_a(mapa, jugador, B, True)
    return mazmorra, mapa, jugador


def cripta_cuadricula(n, azar, cerradas):
    """Cuadrícula n × n con costos 100 o 200 (muchos empates) y 'cerradas' puertas cerradas al azar."""
    tuplas = []
    for f in range(n):
        for c in range(n):
            sala = f * n + c + 1
            if c < n - 1:
                tuplas.append(salida(sala, ESTE, sala + 1, azar.choice([100, 200])))
            if f < n - 1:
                tuplas.append(salida(sala, SUR, sala + n, azar.choice([100, 200])))
    for _ in range(cerradas):
        i = azar.randrange(len(tuplas))
        a, d, b, costo, _, _, vuelta = tuplas[i]
        tuplas[i] = (a, d, b, costo, costo, True, vuelta)
    return cripta_mapa(n * n, tuplas)


def mapas_a_medias():
    """
    Varias criptas con el mapa a medias: salas exploradas (por entrada y por la antorcha), avistadas y desconocidas;
    caras abiertas, cerradas y sin observar; una con la cara de H2-6 y una con una salida sin vuelta.
    """
    resultado = []
    mazmorra, mapa, _ = mapa_h2_5()
    resultado.append((mazmorra, mapa))

    mazmorra = cripta_mapa(4, [salida(A, ESTE, B), salida(B, SUR, C), salida(C, OESTE, D)])
    cara_cerrada_sin_llave(mazmorra, A, B)
    mapa, jugador = mapa_de_prueba(mazmorra, A, HistorialRetroceso())
    mapa.iniciar(A)
    entrar_a(mapa, jugador, B)
    resultado.append((mazmorra, mapa))

    mazmorra = cripta_mapa(6, [salida(A, ESTE, B), salida_sin_vuelta(B, SUR, C), salida(C, ESTE, D),
                               salida(D, NORTE, E, cerrada=True), salida(E, OESTE, F)])
    mapa, jugador = mapa_de_prueba(mazmorra, A, HistorialRetroceso())
    mapa.iniciar(A)
    entrar_a(mapa, jugador, B)
    entrar_a(mapa, jugador, C, True)
    resultado.append((mazmorra, mapa))

    for semilla in (3, 11, 29):
        azar = random.Random(semilla)
        mazmorra = cripta_cuadricula(5, azar, 6)
        mapa, jugador = mapa_de_prueba(mazmorra, 1, HistorialRetroceso())
        mapa.iniciar(1)
        for _ in range(10):
            entrar_a(mapa, jugador, azar.randrange(1, 26), azar.random() < 0.5)
        resultado.append((mazmorra, mapa))
    return resultado


class PruebasGrafoMapaConocido(unittest.TestCase):

    def test_h2_5_a38_fr205_fr212_fr225_ofrece_solo_utilizables_con_costo_igualado(self):
        mazmorra, mapa, jugador = mapa_h2_5()
        self.assertEqual(jugador.Sala_Actual, B)
        for sala in (A, B, C):
            self.assertEqual(mapa.estado_sala(sala), EXPLORADA)
        self.assertEqual(mapa.estado_sala(D), AVISTADA)
        self.assertEqual(mapa.estado_cara(A, ESTE), ABIERTA)          # observada desde B
        self.assertEqual(mapa.estado_cara(A, SUR), SIN_OBSERVAR)      # A–C: el jugador nunca estuvo en A ni en C
        self.assertEqual(mapa.estado_cara(C, NORTE), SIN_OBSERVAR)
        grafo = grafo_de(mapa)
        self.assertEqual(grafo.salidas(A), [(B, 150)])
        self.assertIn((A, 150), grafo.salidas(B))
        destinos_a = [v for v, _ in grafo.salidas(A)]
        self.assertNotIn(C, destinos_a)
        self.assertNotIn(D, destinos_a)
        self.assertIn((B, 150), grafo.entradas(A))
        self.assertNotIn(C, [u for u, _ in grafo.entradas(A)])

    def test_h2_6_a42_fr208_fr225_solo_la_cara_de_origen_abierta_se_ofrece(self):
        mazmorra = cripta_mapa(2, [salida(A, ESTE, B)])
        cara_cerrada_sin_llave(mazmorra, A, B)
        mapa, jugador = mapa_de_prueba(mazmorra, A, HistorialRetroceso())
        mapa.iniciar(A)
        entrar_a(mapa, jugador, B)
        grafo = grafo_de(mapa)
        self.assertEqual(grafo.salidas(A), [])
        self.assertEqual(grafo.salidas(B), [(A, 100)])
        self.assertEqual(grafo.entradas(A), [(B, 100)])
        self.assertEqual(grafo.entradas(B), [])

    def test_fr225_interfaz_de_la_001(self):
        mazmorra, mapa, _ = mapa_h2_5()
        grafo = grafo_de(mapa)
        self.assertEqual(grafo.cantidad_salas(), len(mazmorra.salas))
        for u in range(grafo.cantidad_salas()):
            for par in grafo.salidas(u) + grafo.entradas(u):
                self.assertIsInstance(par, tuple)
                self.assertEqual(len(par), 2)
                self.assertIsInstance(par[0], int)
                self.assertIsInstance(par[1], int)
        self.assertEqual(grafo.salidas(D), [])                       # avistada
        self.assertEqual(grafo.entradas(D), [])

    def test_fr225_misma_ruta_que_paso_desde_cero_sobre_grafo_filtrado(self):
        # Diamante con empates: A–B, A–C, B–D, C–D, todas de costo 100; más los mapas a medias.
        diamante = cripta_mapa(4, [salida(A, ESTE, B), salida(A, SUR, C), salida(B, SUR, D), salida(C, ESTE, D)])
        mapa, jugador = mapa_de_prueba(diamante, A, HistorialRetroceso())
        mapa.iniciar(A)
        entrar_a(mapa, jugador, B, True)
        entrar_a(mapa, jugador, D)
        entrar_a(mapa, jugador, C)
        casos = [(diamante, mapa)] + mapas_a_medias()
        comparados = 0
        for mazmorra, mapa in casos:
            grafo = grafo_de(mapa)
            referencia = GrafoFiltradoAMano(mapa, mazmorra)
            for destino in range(len(mazmorra.salas)):
                if mapa.estado[destino] != EXPLORADA:
                    continue
                for u in range(len(mazmorra.salas)):
                    if mapa.estado[u] != EXPLORADA:
                        continue
                    self.assertEqual(paso_desde_cero(grafo, destino, u, None),
                                     paso_desde_cero(referencia, destino, u, None), f"destino {destino}, desde {u}")
                    comparados += 1
        self.assertGreater(comparados, 50)
        # En el diamante, desde A hacia D hay dos rutas de costo 200: el desempate elige B (menor id).
        self.assertEqual(paso_desde_cero(grafo_de(casos[0][1]), D, A, None), (B, 100))

    def test_fr225_lee_el_mapa_en_vivo(self):
        mazmorra = cripta_mapa(3, [salida(A, ESTE, B), salida(B, SUR, C)])
        historial = HistorialRetroceso()
        mapa, jugador = mapa_de_prueba(mazmorra, A, historial)
        mapa.iniciar(A)
        historial.descartar_intervalo_abierto()
        grafo = grafo_de(mapa)
        self.assertEqual(grafo.salidas(A), [])                       # B solo avistada
        self.assertEqual(grafo.entradas(A), [])
        entrar_a(mapa, jugador, B)
        historial.cerrar_intervalo()
        self.assertEqual(grafo.salidas(A), [(B, 100)])               # el mismo grafo ve la observación nueva
        self.assertEqual(grafo.entradas(A), [(B, 100)])
        mazmorra.salida(A, ESTE).cerrada = True
        mazmorra.salida(B, OESTE).cerrada = True
        mapa.puerta_cambio(A, B)                                     # el jugador está en B: la observa cerrada
        historial.cerrar_intervalo()
        self.assertEqual(grafo.salidas(A), [])
        self.assertEqual(grafo.entradas(B), [])
        historial.deshacer()                                         # el pergamino: vuelve a recordarla abierta
        self.assertEqual(grafo.salidas(A), [(B, 100)])
        self.assertEqual(grafo.entradas(B), [(A, 100)])
        historial.deshacer()                                         # y B vuelve a avistada
        self.assertEqual(grafo.salidas(A), [])
        self.assertEqual(grafo.entradas(A), [])

    def test_fr217_grafo_no_lee_el_estado_real(self):
        mazmorra, mapa, _ = mapa_h2_5()
        grafo = grafo_de(mapa)
        salidas_antes = [list(grafo.salidas(u)) for u in range(grafo.cantidad_salas())]
        entradas_antes = [list(grafo.entradas(u)) for u in range(grafo.cantidad_salas())]
        mazmorra.salida(A, ESTE).cerrada = True                      # cambia en la Mazmorra, sin aviso
        mazmorra.salida(B, OESTE).cerrada = True
        mazmorra.salida(A, SUR).cerrada = False
        self.assertEqual([grafo.salidas(u) for u in range(grafo.cantidad_salas())], salidas_antes)
        self.assertEqual([grafo.entradas(u) for u in range(grafo.cantidad_salas())], entradas_antes)

    def test_fr225_entradas_es_la_inversa_de_salidas(self):
        for mazmorra, mapa in mapas_a_medias():
            grafo = grafo_de(mapa)
            total = grafo.cantidad_salas()
            for u in range(total):
                if mapa.estado[u] != EXPLORADA:
                    self.assertEqual(grafo.salidas(u), [], f"salidas de la no explorada {u}")
                    self.assertEqual(grafo.entradas(u), [], f"entradas de la no explorada {u}")
                for v, c in grafo.salidas(u):
                    self.assertEqual(grafo.salidas(u).count((v, c)), grafo.entradas(v).count((u, c)),
                                     f"({v}, {c}) en salidas({u})")
                for v, c in grafo.entradas(u):
                    self.assertEqual(grafo.entradas(u).count((v, c)), grafo.salidas(v).count((u, c)),
                                     f"({v}, {c}) en entradas({u})")

    def test_fr225_posicion_cero_y_huecos_dan_listas_vacias(self):
        # Salas 1..5 sin la 3 (un hueco); A tiene una salida sin vuelta hacia el hueco.
        salas = salidas_con_costos(5, [salida(A, ESTE, B), salida(B, SUR, D), salida(D, ESTE, E),
                                       salida_sin_vuelta(A, SUR, C)])
        mazmorra = Mazmorra(sala_salida=E, llave_salida="llave")
        mazmorra.cargar_esqueleto([s for s in salas if s.id != C])
        self.assertIsNone(mazmorra.salas[0])
        self.assertIsNone(mazmorra.salas[C])
        mapa, jugador = mapa_de_prueba(mazmorra, A, HistorialRetroceso())
        grafo = grafo_de(mapa)
        self.assertEqual(grafo.salidas(0), [])                       # antes de armar la inversa
        self.assertEqual(grafo.entradas(0), [])
        mapa.iniciar(A)
        entrar_a(mapa, jugador, B, True)
        entrar_a(mapa, jugador, D, True)
        self.assertEqual(grafo.cantidad_salas(), len(mazmorra.salas))
        for hueco in (0, C):
            self.assertEqual(grafo.salidas(hueco), [], f"salidas({hueco})")
            self.assertEqual(grafo.entradas(hueco), [], f"entradas({hueco})")
        self.assertEqual(mapa.estado_sala(C), DESCONOCIDA)           # el hueco nunca se avista
        self.assertIn((B, 100), grafo.salidas(A))


class PruebasBusquedaPorNombre(unittest.TestCase):

    def setUp(self):
        # A, B y C exploradas; D avistada; E y F desconocidas.
        self.mazmorra = cripta_mapa(6, [salida(A, ESTE, B), salida(B, SUR, C), salida(C, ESTE, D),
                                        salida(D, SUR, E), salida(E, ESTE, F)])
        nombres = [(A, "Pasillo"), (B, "Cripta"), (C, "  cripta "), (D, "Pasillo"), (E, "Pasillo"), (F, "Straße")]
        for sala, nombre in nombres:
            self.mazmorra.sala(sala).nombre = nombre
        self.historial = HistorialRetroceso()
        self.mapa, self.jugador = mapa_de_prueba(self.mazmorra, A, self.historial)
        self.mapa.iniciar(A)
        entrar_a(self.mapa, self.jugador, B)
        entrar_a(self.mapa, self.jugador, C)
        self.historial.cerrar_intervalo()

    def test_fr251_buscar_exploradas_cero_uno_y_dos(self):
        self.assertEqual(self.mapa.buscar_exploradas("Biblioteca"), [])
        self.assertEqual(self.mapa.buscar_exploradas("Pasillo"), [A])
        self.assertEqual(self.mapa.buscar_exploradas("Cripta"), [B, C])     # orden creciente de id

    def test_fr206_fr251_avistada_o_desconocida_con_el_mismo_nombre_no_cuenta(self):
        self.assertEqual(self.mapa.estado_sala(D), AVISTADA)
        self.assertEqual(self.mapa.estado_sala(E), DESCONOCIDA)
        self.assertEqual(self.mapa.buscar_exploradas("Pasillo"), [A])
        self.assertEqual(self.mapa.buscar_exploradas("Straße"), [])        # F desconocida

    def test_fr251_comparacion_strip_casefold(self):
        self.assertEqual(self.mapa.buscar_exploradas("  PASILLO\t"), [A])
        self.assertEqual(self.mapa.buscar_exploradas("cRiPtA"), [B, C])
        entrar_a(self.mapa, self.jugador, D)
        entrar_a(self.mapa, self.jugador, E)
        entrar_a(self.mapa, self.jugador, F)
        self.assertEqual(self.mapa.buscar_exploradas("STRASSE"), [F])      # casefold, no lower
        self.assertEqual(self.mapa.buscar_exploradas("pasillo"), [A, D, E])

    def test_fr220_buscar_exploradas_no_cambia_el_estado(self):
        antes = estados(self.mapa)
        self.mapa.buscar_exploradas("Cripta")
        self.mapa.buscar_exploradas("Pasillo")
        self.mapa.buscar_exploradas("nada")
        self.assertEqual(estados(self.mapa), antes)
        self.assertEqual(len(self.historial._abierto), 0)

    def test_fr251_buscar_exploradas_vacio_o_espacios_da_lista_vacia(self):
        self.assertEqual(self.mapa.buscar_exploradas(""), [])
        self.assertEqual(self.mapa.buscar_exploradas("   "), [])

    def test_fr251_buscar_exploradas_no_str_es_value_error(self):
        for nombre in (None, 5, b"x"):
            with self.assertRaises(ValueError, msg=repr(nombre)):
                self.mapa.buscar_exploradas(nombre)

    def test_fr204_fr217_es_explorada_solo_para_exploradas(self):
        antes = estados(self.mapa)
        for sala in (A, B, C):
            self.assertIs(self.mapa.es_explorada(sala), True, f"sala {sala}")
        for sala in (0, D, E, F):                                    # posición 0, avistada y desconocidas
            self.assertIs(self.mapa.es_explorada(sala), False, f"sala {sala}")
        self.assertEqual(estados(self.mapa), antes)
        self.assertEqual(len(self.historial._abierto), 0)


if __name__ == "__main__":
    unittest.main()
