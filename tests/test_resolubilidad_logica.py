"""
Pruebas de Lógica de la feature 003, historia 1 (integrante 2): el veredicto y el orden determinista de llaves de
VerificadorResolubilidad (FR-301 a FR-306, FR-316, FR-322). Criptas pequeñas armadas a mano con
tests/ayudas_resolubilidad.py, en la notación de la spec: salvo que se diga otra cosa, la sala inicial es la 1,
sala_salida es la 9, llave_salida es S y la puerta de salida es la 8–9 (S).

verificar() se importa dentro de la prueba: hasta T024 cada prueba falla por su cuenta al importarlo.
"""
import dataclasses
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.Direcciones import E, N, O, S  # noqa: E402
from DTO.ReporteResolubilidadDTO import NO_RESOLUBLE, RESOLUBLE  # noqa: E402
from DTO.SalaDTO import EnemigoEnSalaDTO, TrampaEnSalaDTO  # noqa: E402
from tests.ayudas_resolubilidad import (abierta, cara, cripta, orden_es_valido, permutar, puerta,  # noqa: E402
                                        ubic)


def verificar(datos):
    """VerificadorResolubilidad.verificar(cripta, salas, ubicaciones). Hasta T024 no existe: es el fallo esperado."""
    from Logic.VerificadorResolubilidad import verificar as verificar_logica
    dto, salas, ubicaciones = datos
    return verificar_logica(dto, salas, ubicaciones)


def motivo_fr322(sala_salida: int = 9, llave_salida: str = "S") -> str:
    """Texto literal del motivo de FR-322 (contrato del reporte)."""
    return (f"Ninguna puerta cerrada por la que se entra a la sala de salida {sala_salida} pide {llave_salida} desde "
            f"la sala de la que se entra (las puertas que piden {llave_salida} pero no llevan a la sala {sala_salida} "
            f"no cuentan): la victoria es imposible (§3.5, P1 §2.12).")


# ---------------------------------------------------------------- criptas de los escenarios
def cripta_h1_1():
    """Única puerta cerrada: la de salida 8–9 (S); S en la sala 3, alcanzable por salidas abiertas."""
    return cripta(9, [abierta(1, E, 2), abierta(2, E, 3), abierta(3, S, 8), puerta(8, E, 9, "S")], [ubic("S", 3)])


def cripta_h1_2():
    """Ninguna puerta cerrada, ni hacia la 9; S en la sala 3."""
    return cripta(9, [abierta(1, E, 2), abierta(2, E, 3), abierta(3, S, 8), abierta(8, E, 9)], [ubic("S", 3)])


def cripta_h1_3():
    """A en 2 (salida 1–2), puerta 1–3 (A), B en 3, puerta 3–4 (B), S en 4; 4–8 abierta y la puerta 8–9 (S)."""
    return cripta(9, [abierta(1, E, 2), puerta(1, S, 3, "A"), puerta(3, E, 4, "B"), abierta(4, S, 8),
                      puerta(8, E, 9, "S")],
                  [ubic("S", 4), ubic("B", 3), ubic("A", 2)])


def cripta_h1_4():
    """Apéndice B, caso 2: B la suelta el errante e-1203, que inicia en la sala 12; puerta 12–8 (B)."""
    return cripta(12, [abierta(1, E, 12), puerta(12, S, 8, "B"), puerta(8, E, 9, "S")],
                  [ubic("B", 12, "e-1203"), ubic("S", 8)])


def cripta_h1_5():
    """Apéndice B, caso 3: A en 2 y B en 3 sin llaves; puertas 5–6 (A) y 6–7 (B); S en 7."""
    return cripta(9, [abierta(1, E, 2), abierta(1, S, 3), abierta(1, O, 5), puerta(5, S, 6, "A"),
                      puerta(6, S, 7, "B"), abierta(7, E, 8), puerta(8, E, 9, "S")],
                  [ubic("S", 7), ubic("B", 3), ubic("A", 2)])


def cripta_h1_6(costo: int | None = None):
    """Enemigo activo en la 2, trampa en la 3, puerta 2–3 (A) con cierre automático; 'costo' en todas las salidas."""
    dto, salas, ubicaciones = cripta(9, [abierta(1, E, 2, costo), puerta(2, E, 3, "A", costo, cierre_automatico=3),
                                         abierta(3, S, 8, costo), puerta(8, E, 9, "S", costo)],
                                     [ubic("A", 2), ubic("S", 3)])
    salas[1] = dataclasses.replace(salas[1], contenido_cargado=True, enemigos=[EnemigoEnSalaDTO("e-201", "ent_x")])
    salas[2] = dataclasses.replace(salas[2], contenido_cargado=True, trampas=[TrampaEnSalaDTO("t-301", "trp_x")])
    return dto, salas, ubicaciones


