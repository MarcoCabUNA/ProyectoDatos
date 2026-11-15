"""
Pruebas de Data y DTO de la feature 003 (contrato de llaves, integrante 2; contracts/contrato-llaves.md):
UbicacionLlaveDTO, las fuentes (FuenteDatos, FuenteJson, FuenteRed, LectorPaquete), DescargadorPaquete,
AlmacenLlaves, validar_ubicaciones y GestorLlaves. Escriben solo en carpetas temporales.
"""
import dataclasses
import json
import os
import shutil
import sys
import tempfile
import unittest
from typing import cast

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from Data.AlmacenCatalogo import AlmacenCatalogo  # noqa: E402
from Data.ClienteHttp import ClienteHttp, ErrorRed, PresupuestoAgotadoError  # noqa: E402
from Data.FuenteJson import FuenteJson  # noqa: E402
from Data.FuenteOffline import FuenteOffline  # noqa: E402
from Data.FuenteRed import FuenteRed  # noqa: E402
from Data.GestorEsqueleto import GestorEsqueleto  # noqa: E402
from Data.ValidacionDatos import ErrorDatos  # noqa: E402
from DTO.UbicacionLlaveDTO import UbicacionLlaveDTO  # noqa: E402
from tests.ayudas_resolubilidad import (FuenteConLlaves, abierta, cripta, paquete_temporal, puerta,  # noqa: E402
                                        ubic)
from tests.TestClienteHttp import RespuestaFalsa, SesionFalsa  # noqa: E402
from tests.Utilidades import ID_CRIPTA, ApiFalsa, FuenteCuadricula, descargador  # noqa: E402

OP_LLAVES = f"ubicación de llaves de {ID_CRIPTA}"


def cripta_chica():
    """Salas 1 a 4: salida 1–2, puerta 2–3 (A), puerta 3–4 (S); A en la sala 2 y S en la sala 3."""
    return cripta(4, [abierta(1, 2, 2), puerta(2, 2, 3, "A"), puerta(3, 2, 4, "S")],
                  [ubic("A", 2), ubic("S", 3, "e-301")], sala_salida=4)


class CarpetaTemporal(unittest.TestCase):
    """Base: una carpeta temporal por prueba, que se borra al terminar."""

    def setUp(self):
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp, ignore_errors=True)

    def leer_json(self, *partes):
        with open(os.path.join(self.temp, *partes), encoding="utf-8") as f:
            return json.load(f)


class PruebasUbicacionLlaveDTO(unittest.TestCase):
    """T004: el DTO de una ubicación de llave (FR-316, FR-303)."""

    def test_fr316_ubicacion_desde_diccionario_con_y_sin_enemigo(self):
        a = UbicacionLlaveDTO.desde_diccionario({"id": "A", "sala": 4})
        self.assertEqual((a.id, a.sala, a.enemigo), ("A", 4, None))
        b = UbicacionLlaveDTO.desde_diccionario({"id": "B", "sala": 12, "enemigo": "e-1203"})
        self.assertEqual((b.id, b.sala, b.enemigo), ("B", 12, "e-1203"))
        c = UbicacionLlaveDTO.desde_diccionario({"id": "C", "sala": 7, "enemigo": None})
        self.assertIsNone(c.enemigo)
        self.assertEqual(UbicacionLlaveDTO("A", 4), a)          # enemigo vale None por defecto

    def test_fr316_a_diccionario_omite_enemigo_none(self):
        self.assertEqual(UbicacionLlaveDTO("A", 4).a_diccionario(), {"id": "A", "sala": 4})
        self.assertEqual(UbicacionLlaveDTO("B", 12, "e-1203").a_diccionario(),
                         {"id": "B", "sala": 12, "enemigo": "e-1203"})
        for d in ({"id": "A", "sala": 4}, {"id": "B", "sala": 12, "enemigo": "e-1203"}):
            self.assertEqual(UbicacionLlaveDTO.desde_diccionario(d).a_diccionario(), d)   # mismo formato del API

    def test_fr316_ubicacion_es_inmutable(self):
        u = UbicacionLlaveDTO("A", 4)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            u.sala = 5  # type: ignore[misc]


