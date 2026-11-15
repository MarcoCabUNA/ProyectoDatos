"""
Pruebas de T058 (feature 001, FR-122): una caché de catálogo vieja en disco, escrita antes de T055/T057, con
una ficha que hoy es inválida. Data tiene que rechazar la sala ANTES de que Lógica la cargue: la sala no puede
quedar a medio cargar (enemigos agregados y contadores_tipo avanzados) ni duplicar enemigos al reintentar.

La caché se escribe a mano en un directorio temporal, con el mismo formato que AlmacenCatalogo
(cache/<version>/VERSION y cache/<version>/<id>.json), sin pasar por la validación del juego.

    python -m unittest tests.test_cache_vieja -v
"""
import copy
import json
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from Data.ClienteHttp import ErrorRed  # noqa: E402
from DTO.AccionDTO import AccionDTO  # noqa: E402
from DTO.ConfiguracionDTO import ConfiguracionDTO  # noqa: E402
from DTO.Direcciones import E  # noqa: E402
from DTO.ObjetoDTO import ObjetoDTO  # noqa: E402
from DTO.SalaDTO import EnemigoEnSalaDTO  # noqa: E402
from Service.ServicioAccionJugador import ServicioAccionJugador  # noqa: E402
from Service.ServicioPartida import ServicioPartida  # noqa: E402
from tests.Utilidades import FuenteCuadricula  # noqa: E402
from tests.ayudas_terreno import ID_ENEMIGO_BOTIN_INVALIDO, ID_OBJETO_DURACION_INVALIDA, ficha_errante  # noqa: E402

VERSION = "v"            # FuenteCuadricula.obtener_version_catalogo()
SALA = 3                 # cuadrícula 3 x 3: 1 -E-> 2 -E-> 3

ERRANTE = ficha_errante(id="ent_errante_ok")
BOTIN_INVALIDO = ficha_errante(id=ID_ENEMIGO_BOTIN_INVALIDO, suelta=[ID_OBJETO_DURACION_INVALIDA])
OBJETO_INVALIDO = ObjetoDTO(ID_OBJETO_DURACION_INVALIDA, "Poción rara", "pocion", 1, 10,
                            modificador_velocidad=20, duracion=0)
CON_POCION = ficha_errante(id="ent_errante_con_pocion", suelta=["obj_pocion_ok"])
POCION = ObjetoDTO("obj_pocion_ok", "Poción", "pocion", 1, 10, modificador_velocidad=20, duracion=5)


class FuenteSala3(FuenteCuadricula):
    """
    Cuadrícula 3 x 3 cuya sala 3 trae 'enemigos' (pares instancia, tipo) y 'objetos' en el suelo. El catálogo
    devuelve las 'fichas' pedidas y anota cada lote. Las primeras 'fallas_catalogo' solicitudes de catálogo
    lanzan ErrorRed (sin conexión).
    """

    def __init__(self, enemigos: list[tuple[str, str]], fichas: list, objetos: list[str] | None = None,
                 fallas_catalogo: int = 0):
        super().__init__(3)
        self.enemigos = enemigos
        self.objetos = objetos or []
        self.fichas = fichas
        self.fallas_catalogo = fallas_catalogo
        self.catalogos: list[list[str]] = []

    def obtener_contenido(self, id_cripta, ids_salas):
        contenidos = super().obtener_contenido(id_cripta, ids_salas)
        for contenido in contenidos:
            if contenido.sala == SALA:
                for instancia, tipo in self.enemigos:
                    contenido.enemigos.append(EnemigoEnSalaDTO(instancia, tipo, 10))
                contenido.objetos.extend(self.objetos)
        return contenidos

    def obtener_catalogo(self, ids):
        if self.fallas_catalogo > 0:
            self.fallas_catalogo -= 1
            raise ErrorRed("catalogo", "sin conexión (simulado)")
        self.catalogos.append(list(ids))
        return [ficha for ficha in self.fichas if ficha.id in ids]


