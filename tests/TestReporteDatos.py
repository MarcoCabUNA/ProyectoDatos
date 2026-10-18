"""
Pruebas de Data/ReporteDatos.py y DTO/ReporteDatosDTO.py (reporte final de la partida, enunciado §6.1).
Juega la cripta REAL del paquete (ApiFalsa cuenta cada solicitud) y escribe la caché en disco
SOLO en carpetas temporales.
"""
import dataclasses
import os
import shutil
import tempfile
import unittest

from Data.FuenteDatos import FuenteDatos
from Data.FuenteOffline import FuenteOffline
from Data.GestorContenido import GestorContenido
from Data.GestorEsqueleto import GestorEsqueleto
from Data.ReporteDatos import generar_reporte
from Data.ResolvedorCatalogo import ResolvedorCatalogo
from DTO.ReporteDatosDTO import ReporteDatosDTO
from tests.Utilidades import ID_CRIPTA, PAQUETE, ApiFalsa, fuente_red, general_real


def jugar(fuente: FuenteDatos, carpeta: str):
    """Lo que hará Servicios: carga la cripta, precarga desde la sala inicial y resuelve cada entidad."""
    cripta = fuente.obtener_datos_generales(ID_CRIPTA)
    esqueleto = GestorEsqueleto(fuente)
    esqueleto.cargar(cripta)
    resolvedor = ResolvedorCatalogo.crear(fuente, 25, carpeta)
    gestor = GestorContenido(fuente, esqueleto, resolvedor=resolvedor)
    gestor.precargar_alrededor(cripta.sala_inicial)
    for id_sala in esqueleto.ids_salas():
        sala = gestor.obtener_contenido(id_sala)
        assert sala is not None
        for enemigo in sala.enemigos:
            resolvedor.ficha(enemigo.tipo)
        for trampa in sala.trampas:
            resolvedor.ficha(trampa.tipo)
        for id_objeto in sala.objetos:
            resolvedor.ficha(id_objeto)
    return cripta, resolvedor, gestor


class PruebasReporteDatos(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.mkdtemp()
        self.carpeta = os.path.join(self.temp, "cache", "catalogo")

    def tearDown(self):
        shutil.rmtree(self.temp)

    def test_partida_real_con_red(self):
        api = ApiFalsa()
        fuente = fuente_red(api)
        cripta, resolvedor, gestor = jugar(fuente, self.carpeta)
        r = generar_reporte(fuente, resolvedor, gestor, cripta)
        # general, salas, versión del catálogo, 1 lote de contenido, 2 lotes de catálogo
        self.assertEqual((r.solicitudes_realizadas, r.presupuesto), (6, general_real()["presupuesto_solicitudes"]))
        self.assertEqual(r.solicitudes_realizadas, api.solicitudes_realizadas)
        # 11 fichas descargadas al precargar = 11 fallos; luego las 12 entidades ya estaban en memoria
        self.assertEqual((r.aciertos_cache, r.fallos_cache), (12, 11))
        self.assertEqual((r.fichas_descargadas, r.solicitudes_catalogo, r.lecturas_disco), (11, 2, 0))
        self.assertEqual((r.lotes_contenido, r.salas_pedidas, r.offline), (1, 6, False))

    def test_segunda_partida_usa_el_disco(self):
        jugar(fuente_red(ApiFalsa()), self.carpeta)
        api = ApiFalsa()
        fuente = fuente_red(api)
        cripta, resolvedor, gestor = jugar(fuente, self.carpeta)       # programa reiniciado
        r = generar_reporte(fuente, resolvedor, gestor, cripta)
        self.assertEqual(r.solicitudes_realizadas, 4)                    # sin lotes de catálogo
        self.assertEqual((r.fichas_descargadas, r.solicitudes_catalogo), (0, 0))
        self.assertEqual(r.lecturas_disco, 11)                           # cada ficha distinta: 1 lectura
        self.assertEqual((r.fallos_cache, r.aciertos_cache), (11, 1))    # la 2da rata ya estaba en memoria

    def test_offline_no_cuenta_solicitudes_y_toma_el_presupuesto_de_la_cripta(self):
        fuente = FuenteOffline(PAQUETE)
        cripta, resolvedor, gestor = jugar(fuente, self.carpeta)
        r = generar_reporte(fuente, resolvedor, gestor, cripta)
        self.assertEqual((r.solicitudes_realizadas, r.offline), (0, True))
        self.assertEqual(r.presupuesto, cripta.presupuesto_solicitudes)
        self.assertEqual(r.fichas_descargadas, 11)                       # leídas del paquete, no de la red
        self.assertIsNone(generar_reporte(fuente, resolvedor).presupuesto)   # sin cripta no se conoce

    def test_sin_gestor_la_precarga_queda_en_cero(self):
        fuente = fuente_red(ApiFalsa())
        r = generar_reporte(fuente, ResolvedorCatalogo.crear(fuente, 25, self.carpeta))
        self.assertEqual((r.lotes_contenido, r.salas_pedidas, r.solicitudes_realizadas), (0, 0, 1))

    def test_generar_no_modifica_nada(self):
        api = ApiFalsa()
        fuente = fuente_red(api)
        cripta, resolvedor, gestor = jugar(fuente, self.carpeta)
        primero = generar_reporte(fuente, resolvedor, gestor, cripta)
        self.assertEqual(generar_reporte(fuente, resolvedor, gestor, cripta), primero)

    # ------------------------------------------------------------ el DTO
    def test_dto_ida_y_vuelta_e_inmutable(self):
        r = ReporteDatosDTO(7, 9, 12, 3, lecturas_disco=2, fichas_descargadas=11, solicitudes_catalogo=2,
                            lotes_contenido=1, salas_pedidas=6, offline=False)
        self.assertEqual(ReporteDatosDTO.desde_diccionario(r.a_diccionario()), r)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            setattr(r, "aciertos_cache", 99)

    def test_dto_minimo(self):
        r = ReporteDatosDTO.desde_diccionario({"solicitudes_realizadas": 0, "aciertos_cache": 0, "fallos_cache": 0})
        self.assertEqual((r.presupuesto, r.lecturas_disco, r.offline), (None, 0, False))


if __name__ == "__main__":
    unittest.main()