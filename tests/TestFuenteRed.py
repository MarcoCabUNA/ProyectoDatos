"""
Pruebas de FuenteRed (y de FuenteJson, que contiene la traducción) con una ApiFalsa
que responde con los JSON REALES del paquete, sin usar la red.
Incluye las fichas de enemigo y trampa (DTOs del Integrante 1).
"""
import unittest

from Data.ClienteHttp import ErrorRed
from Data.FuenteDatos import FuenteDatos
from DTO.FichaEnemigoDTO import FichaEnemigoDTO
from DTO.FichaTrampaDTO import FichaTrampaDTO
from DTO.ObjetoDTO import ObjetoDTO
from tests.Utilidades import ID_CRIPTA, ApiFalsa, catalogo_real, fuente_red, general_real


class PruebasFuenteRed(unittest.TestCase):

    def setUp(self):
        self.api = ApiFalsa()
        self.fuente = fuente_red(self.api)

    def test_FuenteDatos_es_abstracta(self):
        with self.assertRaises(TypeError):
            FuenteDatos()   # type: ignore[abstract]

    def test_listar_criptas(self):
        self.assertEqual([c.id for c in self.fuente.listar_criptas()], [ID_CRIPTA])

    def test_datos_generales_fijan_el_presupuesto(self):
        cripta = self.fuente.obtener_datos_generales(ID_CRIPTA)
        self.assertEqual(cripta.version, general_real()["version"])
        self.assertEqual(self.fuente.presupuesto_solicitudes(), general_real()["presupuesto_solicitudes"])

    def test_versiones(self):
        self.assertEqual(self.fuente.obtener_version_cripta(ID_CRIPTA), general_real()["version"])
        self.assertIsInstance(self.fuente.obtener_version_catalogo(), str)

    def test_pagina_de_salas(self):
        salas = self.fuente.obtener_pagina_salas(ID_CRIPTA, 1, "v")
        self.assertEqual([s.id for s in salas], [1, 2, 3, 4, 5, 6])
        self.assertFalse(any(s.contenido_cargado for s in salas))
        with self.assertRaises(ValueError):
            self.fuente.obtener_pagina_salas(ID_CRIPTA, 0, "v")

    def test_contenido_en_el_orden_pedido(self):
        # ApiFalsa responde en orden invertido a propósito
        self.assertEqual([c.sala for c in self.fuente.obtener_contenido(ID_CRIPTA, [2, 4, 1])], [2, 4, 1])

    def test_lotes_invalidos_no_gastan_solicitudes(self):
        for lote in ([], list(range(1, 12)), [1, 1]):
            with self.assertRaises(ValueError):
                self.fuente.obtener_contenido(ID_CRIPTA, lote)
        with self.assertRaises(ValueError):
            self.fuente.obtener_catalogo(["a"] * 2)
        self.assertEqual(self.fuente.solicitudes_realizadas(), 0)

    def test_las_11_fichas_reales_con_su_DTO_y_en_orden(self):
        ids = [f["id"] for f in catalogo_real()]
        fichas = self.fuente.obtener_catalogo(ids[:10]) + self.fuente.obtener_catalogo(ids[10:])
        self.assertEqual([f.id for f in fichas], ids)
        esperado = {"enemigo": FichaEnemigoDTO, "trampa": FichaTrampaDTO}
        for ficha, datos in zip(fichas, catalogo_real()):
            self.assertIsInstance(ficha, esperado.get(datos["clase"], ObjetoDTO))
            # guardar y volver a leer da el mismo DTO (lo que necesitará la caché)
            self.assertEqual(type(ficha).desde_diccionario(ficha.a_diccionario()), ficha)
        self.assertEqual(self.fuente.solicitudes_realizadas(), 2)

    def test_fichas_del_integrante_1(self):
        rata, guardian, dardos = self.fuente.obtener_catalogo(["ent_rata_gigante", "ent_guardian_oseo", "trp_dardos"])
        self.assertEqual(rata.suelta, ["itm_pocion_menor"])
        self.assertEqual(guardian.suelta, [])         # no trae 'suelta' en el API
        self.assertEqual((dardos.danio, dardos.rearme), (4, 300))

    def test_respuesta_incompleta_o_mal_formada(self):
        with self.assertRaises(ErrorRed):
            self.fuente.obtener_contenido(ID_CRIPTA, [1, 99])       # la sala 99 no llega
        self.api.generales[ID_CRIPTA] = {"id": ID_CRIPTA}              # le faltan campos
        with self.assertRaises(ErrorRed):
            self.fuente.obtener_datos_generales(ID_CRIPTA)

    def test_clase_de_catalogo_desconocida(self):
        self.api.catalogo = [{"id": "raro", "nombre": "?", "clase": "dragon"}]
        with self.assertRaises(ErrorRed):
            self.fuente.obtener_catalogo(["raro"])


if __name__ == "__main__":
    unittest.main()