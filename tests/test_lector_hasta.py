"""
Pruebas de la bandera --hasta de LectorArgumentos (feature 004, T036, FR-410).

No se edita tests/TestLectorArgumentos.py (es del integrante 2): estas pruebas son aparte.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from UIController.LectorArgumentos import ErrorArgumentos, leer_argumentos


class PruebasLectorHasta(unittest.TestCase):

    def test_h2_3_fr410_hasta_sin_valor_es_error_de_uso(self):
        with self.assertRaises(ErrorArgumentos):
            leer_argumentos(["--replay", "partida.log", "--hasta"])

    def test_h2_3_fr410_hasta_no_entero_o_negativo_es_error_de_uso(self):
        for valor in ("abc", "-3", "2.5", ""):
            with self.subTest(valor=valor):
                with self.assertRaises(ErrorArgumentos):
                    leer_argumentos(["--replay", "partida.log", "--hasta", valor])

    def test_h2_3_fr410_hasta_sin_replay_es_error_de_uso(self):
        with self.assertRaises(ErrorArgumentos) as contexto:
            leer_argumentos(["--hasta", "5"])
        self.assertIn("--replay", str(contexto.exception))

    def test_fr410_replay_con_hasta_valido(self):
        config = leer_argumentos(["--replay", "partida.log", "--hasta", "12"])
        self.assertEqual((config.replay, config.hasta), ("partida.log", 12))
        self.assertEqual(leer_argumentos(["--replay", "p.log", "--hasta=0"]).hasta, 0)    # 0 es el estado inicial

    def test_h2_6_fr410_replay_sin_hasta_es_la_partida_completa(self):
        config = leer_argumentos(["--replay", "partida.log"])
        self.assertEqual(config.replay, "partida.log")
        self.assertIsNone(config.hasta)


if __name__ == "__main__":
    unittest.main()
