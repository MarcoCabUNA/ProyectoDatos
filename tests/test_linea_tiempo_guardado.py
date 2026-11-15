"""
Pruebas de guardar y cargar con la línea de tiempo (feature 004, H4, T045): FR-420 y FR-421.

Se juega con el paquete offline y el archivo binario de verdad. La partida se guarda con un servicio y se carga con OTRO
servicio nuevo (su propia fuente, caché y carpeta de logs), como al abrir el programa otra vez.
"""
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ayudas_linea_tiempo import ID_CRIPTA, RAIZ, jugar, partida_de_prueba
from Data import GuardadoBinario
from Data.FuenteOffline import FuenteOffline
from Data.GuardadoBinario import ErrorGuardado
from DTO.ConfiguracionDTO import ConfiguracionDTO
from DTO.AccionDTO import AccionDTO
from Logic.PartidaGuardada import PartidaGuardada
from Service.GrabadoresLinea import ContenidoGrabador, ResolvedorGrabador
from Service.ServicioGuardado import ServicioGuardado
from Service.ServicioLineaTiempo import ServicioLineaTiempo
from Service.ServicioPartida import ServicioPartida

K_GUARDADO = 3
ACCIONES = 20


def _servicio_nuevo(carpeta: str, **config) -> ServicioPartida:
    """Un servicio recién abierto: fuente, caché y logs propios (sin el jugador reforzado de la partida original)."""
    return ServicioPartida(ConfiguracionDTO(offline=True, cache_size=25, **config),
                           fuente=FuenteOffline(str(RAIZ / "paquete")),
                           carpeta_cache=os.path.join(carpeta, "cache"), carpeta_logs=os.path.join(carpeta, "logs"))


def _foto(ctx) -> tuple:
    partida, salas = PartidaGuardada.guardar(ctx.motor, ctx.cripta, ctx.resolvedor.version_catalogo(), ctx.semilla)
    return partida.a_diccionario(), [sala.a_diccionario() for sala in salas]


