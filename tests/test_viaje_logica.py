import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.ViajeDTO import (AMBIGUO, DANO, DESTINO_INVALIDO, ENEMIGOS, LLEGO, TERMINADA, YA_AQUI,  # noqa: E402
                          InicioViajeDTO, ViajeDTO)
from Logic.BusquedaCostoMinimo import paso_desde_cero  # noqa: E402
from Logic.GrafoMapaConocido import GrafoMapaConocido  # noqa: E402
from Logic.ViajeAutomatico import OK, decidir_paso, motivos_de_parada, resolver_destino  # noqa: E402
from tests.ayudas_mapa import (A, B, C, D, ESTE, NORTE, SUR, cara_cerrada_sin_llave, cripta_mapa,  # noqa: E402
                               cuadricula_mapa, entrar_a, mapa_de_prueba, salida)

SIN_OBSERVAR = 0


def explorar(mazmorra, recorrido):
    mapa, jugador = mapa_de_prueba(mazmorra, recorrido[0])
    mapa.iniciar(recorrido[0])
    for sala in recorrido[1:]:
        entrar_a(mapa, jugador, sala)
    return mapa, jugador


def rombo(cerrada_ab=False):
    return cripta_mapa(4, [salida(A, NORTE, B, 100, cerrada_ab), salida(B, ESTE, D, 100),
                           salida(A, ESTE, C, 200), salida(C, NORTE, D, 200)])


def paso(mapa, mazmorra, origen, destino):
    return decidir_paso(GrafoMapaConocido(mapa), mapa, mazmorra, origen, destino)


class PruebasResolverDestino(unittest.TestCase):

    def setUp(self):
        self.mazmorra = cripta_mapa(5, [salida(A, NORTE, B, 100), salida(B, ESTE, C, 100), salida(C, NORTE, D, 100)])
        for sala, nombre in ((A, "Entrada"), (B, "Pasillo"), (C, "Cripta"), (D, "Pasillo"), (5, "Lejos")):
            self.mazmorra.sala(sala).nombre = nombre
        self.mapa, self.jugador = explorar(self.mazmorra, [A, B, C])

    def test_h6_1_apendiceB_caso1_fr251_avistada_desconocida_e_inexistente_mismo_codigo(self):
        self.assertEqual(self.mapa.estado_sala(D), 1)                      # D está avistada (salida de C)
        self.assertEqual(self.mapa.estado_sala(5), 0)                      # la sala 5 es desconocida
        for nombre in ("Pasillo2", "Lejos", "Nada"):
            self.assertEqual(resolver_destino(self.mapa, nombre, A), (DESTINO_INVALIDO, None), nombre)
        self.assertEqual(resolver_destino(self.mapa, "Pasillo", C), (OK, B))   # D (avistada) no cuenta: solo B

    def test_h6_8_a30_fr251_destino_en_la_sala_actual_ya_aqui(self):
        self.assertEqual(resolver_destino(self.mapa, "Entrada", A)[0], YA_AQUI)

    def test_fr251_nombre_de_dos_exploradas_es_ambiguo(self):
        entrar_a(self.mapa, self.jugador, D)
        self.assertEqual(resolver_destino(self.mapa, "Pasillo", A), (AMBIGUO, None))

    def test_fr251_h3_mayusculas_y_espacios_encuentran_la_sala(self):
        self.assertEqual(resolver_destino(self.mapa, "  cRIPTA ", A), (OK, C))

    def test_fr251_nombre_vacio_o_espacios_es_destino_invalido(self):
        for nombre in ("", "   "):
            self.assertEqual(resolver_destino(self.mapa, nombre, A), (DESTINO_INVALIDO, None))

    def test_fr251_nombre_no_str_es_value_error(self):
        for nombre in (None, 5):
            with self.assertRaises(ValueError):
                resolver_destino(self.mapa, nombre, A)


