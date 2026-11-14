"""
Pruebas de FR-122 en Datos (integrante 2, tareas T002 y T052 de specs/001-terreno-cazador/tasks.md).

Los casos son los que pide T050: costo 0, "250" y true; los dos lados de una salida con 100 y 250;
cazador sin rango, con rango null, -1 y true. Además, lo que pide T052: el error de datos se distingue
del error de red, el rechazo se recuerda por sala sin otra solicitud, y solo esa sala queda sin contenido.

Todo pasa por FuenteRed + ApiFalsa (la cripta real del paquete, sin red), así que el JSON recorre el
mismo camino que en el juego: FuenteJson -> DTO -> GestorEsqueleto / ResolvedorCatalogo / GestorContenido.
El escenario H2-9 completo (el movimiento rechazado en Servicios) es la prueba T054 del integrante 1.

T055 (escenarios H2-20 y H2-21): cierre_automatico de una salida y duracion de la ficha de un objeto, los dos
enteros >= 1 si vienen (0, -5, "10" y true son inválidos). La duracion de un efecto de ficha no cambia.
"""
import copy
import os
import shutil
import tempfile
import unittest

import Data.ValidacionDatos as validacion
from Data.ClienteHttp import ErrorRed
from Data.FuenteJson import FuenteJson
from Data.GestorContenido import GestorContenido
from Data.GestorEsqueleto import GestorEsqueleto
from Data.ResolvedorCatalogo import ResolvedorCatalogo
from Data.ValidacionDatos import ErrorDatos, error_de_ficha, es_costo_valido
from DTO.ConfiguracionDTO import ConfiguracionDTO
from DTO.EfectoFichaDTO import leer_efectos
from DTO.FichaEnemigoDTO import FichaEnemigoDTO
from DTO.ObjetoDTO import ObjetoDTO
from Service.ServicioPartida import ServicioPartida
from tests.Utilidades import ID_CRIPTA, ApiFalsa, catalogo_real, contenido_real, fuente_red, pagina_real, sala_de

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


# ---- T055: cierre_automatico y duracion de objeto
POCION = "itm_pocion_prueba"
AUSENTE = object()                       # marca: el campo no viene en el JSON
VALORES_INVALIDOS = (0, -5, "10", True)  # los de los escenarios H2-20 y H2-21


def ficha_pocion(duracion=AUSENTE) -> dict:
    ficha = {"id": POCION, "nombre": "Poción de prueba", "clase": "pocion", "peso": 1, "valor": 10,
             "modificador_velocidad": 20}
    if duracion is not AUSENTE:
        ficha["duracion"] = duracion
    return ficha


def pocion_dto(duracion=AUSENTE) -> ObjetoDTO:
    return ObjetoDTO.desde_diccionario(ficha_pocion(duracion))


def api_con_objeto(sala: int, duracion) -> ApiFalsa:
    """El contenido real de cripta-01 con la poción de prueba agregada al suelo de esa sala."""
    contenido = copy.deepcopy(contenido_real())
    for c in contenido:
        if c["sala"] == sala:
            c.setdefault("objetos", []).append(POCION)
    return ApiFalsa(contenidos={ID_CRIPTA: contenido}, catalogo=catalogo_real() + [ficha_pocion(duracion)])