def cripta_h1_7():
    """A en 2; puertas 1–3 (A) y 4–5 (A) en el camino; S en 5."""
    return cripta(9, [abierta(1, E, 2), puerta(1, S, 3, "A"), abierta(3, E, 4), puerta(4, S, 5, "A"),
                      abierta(5, E, 8), puerta(8, E, 9, "S")],
                  [ubic("A", 2), ubic("S", 5)])


def cripta_h1_10():
    """Puerta 1–3 declarada solo en la cara de la 1 (cerrada, A); la cara de la 3 no declara nada. A en 2, S en 3."""
    return cripta(9, [abierta(1, E, 2), cara(1, S, 3, cerrada=True, llave="A"), cara(3, N, 1), abierta(3, E, 8),
                      puerta(8, E, 9, "S")],
                  [ubic("A", 2), ubic("S", 3)])


def cripta_h1_10_desde_la_3():
    """La misma puerta vista desde la sala 3: se empieza en la 3, T en la 4 y S en la 1, detrás de la cara de la 3."""
    return cripta(9, [cara(1, S, 3, cerrada=True, llave="T"), cara(3, N, 1), abierta(3, E, 4), abierta(1, O, 8),
                      puerta(8, S, 9, "S")],
                  [ubic("T", 4), ubic("S", 1)], sala_inicial=3)


def cripta_h1_11():
    """A en la 4 (alcanzable) y en la 12 (detrás de 11–12 (B), B sin ubicación); puerta 5–6 (A); S en 6."""
    return cripta(12, [abierta(1, E, 4), abierta(4, E, 5), puerta(5, E, 6, "A"), abierta(6, S, 8),
                       puerta(8, E, 9, "S"), abierta(1, S, 11), puerta(11, E, 12, "B")],
                  [ubic("A", 12), ubic("A", 4), ubic("S", 6)])


def cripta_salida_abierta_y_puerta():
    """La 9 se alcanza por la salida abierta 7–9 y también por la puerta de salida 8–9 (S); S en 7."""
    return cripta(9, [abierta(1, E, 7), abierta(7, S, 9), abierta(1, S, 8), puerta(8, E, 9, "S")], [ubic("S", 7)])


def cripta_puerta_s_que_no_lleva_a_la_salida():
    """La 9 solo por la salida abierta 1–9; la puerta 2–3 pide S pero no lleva a la 9."""
    return cripta(9, [abierta(1, E, 2), puerta(2, E, 3, "S"), abierta(1, S, 9)], [ubic("S", 2)])


def cripta_s_solo_en_la_cara_de_la_salida():
    """Puerta 8–9: la cara de la 8 (desde la que se entra) pide A y la de la 9 pide S. A y S en la 1."""
    return cripta(9, [abierta(1, E, 8), cara(8, E, 9, cerrada=True, llave="A"), cara(9, O, 8, cerrada=True, llave="S")],
                  [ubic("A", 1), ubic("S", 1)])


def cripta_s_en_la_sala_inicial():
    """S en la sala inicial; A detrás de la puerta 1–2 (S): S se obtiene en la oleada 0, antes que A."""
    return cripta(9, [puerta(1, E, 2, "S"), abierta(1, S, 8), puerta(8, E, 9, "S")], [ubic("A", 2), ubic("S", 1)])


def cripta_inicial_es_salida_sin_puerta():
    """sala_inicial = sala_salida = 1, sin ninguna puerta hacia la 1."""
    return cripta(3, [abierta(1, E, 2), abierta(2, E, 3)], [ubic("S", 3)], sala_salida=1)


def cripta_inicial_es_salida_s_detras_de_su_puerta():
    """sala_inicial = sala_salida = 1; puerta 1–2 (S) y S en la 2: no se puede obtener."""
    return cripta(3, [puerta(1, E, 2, "S")], [ubic("S", 2)], sala_salida=1)


def cripta_inicial_es_salida_resoluble():
    """sala_inicial = sala_salida = 1; S en la 2 (salida 1–2); puerta 1–3 (S): se vuelve a la 1 desde la 3."""
    return cripta(3, [abierta(1, E, 2), puerta(1, S, 3, "S")], [ubic("S", 2)], sala_salida=1)


