"""
Pruebas de Data/ClienteHttp.py y Security/ValidadorAcceso.py, sin red:
una sesión falsa devuelve respuestas guionizadas y la espera del 429 no duerme de verdad.
"""
import json
import unittest

import requests

from Data.ClienteHttp import ClienteHttp, ErrorRed, PresupuestoAgotadoError
from Security.ValidadorAcceso import es_nombre_seguro, generar_client_id, validar_version

BASE = "https://ejemplo.test/v1"


class RespuestaFalsa:
    def __init__(self, codigo, cuerpo=None, texto=None, cabeceras=()):
        self.status_code = codigo
        self._cuerpo = cuerpo
        self.text = texto if texto is not None else (json.dumps(cuerpo) if cuerpo is not None else "")
        self._cabeceras = tuple(cabeceras)
        self.headers = self

    def get(self, nombre, defecto=None):          # imita respuesta.headers.get(...)
        for n, v in self._cabeceras:
            if n.lower() == nombre.lower():
                return v
        return defecto

    def json(self):
        if self._cuerpo is None:
            raise ValueError("no es JSON")
        return self._cuerpo


class SesionFalsa:
    """Devuelve (o lanza) los elementos del guion en orden y registra cada llamada."""

    def __init__(self, *guion):
        self._guion = list(guion)
        self.llamadas = []

    def get(self, url, headers, timeout):
        self.llamadas.append((url, headers["X-Cripta-Client-Id"], timeout))
        siguiente = self._guion.pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return siguiente


def crear(sesion, **kw):
    esperas = []
    cliente = ClienteHttp(BASE, "id-fijo", sesion=sesion, esperar=esperas.append, **kw)
    return cliente, esperas


