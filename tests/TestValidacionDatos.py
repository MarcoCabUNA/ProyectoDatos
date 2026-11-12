"""
Pruebas de FR-122 en Datos (integrante 2, tareas T002 y T052 de specs/001-terreno-cazador/tasks.md).

Los casos son los que pide T050: costo 0, "250" y true; los dos lados de una salida con 100 y 250;
cazador sin rango, con rango null, -1 y true. Además, lo que pide T052: el error de datos se distingue
del error de red, el rechazo se recuerda por sala sin otra solicitud, y solo esa sala queda sin contenido.

Todo pasa por FuenteRed + ApiFalsa (la cripta real del paquete, sin red), así que el JSON recorre el
mismo camino que en el juego: FuenteJson -> DTO -> GestorEsqueleto / ResolvedorCatalogo / GestorContenido.
El escenario H2-9 completo (el movimiento rechazado en Servicios) es la prueba T054 del integrante 1.
"""
import copy
import os
import shutil
import tempfile
import unittest

from Data.ClienteHttp import ErrorRed
from Data.FuenteJson import FuenteJson
from Data.GestorContenido import GestorContenido
from Data.GestorEsqueleto import GestorEsqueleto
from Data.ResolvedorCatalogo import ResolvedorCatalogo
from Data.ValidacionDatos import ErrorDatos, error_de_ficha, es_costo_valido
from DTO.ConfiguracionDTO import ConfiguracionDTO
from DTO.FichaEnemigoDTO import FichaEnemigoDTO
from Service.ServicioPartida import ServicioPartida
from tests.Utilidades import ID_CRIPTA, ApiFalsa, catalogo_real, contenido_real, fuente_red, pagina_real

CAZADOR = "ent_cazador_prueba"
SIN_RANGO = object()   # marca: la ficha no trae el campo 'rango'


def ficha_cazador(rango=SIN_RANGO) -> dict:
    ficha = {"id": CAZADOR, "nombre": "Cazador de prueba", "clase": "enemigo", "vida_max": 10, "ataque": 3,
             "defensa": 1, "velocidad": 100, "comportamiento": "cazador", "suelta": []}
    if rango is not SIN_RANGO:
        ficha["rango"] = rango
    return ficha


def contenido_con_cazador(sala: int) -> list:
    """El contenido real de cripta-01 con un cazador agregado en esa sala."""
    contenido = copy.deepcopy(contenido_real())
    for c in contenido:
        if c["sala"] == sala:
            c.setdefault("enemigos", []).append({"instancia": "e-999", "tipo": CAZADOR, "vida": 10})
    return contenido


def api_con_cazador(sala: int, rango=SIN_RANGO) -> ApiFalsa:
    return ApiFalsa(contenidos={ID_CRIPTA: contenido_con_cazador(sala)},
                    catalogo=catalogo_real() + [ficha_cazador(rango)])


def api_con_costos(costos: list[tuple[int, str, object]]) -> ApiFalsa:
    """La cripta real con costos declarados: (sala, dirección, costo) por cada cara."""
    pagina = copy.deepcopy(pagina_real())
    for id_sala, direccion, costo in costos:
        for sala in pagina["salas"]:
            if sala["id"] == id_sala:
                sala["salidas"][direccion]["costo"] = costo
    return ApiFalsa(paginas={ID_CRIPTA: [pagina]})


def ficha_dto(rango=SIN_RANGO) -> FichaEnemigoDTO:
    return FichaEnemigoDTO.desde_diccionario(ficha_cazador(rango))


