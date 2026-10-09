"""
Pruebas de Data/GestorEsqueleto.py: el grafo de salas en un array indexado por id.
"""
import copy
import unittest
from dataclasses import replace

from Data.ClienteHttp import ErrorRed
from Data.FuenteOffline import FuenteOffline
from Data.GestorEsqueleto import GestorEsqueleto
from DTO.CriptaDTO import CriptaDTO
from DTO.SalaDTO import ContenidoSalaDTO
from tests.Utilidades import (ID_CRIPTA, PAQUETE, ApiFalsa, contenido_real, fuente_red, general_real,
                              pagina_real, sala_de)


def gestor_con(paginas, cambios_general=None):
    general = dict(general_real())
    general.update(cambios_general or {})
    api = ApiFalsa(generales={ID_CRIPTA: general}, paginas={ID_CRIPTA: paginas})
    return GestorEsqueleto(fuente_red(api)), CriptaDTO.desde_diccionario(general), api


class PruebasGestorEsqueleto(unittest.TestCase):

    def setUp(self):
        fuente = FuenteOffline(PAQUETE)
        self.cripta = fuente.obtener_datos_generales(ID_CRIPTA)
        self.g = GestorEsqueleto(fuente)
        self.g.cargar(self.cripta)

    def test_cripta_real(self):
        self.assertTrue(self.g.esta_cargado())
        self.assertEqual(self.g.ids_salas(), [1, 2, 3, 4, 5, 6])
        self.assertEqual(self.g.cantidad_salas(), 6)
        self.assertEqual(sala_de(self.g, 4).nombre, "Osario profundo")

    def test_vecinos_en_orden_N_S_E_O(self):
        esperado = {1: [2], 2: [3, 1, 5], 3: [4, 2], 4: [3, 6], 5: [2], 6: [4]}
        for sala, vecinos in esperado.items():
            self.assertEqual(self.g.vecinos(sala), vecinos)

    def test_salas_inexistentes(self):
        for i in (0, -1, 99):
            self.assertIsNone(self.g.obtener_sala(i))
            self.assertFalse(self.g.existe_sala(i))
        with self.assertRaises(ValueError):
            self.g.vecinos(99)

    def test_actualizar_con_contenido_y_rechazo_de_cambios_de_esqueleto(self):
        sala2 = sala_de(self.g, 2).con_contenido(ContenidoSalaDTO.desde_diccionario(contenido_real()[1]))
        self.g.actualizar_sala(sala2)
        self.assertTrue(sala_de(self.g, 2).contenido_cargado)
        with self.assertRaises(ValueError):
            self.g.actualizar_sala(replace(sala2, nombre="otro"))

    def test_varias_paginas(self):
        p = pagina_real()["salas"]
        g, cripta, api = gestor_con([{"pagina": 1, "total_paginas": 2, "salas": p[:3]},
                                     {"pagina": 2, "total_paginas": 2, "salas": p[3:]}], {"paginas": 2})
        g.cargar(cripta)
        self.assertEqual(g.ids_salas(), [1, 2, 3, 4, 5, 6])
        self.assertEqual(api.rutas().count(f"criptas/{ID_CRIPTA}/salas"), 2)

    def test_datos_incoherentes_lanzan_ErrorRed_y_no_cargan(self):
        repetida = copy.deepcopy(pagina_real())
        repetida["salas"].append(copy.deepcopy(repetida["salas"][0]))
        falta = copy.deepcopy(pagina_real())
        falta["salas"] = falta["salas"][:5]
        destino = copy.deepcopy(pagina_real())
        destino["salas"][0]["salidas"]["N"]["sala"] = 42
        a_si_misma = copy.deepcopy(pagina_real())
        a_si_misma["salas"][0]["salidas"]["N"]["sala"] = 1
        casos = [
            ([repetida], {"salas_total": 7}),
            ([falta], None),
            ([destino], None),
            ([a_si_misma], None),
            ([pagina_real()], {"sala_salida": 9}),
            ([{"pagina": 1, "total_paginas": 1, "salas": []}], {"salas_total": 0}),
        ]
        for paginas, cambios in casos:
            g, cripta, _ = gestor_con(paginas, cambios)
            with self.assertRaises(ErrorRed):
                g.cargar(cripta)
            self.assertFalse(g.esta_cargado())


if __name__ == "__main__":
    unittest.main()