class PruebasClienteHttp(unittest.TestCase):

    def test_200_devuelve_json_y_cuenta_una(self):
        sesion = SesionFalsa(RespuestaFalsa(200, {"criptas": []}))
        c, _ = crear(sesion)
        self.assertEqual(c.get_json("criptas", "listar criptas"), {"criptas": []})
        self.assertEqual(c.solicitudes_realizadas, 1)
        self.assertEqual(sesion.llamadas[0], (BASE + "/criptas", "id-fijo", 10.0))

    def test_encabezado_client_id_en_todas_las_solicitudes(self):
        sesion = SesionFalsa(RespuestaFalsa(200, {}), RespuestaFalsa(200, {}))
        c, _ = crear(sesion)
        c.get_json("a", "op")
        c.get_json("b", "op")
        self.assertEqual([ll[1] for ll in sesion.llamadas], ["id-fijo", "id-fijo"])

    def test_parametros_en_url(self):
        sesion = SesionFalsa(RespuestaFalsa(200, {"contenido": []}))
        c, _ = crear(sesion)
        c.get_json("/criptas/c-01/contenido", "contenido", (("salas", "1,2,3"),))
        self.assertEqual(sesion.llamadas[0][0], BASE + "/criptas/c-01/contenido?salas=1,2,3")

    def test_429_espera_reintenta_y_cuenta_ambas(self):
        sesion = SesionFalsa(RespuestaFalsa(429, {"error": "lento", "reintentar_en": 3}),
                             RespuestaFalsa(200, {"ok": True}))
        c, esperas = crear(sesion)
        self.assertEqual(c.get_json("x", "op"), {"ok": True})
        self.assertEqual(esperas, [3])                 # espera real (simulada), no el reloj virtual
        self.assertEqual(c.solicitudes_realizadas, 2)  # el reintento también cuenta (§5.1)
        self.assertEqual(c.respuestas_429, 1)

    def test_429_sin_cuerpo_usa_retry_after_o_valor_por_defecto(self):
        sesion = SesionFalsa(RespuestaFalsa(429, None, cabeceras=(("Retry-After", "7"),)),
                             RespuestaFalsa(429, None, texto="basura"),
                             RespuestaFalsa(200, {}))
        c, esperas = crear(sesion)
        c.get_json("x", "op")
        self.assertEqual(esperas, [7, ClienteHttp.ESPERA_POR_DEFECTO])

    def test_429_repetido_supera_el_maximo_de_reintentos(self):
        sesion = SesionFalsa(*[RespuestaFalsa(429, {"error": "e", "reintentar_en": 1})] * 3)
        c, esperas = crear(sesion, max_reintentos_429=2)
        with self.assertRaises(ErrorRed) as ctx:
            c.get_json("x", "op")
        self.assertEqual(ctx.exception.codigo, 429)
        self.assertEqual(len(esperas), 2)
        self.assertEqual(c.solicitudes_realizadas, 3)

    def test_404_error_con_contexto(self):
        sesion = SesionFalsa(RespuestaFalsa(404, {"error": "cripta no existe"}))
        c, _ = crear(sesion)
        with self.assertRaises(ErrorRed) as ctx:
            c.get_json("criptas/zzz", "datos generales de zzz")
        self.assertEqual(ctx.exception.codigo, 404)
        self.assertIn("datos generales de zzz", str(ctx.exception))
        self.assertIn("cripta no existe", str(ctx.exception))

    def test_presupuesto_bloquea_sin_enviar(self):
        sesion = SesionFalsa(RespuestaFalsa(200, {}), RespuestaFalsa(200, {}))
        c, _ = crear(sesion)
        c.fijar_presupuesto(2)
        c.get_json("a", "op")
        c.get_json("b", "op")
        with self.assertRaises(PresupuestoAgotadoError):
            c.get_json("c", "op")
        self.assertEqual(len(sesion.llamadas), 2)       # la tercera nunca salió
        self.assertEqual(c.solicitudes_restantes(), 0)

    def test_reintento_429_tambien_respeta_el_presupuesto(self):
        sesion = SesionFalsa(RespuestaFalsa(429, {"error": "e", "reintentar_en": 1}))
        c, _ = crear(sesion)
        c.fijar_presupuesto(1)
        with self.assertRaises(PresupuestoAgotadoError):
            c.get_json("x", "op")
        self.assertEqual(c.solicitudes_realizadas, 1)

    def test_timeout_y_sin_conexion_se_convierten_en_ErrorRed(self):
        sesion = SesionFalsa(requests.Timeout("t"), requests.ConnectionError("c"))
        c, _ = crear(sesion)
        for _ in range(2):
            with self.assertRaises(ErrorRed):
                c.get_json("x", "op")
        self.assertEqual(c.solicitudes_realizadas, 2)

    def test_200_que_no_es_json(self):
        sesion = SesionFalsa(RespuestaFalsa(200, None, texto="<html>"))
        c, _ = crear(sesion)
        with self.assertRaises(ErrorRed):
            c.get_json("x", "op")

    def test_reiniciar_conteo(self):
        sesion = SesionFalsa(RespuestaFalsa(200, {}))
        c, _ = crear(sesion)
        c.fijar_presupuesto(5)
        c.get_json("x", "op")
        c.reiniciar_conteo()
        self.assertEqual((c.solicitudes_realizadas, c.presupuesto), (0, None))

    def test_client_id_vacio_se_rechaza(self):
        with self.assertRaises(ValueError):
            ClienteHttp(BASE, "")


class PruebasValidadorAcceso(unittest.TestCase):

    def test_client_id_unico_por_ejecucion_y_con_formato_uuid(self):
        import uuid
        primero = generar_client_id()
        self.assertEqual(primero, generar_client_id())
        self.assertEqual(str(uuid.UUID(primero)), primero)   # lanza si no es un UUID válido

    def test_validar_version(self):
        self.assertTrue(validar_version("be68d322d2f5", "be68d322d2f5"))
        for local, remota in (("a", "b"), ("", ""), (None, "a"), ("a", None), (None, None)):
            self.assertFalse(validar_version(local, remota))   # ante la duda, no coincide

    def test_es_nombre_seguro(self):
        for bueno in ("itm_llave_negra", "cripta-01", "be68d322d2f5", "A9", "x" * 100, "console"):
            self.assertTrue(es_nombre_seguro(bueno), bueno)
        for malo in ("", "../hack", "a/b", "a\\b", "a b", "x.json", "ñandú", "x" * 101, "con", "NUL", "Com1"):
            self.assertFalse(es_nombre_seguro(malo), malo)


if __name__ == "__main__":
    unittest.main()