class PruebasReglas(unittest.TestCase):
    """ValidacionDatos por sí solo."""

    def test_fr122_el_error_de_datos_es_un_error_de_red_que_se_puede_distinguir(self):
        error = ErrorDatos("ficha x", "detalle", id_ficha="x")
        self.assertIsInstance(error, ErrorRed)          # los 'except ErrorRed' de la Parte 1 lo siguen atrapando
        self.assertNotIsInstance(ErrorRed("op", "detalle"), ErrorDatos)
        self.assertEqual(error.id_ficha, "x")

    def test_fr122_costos_validos_e_invalidos(self):
        for costo in (1, 100, 250):
            self.assertTrue(es_costo_valido(costo), costo)
        for costo in (0, -5, "250", True, False, 2.5, None):
            self.assertFalse(es_costo_valido(costo), costo)

    def test_fr122_cazador_con_rango_invalido(self):
        for rango in (SIN_RANGO, None, -1, True, "250", 1.5):
            error = error_de_ficha(ficha_dto(rango))
            self.assertIsInstance(error, ErrorDatos, rango)
            assert error is not None
            self.assertEqual(error.id_ficha, CAZADOR)
            self.assertIn(CAZADOR, str(error))           # qué ficha
            self.assertIn("rango", str(error))           # qué campo

    def test_fr122_el_mensaje_dice_el_valor_recibido(self):
        self.assertIn("-1", str(error_de_ficha(ficha_dto(-1))))
        self.assertIn("True", str(error_de_ficha(ficha_dto(True))))
        self.assertIn("falta o es null", str(error_de_ficha(ficha_dto())))

    def test_fr122_fichas_validas(self):
        self.assertIsNone(error_de_ficha(ficha_dto(0)))          # rango 0 es válido (entero >= 0)
        self.assertIsNone(error_de_ficha(ficha_dto(600)))
        sin_rango_no_cazador = dict(ficha_cazador(), comportamiento="errante")
        self.assertIsNone(error_de_ficha(FichaEnemigoDTO.desde_diccionario(sin_rango_no_cazador)))
        for ficha in catalogo_real():                            # el catálogo de la Parte 1 sigue siendo válido
            self.assertIsNone(error_de_ficha(FuenteJson.ficha_desde_diccionario(ficha)), ficha["id"])


class PruebasEsqueleto(unittest.TestCase):
    """T002 (a): costos inválidos en el esqueleto -> error de datos y el gestor queda sin cargar."""

    def cargar(self, api: ApiFalsa) -> GestorEsqueleto:
        fuente = fuente_red(api)
        esqueleto = GestorEsqueleto(fuente)
        esqueleto.cargar(fuente.obtener_datos_generales(ID_CRIPTA))
        return esqueleto

    def assert_rechaza(self, api: ApiFalsa, *textos: str) -> None:
        fuente = fuente_red(api)
        esqueleto = GestorEsqueleto(fuente)
        with self.assertRaises(ErrorDatos) as ctx:
            esqueleto.cargar(fuente.obtener_datos_generales(ID_CRIPTA))
        self.assertFalse(esqueleto.esta_cargado())
        for texto in textos:
            self.assertIn(texto, str(ctx.exception))

    def test_fr122_costo_cero_texto_y_bool(self):
        for costo in (0, "250", True):
            # sala 2, salida N (a la sala 3): el mensaje dice sala, dirección y valor recibido
            self.assert_rechaza(api_con_costos([(2, "N", costo)]), "sala 2", "salida N", repr(costo))

    def test_fr122_los_dos_lados_con_costos_distintos(self):
        self.assert_rechaza(api_con_costos([(2, "N", 100), (3, "S", 250)]),
                            "sala 2", "salida N", "100", "sala 3", "salida S", "250")

    def test_fr122_el_costo_invalido_se_informa_antes_que_la_diferencia(self):
        # 0 en un lado y 250 en el otro: el problema real es el 0
        self.assert_rechaza(api_con_costos([(2, "N", 250), (3, "S", 0)]), "sala 3", "salida S", "costo 0")

    def test_fr101_costos_validos_se_aceptan(self):
        casos = [
            [],                                                # sin costos: igual que la Parte 1
            [(2, "N", 250)],                                   # un solo lado lo declara
            [(2, "N", 250), (3, "S", 250)],                    # los dos lados con el mismo costo
            [(2, "E", 1), (5, "O", 1)],                        # el mínimo, en una puerta con llave
        ]
        for costos in casos:
            esqueleto = self.cargar(api_con_costos(costos))
            self.assertTrue(esqueleto.esta_cargado(), costos)