def escribir_cache_vieja(carpeta_cache: str, fichas: list) -> None:
    """La caché que dejó una versión anterior del juego: cada ficha tal cual, sin validar."""
    carpeta = os.path.join(carpeta_cache, VERSION)
    os.makedirs(carpeta)
    with open(os.path.join(carpeta, "VERSION"), "w", encoding="utf-8") as archivo:
        archivo.write(VERSION)
    for ficha in fichas:
        with open(os.path.join(carpeta, ficha.id + ".json"), "w", encoding="utf-8") as archivo:
            json.dump(ficha.a_diccionario(), archivo, ensure_ascii=False)


class TestCacheVieja(unittest.TestCase):

    def setUp(self):
        self._carpeta = tempfile.TemporaryDirectory()
        self.carpeta = self._carpeta.name
        self.acciones = ServicioAccionJugador()

    def tearDown(self):
        self._carpeta.cleanup()

    def _partida_en_la_sala_2(self, fuente: FuenteSala3, cache_vieja: list):
        """Escribe la caché vieja, inicia la partida y mueve al jugador a la sala 2 (vecina de la sala 3)."""
        cache = os.path.join(self.carpeta, "cache")
        escribir_cache_vieja(cache, cache_vieja)
        partida = ServicioPartida(ConfiguracionDTO(), fuente=fuente, carpeta_cache=cache,
                                  carpeta_logs=os.path.join(self.carpeta, "logs"))
        ctx = partida.iniciar_partida("cuadricula", "Ana", semilla=1)
        estado = self.acciones.ejecutar(ctx, AccionDTO("mover", direccion=E))
        self.assertIsNone(estado.resultado)
        self.assertEqual(estado.sala.id, 2)
        return ctx

    def _entrar_se_rechaza(self, ctx, textos: tuple[str, ...]) -> None:
        """Entrar a la sala 3 se rechaza con el error de datos y la partida queda exactamente igual."""
        reloj = ctx.motor.reloj
        contadores = copy.deepcopy(ctx.mazmorra.contadores_tipo)
        escritas = ctx.bitacora.acciones_escritas()

        estado = self.acciones.ejecutar(ctx, AccionDTO("mover", direccion=E))

        mensaje = estado.resultado
        self.assertIsNotNone(mensaje)
        for texto in textos:
            self.assertIn(texto, mensaje)
        self.assertFalse(mensaje.startswith("Sin conexión"))
        self.assertEqual(estado.sala.id, 2)
        self.assertEqual(estado.reloj, reloj)                                # no consume tiempo
        self.assertEqual(ctx.bitacora.acciones_escritas(), escritas)         # no se anexa a partida.log
        self.assertEqual(ctx.mazmorra.sala(SALA).enemigos, [])              # nada a medio cargar
        self.assertFalse(ctx.mazmorra.contenido_cargado(SALA))
        self.assertEqual(ctx.mazmorra.contadores_tipo, contadores)
        self.assertFalse(ctx.contenido.contenido_disponible(SALA))          # rechazada desde el primer intento

        # El segundo intento da el mismo mensaje y tampoco cambia nada.
        estado = self.acciones.ejecutar(ctx, AccionDTO("mover", direccion=E))
        self.assertEqual(estado.resultado, mensaje)
        self.assertEqual(ctx.mazmorra.contadores_tipo, contadores)
        self.assertEqual(ctx.mazmorra.sala(SALA).enemigos, [])

    def test_t058_fr122_a_cache_vieja_con_enemigo_de_botin_rechazado(self):
        """(a) La caché vieja tiene al enemigo pero no su suelta, que llega inválida: la sala 3 se rechaza entera."""
        self.skipTest("pendiente de T058: GestorContenido.asegurar_sala todavía no valida las fichas de la sala")
        fuente = FuenteSala3(enemigos=[("e-1", ERRANTE.id), ("e-2", BOTIN_INVALIDO.id)],
                             fichas=[ERRANTE, BOTIN_INVALIDO, OBJETO_INVALIDO])
        ctx = self._partida_en_la_sala_2(fuente, cache_vieja=[ERRANTE, BOTIN_INVALIDO])
        self._entrar_se_rechaza(ctx, (ID_ENEMIGO_BOTIN_INVALIDO, "suelta", ID_OBJETO_DURACION_INVALIDA))

    def test_t058_fr122_b_cache_vieja_con_objeto_del_suelo_invalido(self):
        """(b) La caché vieja tiene una poción del suelo con `duracion` 0: la sala 3 se rechaza entera."""
        self.skipTest("pendiente de T058: GestorContenido.asegurar_sala todavía no valida las fichas de la sala")
        fuente = FuenteSala3(enemigos=[("e-1", ERRANTE.id)], objetos=[OBJETO_INVALIDO.id],
                             fichas=[ERRANTE, OBJETO_INVALIDO])
        ctx = self._partida_en_la_sala_2(fuente, cache_vieja=[ERRANTE, OBJETO_INVALIDO])
        self._entrar_se_rechaza(ctx, (ID_OBJETO_DURACION_INVALIDA, "duracion"))

    def test_t058_fr122_c_error_de_red_al_validar_y_reintento_sin_duplicados(self):
        """
        (c) La caché vieja tiene a los dos enemigos pero no la poción que suelta el segundo. Al entrar, bajarla
        falla por la red: el movimiento se rechaza sin cargar nada. Con la red buena, el reintento entra y la
        sala 3 tiene cada enemigo una sola vez, con su número 1.
        """
        self.skipTest("pendiente de T058: GestorContenido.asegurar_sala todavía no valida las fichas de la sala")
        fuente = FuenteSala3(enemigos=[("e-1", ERRANTE.id), ("e-2", CON_POCION.id)],
                             fichas=[ERRANTE, CON_POCION, POCION], fallas_catalogo=1)
        ctx = self._partida_en_la_sala_2(fuente, cache_vieja=[ERRANTE, CON_POCION])
        reloj = ctx.motor.reloj
        contadores = copy.deepcopy(ctx.mazmorra.contadores_tipo)

        estado = self.acciones.ejecutar(ctx, AccionDTO("mover", direccion=E))
        self.assertTrue(estado.resultado.startswith("Sin conexión"))
        self.assertEqual(estado.sala.id, 2)
        self.assertEqual(estado.reloj, reloj)
        self.assertEqual(ctx.mazmorra.sala(SALA).enemigos, [])
        self.assertEqual(ctx.mazmorra.contadores_tipo, contadores)

        estado = self.acciones.ejecutar(ctx, AccionDTO("mover", direccion=E))
        self.assertIsNone(estado.resultado)
        self.assertEqual(estado.sala.id, SALA)
        enemigos = ctx.mazmorra.sala(SALA).enemigos
        self.assertEqual([(e.id, e.ficha.id, e.numero) for e in enemigos],
                         [("e-1", ERRANTE.id, 1), ("e-2", CON_POCION.id, 1)])
        self.assertIn([ERRANTE.id, 1], ctx.mazmorra.contadores_tipo)
        self.assertIn([CON_POCION.id, 1], ctx.mazmorra.contadores_tipo)

    def test_t058_fr122_d_cache_valida_no_agrega_solicitudes(self):
        """(d) Con la caché válida (enemigos y suelta en disco) entrar a la sala 3 no pide nada al catálogo."""
        fuente = FuenteSala3(enemigos=[("e-1", ERRANTE.id), ("e-2", CON_POCION.id)],
                             fichas=[ERRANTE, CON_POCION, POCION])
        ctx = self._partida_en_la_sala_2(fuente, cache_vieja=[ERRANTE, CON_POCION, POCION])
        lotes = len(fuente.lotes)

        estado = self.acciones.ejecutar(ctx, AccionDTO("mover", direccion=E))

        self.assertIsNone(estado.resultado)
        self.assertEqual(estado.sala.id, SALA)
        self.assertEqual(len(ctx.mazmorra.sala(SALA).enemigos), 2)
        self.assertEqual(fuente.catalogos, [])
        self.assertEqual(len(fuente.lotes), lotes)


if __name__ == "__main__":
    unittest.main()
