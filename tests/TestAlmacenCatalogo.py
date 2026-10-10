"""
Pruebas de Data/AlmacenCatalogo.py (caché del catálogo en DISCO, enunciado §4.4).
Escribe SOLO en carpetas temporales: nunca toca la carpeta cache/ real.
"""
import json
import os
import shutil
import tempfile
import unittest

from Data.AlmacenCatalogo import AlmacenCatalogo
from Data.CacheCatalogo import CacheCatalogo
from Data.FuenteOffline import FuenteOffline
from DTO.ObjetoDTO import ObjetoDTO
from tests.Utilidades import PAQUETE, catalogo_real, leer_paquete

VERSION = leer_paquete("catalogo_version.json")["version"]   # la versión real: be68d322d2f5


def fichas_reales() -> list:
    ids = [f["id"] for f in catalogo_real()]
    fuente = FuenteOffline(PAQUETE)
    return fuente.obtener_catalogo(ids[:10]) + fuente.obtener_catalogo(ids[10:])


def ficha(id_ficha: str) -> ObjetoDTO:
    return ObjetoDTO(id=id_ficha, nombre=id_ficha, clase="arma", peso=1, valor=1, ataque_bonus=1)


class PruebasAlmacenCatalogo(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.mkdtemp()
        self.base = os.path.join(self.temp, "cache", "catalogo")

    def tearDown(self):
        shutil.rmtree(self.temp)

    def almacen(self, version=VERSION) -> AlmacenCatalogo:
        a = AlmacenCatalogo(version, self.base)
        a.preparar()
        return a

    def ruta(self, *partes) -> str:
        return os.path.join(self.base, *partes)

    # ------------------------------------------------------------ guardar y leer
    def test_las_11_fichas_reales_sobreviven_al_cierre(self):
        fichas = fichas_reales()
        a = self.almacen()
        for f in fichas:
            a.guardar(f)
        self.assertEqual(a.escrituras(), 11)
        otra_ejecucion = self.almacen()                  # objeto nuevo = programa reiniciado
        for f in fichas:
            self.assertEqual(otra_ejecucion.leer(f.id), f)   # mismo DTO, misma clase y datos
        self.assertEqual(otra_ejecucion.lecturas(), 11)

    def test_formato_en_disco(self):
        a = self.almacen()
        a.guardar(fichas_reales()[1])                    # ent_rata_gigante
        with open(self.ruta(VERSION, "ent_rata_gigante.json"), encoding="utf-8") as f:
            datos = json.load(f)
        self.assertEqual((datos["id"], datos["clase"]), ("ent_rata_gigante", "enemigo"))
        with open(self.ruta(VERSION, "VERSION"), encoding="utf-8") as f:
            self.assertEqual(f.read(), VERSION)
        self.assertFalse(os.path.exists(self.ruta(VERSION, "ent_rata_gigante.json.tmp")))

    def test_ficha_que_nunca_se_guardo(self):
        a = self.almacen()
        self.assertFalse(a.contiene("itm_antorcha"))
        self.assertIsNone(a.leer("itm_antorcha"))
        self.assertEqual(a.lecturas(), 0)               # no hubo archivo que leer

    def test_guardar_otra_vez_reemplaza(self):
        a = self.almacen()
        a.guardar(ficha("x"))
        nueva = ObjetoDTO(id="x", nombre="Nueva", clase="pocion", peso=2, valor=3, cura=5)
        a.guardar(nueva)
        self.assertEqual(a.leer("x"), nueva)

    def test_guardar_sin_preparar_crea_la_carpeta_y_la_marca(self):
        a = AlmacenCatalogo(VERSION, self.base)
        a.guardar(ficha("x"))
        self.assertTrue(os.path.isfile(self.ruta(VERSION, "VERSION")))
        self.assertTrue(a.contiene("x"))

    # ------------------------------------------------------------ versiones
    def test_cambio_de_version_descarta_lo_viejo(self):
        viejo = self.almacen("v1")
        viejo.guardar(ficha("x"))
        nuevo = AlmacenCatalogo("v2", self.base)
        self.assertEqual(nuevo.preparar(), ["v1"])
        self.assertFalse(os.path.exists(self.ruta("v1")))
        self.assertFalse(nuevo.contiene("x"))           # habrá que pedirla de nuevo a la red

    def test_misma_version_conserva_lo_guardado(self):
        self.almacen().guardar(ficha("x"))
        a = AlmacenCatalogo(VERSION, self.base)
        self.assertEqual(a.preparar(), [])
        self.assertTrue(a.contiene("x"))

    def test_no_borra_carpetas_que_no_son_suyas(self):
        ajena = self.ruta("mis_cosas")
        os.makedirs(ajena)
        with open(os.path.join(ajena, "importante.txt"), "w", encoding="utf-8") as f:
            f.write("no borrar")
        marca_falsa = self.ruta("v9")                    # marca que no dice su propio nombre
        os.makedirs(marca_falsa)
        with open(os.path.join(marca_falsa, "VERSION"), "w", encoding="utf-8") as f:
            f.write("otra")
        self.assertEqual(AlmacenCatalogo(VERSION, self.base).preparar(), [])
        self.assertTrue(os.path.isfile(os.path.join(ajena, "importante.txt")))
        self.assertTrue(os.path.isdir(marca_falsa))

    # ------------------------------------------------------------ archivos dañados
    def test_archivo_danado_se_borra_y_no_detiene_nada(self):
        a = self.almacen()
        for id_ficha, contenido in (("roto", "{esto no es json"),
                                    ("incompleto", '{"id": "incompleto", "clase": "arma"}'),
                                    ("clase_rara", '{"id": "clase_rara", "clase": "dragon"}'),
                                    ("lista", "[1, 2, 3]")):
            with open(self.ruta(VERSION, id_ficha + ".json"), "w", encoding="utf-8") as f:
                f.write(contenido)
            self.assertIsNone(a.leer(id_ficha))
            self.assertFalse(a.contiene(id_ficha))      # se borró: la próxima vez se pide y se reescribe
        self.assertEqual(a.danadas(), 4)

    def test_archivo_de_otro_id_no_se_acepta_ni_se_borra(self):
        a = self.almacen()
        a.guardar(ficha("y"))
        shutil.copy(self.ruta(VERSION, "y.json"), self.ruta(VERSION, "x.json"))
        self.assertIsNone(a.leer("x"))
        self.assertTrue(a.contiene("x"))

    # ------------------------------------------------------------ nombres peligrosos
    def test_ids_y_versiones_peligrosos(self):
        a = self.almacen()
        for malo in ("../hack", "a/b", "a\\b", "", "con", "x.json", "ñandú"):
            self.assertFalse(a.contiene(malo))
            self.assertIsNone(a.leer(malo))
            with self.assertRaises(ValueError):
                a.guardar(ficha(malo))
            with self.assertRaises(ValueError):
                AlmacenCatalogo(malo, self.base)
        self.assertFalse(os.path.exists(os.path.join(self.temp, "cache", "hack.json")))

    # ------------------------------------------------------------ junto con la caché en memoria
    def test_ficha_liberada_de_memoria_sigue_en_disco(self):
        """§4.4: recuperar una ficha liberada cuesta una lectura de disco, no una solicitud."""
        memoria = CacheCatalogo(2)
        disco = self.almacen()
        a, b, c = ficha("a"), ficha("b"), ficha("c")
        for f in (a, b, c):
            disco.guardar(f)                             # toda ficha nueva se persiste
            memoria.insertar(f)
        self.assertFalse(memoria.contiene("a"))         # la liberó la caché (LRU)
        self.assertEqual(disco.leer("a"), a)            # pero sigue en disco
        self.assertEqual(disco.lecturas(), 1)


if __name__ == "__main__":
    unittest.main()