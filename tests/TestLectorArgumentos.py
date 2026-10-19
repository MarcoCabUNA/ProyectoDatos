"""
Pruebas de UIController/LectorArgumentos.py (argparse) y DTO/ConfiguracionDTO.py (banderas del programa).
Ningún caso debe cerrar el programa: los errores llegan como ErrorArgumentos y la ayuda como un campo del DTO.
"""
import dataclasses
import unittest

from Data.CacheCatalogo import TOPE_POR_DEFECTO
from DTO.ConfiguracionDTO import CACHE_SIZE_POR_DEFECTO, ConfiguracionDTO
from UIController.LectorArgumentos import TEXTO_AYUDA, ErrorArgumentos, leer_argumentos


class PruebasLectorArgumentos(unittest.TestCase):

    def falla(self, argumentos, *textos_esperados):
        """Comprueba que lanza ErrorArgumentos (no SystemExit) y que el mensaje nombra lo que hay que corregir."""
        with self.assertRaises(ErrorArgumentos) as ctx:
            leer_argumentos(argumentos)
        for texto in textos_esperados:
            self.assertIn(texto, str(ctx.exception))

    # ------------------------------------------------------------ casos válidos
    def test_sin_argumentos_usa_los_valores_por_defecto(self):
        c = leer_argumentos([])
        self.assertEqual(c, ConfiguracionDTO())
        self.assertEqual((c.offline, c.cache_size, c.replay, c.bench, c.ayuda), (False, 25, None, False, False))

    def test_el_valor_por_defecto_coincide_con_la_cache(self):
        self.assertEqual(CACHE_SIZE_POR_DEFECTO, TOPE_POR_DEFECTO)

    def test_cada_bandera(self):
        self.assertTrue(leer_argumentos(["--offline"]).offline)
        self.assertTrue(leer_argumentos(["--bench"]).bench)
        self.assertEqual(leer_argumentos(["--cache-size", "40"]).cache_size, 40)
        self.assertEqual(leer_argumentos(["--replay", "partida.log"]).replay, "partida.log")

    def test_ayuda_no_cierra_el_programa(self):
        for ayuda in ("-h", "--help", "--ayuda"):
            self.assertTrue(leer_argumentos([ayuda]).ayuda)

    def test_valor_con_igual(self):
        self.assertEqual(leer_argumentos(["--cache-size=7"]).cache_size, 7)
        self.assertEqual(leer_argumentos(["--replay=logs/p1.log"]).replay, "logs/p1.log")

    def test_combinaciones_en_cualquier_orden(self):
        c = leer_argumentos(["--cache-size", "1", "--offline", "--replay", "a.log"])
        self.assertEqual((c.offline, c.cache_size, c.replay, c.bench), (True, 1, "a.log", False))
        self.assertEqual(leer_argumentos(["--bench", "--offline", "--cache-size=50"]),
                         ConfiguracionDTO(offline=True, cache_size=50, bench=True))

    def test_ruta_con_espacios_y_ceros_a_la_izquierda(self):
        self.assertEqual(leer_argumentos(["--replay", "mis partidas/p 1.log"]).replay, "mis partidas/p 1.log")
        self.assertEqual(leer_argumentos(["--cache-size", "007"]).cache_size, 7)

    def test_si_se_repite_vale_la_ultima(self):
        self.assertEqual(leer_argumentos(["--cache-size", "3", "--cache-size=4"]).cache_size, 4)

    # ------------------------------------------------------------ --cache-size inválido
    def test_cache_size_invalido(self):
        for malo in ("0", "-5", "abc", "2.5", "1e3", " 3", "", "²"):
            self.falla(["--cache-size", malo], "--cache-size")
        self.falla(["--cache-size=0"], "mayor o igual a 1")
        self.falla(["--cache-size="], "--cache-size")

    def test_falta_el_valor(self):
        self.falla(["--cache-size"], "--cache-size")
        self.falla(["--replay"], "--replay")
        self.falla(["--replay", "--offline"], "--replay")      # no toma otra bandera como archivo
        self.falla(["--replay="], "--replay")
        self.falla(["--replay", "   "], "--replay")

    # ------------------------------------------------------------ otros errores
    def test_opcion_desconocida_mal_escrita_o_abreviada(self):
        self.falla(["--offlin"], "--offlin")
        self.falla(["--off"], "--off")                         # sin abreviaturas
        self.falla(["--cache_size", "3"], "--cache_size")
        self.falla(["partida.log"], "partida.log")
        self.falla(["-x"], "-x")

    def test_bandera_que_no_lleva_valor(self):
        self.falla(["--offline=true"], "--offline")
        self.falla(["--bench=1"], "--bench")

    def test_replay_y_bench_juntos(self):
        self.falla(["--replay", "a.log", "--bench"], "--replay", "--bench")

    # ------------------------------------------------------------ DTO y ayuda
    def test_dto_inmutable(self):
        c = leer_argumentos(["--offline"])
        with self.assertRaises(dataclasses.FrozenInstanceError):
            setattr(c, "offline", False)

    def test_texto_de_ayuda_menciona_todas_las_banderas(self):
        for bandera in ("--offline", "--cache-size", "--replay", "--bench", "--ayuda"):
            self.assertIn(bandera, TEXTO_AYUDA)

    def test_es_un_valueerror(self):
        """Quien no conozca ErrorArgumentos igual puede atraparlo como ValueError."""
        with self.assertRaises(ValueError):
            leer_argumentos(["--nada"])


if __name__ == "__main__":
    unittest.main()