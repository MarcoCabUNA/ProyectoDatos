"""
Pruebas de FuenteOffline con el paquete/ REAL del repositorio:
debe entregar exactamente los mismos DTOs que FuenteRed, sin contar solicitudes.
"""
import os
import shutil
import tempfile
import unittest

from Data.ClienteHttp import ErrorRed
from Data.FuenteDatos import FuenteDatos
from Data.FuenteOffline import FuenteOffline
from tests.Utilidades import ID_CRIPTA, PAQUETE, ApiFalsa, fuente_red


class PruebasFuenteOffline(unittest.TestCase):

    def setUp(self):
        self.offline = FuenteOffline(PAQUETE)
        self.red = fuente_red(ApiFalsa())   # misma información, pero "por la red"

    def test_es_una_FuenteDatos(self):
        self.assertIsInstance(self.offline, FuenteDatos)

    def test_mismos_DTOs_que_FuenteRed_en_los_7_metodos(self):
        o, r = self.offline, self.red
        self.assertEqual(o.listar_criptas(), r.listar_criptas())
        cripta = o.obtener_datos_generales(ID_CRIPTA)
        self.assertEqual(cripta, r.obtener_datos_generales(ID_CRIPTA))
        self.assertEqual(o.obtener_version_cripta(ID_CRIPTA), r.obtener_version_cripta(ID_CRIPTA))
        self.assertEqual(o.obtener_pagina_salas(ID_CRIPTA, 1, cripta.version),
                         r.obtener_pagina_salas(ID_CRIPTA, 1, cripta.version))
        self.assertEqual(o.obtener_contenido(ID_CRIPTA, [1, 2, 3, 4, 5, 6]),
                         r.obtener_contenido(ID_CRIPTA, [1, 2, 3, 4, 5, 6]))
        self.assertEqual(o.obtener_version_catalogo(), r.obtener_version_catalogo())
        ids = ["trp_dardos", "itm_antidoto", "ent_guardian_oseo"]
        self.assertEqual(o.obtener_catalogo(ids), r.obtener_catalogo(ids))

    def test_responde_lotes_distintos_a_los_de_la_descarga(self):
        self.assertEqual([c.sala for c in self.offline.obtener_contenido(ID_CRIPTA, [5, 2])], [5, 2])
        self.assertEqual([f.id for f in self.offline.obtener_catalogo(["itm_antidoto", "itm_antorcha"])],
                         ["itm_antidoto", "itm_antorcha"])

    def test_no_cuenta_solicitudes_ni_fija_presupuesto(self):
        self.offline.obtener_datos_generales(ID_CRIPTA)
        self.offline.obtener_catalogo(["itm_antorcha"])
        self.assertEqual(self.offline.solicitudes_realizadas(), 0)
        self.assertIsNone(self.offline.presupuesto_solicitudes())

    def test_errores_claros(self):
        casos = [
            lambda: FuenteOffline(os.path.join(PAQUETE, "no_existe")),
            lambda: self.offline.obtener_datos_generales("cripta-99"),
            lambda: self.offline.obtener_contenido(ID_CRIPTA, [2, 99]),
            lambda: self.offline.obtener_catalogo(["itm_inventado"]),
            lambda: self.offline.obtener_pagina_salas(ID_CRIPTA, 2, "v"),
            lambda: self.offline.obtener_datos_generales("../paquete"),
        ]
        for caso in casos:
            with self.assertRaises(ErrorRed):
                caso()

    def test_json_danado(self):
        carpeta = tempfile.mkdtemp()
        try:
            copia = os.path.join(carpeta, "paquete")
            shutil.copytree(PAQUETE, copia)
            with open(os.path.join(copia, "catalogo.json"), "w", encoding="utf-8") as f:
                f.write("{roto")
            with self.assertRaises(ErrorRed):
                FuenteOffline(copia).obtener_catalogo(["itm_antorcha"])
        finally:
            shutil.rmtree(carpeta)


if __name__ == "__main__":
    unittest.main()