class PruebasDecidirPaso(unittest.TestCase):

    def test_h6_2_a24_fr253_ruta_de_menor_costo(self):
        mazmorra = rombo()
        mapa, _ = explorar(mazmorra, [A, B, D, C, A])
        self.assertEqual(paso(mapa, mazmorra, A, D), (NORTE, B, 100))

    def test_h6_3_a25_fr253_empate_va_a_la_vecina_de_menor_id(self):
        mazmorra = cripta_mapa(4, [salida(A, NORTE, B, 100), salida(B, ESTE, D, 100),
                                   salida(A, ESTE, C, 100), salida(C, NORTE, D, 100)])
        mapa, _ = explorar(mazmorra, [A, B, D, C, A])
        self.assertEqual(paso(mapa, mazmorra, A, D), (NORTE, B, 100))

    def test_h6_4_a26_fr252_fr257_fr259_salida_recordada_cerrada_no_se_usa(self):
        mazmorra = rombo(cerrada_ab=True)
        mapa, _ = explorar(mazmorra, [A, C, D, B, A])
        self.assertEqual(paso(mapa, mazmorra, A, D), (ESTE, C, 200))
        sin_otra = cripta_mapa(2, [salida(A, NORTE, B, 100, True)])
        mapa2, _ = explorar(sin_otra, [A, B])
        self.assertIsNone(paso(mapa2, sin_otra, A, B))

    def test_h6_5_a27_fr212_fr252_cara_sin_observar_no_cuenta(self):
        mazmorra = rombo()
        mapa, _ = explorar(mazmorra, [A, B, D, C, A])
        mapa.caras[A * 4 + NORTE] = SIN_OBSERVAR
        self.assertEqual(paso(mapa, mazmorra, A, D), (ESTE, C, 200))

    def test_h6_6_a28_fr217_fr252_no_atraviesa_avistadas_ni_desconocidas(self):
        mazmorra = rombo()
        mapa, _ = explorar(mazmorra, [A, D])
        self.assertEqual((mapa.estado_sala(B), mapa.estado_sala(C)), (1, 1))
        self.assertIsNone(paso(mapa, mazmorra, A, D))

    def test_h2_6_a42_fr252_solo_la_cara_de_origen_abierta(self):
        mazmorra = cripta_mapa(2, [salida(A, NORTE, B, 100)])
        cara_cerrada_sin_llave(mazmorra, A, B)
        mapa, _ = explorar(mazmorra, [A, B])
        self.assertIsNone(paso(mapa, mazmorra, A, B))
        self.assertEqual(paso(mapa, mazmorra, B, A), (SUR, A, 100))

    def test_fr252_direccion_de_menor_numero_con_ese_costo(self):
        mazmorra = cripta_mapa(2, [salida(A, ESTE, B, 100), salida(A, NORTE, B, 100)])
        mapa, _ = explorar(mazmorra, [A, B, A])
        self.assertEqual(paso(mapa, mazmorra, A, B), (NORTE, B, 100))

    def test_fr252_h4_cara_recordada_cerrada_de_menor_direccion_no_se_elige(self):
        mazmorra = cripta_mapa(2, [salida(A, NORTE, B, 100, True), salida(A, ESTE, B, 100)])
        mapa, _ = explorar(mazmorra, [A, B, A])
        self.assertEqual(paso(mapa, mazmorra, A, B), (ESTE, B, 100))
        ambas = cripta_mapa(2, [salida(A, NORTE, B, 100, True), salida(A, ESTE, B, 100, True)])
        mapa2, _ = explorar(ambas, [A, B, A])
        self.assertIsNone(paso(mapa2, ambas, A, B))

    def test_sc251_fr255_cada_decision_igual_a_paso_desde_cero(self):
        for semilla in (1, 2, 3):
            mazmorra, _ = cuadricula_mapa(3, semilla)
            mapa, _ = explorar(mazmorra, list(range(1, 10)))
            grafo = GrafoMapaConocido(mapa)
            for origen in range(1, 10):
                for destino in range(1, 10):
                    esperado = paso_desde_cero(grafo, destino, origen, None)
                    decidido = decidir_paso(grafo, mapa, mazmorra, origen, destino)
                    if esperado is None:
                        self.assertIsNone(decidido)
                        continue
                    self.assertEqual(decidido[1:], esperado)
                    self.assertEqual(mazmorra.salida(origen, decidido[0]).destino, esperado[0])


class PruebasMotivosDeParada(unittest.TestCase):

    def test_h7_3_apendiceB_caso3_fr258_entra_a_sala_con_enemigos(self):
        self.assertEqual(motivos_de_parada(B, D, True, False, False), [ENEMIGOS])

    def test_h7_4_a33_fr258_fr260_enemigos_en_el_destino_dan_dos_motivos(self):
        self.assertEqual(motivos_de_parada(D, D, True, False, False), [LLEGO, ENEMIGOS])

    def test_h7_5_a34_fr258_dano_detiene(self):
        self.assertEqual(motivos_de_parada(B, D, False, True, False), [DANO])

    def test_h7_6_a35_fr258_fr260_llego(self):
        self.assertEqual(motivos_de_parada(D, D, False, False, False), [LLEGO])

    def test_fr260_varios_motivos_en_orden_fijo(self):
        self.assertEqual(motivos_de_parada(D, D, True, True, True), [LLEGO, ENEMIGOS, DANO, TERMINADA])

    def test_i3_7_fr258_terminada_junto_con_dano_o_llego(self):
        self.assertEqual(motivos_de_parada(B, D, False, True, True), [DANO, TERMINADA])
        self.assertEqual(motivos_de_parada(D, D, False, False, True), [LLEGO, TERMINADA])

    def test_fr258_sin_motivos_el_viaje_sigue(self):
        self.assertEqual(motivos_de_parada(B, D, False, False, False), [])


class PruebasViajeDTO(unittest.TestCase):

    def test_es_inmutable_y_guarda_los_datos(self):
        viaje = ViajeDTO(4, "Cripta", 0, 7)
        with self.assertRaises(AttributeError):
            viaje.pasos_dados = 1
        self.assertEqual((viaje.destino, viaje.nombre_destino, viaje.acciones_esperadas), (4, "Cripta", 7))
        self.assertEqual(InicioViajeDTO(None, [DESTINO_INVALIDO]).motivos, [DESTINO_INVALIDO])


if __name__ == "__main__":
    unittest.main()
