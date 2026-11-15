"""
Pruebas de la historia 2 en Logic (feature 002, integrante 2): el estado recordado de cada cara (FR-207 a FR-209) y
la re-observación de las puertas de la sala del jugador al recibir puerta_cambio. Sin motor: MapaConocido con una
Mazmorra y un JugadorPrueba (tests/ayudas_mapa.py). Las variantes con el motor llegan en T031.

Lo que se ofrece a «ir a» (H2-5 y la mitad de H2-6) está en tests/test_grafo_mapa_conocido.py.
"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from Logic.HistorialRetroceso import HistorialRetroceso  # noqa: E402
from tests.ayudas_mapa import (A, B, C, D, ESTE, F, NORTE, SUR, X, cara_cerrada_sin_llave, cripta_mapa,  # noqa: E402
                               entrar_a, estados, mapa_de_prueba, salida, salida_sin_vuelta)

# Constantes del mapa con sus valores de data-model §1.
DESCONOCIDA, AVISTADA, EXPLORADA = 0, 1, 2
SIN_OBSERVAR, ABIERTA, CERRADA = 0, 1, 2


def cripta_h2():
    """
    A –E– B, B –S– C, C –E– D, A –N→ F (sin vuelta), X –E→ A (sin vuelta). Salas 1..24 (X = 24); las demás aisladas.
    D no tiene cara en las puertas A–B ni B–C.
    """
    return cripta_mapa(24, [salida(A, ESTE, B), salida(B, SUR, C), salida(C, ESTE, D),
                            salida_sin_vuelta(A, NORTE, F), salida_sin_vuelta(X, ESTE, A)])


def cerrar_puerta(mazmorra, a: int, b: int) -> None:
    """Cierra en la Mazmorra las caras de la puerta a–b (la de a y, si existe, la de vuelta), sin avisar a nadie."""
    poner_puerta(mazmorra, a, b, True)


def abrir_sin_aviso(mazmorra, a: int, b: int) -> None:
    """Abre en la Mazmorra las caras de la puerta a–b, sin avisar a nadie."""
    poner_puerta(mazmorra, a, b, False)


def poner_puerta(mazmorra, a: int, b: int, cerrada: bool) -> None:
    for s in mazmorra.sala(a).salidas:
        if s is not None and s.destino == b:
            s.cerrada = cerrada
            inversa = mazmorra._salida_inversa(a, b)
            if inversa is not None:
                inversa.cerrada = cerrada
            return
    raise ValueError(f"la sala {a} no tiene salida hacia {b}")


class PruebasPuertasRecordadas(unittest.TestCase):

    def setUp(self):
        self.mazmorra = cripta_h2()
        self.historial = HistorialRetroceso()

    def nuevo_mapa(self, sala):
        mapa, jugador = mapa_de_prueba(self.mazmorra, sala, self.historial)
        mapa.iniciar(sala)
        return mapa, jugador

    def comprobar_recordado_igual_a_real(self, mapa, x):
        """Invariante 5 del data-model: con el jugador en x, cada cara de cada puerta con cara en x es la real."""
        for d in range(4):
            s = self.mazmorra.sala(x).salidas[d]
            if s is None:
                continue
            self.assertEqual(mapa.estado_cara(x, d), CERRADA if s.cerrada else ABIERTA, f"cara {x}/{d}")
            inversa = self.mazmorra._salida_inversa(x, s.destino)
            if inversa is None:
                continue
            for d2 in range(4):
                if self.mazmorra.sala(s.destino).salidas[d2] is inversa:
                    self.assertEqual(mapa.estado_cara(s.destino, d2), CERRADA if inversa.cerrada else ABIERTA,
                                     f"cara de vuelta {s.destino}/{d2}")

    def test_h2_1_apendiceB_caso2a_fr207_fr209_puerta_recordada_abierta_se_actualiza(self):
        # Llegando a B.
        mapa, jugador = self.nuevo_mapa(B)
        self.assertEqual(mapa.estado_cara(B, SUR), ABIERTA)
        entrar_a(mapa, jugador, A)
        cerrar_puerta(self.mazmorra, B, C)                    # cambia lejos del jugador: el mapa no se entera
        self.assertEqual(mapa.estado_cara(B, SUR), ABIERTA)
        self.assertEqual(mapa.estado_cara(C, NORTE), ABIERTA)
        entrar_a(mapa, jugador, B)
        self.assertEqual(mapa.estado_cara(B, SUR), CERRADA)
        self.assertEqual(mapa.estado_cara(C, NORTE), CERRADA)
        # Y lo mismo llegando a C.
        abrir_sin_aviso(self.mazmorra, B, C)
        mapa, jugador = self.nuevo_mapa(B)
        entrar_a(mapa, jugador, A)
        cerrar_puerta(self.mazmorra, B, C)
        entrar_a(mapa, jugador, C)
        self.assertEqual(mapa.estado_cara(B, SUR), CERRADA)
        self.assertEqual(mapa.estado_cara(C, NORTE), CERRADA)

    def test_h2_2_a4_fr208_cierre_automatico_lejos_sigue_abierta(self):
        mapa, jugador = self.nuevo_mapa(A)
        entrar_a(mapa, jugador, B)
        entrar_a(mapa, jugador, D)                            # D no tiene cara en A–B
        cerrar_puerta(self.mazmorra, A, B)
        mapa.puerta_cambio(A, B)                              # como el aviso de CierrePuerta
        self.assertEqual(mapa.estado_cara(A, ESTE), ABIERTA)
        self.assertEqual(mapa.estado_cara(B, 3), ABIERTA)

    def test_h2_3_a15_fr207_cambio_con_el_jugador_en_la_sala(self):
        mapa, jugador = self.nuevo_mapa(A)
        entrar_a(mapa, jugador, B)
        self.assertEqual(mapa.estado_cara(B, SUR), ABIERTA)
        cerrar_puerta(self.mazmorra, B, C)
        mapa.puerta_cambio(C, B)
        self.assertEqual(mapa.estado_cara(B, SUR), CERRADA)
        self.assertEqual(mapa.estado_cara(C, NORTE), CERRADA)

    def test_h2_4_a16_fr204_fr207_salida_sin_vuelta_solo_desde_su_origen(self):
        mapa, jugador = self.nuevo_mapa(A)
        self.assertEqual(mapa.estado_cara(A, NORTE), ABIERTA)  # recordada abierta
        cerrar_puerta(self.mazmorra, A, F)                     # en realidad está cerrada
        entrar_a(mapa, jugador, B)
        entrar_a(mapa, jugador, A)                             # el jugador está en A: la observa
        self.assertEqual(mapa.estado_cara(A, NORTE), CERRADA)
        abrir_sin_aviso(self.mazmorra, A, F)
        entrar_a(mapa, jugador, F)                             # en F no tiene cara: no se observa
        self.assertEqual(mapa.estado_cara(A, NORTE), CERRADA)
        for d in range(4):
            self.assertEqual(mapa.estado_cara(F, d), SIN_OBSERVAR)
        # X tiene una salida sin vuelta hacia A: sigue desconocida y esa cara no se observa.
        self.assertEqual(mapa.estado_sala(X), DESCONOCIDA)
        self.assertEqual(mapa.estado_cara(X, ESTE), SIN_OBSERVAR)

    def test_h2_6_a42_fr207_fr208_caras_distintas_se_recuerdan_por_separado(self):
        cara_cerrada_sin_llave(self.mazmorra, A, B)
        for sala in (A, B):
            mapa, _ = mapa_de_prueba(self.mazmorra, sala, HistorialRetroceso())
            mapa.iniciar(sala)
            self.assertEqual(mapa.estado_cara(A, ESTE), CERRADA, f"observada desde {sala}")
            self.assertEqual(mapa.estado_cara(B, 3), ABIERTA, f"observada desde {sala}")

    def test_fr207_en_la_sala_del_jugador_recordado_igual_a_real(self):
        mapa, jugador = self.nuevo_mapa(A)
        entrar_a(mapa, jugador, B)
        self.mazmorra.observador_puertas = mapa              # abrir_puerta avisa al mapa
        self.comprobar_recordado_igual_a_real(mapa, B)
        for _ in range(3):
            cerrar_puerta(self.mazmorra, B, C)
            mapa.puerta_cambio(B, C)
            self.comprobar_recordado_igual_a_real(mapa, B)
            cerrar_puerta(self.mazmorra, A, B)
            mapa.puerta_cambio(A, B)
            self.comprobar_recordado_igual_a_real(mapa, B)
            self.mazmorra.abrir_puerta(B, SUR, None)
            self.comprobar_recordado_igual_a_real(mapa, B)
            self.mazmorra.abrir_puerta(B, 3, None)
            self.comprobar_recordado_igual_a_real(mapa, B)

    def test_fr207_puerta_cambio_sin_cambios_no_registra(self):
        mapa, jugador = self.nuevo_mapa(A)
        entrar_a(mapa, jugador, B)
        self.historial.cerrar_intervalo()
        antes = estados(mapa)
        cerrar_puerta(self.mazmorra, C, D)                    # puerta lejana: sin cara en B
        mapa.puerta_cambio(C, D)
        self.assertEqual(len(self.historial._abierto), 0)
        self.assertEqual(estados(mapa), antes)


if __name__ == "__main__":
    unittest.main()