class PruebasFichas(unittest.TestCase):
    """T052: la ficha inválida se rechaza sola, se recuerda y no se vuelve a pedir."""

    def setUp(self):
        self.temp = tempfile.mkdtemp()
        self.carpeta = os.path.join(self.temp, "cache", "catalogo")

    def tearDown(self):
        shutil.rmtree(self.temp)

    def crear(self, api: ApiFalsa) -> tuple[ResolvedorCatalogo, GestorContenido]:
        fuente = fuente_red(api)
        resolvedor = ResolvedorCatalogo.crear(fuente, 25, self.carpeta)
        esqueleto = GestorEsqueleto(fuente)
        esqueleto.cargar(fuente.obtener_datos_generales(ID_CRIPTA))
        return resolvedor, GestorContenido(fuente, esqueleto, resolvedor=resolvedor)

    def test_t052_solo_la_ficha_invalida_queda_fuera(self):
        api = api_con_cazador(3)
        resolvedor, contenido = self.crear(api)
        contenido.asegurar_sala(1)                                   # un lote con las 6 salas
        self.assertIsInstance(resolvedor.rechazo(CAZADOR), ErrorDatos)
        self.assertIsNone(resolvedor.rechazo("ent_rata_gigante"))
        self.assertIsNotNone(resolvedor.ficha("ent_rata_gigante"))   # las demás del lote sí se guardaron
        # no quedó en disco: un juego nuevo con la misma carpeta la vuelve a revisar (y la vuelve a rechazar)
        self.assertFalse(os.path.isfile(os.path.join(self.carpeta, resolvedor.version_catalogo(), CAZADOR + ".json")))

    def test_t052_la_ficha_rechazada_no_se_vuelve_a_pedir(self):
        api = api_con_cazador(3)
        resolvedor, contenido = self.crear(api)
        contenido.asegurar_sala(1)
        antes = api.solicitudes_realizadas
        for _ in range(2):
            with self.assertRaises(ErrorDatos) as ctx:
                resolvedor.ficha(CAZADOR)
            self.assertIn("rango", str(ctx.exception))
        self.assertEqual(resolvedor.resolver([CAZADOR]), 0)
        self.assertEqual(api.solicitudes_realizadas, antes)

    def test_t052_ficha_pedida_sola_e_invalida(self):
        # ficha(id) cuando la ficha no estaba en ningún lado: llega por la red, inválida -> ErrorDatos
        api = ApiFalsa(catalogo=catalogo_real() + [ficha_cazador(-1)])
        resolvedor = ResolvedorCatalogo.crear(fuente_red(api), 25, self.carpeta)
        with self.assertRaises(ErrorDatos):
            resolvedor.ficha(CAZADOR)
        antes = api.solicitudes_realizadas
        with self.assertRaises(ErrorDatos):
            resolvedor.ficha(CAZADOR)
        self.assertEqual(api.solicitudes_realizadas, antes)

    def test_t052_solo_esa_sala_queda_sin_contenido(self):
        api = api_con_cazador(3)
        _, contenido = self.crear(api)
        contenido.asegurar_sala(1)
        self.assertEqual(contenido.lotes_realizados(), 1)
        for id_sala in (1, 2, 4, 5, 6):
            self.assertTrue(contenido.contenido_disponible(id_sala), id_sala)
        self.assertFalse(contenido.contenido_disponible(3))
        self.assertIsNone(contenido.obtener_contenido(3))

    def test_t052_entrar_lanza_el_mismo_error_sin_otra_solicitud(self):
        api = api_con_cazador(3)
        _, contenido = self.crear(api)
        contenido.asegurar_sala(1)
        antes = api.solicitudes_realizadas
        mensajes = []
        for _ in range(2):
            with self.assertRaises(ErrorDatos) as ctx:
                contenido.asegurar_sala(3)
            mensajes.append(str(ctx.exception))
        self.assertEqual(mensajes[0], mensajes[1])
        self.assertIn(CAZADOR, mensajes[0])
        self.assertIn("rango", mensajes[0])
        self.assertEqual(api.solicitudes_realizadas, antes)
        self.assertEqual(contenido.precargar_alrededor(4), 0)       # la precarga tampoco la vuelve a pedir
        self.assertEqual(api.solicitudes_realizadas, antes)

    def test_t052_la_precarga_no_se_interrumpe(self):
        # la sala del cazador llega con la precarga: no se lanza nada y la sala inicial sigue disponible
        api = api_con_cazador(2)
        _, contenido = self.crear(api)
        self.assertEqual(contenido.precargar_alrededor(1), 6)
        self.assertTrue(contenido.contenido_disponible(1))
        self.assertFalse(contenido.contenido_disponible(2))

    def test_t052_cazador_valido_se_carga_normal(self):
        for rango in (0, 600):
            api = api_con_cazador(3, rango)
            resolvedor, contenido = self.crear(api)
            contenido.asegurar_sala(1)
            self.assertTrue(contenido.contenido_disponible(3), rango)
            self.assertEqual(resolvedor.ficha(CAZADOR).rango, rango)
            shutil.rmtree(self.carpeta)

    def test_t052_ficha_que_no_llego_por_un_fallo_de_red_se_revisa_al_entrar(self):
        # El catálogo falla (presupuesto) después del contenido: la sala 3 queda cargada sin su ficha.
        # Al entrar, asegurar_sala la pide; como es inválida, rechaza la sala antes de que Lógica la cargue.
        api = api_con_cazador(3)
        api.falla_en = 4          # 0 versión catálogo, 1 general, 2 salas, 3 contenido, 4 catálogo
        resolvedor, contenido = self.crear(api)
        with self.assertRaises(ErrorRed) as ctx:
            contenido.asegurar_sala(1)
        self.assertNotIsInstance(ctx.exception, ErrorDatos)          # este sí es un fallo de red
        self.assertTrue(contenido.contenido_disponible(3))
        self.assertIsNone(resolvedor.rechazo(CAZADOR))
        with self.assertRaises(ErrorDatos):
            contenido.asegurar_sala(3)
        self.assertFalse(contenido.contenido_disponible(3))
        antes = api.solicitudes_realizadas
        with self.assertRaises(ErrorDatos):
            contenido.asegurar_sala(3)
        self.assertEqual(api.solicitudes_realizadas, antes)