def cripta_llave_innecesaria():
    """La del H1-1 más la llave X en la sala 2, que no abre ninguna puerta."""
    dto, salas, ubicaciones = cripta_h1_1()
    return dto, salas, ubicaciones + [ubic("X", 2)]


def cripta_cierre_con_llaves_distintas():
    """Puerta 2–3 con cierre automático: la cara de la 2 pide A y la de la 3 pide B (sin ubicación). A en 1, S en 3."""
    return cripta(9, [abierta(1, E, 2), cara(2, E, 3, cerrada=True, llave="A", cierre_automatico=2),
                      cara(3, O, 2, cerrada=True, llave="B", cierre_automatico=2), abierta(2, S, 8),
                      puerta(8, E, 9, "S")],
                  [ubic("A", 1), ubic("S", 3)])


# Todas las criptas resolubles de este archivo (SC-304) y todas las de este archivo (FR-306).
RESOLUBLES = [cripta_h1_1, cripta_h1_3, cripta_h1_4, cripta_h1_5, cripta_h1_6, cripta_h1_7, cripta_h1_10,
              cripta_h1_10_desde_la_3, cripta_h1_11, cripta_salida_abierta_y_puerta, cripta_s_en_la_sala_inicial,
              cripta_inicial_es_salida_resoluble, cripta_llave_innecesaria, cripta_cierre_con_llaves_distintas]
NO_RESOLUBLES = [cripta_h1_2, cripta_puerta_s_que_no_lleva_a_la_salida, cripta_s_solo_en_la_cara_de_la_salida,
                 cripta_inicial_es_salida_sin_puerta, cripta_inicial_es_salida_s_detras_de_su_puerta]


class PruebasHistoria1(unittest.TestCase):
    """T020: escenarios de la historia 1 que son de Lógica."""

    def comprobar_resoluble(self, datos, orden):
        reporte = verificar(datos)
        self.assertEqual(reporte.veredicto, RESOLUBLE)
        self.assertEqual(reporte.orden_llaves, orden)
        self.assertEqual((reporte.id_cripta, reporte.version_cripta, reporte.llave_salida),
                         (datos[0].id, datos[0].version, datos[0].llave_salida))
        self.assertEqual((reporte.llaves_no_obtenibles, reporte.frontera, reporte.ciclos), ([], [], []))
        self.assertIsNone(reporte.motivo)
        self.assertIsNone(reporte.mensaje)
        return reporte

    def test_h1_1_fr301_fr304_fr305_unica_puerta_cerrada_es_la_de_salida(self):
        dto, salas, ubicaciones = cripta_h1_1()
        self.comprobar_resoluble((dto, salas, ubicaciones), ["S"])
        self.assertEqual(cripta_h1_1()[1], salas)          # FR-301: no modifica lo que recibe

    def test_h1_2_fr304_fr322_sin_puertas_cerradas_no_resoluble_con_motivo(self):
        reporte = verificar(cripta_h1_2())
        self.assertEqual(reporte.veredicto, NO_RESOLUBLE)
        self.assertEqual(reporte.motivo, motivo_fr322())
        self.assertEqual(reporte.orden_llaves, [])
        self.assertNotIn("S", [ll.id for ll in reporte.llaves_no_obtenibles])
        self.assertEqual(reporte.frontera, [])
        self.assertEqual(reporte.llave_salida, "S")

    def test_h1_3_fr304_fr305_cadena_a_b_llave_salida(self):
        self.comprobar_resoluble(cripta_h1_3(), ["A", "B", "S"])

    def test_h1_4_apendiceB_caso2_fr303_fr316_llave_de_enemigo_errante(self):
        self.comprobar_resoluble(cripta_h1_4(), ["B", "S"])        # B obtenible en la sala 12, la de e-1203

    def test_h1_5_apendiceB_caso3_fr305_fr306_mismo_orden_en_dos_ejecuciones(self):
        primero = verificar(cripta_h1_5())
        segundo = verificar(cripta_h1_5())
        self.assertEqual(primero.orden_llaves, ["A", "B", "S"])
        self.assertEqual(segundo, primero)
        dto, salas, ubicaciones = cripta_h1_5()
        for semilla in range(4):
            otra = verificar((dto, permutar(salas, semilla), permutar(ubicaciones, semilla + 10)))
            self.assertEqual(otra.orden_llaves, ["A", "B", "S"], semilla)

    def test_h1_6_fr302_enemigo_trampa_cierre_y_costo_no_bloquean(self):
        sin_costo = self.comprobar_resoluble(cripta_h1_6(), ["A", "S"])
        for costo in (1, 250, 999):
            self.assertEqual(verificar(cripta_h1_6(costo)), sin_costo, costo)

    def test_h1_7_fr302_las_llaves_no_se_consumen(self):
        self.comprobar_resoluble(cripta_h1_7(), ["A", "S"])

    def test_h1_10_fr302_fr305_llave_declarada_en_una_sola_cara(self):
        self.comprobar_resoluble(cripta_h1_10(), ["A", "S"])
        # Desde la sala 3 también está cerrada con T: S (en la 1) llega en la oleada siguiente a T, aunque S < T.
        self.comprobar_resoluble(cripta_h1_10_desde_la_3(), ["T", "S"])

    def test_h1_11_fr316_fr305_copia_alcanzable_de_la_llave(self):
        self.comprobar_resoluble(cripta_h1_11(), ["A", "S"])


