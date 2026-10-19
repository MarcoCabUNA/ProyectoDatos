"""
Pruebas de Data/ResolvedorCatalogo.py (resolución de referencias del catálogo, enunciado §4.3 y §4.4).
Usa la cripta REAL del paquete servida por ApiFalsa (cuenta cada solicitud) y escribe la caché en
disco SOLO en carpetas temporales.
"""
import os
import shutil
import tempfile
import unittest

from Data.ClienteHttp import ErrorRed
from Data.FuenteOffline import FuenteOffline
from Data.GestorContenido import GestorContenido
from Data.GestorEsqueleto import GestorEsqueleto
from Data.ResolvedorCatalogo import ResolvedorCatalogo
from DTO.FichaEnemigoDTO import FichaEnemigoDTO
from DTO.SalaDTO import ContenidoSalaDTO, EnemigoEnSalaDTO
from tests.Utilidades import (ID_CRIPTA, PAQUETE, ApiFalsa, catalogo_real, contenido_real, fuente_red,
                              general_real, leer_paquete)

IDS_REALES = 11   # fichas distintas que menciona el contenido de cripta-01 (incluye lo que suelta la rata)


def contenidos_reales() -> list[ContenidoSalaDTO]:
    return [ContenidoSalaDTO.desde_diccionario(c) for c in contenido_real()]


def ids_pedidos_al_catalogo(api: ApiFalsa) -> list[list[str]]:
    """Cada lote de ids que se pidió a /catalogo, en orden."""
    lotes = []
    for ruta, parametros in api.pedidos:
        if ruta == "catalogo":
            for clave, valor in parametros:
                if clave == "ids":
                    lotes.append(valor.split(","))
    return lotes


