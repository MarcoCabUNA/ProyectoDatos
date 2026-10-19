"""
Pruebas de Data/DescargadorPaquete.py. Escribe SOLO en carpetas temporales:
nunca toca el paquete/ del repositorio.
"""
import json
import os
import shutil
import tempfile
import unittest

from Data.ClienteHttp import ErrorRed
from Data.FuenteOffline import FuenteOffline
from tests.Utilidades import (ID_CRIPTA, ApiFalsa, catalogo_real, contenido_real, descargador, general_real,
                              leer_paquete, pagina_real)


class PruebasDescargadorPaquete(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.mkdtemp()
        self.carpeta = os.path.join(self.temp, "paquete")

    def tearDown(self):
        shutil.rmtree(self.temp)

    def leer(self, *partes):
        with open(os.path.join(self.carpeta, *partes), encoding="utf-8") as f:
            return json.load(f)

    def test_cripta_real_queda_identica_al_API_con_7_solicitudes(self):
        d = descargador(self.carpeta, ApiFalsa())
        d.descargar(ID_CRIPTA)
        self.assertEqual(d.solicitudes_realizadas(), 7)
        self.assertEqual(self.leer("criptas.json"), leer_paquete("criptas.json"))
        self.assertEqual(self.leer(ID_CRIPTA, "general.json"), general_real())
        self.assertEqual(self.leer(ID_CRIPTA, "salas_p1.json"), pagina_real())
        self.assertEqual(self.leer(ID_CRIPTA, "contenido.json")["contenido"], contenido_real())
        ids = sorted(f["id"] for f in self.leer("catalogo.json")["entidades"])   # sorted solo para comparar en la prueba
        self.assertEqual(ids, sorted(f["id"] for f in catalogo_real()))
        # y FuenteOffline puede leer lo que se descargó
        self.assertEqual(len(FuenteOffline(self.carpeta).obtener_pagina_salas(ID_CRIPTA, 1, "v")), 6)

    def _cripta_grande(self):
        """23 salas en 2 páginas, 14 objetos y un enemigo que suelta un objeto nuevo."""
        salas = [{"id": i, "nombre": f"S{i}", "salidas": {}} for i in range(1, 24)]
        general = dict(general_real())
        general.update(id="cripta-02", salas_total=23, paginas=2, sala_salida=23)
        contenido = [{"sala": i, "enemigos": [], "objetos": [f"itm_{i % 14}"], "trampas": []} for i in range(1, 24)]
        contenido[0]["enemigos"] = [{"instancia": "e-1", "tipo": "ent_x"}]
        catalogo = [{"id": f"itm_{k}", "nombre": "x", "clase": "arma", "peso": 1, "valor": 1, "ataque_bonus": 1}
                    for k in range(14)]
        catalogo += [{"id": "ent_x", "nombre": "X", "clase": "enemigo", "vida_max": 1, "ataque": 1, "defensa": 1,
                      "velocidad": 1, "comportamiento": "errante", "suelta": ["itm_raro"]},
                     {"id": "itm_raro", "nombre": "R", "clase": "pocion", "peso": 1, "valor": 1}]
        catalogo += catalogo_real()
        criptas = {"criptas": leer_paquete("criptas.json")["criptas"] +
                   [{"id": "cripta-02", "nombre": "Grande", "salas": 23, "dificultad": 2}]}
        return ApiFalsa(criptas=criptas, generales={"cripta-02": general},
                        paginas={"cripta-02": [{"pagina": 1, "total_paginas": 2, "salas": salas[:12]},
                                               {"pagina": 2, "total_paginas": 2, "salas": salas[12:]}]},
                        contenidos={"cripta-02": contenido}, catalogo=catalogo)

    def test_cripta_grande_paginas_lotes_y_lo_que_sueltan_los_enemigos(self):
        descargador(self.carpeta, ApiFalsa()).descargar(ID_CRIPTA)   # catálogo previo de cripta-01
        api = self._cripta_grande()
        descargador(self.carpeta, api).descargar("cripta-02")
        self.assertEqual(api.rutas().count("criptas/cripta-02/salas"), 2)
        self.assertEqual(api.rutas().count("criptas/cripta-02/contenido"), 3)    # 10 + 10 + 3
        self.assertEqual([c["sala"] for c in self.leer("cripta-02", "contenido.json")["contenido"]],
                         list(range(1, 24)))
        ids = [f["id"] for f in self.leer("catalogo.json")["entidades"]]
        self.assertEqual(len(ids), len(set(ids)))           # sin repetidos
        self.assertIn("itm_raro", ids)                      # lo que suelta ent_x
        self.assertEqual(len(ids), 11 + 16)                 # se conservaron las 11 de cripta-01
        for _, parametros in api.pedidos:                   # la llave negra ya estaba: no se pidió
            for clave, valor in parametros:
                if clave == "ids":
                    self.assertNotIn("itm_llave_negra", valor.split(","))

    def test_version_de_catalogo_distinta_empieza_de_cero(self):
        descargador(self.carpeta, self._cripta_grande()).descargar("cripta-02")
        descargador(self.carpeta, ApiFalsa(version_catalogo="OTRA")).descargar(ID_CRIPTA)
        self.assertEqual(len(self.leer("catalogo.json")["entidades"]), 11)

    def test_fallo_a_mitad_deja_el_paquete_anterior_intacto(self):
        descargador(self.carpeta, ApiFalsa()).descargar(ID_CRIPTA)
        catalogo_antes = self.leer("catalogo.json")
        contenido_antes = self.leer(ID_CRIPTA, "contenido.json")
        # Solicitudes: 0 criptas, 1 general, 2 salas, 3 contenido -> falla en el contenido
        with self.assertRaises(ErrorRed):
            descargador(self.carpeta, ApiFalsa(falla_en=3)).descargar(ID_CRIPTA)
        self.assertEqual(self.leer("catalogo.json"), catalogo_antes)
        self.assertEqual(self.leer(ID_CRIPTA, "contenido.json"), contenido_antes)

    def test_segunda_descarga_reutiliza_el_catalogo(self):
        descargador(self.carpeta, ApiFalsa()).descargar(ID_CRIPTA)
        api = ApiFalsa()
        descargador(self.carpeta, api).descargar(ID_CRIPTA)
        self.assertNotIn("catalogo", api.rutas())          # las 11 fichas ya estaban y la versión coincide
        self.assertEqual(api.solicitudes_realizadas, 5)

    def test_ids_invalidos(self):
        with self.assertRaises(ErrorRed):
            descargador(self.carpeta, ApiFalsa()).descargar("no-existe")
        for malo in ("../hack", "", "a b"):
            with self.assertRaises(ValueError):
                descargador(self.carpeta, ApiFalsa()).descargar(malo)


if __name__ == "__main__":
    unittest.main()