"""
Pruebas del núcleo de Logic/MapaConocido.py (feature 002, integrante 2): los dos arreglos, las consultas y las
dos únicas escrituras (_poner_estado / _poner_cara), que registran su reversión en el historial (research R1, R3).

Hasta T012 fallan al importar Logic.MapaConocido (dentro de mapa_de_prueba): es el fallo esperado.
"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.SalaDTO import SalaDTO  # noqa: E402
from Logic.HistorialRetroceso import HistorialRetroceso  # noqa: E402
from tests.ayudas_mapa import (A, B, C, D, E, ESTE, F, G, H, NORTE, OESTE, SUR, casillas_distintas,  # noqa: E402
                               cripta_mapa, entrar_a, estados, mapa_de_prueba, salida, salida_sin_vuelta)

# Constantes del mapa con sus valores de data-model §1 (las pruebas no las importan para no depender de T011).
DESCONOCIDA, AVISTADA, EXPLORADA = 0, 1, 2
SIN_OBSERVAR, ABIERTA, CERRADA = 0, 1, 2


def cripta_chica():
    """A –E– B –S– C, y A –N– D. Cuatro salas: S = 5 (la posición 0 queda vacía)."""
    return cripta_mapa(4, [salida(A, ESTE, B), salida(B, SUR, C), salida(A, NORTE, D)])


class PruebasNucleoMapaConocido(unittest.TestCase):

    def setUp(self):
        self.mazmorra = cripta_chica()
        self.historial = HistorialRetroceso()
        self.mapa, self.jugador = mapa_de_prueba(self.mazmorra, A, self.historial)

    def test_fr201_fr206_mapa_nuevo_todo_desconocido(self):
        s = len(self.mazmorra.salas)
        estado, caras = estados(self.mapa)
        self.assertEqual(estado, [DESCONOCIDA] * s)
        self.assertEqual(caras, [SIN_OBSERVAR] * (4 * s))

    def test_nfr201_consultas_estado_sala_y_cara(self):
        self.mapa.estado[B] = AVISTADA
        self.mapa.caras[C * 4 + SUR] = CERRADA
        self.assertEqual(self.mapa.estado_sala(B), AVISTADA)
        self.assertEqual(self.mapa.estado_sala(C), DESCONOCIDA)
        self.assertEqual(self.mapa.estado_cara(C, SUR), CERRADA)
        self.assertEqual(self.mapa.estado_cara(C, NORTE), SIN_OBSERVAR)

    def test_fr222_poner_igual_no_registra(self):
        antes = estados(self.mapa)
        self.mapa._poner_estado(B, DESCONOCIDA)
        self.mapa._poner_cara(A * 4 + ESTE, SIN_OBSERVAR)
        self.historial.cerrar_intervalo()
        self.mapa.estado[B] = AVISTADA          # cambio sin registrar: deshacer no debe tocarlo
        self.historial.deshacer()
        self.assertEqual(self.mapa.estado_sala(B), AVISTADA)
        self.assertEqual(estados(self.mapa)[1], antes[1])

    def test_fr222_poner_distinto_registra_su_reversion(self):
        antes = estados(self.mapa)
        self.mapa._poner_estado(B, EXPLORADA)
        self.mapa._poner_cara(A * 4 + ESTE, ABIERTA)
        self.assertEqual(self.mapa.estado_sala(B), EXPLORADA)
        self.assertEqual(self.mapa.estado_cara(A, ESTE), ABIERTA)
        self.historial.cerrar_intervalo()
        self.assertTrue(self.historial.deshacer())
        self.assertEqual(estados(self.mapa), antes)

    def test_fr222_cambios_repetidos_vuelven_al_primer_valor(self):
        self.mapa._poner_estado(D, AVISTADA)
        self.mapa._poner_cara(B * 4 + SUR, ABIERTA)
        self.historial.cerrar_intervalo()
        antes = estados(self.mapa)
        self.mapa._poner_estado(C, AVISTADA)        # la misma casilla cambia dos veces en un intervalo
        self.mapa._poner_estado(C, EXPLORADA)
        self.mapa._poner_cara(B * 4 + SUR, CERRADA)
        self.mapa._poner_cara(B * 4 + SUR, ABIERTA)
        self.mapa._poner_cara(B * 4 + SUR, CERRADA)
        self.historial.cerrar_intervalo()
        self.historial.deshacer()
        self.assertEqual(estados(self.mapa), antes)
        self.historial.deshacer()                   # y el intervalo anterior también vuelve
        self.assertEqual(self.mapa.estado_sala(D), DESCONOCIDA)
        self.assertEqual(self.mapa.estado_cara(B, SUR), SIN_OBSERVAR)

    def test_nfr203_historial_none_no_registra(self):
        mapa, _ = mapa_de_prueba(self.mazmorra, A, None)
        mapa._poner_estado(B, EXPLORADA)
        mapa._poner_cara(A * 4 + ESTE, CERRADA)
        self.assertEqual(mapa.estado_sala(B), EXPLORADA)
        self.assertEqual(mapa.estado_cara(A, ESTE), CERRADA)


def cripta_h1():
    """
    Cripta de la historia 1 (S = 9; la posición 0 queda vacía):
        A –E– B (abierta), A –S– C (cerrada), A –N→ F (sin vuelta);
        B –E– D, B –S– E; E –E– G; H –E→ A (sin vuelta: A no tiene cara hacia H).
    """
    return cripta_mapa(8, [salida(A, ESTE, B), salida(A, SUR, C, cerrada=True), salida_sin_vuelta(A, NORTE, F),
                           salida(B, ESTE, D), salida(B, SUR, E), salida(E, ESTE, G),
                           salida_sin_vuelta(H, ESTE, A)])


class PruebasHistoria1(unittest.TestCase):
    """Historia 1: iniciar y entrar (sin antorcha) mantienen los tres estados de cada sala (FR-201 a FR-206)."""

    def setUp(self):
        self.mazmorra = cripta_h1()
        self.historial = HistorialRetroceso()
        self.mapa, self.jugador = mapa_de_prueba(self.mazmorra, A, self.historial)

    def comprobar_invariantes(self, antes=None):
        """Invariantes 2, 3 y 4 del data-model §2 (y que ningún estado bajó respecto de 'antes')."""
        mapa, salas = self.mapa, self.mazmorra.salas
        for u in range(len(salas)):
            if mapa.estado[u] != EXPLORADA:
                continue
            for s in salas[u].salidas:
                if s is not None:
                    self.assertNotEqual(mapa.estado[s.destino], DESCONOCIDA, f"destino {s.destino} de {u}")
        for v in range(len(salas)):
            if mapa.estado[v] != AVISTADA:
                continue
            tiene_origen = False
            for u in range(len(salas)):
                if salas[u] is None or mapa.estado[u] != EXPLORADA:
                    continue
                for s in salas[u].salidas:
                    if s is not None and s.destino == v:
                        tiene_origen = True
            self.assertTrue(tiene_origen, f"la sala avistada {v} no es destino de una explorada")
        if antes is not None:
            for i in range(len(antes)):
                self.assertGreaterEqual(mapa.estado[i], antes[i], f"bajó el estado de la sala {i}")

    def test_h1_1_a1_fr201_fr202_fr204_fr205_fr206_sala_inicial_explorada(self):
        self.mapa.iniciar(A)
        estado, caras = estados(self.mapa)
        esperado = [DESCONOCIDA] * len(self.mazmorra.salas)
        esperado[A] = EXPLORADA
        esperado[B] = AVISTADA
        esperado[C] = AVISTADA
        esperado[F] = AVISTADA
        self.assertEqual(estado, esperado)
        caras_esperadas = [SIN_OBSERVAR] * (4 * len(self.mazmorra.salas))
        caras_esperadas[A * 4 + ESTE] = ABIERTA
        caras_esperadas[A * 4 + SUR] = CERRADA
        caras_esperadas[A * 4 + NORTE] = ABIERTA      # sin vuelta: se observa desde A
        caras_esperadas[B * 4 + OESTE] = ABIERTA      # la otra cara de A–B
        caras_esperadas[C * 4 + NORTE] = CERRADA      # la otra cara de A–C
        self.assertEqual(caras, caras_esperadas)

    def test_h1_2_a2_fr203_entrar_explora_y_avista(self):
        self.mapa.iniciar(A)
        self.assertEqual(self.mapa.estado_sala(B), AVISTADA)
        self.assertEqual(self.mapa.estado_sala(D), DESCONOCIDA)
        self.assertEqual(self.mapa.estado_sala(E), DESCONOCIDA)
        entrar_a(self.mapa, self.jugador, B)
        self.assertEqual(self.mapa.estado_sala(B), EXPLORADA)
        self.assertEqual(self.mapa.estado_sala(D), AVISTADA)
        self.assertEqual(self.mapa.estado_sala(E), AVISTADA)
        self.assertEqual(self.mapa.estado_sala(G), DESCONOCIDA)

    def test_h1_3_a13_fr204_salida_sin_vuelta_avista_su_destino(self):
        self.mapa.iniciar(A)
        self.assertEqual(self.mapa.estado_sala(F), AVISTADA)
        for d in range(4):
            self.assertEqual(self.mapa.estado_cara(F, d), SIN_OBSERVAR)

    def test_h1_5_a3_fr217_fr218_precarga_y_esqueleto_no_cambian_el_mapa(self):
        # El esqueleto ya se cargó una sola vez al armar la Mazmorra (cripta_mapa). La precarga carga el contenido
        # de una sala desconocida, sin volver a cargar el esqueleto.
        self.mapa.iniciar(A)
        entrar_a(self.mapa, self.jugador, B)
        self.assertEqual(self.mapa.estado_sala(G), DESCONOCIDA)
        antes = estados(self.mapa)
        self.mazmorra.sala(G).contenido_cargado = False
        self.mazmorra.cargar_contenido(SalaDTO(G, "Sala 7", [None, None, None, None], "1", objetos=["obj_x"]),
                                       lambda tipo: None)
        self.assertTrue(self.mazmorra.contenido_cargado(G))
        self.assertEqual(estados(self.mapa), antes)
        self.assertEqual(self.mapa.estado_sala(G), DESCONOCIDA)

    def test_h1_6_a2_fr203_volver_no_baja_el_estado(self):
        self.mapa.iniciar(A)
        entrar_a(self.mapa, self.jugador, B)
        entrar_a(self.mapa, self.jugador, A)
        self.assertEqual(self.mapa.estado_sala(B), EXPLORADA)
        self.assertEqual(self.mapa.estado_sala(D), AVISTADA)
        self.assertEqual(self.mapa.estado_sala(E), AVISTADA)

    def test_fr203_vecina_de_si_misma_y_varias_salidas_una_sola_vez(self):
        # A tiene una salida hacia sí misma (E y O) y dos salidas hacia B (N y S).
        mazmorra = cripta_mapa(2, [salida(A, ESTE, A), salida(A, NORTE, B), salida(A, SUR, B)])
        historial = HistorialRetroceso()
        mapa, jugador = mapa_de_prueba(mazmorra, A, historial)
        antes = estados(mapa)
        mapa.iniciar(A)
        despues = estados(mapa)
        self.assertEqual(mapa.estado_sala(A), EXPLORADA)
        self.assertEqual(mapa.estado_sala(B), AVISTADA)
        self.assertEqual(len(historial._abierto), casillas_distintas(antes, despues))   # un cambio por casilla
        historial.cerrar_intervalo()
        antes = estados(mapa)
        entrar_a(mapa, jugador, B)
        self.assertEqual(len(historial._abierto), casillas_distintas(antes, estados(mapa)))
        self.assertEqual(mapa.estado_sala(B), EXPLORADA)

    def test_fr203_sala_de_origen_no_cambia(self):
        self.mapa.iniciar(A)
        antes = estados(self.mapa)
        entrar_a(self.mapa, self.jugador, B)
        despues = estados(self.mapa)
        self.assertEqual(despues[0][A], antes[0][A])
        for d in range(4):
            self.assertEqual(despues[1][A * 4 + d], antes[1][A * 4 + d])

    def test_fr203_fr204_invariantes_del_mapa(self):
        self.mapa.iniciar(A)
        self.comprobar_invariantes()
        for sala in [B, E, G, E, B, D, B, A, C, A]:
            antes = list(self.mapa.estado)
            entrar_a(self.mapa, self.jugador, sala)
            self.comprobar_invariantes(antes)

    def test_fr204_origen_de_salida_sin_vuelta_hacia_explorada_sigue_desconocida(self):
        self.mapa.iniciar(A)
        entrar_a(self.mapa, self.jugador, B)
        entrar_a(self.mapa, self.jugador, A)
        self.assertEqual(self.mapa.estado_sala(H), DESCONOCIDA)
        self.assertEqual(self.mapa.estado_cara(H, ESTE), SIN_OBSERVAR)


if __name__ == "__main__":
    unittest.main()