class PruebasResolvedorCatalogo(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.mkdtemp()
        self.carpeta = os.path.join(self.temp, "cache", "catalogo")

    def tearDown(self):
        shutil.rmtree(self.temp)

    def crear(self, api: ApiFalsa, tope: int = 25) -> ResolvedorCatalogo:
        return ResolvedorCatalogo.crear(fuente_red(api), tope, self.carpeta)

    # ------------------------------------------------------------ crear
    def test_crear_hace_una_sola_solicitud_liviana(self):
        api = ApiFalsa()
        r = self.crear(api)
        self.assertEqual(api.rutas(), ["catalogo/version"])
        self.assertEqual(r.version_catalogo(), leer_paquete("catalogo_version.json")["version"])
        self.assertTrue(os.path.isdir(os.path.join(self.carpeta, r.version_catalogo())))

    def test_version_con_formato_peligroso(self):
        with self.assertRaises(ErrorRed):
            self.crear(ApiFalsa(version_catalogo="../hack"))

    # ------------------------------------------------------------ resolver por lotes
    def test_contenido_real_en_dos_lotes_sin_repetir(self):
        api = ApiFalsa()
        r = self.crear(api)
        self.assertEqual(r.resolver_contenido(contenidos_reales()), IDS_REALES)
        lotes = ids_pedidos_al_catalogo(api)
        self.assertEqual([len(l) for l in lotes], [10, 1])           # 11 ids -> 10 + 1
        todos = lotes[0] + lotes[1]
        self.assertEqual(len(todos), len(set(todos)))                 # ningún id pedido dos veces
        # Orden de descubrimiento: sala 1, sala 2 (enemigos, trampas, objetos), sala 3, ...
        self.assertEqual(todos[:4], ["itm_antorcha", "ent_rata_gigante", "trp_dardos", "itm_daga_oxidada"])
        self.assertEqual(r.solicitudes_catalogo(), 2)

    def test_cada_ficha_descargada_cuenta_como_un_fallo(self):
        r = self.crear(ApiFalsa())
        r.resolver_contenido(contenidos_reales())
        self.assertEqual((r.aciertos(), r.fallos()), (0, IDS_REALES))   # la precarga sí cuenta sus fallos
        r.resolver_contenido(contenidos_reales())                      # ya estaba todo: nada nuevo
        self.assertEqual((r.aciertos(), r.fallos()), (0, IDS_REALES))
        r.ficha("ent_rata_gigante")
        self.assertEqual((r.aciertos(), r.fallos()), (1, IDS_REALES))

    def test_precargar_desde_disco_no_cuenta_el_fallo_dos_veces(self):
        self.crear(ApiFalsa()).resolver_contenido(contenidos_reales())
        r = self.crear(ApiFalsa())                                     # el programa se reinició
        r.resolver_contenido(contenidos_reales())                      # están en disco: no se descarga nada
        self.assertEqual(r.fallos(), 0)
        r.ficha("ent_rata_gigante")                                    # el fallo se cuenta al leerla del disco
        self.assertEqual(r.fallos(), 1)

    def test_segunda_vez_no_pide_nada(self):
        api = ApiFalsa()
        r = self.crear(api)
        r.resolver_contenido(contenidos_reales())
        antes = api.solicitudes_realizadas
        self.assertEqual(r.resolver_contenido(contenidos_reales()), 0)
        self.assertEqual(api.solicitudes_realizadas, antes)

    def test_otra_ejecucion_lee_del_disco_y_no_de_la_red(self):
        self.crear(ApiFalsa()).resolver_contenido(contenidos_reales())
        api = ApiFalsa()
        r = self.crear(api)                                            # el programa se reinició
        self.assertEqual(r.resolver_contenido(contenidos_reales()), 0)
        rata = r.ficha("ent_rata_gigante")
        self.assertIsInstance(rata, FichaEnemigoDTO)
        self.assertEqual(api.rutas(), ["catalogo/version"])           # solo la consulta liviana
        self.assertEqual((r.fallos(), r.lecturas_disco()), (1, 1))     # no estaba en memoria: 1 lectura de disco
        r.ficha("ent_rata_gigante")
        self.assertEqual((r.aciertos(), r.lecturas_disco()), (1, 1))   # ahora sí está en memoria

    def test_si_cambia_la_version_se_vuelve_a_pedir(self):
        self.crear(ApiFalsa()).resolver_contenido(contenidos_reales())
        api = ApiFalsa(version_catalogo="nueva")
        r = self.crear(api)
        self.assertEqual(r.resolver_contenido(contenidos_reales()), IDS_REALES)
        self.assertEqual(len(ids_pedidos_al_catalogo(api)), 2)

    def test_lo_que_sueltan_los_enemigos_se_resuelve_en_el_siguiente_lote(self):
        catalogo = catalogo_real() + [
            {"id": "ent_lobo", "nombre": "Lobo", "clase": "enemigo", "vida_max": 5, "ataque": 2,
             "defensa": 1, "velocidad": 100, "comportamiento": "errante", "suelta": ["itm_colmillo"]},
            {"id": "itm_colmillo", "nombre": "Colmillo", "clase": "arma", "peso": 1, "valor": 3,
             "ataque_bonus": 1}]
        api = ApiFalsa(catalogo=catalogo)
        r = self.crear(api)
        sala = ContenidoSalaDTO(9, [EnemigoEnSalaDTO("e-1", "ent_lobo")], [], [])
        self.assertEqual(r.resolver_contenido([sala]), 2)
        self.assertEqual(ids_pedidos_al_catalogo(api), [["ent_lobo"], ["itm_colmillo"]])
        # Cuando el lobo muera, su colmillo ya se puede mostrar sin ir a la red.
        antes = api.solicitudes_realizadas
        self.assertEqual(r.ficha("itm_colmillo").nombre, "Colmillo")
        self.assertEqual(api.solicitudes_realizadas, antes)

    def test_muchos_ids_salen_en_lotes_de_10_en_orden(self):
        extra = [{"id": f"itm_x{k:02d}", "nombre": "x", "clase": "arma", "peso": 1, "valor": 1}
                 for k in range(23)]
        api = ApiFalsa(catalogo=extra)
        r = self.crear(api)
        ids = [f["id"] for f in extra]
        self.assertEqual(r.resolver(ids + ids), 23)                   # repetidos a propósito
        lotes = ids_pedidos_al_catalogo(api)
        self.assertEqual([len(l) for l in lotes], [10, 10, 3])
        self.assertEqual(lotes[0] + lotes[1] + lotes[2], ids)

    def test_ids_con_formato_peligroso(self):
        r = self.crear(ApiFalsa())
        with self.assertRaises(ErrorRed):
            r.resolver(["../hack"])

    # ------------------------------------------------------------ ficha(id): nunca None
    def test_ficha_nunca_devuelve_none(self):
        api = ApiFalsa()
        r = self.crear(api)
        dardos = r.ficha("trp_dardos")                                 # no estaba en ningún lado: 1 solicitud
        self.assertEqual(dardos.id, "trp_dardos")
        self.assertEqual(ids_pedidos_al_catalogo(api), [["trp_dardos"]])
        self.assertIs(r.ficha("trp_dardos"), dardos)                  # segunda vez: memoria
        self.assertEqual((r.aciertos(), r.fallos()), (1, 1))

    def test_ficha_de_un_enemigo_trae_tambien_lo_que_suelta(self):
        api = ApiFalsa()
        r = self.crear(api)
        r.ficha("ent_rata_gigante")
        self.assertEqual(ids_pedidos_al_catalogo(api), [["ent_rata_gigante"], ["itm_pocion_menor"]])
        self.assertEqual(r.fallos(), 2)                                # la rata (una sola vez) y la poción

    def test_ficha_inexistente_lanza_error_en_vez_de_none(self):
        r = self.crear(ApiFalsa())
        with self.assertRaises(ErrorRed):
            r.ficha("itm_no_existe")

    def test_ficha_liberada_de_memoria_vuelve_desde_disco(self):
        api = ApiFalsa()
        r = self.crear(api, tope=2)
        r.resolver_contenido(contenidos_reales())                      # 11 fichas, solo caben 2 en memoria
        antes = api.solicitudes_realizadas
        for f in catalogo_real():
            self.assertEqual(r.ficha(f["id"]).id, f["id"])
        self.assertEqual(api.solicitudes_realizadas, antes)           # todo salió del disco, nada de la red
        self.assertGreater(r.lecturas_disco(), 0)

    def test_consulta_de_vista_no_infla_los_aciertos(self):
        api = ApiFalsa()
        r = self.crear(api, tope=2)
        r.resolver(["itm_antorcha", "itm_antidoto", "trp_dardos"])   # con tope 2 la antorcha ya salió
        aciertos, fallos = r.aciertos(), r.fallos()
        for _ in range(5):                                             # 5 turnos mostrando el suelo
            self.assertEqual(r.ficha("trp_dardos", contar_acierto=False).id, "trp_dardos")
        self.assertEqual((r.aciertos(), r.fallos()), (aciertos, fallos))
        antes = api.solicitudes_realizadas
        self.assertEqual(r.ficha("itm_antorcha", contar_acierto=False).id, "itm_antorcha")
        self.assertEqual((r.aciertos(), r.fallos()), (aciertos, fallos + 1))   # tuvo que ir al disco: fallo
        self.assertEqual(api.solicitudes_realizadas, antes)

    # ------------------------------------------------------------ fichas en uso
    def test_marcar_en_uso_recupera_la_ficha_si_ya_no_estaba_en_memoria(self):
        r = self.crear(ApiFalsa(), tope=1)
        r.resolver(["itm_antorcha", "itm_antidoto"])                  # con tope 1, la antorcha ya salió
        r.marcar_en_uso("itm_antorcha")                                # la trae del disco y la protege
        r.ficha("itm_antidoto")
        r.ficha("trp_dardos")
        self.assertEqual(r.ficha("itm_antorcha").id, "itm_antorcha")
        lecturas = r.lecturas_disco()
        r.ficha("itm_antorcha")
        self.assertEqual(r.lecturas_disco(), lecturas)                # sigue en memoria: estaba en uso
        r.liberar_uso("itm_antorcha")

    # ------------------------------------------------------------ después de un retroceso
    def test_sincronizar_usos_tras_un_retroceso(self):
        r = self.crear(ApiFalsa(), tope=2)
        r.resolver_contenido(contenidos_reales())                      # 11 fichas en disco, 2 en memoria
        r.marcar_en_uso("itm_antorcha")                                # antes del retroceso: antorcha en el inventario
        # Al deshacer: revive la rata (dos instancias) y la antorcha ya no está en el inventario.
        liberadas = r.sincronizar_usos(["ent_rata_gigante", "ent_rata_gigante"])
        self.assertNotIn("ent_rata_gigante", liberadas)
        lecturas = r.lecturas_disco()
        r.liberar_uso("ent_rata_gigante")                              # muere una rata: la otra sigue
        self.assertEqual(r.ficha("ent_rata_gigante").id, "ent_rata_gigante")
        self.assertEqual(r.lecturas_disco(), lecturas)                 # sigue en memoria (en uso)
        r.liberar_uso("ent_rata_gigante")
        with self.assertRaises(ValueError):
            r.liberar_uso("itm_antorcha")                              # la antorcha ya no estaba en uso

    def test_sincronizar_usos_no_desaloja_en_medio_lo_que_va_a_marcar(self):
        api = ApiFalsa()
        r = self.crear(api, tope=1)
        r.resolver_contenido(contenidos_reales())
        ids = ["itm_antorcha", "trp_dardos", "itm_daga_oxidada"]       # 3 en uso con tope 1
        antes = api.solicitudes_realizadas
        self.assertEqual(r.sincronizar_usos(ids), [])                  # nada en uso se libera
        lecturas = r.lecturas_disco()
        for id_ficha in ids:
            self.assertEqual(r.ficha(id_ficha).id, id_ficha)
        self.assertEqual(r.lecturas_disco(), lecturas)                 # las 3 quedaron en memoria
        self.assertEqual(api.solicitudes_realizadas, antes)            # y nada salió de la red

    # ------------------------------------------------------------ errores de red
    def test_fallo_a_mitad_conserva_lo_descargado(self):
        # Solicitudes: 0 versión, 1 primer lote de catálogo, 2 segundo lote -> falla
        api = ApiFalsa(falla_en=2)
        r = self.crear(api)
        with self.assertRaises(ErrorRed):
            r.resolver_contenido(contenidos_reales())
        api2 = ApiFalsa()
        r2 = self.crear(api2)
        self.assertEqual(r2.resolver_contenido(contenidos_reales()), 1)   # solo falta la del lote que falló
        self.assertEqual(ids_pedidos_al_catalogo(api2), [["itm_antidoto"]])

    # ------------------------------------------------------------ modo --offline
    def test_offline_no_cuenta_solicitudes(self):
        fuente = FuenteOffline(PAQUETE)
        r = ResolvedorCatalogo.crear(fuente, 25, self.carpeta)
        self.assertEqual(r.resolver_contenido(contenidos_reales()), IDS_REALES)
        self.assertEqual(fuente.solicitudes_realizadas(), 0)


class PruebasIntegracionConGestorContenido(unittest.TestCase):
    """El flujo completo de la cripta real: esqueleto, precarga del contenido y su catálogo."""

    def setUp(self):
        self.temp = tempfile.mkdtemp()
        self.carpeta = os.path.join(self.temp, "cache", "catalogo")

    def tearDown(self):
        shutil.rmtree(self.temp)

    def test_cripta_real_completa_dentro_del_presupuesto(self):
        api = ApiFalsa()
        fuente = fuente_red(api)
        esqueleto = GestorEsqueleto(fuente)
        esqueleto.cargar(fuente.obtener_datos_generales(ID_CRIPTA))   # datos generales + 1 página
        resolvedor = ResolvedorCatalogo.crear(fuente, 25, self.carpeta)
        gestor = GestorContenido(fuente, esqueleto, radio=2, resolvedor=resolvedor)
        cripta = esqueleto.cripta()
        assert cripta is not None
        gestor.precargar_alrededor(cripta.sala_inicial)                # contenido + su catálogo
        # Toda entidad de toda sala ya se puede resolver sin ir a la red (fn_ficha de Mazmorra).
        antes = api.solicitudes_realizadas
        for id_sala in esqueleto.ids_salas():
            sala = gestor.obtener_contenido(id_sala)
            assert sala is not None
            for enemigo in sala.enemigos:
                self.assertIsNotNone(resolvedor.ficha(enemigo.tipo))
            for trampa in sala.trampas:
                self.assertIsNotNone(resolvedor.ficha(trampa.tipo))
            for id_objeto in sala.objetos:
                self.assertIsNotNone(resolvedor.ficha(id_objeto))
        self.assertEqual(api.solicitudes_realizadas, antes)
        # general, salas, versión del catálogo, 1 lote de contenido, 2 lotes de catálogo
        self.assertEqual(api.solicitudes_realizadas, 6)
        self.assertLessEqual(api.solicitudes_realizadas, general_real()["presupuesto_solicitudes"])

    def test_si_falla_el_catalogo_el_contenido_igual_queda(self):
        api = ApiFalsa(falla_en=5)                                     # 0 general, 1 salas, 2 versión, 3 contenido, 4 catálogo, 5 catálogo
        fuente = fuente_red(api)
        esqueleto = GestorEsqueleto(fuente)
        esqueleto.cargar(fuente.obtener_datos_generales(ID_CRIPTA))
        resolvedor = ResolvedorCatalogo.crear(fuente, 25, self.carpeta)
        gestor = GestorContenido(fuente, esqueleto, radio=2, resolvedor=resolvedor)
        self.assertEqual(gestor.precargar_alrededor(1), 0)             # el error no detiene el juego
        self.assertTrue(gestor.contenido_disponible(4))
        sala4 = gestor.obtener_contenido(4)
        assert sala4 is not None
        self.assertEqual([e.tipo for e in sala4.enemigos], ["ent_guardian_oseo"])

    def test_si_falla_el_catalogo_las_salas_que_seguian_se_podran_pedir_despues(self):
        """12 salas = 2 lotes de contenido. El catálogo del 1er lote falla: el 2do lote no queda trabado."""
        general = dict(general_real())
        general.update(id="cripta-12", salas_total=12, paginas=1, sala_inicial=1, sala_salida=12)
        salas = [{"id": i, "nombre": f"S{i}", "salidas": {}} for i in range(1, 13)]
        contenido = [{"sala": i, "enemigos": [], "objetos": [f"itm_x{i}"], "trampas": []} for i in range(1, 13)]
        catalogo = [{"id": f"itm_x{i}", "nombre": "x", "clase": "arma", "peso": 1, "valor": 1} for i in range(1, 13)]
        # Solicitudes: 0 general, 1 salas, 2 versión, 3 contenido (lote 1), 4 catálogo -> falla
        api = ApiFalsa(generales={"cripta-12": general},
                       paginas={"cripta-12": [{"pagina": 1, "total_paginas": 1, "salas": salas}]},
                       contenidos={"cripta-12": contenido}, catalogo=catalogo, falla_en=4)
        fuente = fuente_red(api)
        esqueleto = GestorEsqueleto(fuente)
        esqueleto.cargar(fuente.obtener_datos_generales("cripta-12"))
        gestor = GestorContenido(fuente, esqueleto, resolvedor=ResolvedorCatalogo.crear(fuente, 25, self.carpeta))
        for id_sala in range(1, 13):
            gestor.solicitar_si_falta(id_sala)
        with self.assertRaises(ErrorRed):
            gestor.resolver_pendientes()
        self.assertTrue(gestor.contenido_disponible(10))               # el 1er lote sí llegó
        self.assertFalse(gestor.contenido_disponible(11))
        self.assertTrue(gestor.solicitar_si_falta(11))                 # volvió a NO_PEDIDA: se puede pedir
        gestor.resolver_pendientes()
        self.assertTrue(gestor.contenido_disponible(11))

    def test_sin_resolvedor_funciona_igual_que_antes(self):
        api = ApiFalsa()
        fuente = fuente_red(api)
        esqueleto = GestorEsqueleto(fuente)
        esqueleto.cargar(fuente.obtener_datos_generales(ID_CRIPTA))
        GestorContenido(fuente, esqueleto).precargar_alrededor(1)
        self.assertNotIn("catalogo", api.rutas())


if __name__ == "__main__":
    unittest.main()