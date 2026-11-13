"""
Pruebas de las banderas --checkpoint-cada y --hasta de UIController/LectorArgumentos.py (feature 004).

Solo la LECTURA de argumentos (FR-410 y FR-415): validan la forma y devuelven un ConfiguracionDTO. Qué se hace
con ellos (la línea de tiempo, el replay hasta t) llega en T037/T039/T041 y T050. No toca los archivos de
prueba del integrante 2 (tests/TestLectorArgumentos.py).
"""
import dataclasses
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from DTO.ConfiguracionDTO import CHECKPOINT_POR_DEFECTO, ConfiguracionDTO
from UIController.LectorArgumentos import TEXTO_AYUDA, ErrorArgumentos, leer_argumentos


class PruebasCheckpointCada(unittest.TestCase):

    def test_h5_4_fr415_sin_la_bandera_se_usa_el_valor_por_defecto(self):
        self.assertEqual(leer_argumentos([]).checkpoint_cada, CHECKPOINT_POR_DEFECTO)

    def test_fr415_valores_validos(self):
        self.assertEqual(leer_argumentos(["--checkpoint-cada", "1"]).checkpoint_cada, 1)
        self.assertEqual(leer_argumentos(["--checkpoint-cada", "50"]).checkpoint_cada, 50)
        self.assertEqual(leer_argumentos(["--checkpoint-cada=7"]).checkpoint_cada, 7)

    def test_h5_3_fr415_valores_invalidos_son_error_de_uso(self):
        for malo in ("0", "-2", "abc", "2.5", "", " 3", "²"):
            with self.subTest(malo=malo):
                with self.assertRaises(ErrorArgumentos):
                    leer_argumentos(["--checkpoint-cada", malo])

    def test_h5_3_fr415_sin_valor_es_error_de_uso(self):
        with self.assertRaises(ErrorArgumentos):
            leer_argumentos(["--checkpoint-cada"])
        with self.assertRaises(ErrorArgumentos):
            leer_argumentos(["--checkpoint-cada", "--offline"])

    def test_fr415_se_combina_con_las_otras_banderas(self):
        config = leer_argumentos(["--offline", "--checkpoint-cada", "5", "--cache-size", "40"])
        self.assertTrue(config.offline)
        self.assertEqual((config.checkpoint_cada, config.cache_size), (5, 40))


class PruebasHasta(unittest.TestCase):

    def test_h2_6_fr410_replay_sin_hasta_es_la_partida_completa(self):
        config = leer_argumentos(["--replay", "partida.log"])
        self.assertEqual(config.replay, "partida.log")
        self.assertIsNone(config.hasta)

    def test_fr410_replay_con_hasta_valido(self):
        config = leer_argumentos(["--replay", "partida.log", "--hasta", "300"])
        self.assertEqual((config.replay, config.hasta), ("partida.log", 300))
        self.assertEqual(leer_argumentos(["--hasta", "300", "--replay", "p.log"]).hasta, 300)   # en cualquier orden
        self.assertEqual(leer_argumentos(["--replay", "p.log", "--hasta=45"]).hasta, 45)

    def test_h2_5_fr410_hasta_cero_es_valido(self):
        self.assertEqual(leer_argumentos(["--replay", "p.log", "--hasta", "0"]).hasta, 0)

    def test_h2_3_fr410_hasta_sin_valor_es_error_de_uso(self):
        with self.assertRaises(ErrorArgumentos):
            leer_argumentos(["--replay", "p.log", "--hasta"])

    def test_h2_3_fr410_hasta_no_entero_o_negativo_es_error_de_uso(self):
        for malo in ("abc", "-3", "2.5", "", " 3", "1e3"):
            with self.subTest(malo=malo):
                with self.assertRaises(ErrorArgumentos):
                    leer_argumentos(["--replay", "p.log", "--hasta", malo])

    def test_h2_3_fr410_hasta_sin_replay_es_error_de_uso(self):
        with self.assertRaises(ErrorArgumentos):
            leer_argumentos(["--hasta", "300"])
        with self.assertRaises(ErrorArgumentos):
            leer_argumentos(["--offline", "--hasta", "300"])
        with self.assertRaises(ErrorArgumentos):
            leer_argumentos(["--bench", "--hasta", "300"])

    def test_fr410_el_error_de_hasta_sin_replay_dice_que_falta_replay(self):
        with self.assertRaises(ErrorArgumentos) as error:
            leer_argumentos(["--hasta", "300"])
        self.assertIn("--replay", str(error.exception))


class PruebasConfiguracionYAyuda(unittest.TestCase):

    def test_hasta_va_despues_de_checkpoint_cada_al_final_del_dto_fr410(self):
        nombres = [campo.name for campo in dataclasses.fields(ConfiguracionDTO)]
        self.assertEqual(nombres[5:7], ["checkpoint_cada", "hasta"])
        self.assertIsNone(ConfiguracionDTO().hasta)

    def test_el_texto_de_ayuda_menciona_las_banderas_nuevas(self):
        self.assertIn("--checkpoint-cada", TEXTO_AYUDA)
        self.assertIn("--hasta", TEXTO_AYUDA)

    def test_fr410_fr415_el_programa_sale_con_codigo_2_ante_una_bandera_invalida(self):
        for argumentos in (["--checkpoint-cada", "0"], ["--hasta", "5"], ["--replay", "p.log", "--hasta", "-1"]):
            with self.subTest(argumentos=argumentos):
                proceso = subprocess.run([sys.executable, "-B", "main.py", *argumentos], cwd=RAIZ,
                                         capture_output=True, text=True, encoding="utf-8", errors="replace",
                                         timeout=60)
                self.assertEqual(proceso.returncode, 2, proceso.stdout + proceso.stderr)


if __name__ == "__main__":
    unittest.main()