class PruebasCasosBordeHistoria1(unittest.TestCase):
    """T021: casos borde y criterios sin escenario propio."""

    def test_fr304_salida_alcanzable_por_salida_abierta_y_por_puerta_de_salida(self):
        reporte = verificar(cripta_salida_abierta_y_puerta())
        self.assertEqual((reporte.veredicto, reporte.orden_llaves), (RESOLUBLE, ["S"]))

    def test_fr304_fr322_puerta_con_llave_salida_que_no_lleva_a_sala_salida(self):
        reporte = verificar(cripta_puerta_s_que_no_lleva_a_la_salida())
        self.assertEqual((reporte.veredicto, reporte.motivo), (NO_RESOLUBLE, motivo_fr322()))

    def test_fr304_solo_la_cara_de_sala_salida_pide_llave_salida(self):
        reporte = verificar(cripta_s_solo_en_la_cara_de_la_salida())
        self.assertEqual((reporte.veredicto, reporte.motivo), (NO_RESOLUBLE, motivo_fr322()))

    def test_fr304_llave_salida_en_la_sala_inicial(self):
        reporte = verificar(cripta_s_en_la_sala_inicial())
        self.assertEqual((reporte.veredicto, reporte.orden_llaves), (RESOLUBLE, ["S", "A"]))   # S en la oleada 0

    def test_fr304_sala_inicial_es_sala_salida(self):
        sin_puerta = verificar(cripta_inicial_es_salida_sin_puerta())
        self.assertEqual((sin_puerta.veredicto, sin_puerta.motivo), (NO_RESOLUBLE, motivo_fr322(1)))
        encerrada = verificar(cripta_inicial_es_salida_s_detras_de_su_puerta())
        self.assertEqual((encerrada.veredicto, encerrada.motivo), (NO_RESOLUBLE, None))
        resoluble = verificar(cripta_inicial_es_salida_resoluble())
        self.assertEqual((resoluble.veredicto, resoluble.orden_llaves), (RESOLUBLE, ["S"]))

    def test_fr305_llave_innecesaria_aparece_en_el_orden(self):
        reporte = verificar(cripta_llave_innecesaria())
        self.assertEqual((reporte.veredicto, reporte.orden_llaves), (RESOLUBLE, ["S", "X"]))

    def test_fr302_cierre_automatico_con_llaves_distintas_por_cara_no_bloquea(self):
        # Decisión del grupo, límite conocido: el motor la cierra y volver pide B, pero la verificación dice resoluble.
        reporte = verificar(cripta_cierre_con_llaves_distintas())
        self.assertEqual((reporte.veredicto, reporte.orden_llaves), (RESOLUBLE, ["A", "S"]))

    def test_sc304_orden_valido_en_todas_las_criptas_resolubles(self):
        for armar in RESOLUBLES:
            with self.subTest(armar.__name__):
                dto, salas, ubicaciones = armar()
                reporte = verificar((dto, salas, ubicaciones))
                self.assertEqual(reporte.veredicto, RESOLUBLE)
                self.assertTrue(orden_es_valido(dto, salas, ubicaciones, reporte.orden_llaves), reporte.orden_llaves)

    def test_fr306_entrada_permutada_mismo_resultado(self):
        for armar in RESOLUBLES + NO_RESOLUBLES:
            with self.subTest(armar.__name__):
                dto, salas, ubicaciones = armar()
                esperado = verificar((dto, salas, ubicaciones))
                for semilla in range(5):
                    otra = verificar((dto, permutar(salas, semilla), permutar(ubicaciones, 100 + semilla)))
                    self.assertEqual(otra, esperado, semilla)


if __name__ == "__main__":
    unittest.main()
