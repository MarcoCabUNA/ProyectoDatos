"""
Pruebas de Data/AlmacenPuntajes.py (tabla de puntajes local, enunciado §2.12).
Todo se escribe en carpetas temporales.
"""
import os
import shutil
import tempfile
import unittest

from Data.AlmacenPuntajes import RUTA_POR_DEFECTO, AlmacenPuntajes, ErrorPuntajes
from DTO.PuntajeDTO import PuntajeDTO

P1 = PuntajeDTO("Derek", "cripta-01", "fd58f7743b9e", 42, 3, 4200)
P2 = PuntajeDTO("Kristel", "cripta-01", "fd58f7743b9e", 30, 5, 3100)
P3 = PuntajeDTO("Marco", "cripta-02", "aaaa", 10, 0, 900)


class PruebasAlmacenPuntajes(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.mkdtemp()
        self.ruta = os.path.join(self.temp, "saves", "puntajes.jsonl")
        self.almacen = AlmacenPuntajes(self.ruta)

    def tearDown(self):
        shutil.rmtree(self.temp)

    def contenido(self) -> str:
        with open(self.ruta, encoding="utf-8", newline="") as f:
            return f.read()

    def escribir_a_mano(self, texto: str) -> None:
        os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
        with open(self.ruta, "w", encoding="utf-8", newline="") as f:
            f.write(texto)

    def test_sin_archivo_la_tabla_esta_vacia(self):
        self.assertEqual(self.almacen.leer(), [])
        self.assertFalse(os.path.exists(self.ruta))

    def test_agregar_y_leer_en_el_orden_jugado(self):
        for p in (P1, P2, P3):
            self.almacen.agregar(p)
        self.assertEqual(self.almacen.leer(), [P1, P2, P3])        # sin ordenar: eso es de Servicios
        self.assertEqual(AlmacenPuntajes(self.ruta).leer(), [P1, P2, P3])   # otra ejecución

    def test_solo_anexa(self):
        self.almacen.agregar(P1)
        antes = self.contenido()
        self.almacen.agregar(P2)
        self.assertTrue(self.contenido().startswith(antes))
        self.assertEqual(self.contenido().count("\n"), 2)

    def test_nombres_raros(self):
        raros = [PuntajeDTO("Ñandú \"el bravo\"", "c", "v", 1, 1, 1),
                 PuntajeDTO("dos\nlíneas", "c", "v", 1, 1, 1),         # no parte la línea del archivo
                 PuntajeDTO("", "c", "v", 0, 0, 0)]
        for p in raros:
            self.almacen.agregar(p)
        self.assertEqual(self.almacen.leer(), raros)
        self.assertEqual(self.contenido().count("\n"), 3)

    def test_puntaje_invalido_no_se_guarda(self):
        malos = [PuntajeDTO("a", "c", "v", True, 1, 1),                 # type: ignore[arg-type]
                 PuntajeDTO(None, "c", "v", 1, 1, 1),                    # type: ignore[arg-type]
                 PuntajeDTO("a", "c", "v", 1, 1, 1.5)]                   # type: ignore[arg-type]
        for p in malos:
            with self.assertRaises(ErrorPuntajes, msg=repr(p)):
                self.almacen.agregar(p)
        with self.assertRaises(ErrorPuntajes):
            self.almacen.agregar(P1.a_diccionario())                    # type: ignore[arg-type]
        self.assertFalse(os.path.exists(self.ruta))

    def test_ultima_linea_a_medio_escribir_se_descarta(self):
        self.almacen.agregar(P1)
        self.escribir_a_mano(self.contenido() + '{"nombre":"Kris')
        self.assertEqual(self.almacen.leer(), [P1])

    def test_linea_danada_dice_cual(self):
        self.almacen.agregar(P1)
        base = self.contenido()
        for mala in ("esto no es json\n", '{"nombre":"x"}\n', "[1,2]\n", "\n",
                     '{"nombre":"x","mazmorra":"c","version":"v","acciones":"1","enemigos_derrotados":1,'
                     '"tiempo_final":1}\n'):
            self.escribir_a_mano(base + mala)
            with self.assertRaises(ErrorPuntajes) as ctx:
                self.almacen.leer()
            self.assertIn("línea 2", str(ctx.exception))

    def test_acepta_finales_de_linea_de_windows(self):
        self.almacen.agregar(P1)
        self.almacen.agregar(P2)
        self.escribir_a_mano(self.contenido().replace("\n", "\r\n"))
        self.assertEqual(self.almacen.leer(), [P1, P2])

    def test_ruta_por_defecto_en_saves(self):
        self.assertEqual(RUTA_POR_DEFECTO, os.path.join("saves", "puntajes.jsonl"))
        self.assertEqual(AlmacenPuntajes().ruta(), RUTA_POR_DEFECTO)

    def test_es_un_valueerror(self):
        self.escribir_a_mano("roto\n")
        with self.assertRaises(ValueError):
            self.almacen.leer()


if __name__ == "__main__":
    unittest.main()