class PruebasInicioDePartida(unittest.TestCase):
    """T002 (a) y (b): la partida no inicia; el programa no se cae (el error es un ErrorRed esperado)."""

    def setUp(self):
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp)

    def iniciar(self, api: ApiFalsa):
        partida = ServicioPartida(ConfiguracionDTO(), fuente=fuente_red(api),
                                  carpeta_cache=os.path.join(self.temp, "cache"),
                                  carpeta_logs=os.path.join(self.temp, "logs"))
        return partida.iniciar_partida(ID_CRIPTA, "Ana", semilla=1)

    def test_fr122_costo_invalido_la_partida_no_inicia(self):
        with self.assertRaises(ErrorDatos) as ctx:
            self.iniciar(api_con_costos([(2, "N", 0)]))
        self.assertIn("costo", str(ctx.exception))
        self.assertFalse(os.path.isdir(os.path.join(self.temp, "logs")))   # no se creó ningún log

    def test_fr122_cazador_invalido_en_la_sala_inicial_la_partida_no_inicia(self):
        with self.assertRaises(ErrorDatos) as ctx:
            self.iniciar(api_con_cazador(1))
        self.assertIn(CAZADOR, str(ctx.exception))
        self.assertIn("rango", str(ctx.exception))

    def test_fr122_cazador_invalido_en_otra_sala_la_partida_inicia(self):
        contexto = self.iniciar(api_con_cazador(3))
        self.assertEqual(contexto.jugador.Sala_Actual, 1)
        self.assertFalse(contexto.contenido.contenido_disponible(3))


if __name__ == "__main__":
    unittest.main()