def api_con_cierre(id_sala: int, direccion: str, cierre) -> ApiFalsa:
    """La cripta real con ese cierre_automatico en una salida (AUSENTE: se quita el campo)."""
    pagina = copy.deepcopy(pagina_real())
    for sala in pagina["salas"]:
        if sala["id"] == id_sala:
            salida = sala["salidas"][direccion]
            salida.pop("cierre_automatico", None)
            if cierre is not AUSENTE:
                salida["cierre_automatico"] = cierre
    return ApiFalsa(paginas={ID_CRIPTA: [pagina]})


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

    def test_t055_fr122_cierres_validos_e_invalidos(self):
        for cierre in (None, 1, 500):
            self.assertTrue(validacion.es_cierre_valido(cierre), cierre)
        for cierre in (0, -5, "10", True, False, 1.5):
            self.assertFalse(validacion.es_cierre_valido(cierre), cierre)

    def test_t055_fr122_objeto_con_duracion_invalida(self):
        for duracion in VALORES_INVALIDOS:
            with self.subTest(duracion=duracion):
                error = error_de_ficha(pocion_dto(duracion))
                self.assertIsInstance(error, ErrorDatos)
                assert error is not None
                self.assertEqual(error.id_ficha, POCION)
                # mismo formato que el rango del cazador: qué ficha, qué campo y el valor recibido
                self.assertEqual(str(error), f"Datos inválidos en 'ficha {POCION}': el campo 'duracion' de un "
                                             f"objeto debe ser un entero >= 1 (se recibió {duracion!r})")

    def test_t055_fr122_objeto_con_duracion_valida_o_sin_duracion(self):
        for duracion in (AUSENTE, None, 1):
            self.assertIsNone(error_de_ficha(pocion_dto(duracion)))

    def test_t055_fr122_la_ficha_de_cazador_sigue_igual(self):
        self.assertEqual(str(error_de_ficha(ficha_dto(-1))),
                         f"Datos inválidos en 'ficha {CAZADOR}': el campo 'rango' de un cazador debe ser un "
                         f"entero >= 0 (se recibió -1)")
        self.assertIsNone(error_de_ficha(ficha_dto(0)))

    def test_t055_fr122_la_duracion_de_un_efecto_no_cambia(self):
        # P1: una duracion <= 0 dentro de un efecto se convierte en None, sin error (EfectoFichaDTO no se valida)
        for duracion in (0, -5):
            efectos = leer_efectos({"veneno": {"daño": 2, "duracion": duracion}})
            self.assertEqual(len(efectos), 1)
            self.assertIsNone(efectos[0].duracion)
            enemigo = dict(ficha_cazador(600), comportamiento="errante", veneno={"daño": 2, "duracion": duracion})
            self.assertIsNone(error_de_ficha(FichaEnemigoDTO.desde_diccionario(enemigo)))


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

    def mensaje_de(self, api: ApiFalsa) -> str:
        fuente = fuente_red(api)
        with self.assertRaises(ErrorDatos) as ctx:
            GestorEsqueleto(fuente).cargar(fuente.obtener_datos_generales(ID_CRIPTA))
        return str(ctx.exception)

    def test_t055_fr122_cierre_automatico_invalido_no_carga(self):
        for cierre in VALORES_INVALIDOS + (1.5,):
            with self.subTest(cierre_automatico=cierre):
                # sala 2, salida N (a la sala 3): sala, dirección, campo y valor recibido
                self.assert_rechaza(api_con_cierre(2, "N", cierre), "sala 2", "salida N", "cierre_automatico",
                                    repr(cierre))
                # mismo formato que el error de costo, cambiando solo el nombre del campo
                costo = self.mensaje_de(api_con_costos([(2, "N", cierre)]))
                self.assertEqual(self.mensaje_de(api_con_cierre(2, "N", cierre)),
                                 costo.replace("costo", "cierre_automatico"))

    def test_t055_fr122_cierre_automatico_valido_carga_normal(self):
        for cierre in (AUSENTE, None, 1, 500):
            with self.subTest(cierre_automatico=cierre):
                esqueleto = self.cargar(api_con_cierre(2, "N", cierre))
                self.assertTrue(esqueleto.esta_cargado())
                salida = sala_de(esqueleto, 2).salidas[0]          # N
                self.assertEqual(salida.cierre_automatico, None if cierre is AUSENTE else cierre)


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

    def test_t055_fr122_objeto_con_duracion_invalida_deja_solo_esa_sala_sin_contenido(self):
        # Igual que el cazador sin rango (T052): se rechaza, se recuerda, solo la sala 3 queda sin contenido
        # y las demás fichas del lote siguen.
        for duracion in VALORES_INVALIDOS:
            with self.subTest(duracion=duracion):
                api = api_con_objeto(3, duracion)
                resolvedor, contenido = self.crear(api)
                contenido.asegurar_sala(1)                                   # un lote con las 6 salas
                self.assertIsInstance(resolvedor.rechazo(POCION), ErrorDatos)
                self.assertIsNotNone(resolvedor.ficha("itm_coraza_cuero"))   # la otra ficha de la sala 3
                self.assertIsNotNone(resolvedor.ficha("ent_rata_gigante"))
                for id_sala in (1, 2, 4, 5, 6):
                    self.assertTrue(contenido.contenido_disponible(id_sala), id_sala)
                self.assertFalse(contenido.contenido_disponible(3))
                self.assertIsNone(contenido.obtener_contenido(3))
                antes = api.solicitudes_realizadas
                for _ in range(2):                                           # recordado, sin otra solicitud
                    with self.assertRaises(ErrorDatos) as ctx:
                        contenido.asegurar_sala(3)
                    self.assertIn(POCION, str(ctx.exception))
                    self.assertIn("duracion", str(ctx.exception))
                    with self.assertRaises(ErrorDatos):
                        resolvedor.ficha(POCION)
                self.assertEqual(api.solicitudes_realizadas, antes)
                shutil.rmtree(self.carpeta)

    def test_t055_fr122_objeto_valido_se_carga_normal(self):
        for duracion in (AUSENTE, None, 1):
            with self.subTest(duracion=duracion):
                resolvedor, contenido = self.crear(api_con_objeto(3, duracion))
                contenido.asegurar_sala(1)
                self.assertTrue(contenido.contenido_disponible(3))
                self.assertIsNone(resolvedor.rechazo(POCION))
                shutil.rmtree(self.carpeta)


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

    def test_t055_fr122_cierre_automatico_invalido_la_partida_no_inicia(self):
        with self.assertRaises(ErrorDatos) as ctx:
            self.iniciar(api_con_cierre(2, "N", 0))
        self.assertIn("cierre_automatico", str(ctx.exception))
        self.assertFalse(os.path.isdir(os.path.join(self.temp, "logs")))   # no se creó ningún log

    def test_t055_fr122_objeto_invalido_en_la_sala_inicial_la_partida_no_inicia(self):
        with self.assertRaises(ErrorDatos) as ctx:
            self.iniciar(api_con_objeto(1, -5))                              # la sala 1 es la inicial
        self.assertIn(POCION, str(ctx.exception))
        self.assertIn("duracion", str(ctx.exception))

    def test_t055_fr122_objeto_invalido_en_otra_sala_la_partida_inicia(self):
        contexto = self.iniciar(api_con_objeto(3, 0))
        self.assertEqual(contexto.jugador.Sala_Actual, 1)
        self.assertFalse(contexto.contenido.contenido_disponible(3))


if __name__ == "__main__":
    unittest.main()