def _consultas(ctx) -> list:
    """Varios `historia <t>` y `historia #k` del contexto, como resúmenes."""
    servicio = ServicioLineaTiempo()
    reloj, hechas = ctx.motor.reloj, ctx.jugador.acciones
    instantes = sorted({0, reloj // 3, reloj // 2, ctx.linea.accion(hechas).tiempo, reloj})
    acciones = sorted({1, 2, hechas // 2, hechas - 1, hechas})
    return ([servicio.consultar_por_instante(ctx, t) for t in instantes] +
            [servicio.consultar_por_accion(ctx, k) for k in acciones])


class _ConPartidaGuardada(unittest.TestCase):

    def setUp(self):
        self._temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporal.cleanup)
        self.carpeta = self._temporal.name
        self.partida, self.ctx = partida_de_prueba(os.path.join(self.carpeta, "a"), semilla=2026, k=K_GUARDADO)
        jugar(self.ctx, ACCIONES)
        self.assertGreaterEqual(self.ctx.jugador.acciones, 12)           # una partida con historia de verdad
        self.ruta = os.path.join(self.carpeta, "saves", "partida.sav")
        ServicioGuardado(self.partida).guardar(self.ctx, self.ruta)

    def cargar(self, **config):
        nueva = _servicio_nuevo(os.path.join(self.carpeta, "b"), **config)
        return nueva, ServicioGuardado(nueva).cargar(self.ruta, "Beto")


class PruebasGuardarYCargarConLinea(_ConPartidaGuardada):

    def test_h4_1_fr420_mismos_resumenes_tras_guardar_y_cargar(self):
        antes = _consultas(self.ctx)
        _, ctx2 = self.cargar()
        self.assertIsNotNone(ctx2.linea)
        self.assertEqual(len(ctx2.linea.acciones), len(self.ctx.linea.acciones))
        self.assertEqual([p.acciones_completadas for p in ctx2.linea.puntos],
                         [p.acciones_completadas for p in self.ctx.linea.puntos])
        despues = _consultas(ctx2)
        self.assertEqual(len(antes), len(despues))
        for esperado, obtenido in zip(antes, despues):
            self.assertEqual(obtenido, esperado)

    def test_h4_1_fr420_la_partida_cargada_guarda_otra_vez_la_misma_linea(self):
        _, ctx2 = self.cargar()
        self.assertEqual(ctx2.linea.a_guardada(), self.ctx.linea.a_guardada())        # guardar, cargar y guardar es estable

    def test_h4_2_fr420_se_puede_seguir_jugando_tras_cargar(self):
        servicio = ServicioLineaTiempo()
        hechas, reloj = self.ctx.jugador.acciones, self.ctx.motor.reloj
        t_anterior = self.ctx.linea.accion(hechas // 2).tiempo + 1
        esperado = servicio.consultar_por_instante(self.ctx, t_anterior)
        _, ctx2 = self.cargar()
        jugar(ctx2, 6)
        self.assertGreater(ctx2.jugador.acciones, hechas)                              # la partida siguió
        self.assertEqual(len(ctx2.linea.acciones), ctx2.jugador.acciones)              # y la línea la acompañó
        self.assertEqual(servicio.consultar_por_instante(ctx2, t_anterior), esperado)  # un instante anterior al guardado
        self.assertEqual(servicio.consultar_por_instante(ctx2, reloj).reloj, reloj)    # el instante del guardado
        ultima = ctx2.jugador.acciones
        self.assertEqual(servicio.consultar_por_accion(ctx2, ultima).instante_pedido, ultima)   # y una acción nueva

    def test_h4_2_fr420_la_partida_cargada_sigue_grabando_las_cargas_y_fichas(self):
        _, ctx2 = self.cargar()
        self.assertIsInstance(ctx2.contenido, ContenidoGrabador)       # los grabadores quedan instalados (R3)
        self.assertIsInstance(ctx2.resolvedor, ResolvedorGrabador)
        antes = len(ctx2.linea.cargas)
        jugar(ctx2, 40)
        self.assertGreaterEqual(len(ctx2.linea.cargas), antes)         # si entra a salas nuevas, las registra
        for registro in ctx2.linea.cargas:                             # una sola vez por sala
            self.assertEqual(1, len([r for r in ctx2.linea.cargas if r.sala.id == registro.sala.id]))

    def test_h4_k_guardado_se_conserva_al_cargar(self):
        _, ctx2 = self.cargar(checkpoint_cada=7)                       # se pide otro K: manda el guardado
        self.assertEqual(ctx2.linea.k, K_GUARDADO)
        jugar(ctx2, 8)
        posiciones = [p.acciones_completadas for p in ctx2.linea.puntos]
        for anterior, siguiente in zip(posiciones, posiciones[1:]):
            self.assertLessEqual(siguiente - anterior, K_GUARDADO)     # nunca más de K entre dos puntos (FR-416)

    def test_la_partida_cargada_toma_el_motor_nuevo(self):
        _, ctx2 = self.cargar()
        self.assertIs(ctx2.motor.jugador, ctx2.jugador)
        self.assertIs(ctx2.motor.mazmorra, ctx2.mazmorra)
        self.assertIsNot(ctx2.motor, self.ctx.motor)


class PruebasArchivosIncompatibles(_ConPartidaGuardada):

    def test_h4_3_apendiceB_caso6_fr421_archivo_de_la_primera_parte(self):
        datos = bytearray(Path(self.ruta).read_bytes())
        struct.pack_into("<H", datos, 4, 1)                            # un archivo de la primera parte: versión 1
        Path(self.ruta).write_bytes(bytes(datos[:40]))
        foto = _foto(self.ctx)
        reloj = self.ctx.motor.reloj
        with self.assertRaises(ErrorGuardado) as error:                # nunca en silencio
            ServicioGuardado(_servicio_nuevo(os.path.join(self.carpeta, "b"))).cargar(self.ruta, "Beto")
        mensaje = str(error.exception)
        self.assertIn("versión 1", mensaje)                            # dice qué versión leyó
        self.assertIn("versión 2", mensaje)                            # y cuál espera
        self.assertIn("partida.sav", mensaje)                       # y de qué archivo hablaba
        self.assertEqual(_foto(self.ctx), foto)                        # la partida actual no se tocó
        self.assertEqual(self.ctx.motor.reloj, reloj)
        jugar(self.ctx, 1)                                             # y sigue jugable

    def test_h4_fr421_el_programa_no_se_cae(self):
        original = Path(self.ruta).read_bytes()
        cortes = (len(original) - 1, len(original) // 2, 70, 10, 0)
        for largo in cortes:                                           # archivos cortados, también dentro del bloque de la línea
            Path(self.ruta).write_bytes(original[:largo])
            with self.subTest(largo=largo):
                with self.assertRaises(ErrorGuardado):
                    ServicioGuardado(_servicio_nuevo(os.path.join(self.carpeta, "b"))).cargar(self.ruta, "Beto")
        Path(self.ruta).write_bytes(original + b"\x00")                # bytes de más
        with self.assertRaises(ErrorGuardado):
            ServicioGuardado(_servicio_nuevo(os.path.join(self.carpeta, "b"))).cargar(self.ruta, "Beto")
        Path(self.ruta).write_bytes(original)                          # el archivo bueno, de nuevo, carga
        _, ctx2 = self.cargar()
        self.assertEqual(len(ctx2.linea.acciones), len(self.ctx.linea.acciones))

    def test_h4_fr421_un_archivo_sin_linea_carga_una_partida_sin_linea(self):
        """Un guardado de la versión 2 con linea=None (largo 0) no se cae: la partida carga y juega, sin línea."""
        partida, salas = PartidaGuardada.guardar(self.ctx.motor, self.ctx.cripta,
                                                 self.ctx.resolvedor.version_catalogo(), self.ctx.semilla)
        GuardadoBinario.guardar(self.ruta, partida, salas)             # sin línea
        _, ctx2 = self.cargar()
        self.assertIsNone(ctx2.linea)                                  # igual que un contexto armado a mano
        antes = ctx2.jugador.acciones
        jugar(ctx2, 3)                                                 # se puede seguir jugando
        self.assertGreater(ctx2.jugador.acciones, antes)


if __name__ == "__main__":
    unittest.main()