class PruebasFuentesYPaquete(CarpetaTemporal):
    """T009: obtener_llaves en las fuentes, el lector del paquete y el descargador (FR-316 a FR-318, FR-320)."""

    def test_fr317_fuente_por_defecto_lanza_error_red(self):
        from Service.BenchDatos import _FuenteCuadricula
        for fuente in (FuenteCuadricula(2), _FuenteCuadricula(2)):     # las fuentes falsas siguen instanciándose
            with self.assertRaises(ErrorRed) as ctx:
                fuente.obtener_llaves("x")
            self.assertEqual(ctx.exception.operacion, "ubicación de llaves de x")
            self.assertEqual(ctx.exception.detalle, "esta fuente no entrega la ubicación de las llaves")
            self.assertNotIsInstance(ctx.exception, ErrorDatos)

    def test_fr316_fuente_json_traduce_en_el_orden_de_la_respuesta(self):
        respuesta = {"llaves": [{"id": "B", "sala": 12, "enemigo": "e-1203"}, {"id": "A", "sala": 4},
                                {"id": "B", "sala": 12, "enemigo": "e-1203"}, {"id": "A", "sala": 2, "enemigo": None}]}
        api = ApiFalsa(llaves={ID_CRIPTA: respuesta})
        ubicaciones = FuenteRed(cast(ClienteHttp, api)).obtener_llaves(ID_CRIPTA)
        self.assertEqual(ubicaciones, [UbicacionLlaveDTO("B", 12, "e-1203"), UbicacionLlaveDTO("A", 4),
                                       UbicacionLlaveDTO("B", 12, "e-1203"), UbicacionLlaveDTO("A", 2)])
        self.assertEqual(api.rutas(), [f"criptas/{ID_CRIPTA}/llaves"])

    def test_fr316_formato_invalido_es_error_red(self):
        invalidos = [
            ("raíz sin llaves", {}),
            ("raíz que no es objeto", [{"id": "A", "sala": 1}]),
            ("llaves no es lista", {"llaves": {"id": "A", "sala": 1}}),
            ("elemento que no es objeto", {"llaves": ["A"]}),
            ("id ausente", {"llaves": [{"sala": 1}]}),
            ("id no texto", {"llaves": [{"id": 5, "sala": 1}]}),
            ("id vacío", {"llaves": [{"id": "", "sala": 1}]}),
            ("sala ausente", {"llaves": [{"id": "A"}]}),
            ("sala texto", {"llaves": [{"id": "A", "sala": "4"}]}),
            ("sala bool", {"llaves": [{"id": "A", "sala": True}]}),
            ("sala no entera", {"llaves": [{"id": "A", "sala": 4.0}]}),
            ("enemigo no texto", {"llaves": [{"id": "A", "sala": 4, "enemigo": 7}]}),
            ("enemigo vacío", {"llaves": [{"id": "A", "sala": 4, "enemigo": ""}]}),
            ("válida y luego inválida", {"llaves": [{"id": "A", "sala": 4}, {"id": "B"}]}),
        ]
        for nombre, respuesta in invalidos:
            with self.subTest(nombre):
                fuente = FuenteRed(cast(ClienteHttp, ApiFalsa(llaves={ID_CRIPTA: respuesta})))
                with self.assertRaises(ErrorRed) as ctx:
                    fuente.obtener_llaves(ID_CRIPTA)
                self.assertNotIsInstance(ctx.exception, ErrorDatos)
                self.assertEqual(ctx.exception.operacion, OP_LLAVES)
                self.assertIn("formato", ctx.exception.detalle)

    def test_fr321_lista_vacia_es_valida(self):
        fuente = FuenteRed(cast(ClienteHttp, ApiFalsa(llaves={ID_CRIPTA: {"llaves": []}})))
        self.assertEqual(fuente.obtener_llaves(ID_CRIPTA), [])

    def test_fr317_obtener_llaves_es_una_solicitud_que_cuenta(self):
        dto, _, _ = cripta_chica()
        general = dataclasses.replace(dto, presupuesto_solicitudes=2).a_diccionario()
        sesion = SesionFalsa(RespuestaFalsa(200, general), RespuestaFalsa(200, {"llaves": [{"id": "A", "sala": 2}]}))
        cliente = ClienteHttp("https://ejemplo.test/v1", "id-fijo", sesion=sesion, esperar=lambda s: None)
        fuente = FuenteRed(cliente)
        fuente.obtener_datos_generales("prueba")                # fija el presupuesto de la cripta: 2
        self.assertEqual(fuente.obtener_llaves("prueba"), [UbicacionLlaveDTO("A", 2)])
        self.assertEqual(len(sesion.llamadas), 2)
        self.assertEqual(sesion.llamadas[1][0], "https://ejemplo.test/v1/criptas/prueba/llaves")
        self.assertEqual(sesion.llamadas[1][1], "id-fijo")      # lleva X-Cripta-Client-Id como las demás
        self.assertEqual((fuente.solicitudes_realizadas(), fuente.presupuesto_solicitudes()), (2, 2))
        with self.assertRaises(PresupuestoAgotadoError):        # una tercera ya no entra en el presupuesto
            fuente.obtener_llaves("prueba")

    def test_fr318_lector_paquete_lee_llaves_json(self):
        dto, salas, ubicaciones = cripta_chica()
        fuente = FuenteOffline(paquete_temporal(self.temp, dto, salas, ubicaciones))
        self.assertEqual(fuente.obtener_llaves("prueba"), ubicaciones)
        self.assertEqual(fuente.solicitudes_realizadas(), 0)

    def test_fr320_paquete_sin_llaves_json_es_error_red(self):
        dto, salas, _ = cripta_chica()
        fuente = FuenteOffline(paquete_temporal(self.temp, dto, salas, None))
        with self.assertRaises(ErrorRed) as ctx:
            fuente.obtener_llaves("prueba")
        self.assertNotIsInstance(ctx.exception, ErrorDatos)
        self.assertEqual(ctx.exception.operacion, "ubicación de llaves de prueba")
        self.assertIn("falta el archivo", ctx.exception.detalle)
        self.assertIn("llaves.json", ctx.exception.detalle)

    def test_fr318_descargador_escribe_llaves_json_tal_cual(self):
        carpeta = os.path.join(self.temp, "paquete")
        respuesta = {"llaves": [{"id": "itm_x", "sala": 3}, {"id": "itm_x", "sala": 3},
                                {"id": "itm_y", "sala": 5, "enemigo": "e-1"}]}
        api = ApiFalsa(llaves={ID_CRIPTA: respuesta})
        descargador(carpeta, api).descargar(ID_CRIPTA)
        with open(os.path.join(carpeta, ID_CRIPTA, "llaves.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f), respuesta)                      # tal cual, sin ordenar ni deduplicar
        rutas = api.rutas()
        self.assertEqual(rutas.count(f"criptas/{ID_CRIPTA}/llaves"), 1)
        ultima_pagina = len(rutas) - 1 - rutas[::-1].index(f"criptas/{ID_CRIPTA}/salas")
        self.assertGreater(rutas.index(f"criptas/{ID_CRIPTA}/llaves"), ultima_pagina)   # después del esqueleto
        self.assertEqual(FuenteOffline(carpeta).obtener_llaves(ID_CRIPTA), [UbicacionLlaveDTO("itm_x", 3),
                         UbicacionLlaveDTO("itm_x", 3), UbicacionLlaveDTO("itm_y", 5, "e-1")])
        # Si la solicitud de llaves falla (0 criptas, 1 general, 2 salas, 3 llaves), el paquete anterior queda intacto.
        otra = ApiFalsa(llaves={ID_CRIPTA: {"llaves": []}}, falla_en=3)
        with self.assertRaises(ErrorRed):
            descargador(carpeta, otra).descargar(ID_CRIPTA)
        self.assertEqual(otra.rutas()[-1], f"criptas/{ID_CRIPTA}/salas")
        with open(os.path.join(carpeta, ID_CRIPTA, "llaves.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f), respuesta)


def almacen_en(carpeta: str):
    """AlmacenLlaves sobre una carpeta temporal. Hasta T015 no existe: es el fallo esperado."""
    from Data.AlmacenLlaves import AlmacenLlaves
    return AlmacenLlaves(carpeta)


UBICACIONES = [UbicacionLlaveDTO("B", 12, "e-1203"), UbicacionLlaveDTO("A", 4), UbicacionLlaveDTO("A", 4)]


class PruebasAlmacenLlaves(CarpetaTemporal):
    """T014: persistencia por versión de la ubicación de las llaves (FR-317, FR-319)."""

    def setUp(self):
        super().setUp()
        self.carpeta = os.path.join(self.temp, "cache", "llaves")
        self.almacen = almacen_en(self.carpeta)

    def ruta(self, id_cripta="prueba"):
        return os.path.join(self.carpeta, id_cripta + ".json")

    def test_fr317_almacen_guarda_y_lee_la_misma_version(self):
        self.assertIsNone(self.almacen.leer("prueba", "v1"))                     # ausente
        self.almacen.guardar("prueba", "v1", UBICACIONES)
        with open(self.ruta(), encoding="utf-8") as f:
            self.assertEqual(json.load(f), {"id": "prueba", "version": "v1",
                                            "llaves": [u.a_diccionario() for u in UBICACIONES]})
        self.assertEqual(self.almacen.leer("prueba", "v1"), UBICACIONES)          # mismo orden, con repetidas
        self.assertEqual(almacen_en(self.carpeta).leer("prueba", "v1"), UBICACIONES)   # sobrevive al cierre

    def test_fr319_almacen_otra_version_es_ausente(self):
        self.almacen.guardar("prueba", "v1", UBICACIONES)
        self.assertIsNone(self.almacen.leer("prueba", "v2"))
        self.assertTrue(os.path.isfile(self.ruta()))                              # nadie lo borra a mano
        self.almacen.guardar("prueba", "v2", UBICACIONES[:1])                     # la escritura lo reemplaza
        self.assertEqual(self.almacen.leer("prueba", "v2"), UBICACIONES[:1])
        self.assertIsNone(self.almacen.leer("prueba", "v1"))

    def test_fr319_almacen_archivo_danado_se_borra(self):
        os.makedirs(self.carpeta)
        for texto in ("{no es json", json.dumps({"id": "prueba", "version": "v1", "llaves": [{"id": "A"}]}),
                      json.dumps(["no", "es", "objeto"]), json.dumps({"id": "prueba", "llaves": []})):
            with self.subTest(texto):
                with open(self.ruta(), "w", encoding="utf-8") as f:
                    f.write(texto)
                self.assertIsNone(self.almacen.leer("prueba", "v1"))
                self.assertFalse(os.path.exists(self.ruta()))

    def test_fr319_almacen_id_distinto_es_ausente(self):
        os.makedirs(self.carpeta)
        with open(self.ruta(), "w", encoding="utf-8") as f:
            json.dump({"id": "otra", "version": "v1", "llaves": [{"id": "A", "sala": 4}]}, f)
        self.assertIsNone(self.almacen.leer("prueba", "v1"))

    def test_fr317_almacen_id_inseguro_no_se_lee_ni_se_escribe(self):
        for malo in ("../hack", "a b", "", "con"):
            with self.subTest(malo):
                self.almacen.guardar(malo, "v1", UBICACIONES)                    # no lanza: simplemente no escribe
                self.assertIsNone(self.almacen.leer(malo, "v1"))
        self.assertFalse(os.path.exists(os.path.join(self.temp, "cache", "hack.json")))
        self.assertTrue(not os.path.isdir(self.carpeta) or os.listdir(self.carpeta) == [])

    def test_fr317_almacen_escribe_con_tmp_y_replace(self):
        reemplazos = []
        original = os.replace

        def espiar(origen, destino):
            reemplazos.append((origen, destino))
            original(origen, destino)

        os.replace = espiar
        try:
            self.almacen.guardar("prueba", "v1", UBICACIONES)
        finally:
            os.replace = original
        self.assertEqual(reemplazos, [(self.ruta() + ".tmp", self.ruta())])
        self.assertFalse(os.path.exists(self.ruta() + ".tmp"))


def gestor_llaves(fuente, almacen):
    """GestorLlaves(fuente, almacen). Hasta T018 no existe: es el fallo esperado."""
    from Data.GestorLlaves import GestorLlaves
    return GestorLlaves(fuente, almacen)


def validar(operacion, ubicaciones, existe_sala):
    """validar_ubicaciones de ValidacionDatos. Hasta T017 no existe: es el fallo esperado."""
    from Data.ValidacionDatos import validar_ubicaciones
    return validar_ubicaciones(operacion, ubicaciones, existe_sala)


class PruebasGestorLlaves(CarpetaTemporal):
    """T016: validar_ubicaciones, GestorLlaves y los escenarios de datos (FR-317 a FR-321, H2-7, H2-8, H3-4 a H3-7)."""

    def preparar(self, ubicaciones=None, salidas_extra=(), **kw):
        """FuenteConLlaves sobre las salas 1 a 4 de cripta_chica y su esqueleto ya cargado."""
        dto, salas, ubic_base = cripta_chica()
        if salidas_extra:
            dto, salas, ubic_base = cripta(4, [abierta(1, 2, 2), puerta(2, 2, 3, "A"), puerta(3, 2, 4, "S"),
                                               *salidas_extra], ubic_base, sala_salida=4)
        fuente = FuenteConLlaves(dto, salas, ubic_base if ubicaciones is None else ubicaciones, **kw)
        esqueleto = GestorEsqueleto(fuente)
        esqueleto.cargar(fuente.obtener_datos_generales("prueba"))
        return dto, fuente, esqueleto

    def almacen(self):
        return almacen_en(os.path.join(self.temp, "cache", "llaves"))

    def test_h2_7_fr321_fr320_sala_inexistente_es_error_de_datos(self):
        for enemigo, esperado in ((None, None), ("e-9901", "(enemigo e-9901)")):
            with self.subTest(enemigo=enemigo):
                ubicaciones = [ubic("S", 3), ubic("A", 99, enemigo), ubic("B", 98)]
                dto, fuente, esqueleto = self.preparar(ubicaciones)
                with self.assertRaises(ErrorDatos) as ctx:
                    gestor_llaves(fuente, None).obtener(dto, esqueleto)
                e = ctx.exception
                self.assertEqual(e.operacion, "ubicación de llaves de prueba")
                self.assertIn("la llave A está en la sala 99", e.detalle)      # la PRIMERA ubicación inválida
                self.assertIn("que no existe en el esqueleto", e.detalle)
                self.assertNotIn("98", e.detalle)
                if esperado is not None:
                    self.assertIn(esperado, e.detalle)
                self.assertIsInstance(e, ErrorRed)                              # los except ErrorRed lo atrapan
        with self.assertRaises(ErrorDatos):
            validar("op", [ubic("A", 99)], esqueleto.existe_sala)
        validar("op", [ubic("A", 1), ubic("A", 4)], esqueleto.existe_sala)    # válidas: no lanza

    def test_h2_8_fr321_fr301_enemigo_inexistente_no_se_valida(self):
        ubicaciones = [ubic("A", 2), ubic("B", 3, "e-9999"), ubic("S", 3)]
        dto, fuente, esqueleto = self.preparar(ubicaciones)
        self.assertEqual(gestor_llaves(fuente, None).obtener(dto, esqueleto), ubicaciones)
        self.assertEqual((fuente.pedidos_contenido, fuente.pedidos_catalogo), (0, 0))   # sin contenido de salas

    def test_fr321_llave_sin_ubicacion_no_es_error_de_datos(self):
        ubicaciones = [ubic("A", 2), ubic("S", 3)]                            # C la pide la puerta 1–4, sin ubicación
        dto, fuente, esqueleto = self.preparar(ubicaciones, salidas_extra=[puerta(1, 1, 4, "C")])
        self.assertEqual(gestor_llaves(fuente, None).obtener(dto, esqueleto), ubicaciones)

    def test_h3_4_fr317_solicitud_de_llaves_cuenta_y_se_persiste(self):
        dto, fuente, esqueleto = self.preparar()
        antes = fuente.solicitudes_realizadas()
        almacen = self.almacen()
        ubicaciones = gestor_llaves(fuente, almacen).obtener(dto, esqueleto)
        self.assertEqual(fuente.pedidos_llaves, 1)
        self.assertEqual(fuente.solicitudes_realizadas(), antes + 1)
        self.assertLessEqual(fuente.solicitudes_realizadas(), fuente.presupuesto_solicitudes())
        self.assertEqual(almacen.leer("prueba", dto.version), ubicaciones)
        self.assertTrue(os.path.isfile(os.path.join(self.temp, "cache", "llaves", "prueba.json")))

    def test_h3_5_fr317_no_repite_la_solicitud(self):
        dto, fuente, esqueleto = self.preparar()
        primera = gestor_llaves(fuente, self.almacen()).obtener(dto, esqueleto)
        _, otra, esqueleto2 = self.preparar()                                 # otra ejecución, misma versión
        self.assertEqual(gestor_llaves(otra, self.almacen()).obtener(dto, esqueleto2), primera)
        self.assertEqual(otra.pedidos_llaves, 0)

    def test_h3_6_fr319_datos_de_la_primera_parte_se_invalidan(self):
        dto, fuente, esqueleto = self.preparar()
        almacen = self.almacen()
        almacen.guardar("prueba", "version-vieja", [ubic("Z", 1)])
        ubicaciones = gestor_llaves(fuente, almacen).obtener(dto, esqueleto)
        self.assertEqual(fuente.pedidos_llaves, 1)                            # se volvió a pedir
        self.assertEqual(ubicaciones, fuente.ubicaciones)
        self.assertEqual(almacen.leer("prueba", dto.version), ubicaciones)    # y se reemplazó
        self.assertIsNone(almacen.leer("prueba", "version-vieja"))
        # Los datos de la primera parte en AlmacenCatalogo (sin cambiarlo): otra versión del catálogo los invalida.
        base = os.path.join(self.temp, "cache", "catalogo")
        ficha = FuenteJson.ficha_desde_diccionario({"id": "itm_x", "nombre": "X", "clase": "arma", "peso": 1,
                                                    "valor": 1, "ataque_bonus": 1})
        viejo = AlmacenCatalogo("cat-p1", base)
        viejo.preparar()
        viejo.guardar(ficha)
        nuevo = AlmacenCatalogo("cat-p2", base)
        self.assertEqual(nuevo.preparar(), ["cat-p1"])                        # lo descarta la validación de versión
        self.assertIsNone(nuevo.leer("itm_x"))                                # se volverá a obtener
        self.assertFalse(os.path.isdir(os.path.join(base, "cat-p1")))

    def test_h3_7_fr320_no_se_pudo_obtener_la_ubicacion(self):
        for modo in ("presupuesto", "429", "red"):
            with self.subTest(modo):
                dto, fuente, esqueleto = self.preparar(falla_llaves=modo)
                almacen = self.almacen()
                with self.assertRaises(ErrorRed) as ctx:
                    gestor_llaves(fuente, almacen).obtener(dto, esqueleto)
                self.assertNotIsInstance(ctx.exception, ErrorDatos)
                self.assertEqual(ctx.exception.operacion, "ubicación de llaves de prueba")
                self.assertIn("ubicación de llaves de prueba", str(ctx.exception))    # mensaje con contexto
                if modo == "presupuesto":
                    self.assertIsInstance(ctx.exception, PresupuestoAgotadoError)
                if modo == "429":
                    self.assertEqual(ctx.exception.codigo, 429)
                self.assertIsNone(almacen.leer("prueba", dto.version))                # nada persistido
        dto, salas, _ = cripta_chica()
        fuente = FuenteOffline(paquete_temporal(os.path.join(self.temp, "paquete"), dto, salas, None))
        esqueleto = GestorEsqueleto(fuente)
        esqueleto.cargar(fuente.obtener_datos_generales("prueba"))
        with self.assertRaises(ErrorRed) as ctx:
            gestor_llaves(fuente, None).obtener(dto, esqueleto)
        self.assertIn("falta el archivo", ctx.exception.detalle)

    def test_fr317_se_persiste_antes_de_validar_fr321(self):
        ubicaciones = [ubic("A", 2), ubic("A", 99)]
        dto, fuente, esqueleto = self.preparar(ubicaciones)
        almacen = self.almacen()
        with self.assertRaises(ErrorDatos) as primero:
            gestor_llaves(fuente, almacen).obtener(dto, esqueleto)
        self.assertEqual(almacen.leer("prueba", dto.version), ubicaciones)    # quedó guardado
        _, otra, esqueleto2 = self.preparar(ubicaciones)
        with self.assertRaises(ErrorDatos) as segundo:
            gestor_llaves(otra, almacen).obtener(dto, esqueleto2)
        self.assertEqual(str(segundo.exception), str(primero.exception))     # el mismo error
        self.assertEqual(otra.pedidos_llaves, 0)                              # sin otra solicitud

    def test_fr318_sin_almacen_no_se_usa_cache(self):
        dto, salas, ubicaciones = cripta_chica()
        almacen = self.almacen()
        almacen.guardar("prueba", dto.version, ubicaciones)                  # una respuesta en línea persistida
        fuente = FuenteOffline(paquete_temporal(os.path.join(self.temp, "paquete"), dto, salas, None))
        esqueleto = GestorEsqueleto(fuente)
        esqueleto.cargar(fuente.obtener_datos_generales("prueba"))
        with self.assertRaises(ErrorRed):                                     # --offline: sin almacén, H3-7
            gestor_llaves(fuente, None).obtener(dto, esqueleto)
        # Con el almacén la habría tapado: por eso con --offline no se usa.
        self.assertEqual(gestor_llaves(fuente, almacen).obtener(dto, esqueleto), ubicaciones)


if __name__ == "__main__":
    unittest.main()
