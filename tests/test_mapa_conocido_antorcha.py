"""
Pruebas de la historia 3 en Logic (feature 002, integrante 2): con la antorcha encendida, entrar explora las
vecinas sin ir más allá (FR-210 a FR-214) y el costo es proporcional a lo revelado (NFR-202). Sin motor: el
booleano 'antorcha' de MapaConocido.entrar es lo que en la partida pasa el motor. Las variantes con el motor
(H3-1 con enemigos, trampas y reloj; H3-5, H3-7 y H3-8) llegan en T031.
"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from Logic.HistorialRetroceso import HistorialRetroceso  # noqa: E402
from Logic.Mazmorra import Mazmorra  # noqa: E402
from tests.ayudas_mapa import (A, B, C, D, E, ESTE, H, I, J, NORTE, OESTE, SUR, casillas_distintas,  # noqa: E402
                               cripta_mapa, entrar_a, estados, mapa_de_prueba, salida)
from tests.Utilidades import id_cuadricula, salas_cuadricula  # noqa: E402

# Constantes del mapa con sus valores de data-model §1.
DESCONOCIDA, AVISTADA, EXPLORADA = 0, 1, 2
SIN_OBSERVAR, ABIERTA, CERRADA = 0, 1, 2


def cripta_h3():
    """
    A –E– B; B –S– C, B –E– D, B –N– E (cerrada con llave); C –S– H, C –E– I, C –O– J. Salas 1..10.
    """
    mazmorra = cripta_mapa(10, [salida(A, ESTE, B), salida(B, SUR, C), salida(B, ESTE, D),
                                salida(B, NORTE, E, cerrada=True),
                                salida(C, SUR, H), salida(C, ESTE, I), salida(C, OESTE, J)])
    mazmorra.salida(B, NORTE).llave = "llave_que_no_tiene"
    mazmorra.salida(E, SUR).llave = "llave_que_no_tiene"
    return mazmorra


class PruebasAntorcha(unittest.TestCase):

    def setUp(self):
        self.mazmorra = cripta_h3()
        self.historial = HistorialRetroceso()
        self.mapa, self.jugador = mapa_de_prueba(self.mazmorra, A, self.historial)
        self.mapa.iniciar(A)

    def test_h3_1_apendiceB_caso4_fr210_fr211_antorcha_explora_vecinas(self):
        entrar_a(self.mapa, self.jugador, B, True)
        for sala in (B, C, D):
            self.assertEqual(self.mapa.estado_sala(sala), EXPLORADA, f"sala {sala}")
        for sala in (B, C, D):                                # el mapa no carga ni toca contenido
            self.assertEqual(self.mazmorra.sala(sala).enemigos, [])
            self.assertEqual(self.mazmorra.sala(sala).trampas, [])

    def test_h3_2_a5_fr210_explora_a_traves_de_una_puerta_cerrada(self):
        entrar_a(self.mapa, self.jugador, B, True)
        self.assertEqual(self.mapa.estado_sala(E), EXPLORADA)
        self.assertEqual(self.mapa.estado_cara(B, NORTE), CERRADA)

    def test_h3_3_a6_fr214_antorcha_apagada_solo_avista(self):
        entrar_a(self.mapa, self.jugador, B, False)
        self.assertEqual(self.mapa.estado_sala(B), EXPLORADA)
        for sala in (C, D, E):
            self.assertEqual(self.mapa.estado_sala(sala), AVISTADA, f"sala {sala}")
        for sala in (H, I, J):
            self.assertEqual(self.mapa.estado_sala(sala), DESCONOCIDA, f"sala {sala}")

    def test_h3_4_a17_fr213_no_explora_mas_alla_de_las_vecinas(self):
        entrar_a(self.mapa, self.jugador, B, True)
        self.assertEqual(self.mapa.estado_sala(C), EXPLORADA)
        for sala in (H, I, J):
            self.assertEqual(self.mapa.estado_sala(sala), AVISTADA, f"sala {sala}")

    def test_h3_6_a19_fr205_fr207_fr212_puertas_de_la_vecina_sin_observar(self):
        entrar_a(self.mapa, self.jugador, B, True)
        self.assertEqual(self.mapa.estado_sala(C), EXPLORADA)         # explorada por la antorcha
        self.assertEqual(self.mapa.estado_cara(B, SUR), ABIERTA)      # observada desde B
        self.assertEqual(self.mapa.estado_cara(C, NORTE), ABIERTA)    # la cara de C hacia B, también desde B
        self.assertEqual(self.mapa.estado_cara(C, OESTE), SIN_OBSERVAR)   # C → J: nunca observada
        self.assertEqual(self.mapa.estado_cara(C, SUR), SIN_OBSERVAR)
        self.assertEqual(self.mapa.estado_cara(C, ESTE), SIN_OBSERVAR)

    def test_h3_8_a43_fr210_fr214_entrar_con_y_sin_antorcha_en_el_mismo_instante(self):
        otro_mapa, otro_jugador = mapa_de_prueba(self.mazmorra, A, HistorialRetroceso())
        otro_mapa.iniciar(A)
        self.assertEqual(estados(otro_mapa), estados(self.mapa))      # el mismo mapa de partida
        entrar_a(self.mapa, self.jugador, B, False)                   # el fin se atendió antes: apagada
        entrar_a(otro_mapa, otro_jugador, B, True)                    # el fin se atiende después: encendida
        for sala in (C, D, E):
            self.assertEqual(self.mapa.estado_sala(sala), AVISTADA, f"apagada, sala {sala}")
            self.assertEqual(otro_mapa.estado_sala(sala), EXPLORADA, f"encendida, sala {sala}")

    def test_fr210_vecina_ya_explorada_no_cambia_ni_registra(self):
        entrar_a(self.mapa, self.jugador, B, False)
        entrar_a(self.mapa, self.jugador, C, False)                   # C explorada y sus puertas observadas
        entrar_a(self.mapa, self.jugador, A, False)
        self.historial.cerrar_intervalo()
        antes = estados(self.mapa)
        entrar_a(self.mapa, self.jugador, B, True)
        despues = estados(self.mapa)
        self.assertEqual(len(self.historial._abierto), casillas_distintas(antes, despues))
        self.assertEqual(despues[0][C], EXPLORADA)
        self.assertEqual(despues[0][D], EXPLORADA)                   # la antorcha sí exploró las otras vecinas
        for sala in (H, I, J):                                        # no se recorrieron sus salidas de nuevo
            self.assertEqual(despues[0][sala], antes[0][sala])
        for d in range(4):
            self.assertEqual(despues[1][C * 4 + d], antes[1][C * 4 + d])

    def test_nfr202_cambios_proporcionales_a_lo_revelado(self):
        chico = self.cambios_al_entrar_al_centro(5)
        grande = self.cambios_al_entrar_al_centro(32)                # 1 024 salas, casi todo explorado
        self.assertEqual(chico, grande)
        cambios_estado, cambios_caras, registrados = grande
        self.assertEqual(cambios_estado, 5 + 8)                       # el centro y sus 4 vecinas; 8 a distancia 2
        self.assertLessEqual(cambios_estado, 5 + 16)                  # 5 de exploración y a lo sumo 16 avistadas
        self.assertLessEqual(cambios_caras, 8)
        # Registros: 5 de exploración, a lo sumo 16 de avistamiento y 8 de caras. Una vecina avistada al explorar
        # el centro y explorada enseguida por la antorcha registra dos cambios (data-model §2: _explorar avista y
        # después la antorcha explora), así que se acota el total, no se iguala a las casillas distintas.
        self.assertLessEqual(registrados, 5 + 16 + 8)

    def cambios_al_entrar_al_centro(self, n):
        """
        En una cuadrícula n × n: las salas a distancia ≥ 4 del centro exploradas, a distancia 3 avistadas y el resto
        desconocidas (puesto a mano, sin historial). Entra al centro con la antorcha y devuelve
        (casillas de estado cambiadas, casillas de caras cambiadas, cambios registrados en el historial).
        """
        mazmorra = Mazmorra(sala_salida=n * n, llave_salida="llave")
        mazmorra.cargar_esqueleto(salas_cuadricula(n))
        historial = HistorialRetroceso()
        mapa, jugador = mapa_de_prueba(mazmorra, 1, historial)
        centro_f = centro_c = n // 2
        for f in range(n):
            for c in range(n):
                distancia = abs(f - centro_f) + abs(c - centro_c)
                if distancia >= 4:
                    mapa.estado[id_cuadricula(f, c, n)] = EXPLORADA
                elif distancia == 3:
                    mapa.estado[id_cuadricula(f, c, n)] = AVISTADA
        antes = estados(mapa)
        entrar_a(mapa, jugador, id_cuadricula(centro_f, centro_c, n), True)
        despues = estados(mapa)
        cambios_estado = casillas_distintas((antes[0], []), (despues[0], []))
        cambios_caras = casillas_distintas(([], antes[1]), ([], despues[1]))
        return cambios_estado, cambios_caras, len(historial._abierto)


if __name__ == "__main__":
    unittest.main()
