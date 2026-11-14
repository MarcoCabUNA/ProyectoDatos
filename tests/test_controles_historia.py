"""
Pruebas de la línea de comandos de «historia» en los controles de la partida (feature 004, T052, FR-409, FR-423, FR-407).

ControlesJuego.procesar_comando(texto) valida solo la ESTRUCTURA (`historia <t>` con entero >= 0, `historia #k` con
entero >= 1) y llama al backend; el rango lo valida Logic y su mensaje se muestra tal cual. Una consulta no consume
tiempo, no es una acción y no se registra en `partida.log`.
"""
import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame, tecla  # noqa: E402  (fija SDL_VIDEODRIVER=dummy antes de importar pygame)
from ayudas_controladores import crear_backend  # noqa: E402

from DTO.ResumenHistoriaDTO import ResumenHistoriaDTO  # noqa: E402
from DTO.ActorDTO import ActorDTO  # noqa: E402
from UIController.ControladorBackend import ErrorOperacion  # noqa: E402
from UIController.ControlesJuego import MENSAJE_USO_HISTORIA, ControlesJuego  # noqa: E402

JUGADOR = ActorDTO("jugador", "jugador", "J", 30, 30, 5, 1, 100, 1)


def resumen(reloj=10, instante=10):
    return ResumenHistoriaDTO(reloj=reloj, sala_id=1, sala_nombre="Sala", jugador=JUGADOR, inventario=[],
                              arma_equipada=None, armadura_equipada=None, efectos=[], enemigos=[],
                              instante_pedido=instante)


class BackendQueAnota:
    """Anota las consultas de historia; devuelve un resumen o falla con el mensaje que se le pida."""

    def __init__(self):
        self.llamadas = []
        self.falla_con = None

    def _consulta(self, nombre, valor):
        self.llamadas.append((nombre, valor))
        if self.falla_con is not None:
            raise ErrorOperacion(self.falla_con)
        return resumen(instante=valor)

    def historia_por_instante(self, t): return self._consulta("instante", t)
    def historia_por_accion(self, k): return self._consulta("accion", k)


def controles_con(backend):
    from DTO.EstadoJuegoDTO import EstadoJuegoDTO
    from DTO.InventarioDTO import InventarioDTO
    from DTO.SalaDTO import SalaDTO
    estado = EstadoJuegoDTO(sala=SalaDTO(1, "Sala", [None, None, None, None], "v"), jugador=JUGADOR, enemigos=[],
                            objetos_suelo=[], efectos=[], inventario=InventarioDTO([], 0, 0, 10), mensajes=[], reloj=0)
    return ControlesJuego(backend, estado)


class PruebasComandoHistoria(unittest.TestCase):

    def test_h1_11_fr423_historia_t(self):
        backend = BackendQueAnota()
        controles = controles_con(backend)
        controles.procesar_comando("historia 300")
        self.assertEqual(backend.llamadas, [("instante", 300)])              # un entero, no el texto
        self.assertEqual(controles.resumen, resumen(instante=300))
        self.assertIsNone(controles.aviso)
        controles.procesar_comando("  historia   0  ")                       # el cero y los espacios sobrantes valen
        self.assertEqual(backend.llamadas[-1], ("instante", 0))

    def test_h1_11_fr423_historia_k(self):
        backend = BackendQueAnota()
        controles = controles_con(backend)
        controles.procesar_comando("historia #3")
        self.assertEqual(backend.llamadas, [("accion", 3)])
        self.assertEqual(controles.resumen, resumen(instante=3))
        self.assertIsNone(controles.aviso)

    def test_fr409_historia_mal_formada_se_rechaza_con_uso(self):
        for texto in ("historia", "historia abc", "historia -3", "historia #x", "historia #0", "historia #", "historia 2.5",
                      "historia 1 2", "historia #-1", "historia # 3", "", "   ", "otra cosa", "historia ٣"):
            with self.subTest(texto=texto):
                backend = BackendQueAnota()
                controles = controles_con(backend)
                antes = (controles.estado, controles.resumen)
                controles.procesar_comando(texto)
                self.assertEqual(controles.aviso, MENSAJE_USO_HISTORIA)
                self.assertEqual(backend.llamadas, [], "la estructura mala no llega al backend")
                self.assertEqual((controles.estado, controles.resumen), antes)    # partida y panel sin cambios

    def test_fr409_el_mensaje_de_rango_de_logic_se_muestra_tal_cual(self):
        backend = BackendQueAnota()
        backend.falla_con = "El instante 999 es posterior al reloj actual: debe estar entre 0 y 120"
        controles = controles_con(backend)
        controles.procesar_comando("historia 999")
        self.assertEqual(controles.aviso, backend.falla_con)
        self.assertIsNone(controles.resumen)

    def test_un_resumen_bueno_no_se_borra_por_una_orden_mala(self):
        backend = BackendQueAnota()
        controles = controles_con(backend)
        controles.procesar_comando("historia 5")
        controles.procesar_comando("historia nada")
        self.assertEqual(controles.resumen, resumen(instante=5))                  # sigue el último resumen bueno
        self.assertEqual(controles.aviso, MENSAJE_USO_HISTORIA)

    def test_fr407_historia_no_cambia_el_estado_de_la_partida(self):
        carpeta = tempfile.mkdtemp()
        try:
            backend = crear_backend(carpeta)
            estado = backend.iniciar("cripta-01", "Ana")
            controles = ControlesJuego(backend, estado)
            controles.procesar_evento(tecla(pygame.K_z))                          # esperar: la línea tiene 1 acción
            controles.procesar_evento(tecla(pygame.K_z))
            antes = backend.estado()
            ruta = backend._contexto.bitacora.ruta()
            with open(ruta, encoding="utf-8") as archivo:
                log_antes = archivo.read()
            acciones_antes = backend._contexto.jugador.acciones
            controles.procesar_comando("historia 0")
            controles.procesar_comando("historia #1")
            controles.procesar_comando("historia #2")
            controles.procesar_comando("historia 99999")                          # fuera de rango: error, nada cambia
            self.assertIsNotNone(controles.aviso)
            self.assertEqual(backend.estado(), antes)                             # mismo reloj, sala, inventario y mensajes
            self.assertEqual(backend._contexto.jugador.acciones, acciones_antes)  # no cuenta como acción
            with open(ruta, encoding="utf-8") as archivo:
                self.assertEqual(archivo.read(), log_antes)                       # nada en partida.log
        finally:
            shutil.rmtree(carpeta, ignore_errors=True)


class PruebasBackendHistoria(unittest.TestCase):
    """T053: ControladorBackend.historia_por_instante / historia_por_accion y la línea alimentada por las acciones."""

    def setUp(self):
        self.carpeta = tempfile.mkdtemp()
        self.backend = crear_backend(self.carpeta)
        self.backend.iniciar("cripta-01", "Ana")

    def tearDown(self):
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def test_fr423_las_acciones_alimentan_la_linea_y_las_consultas_la_leen(self):
        for _ in range(3):
            self.backend.esperar()
        self.assertEqual(len(self.backend._contexto.linea.acciones), 3)           # la línea se alimenta por el backend
        por_accion = self.backend.historia_por_accion(2)
        self.assertEqual((por_accion.instante_pedido, por_accion.reloj), (2, 100))   # esperar cuesta 100: antes de la 2.ª
        inicial = self.backend.historia_por_instante(0)
        self.assertEqual((inicial.reloj, inicial.sala_id), (0, 1))
        self.assertFalse(inicial.terminada_antes)

    def test_fr409_el_rango_lo_valida_logic_y_sale_como_error_de_operacion(self):
        self.backend.esperar()
        with self.assertRaises(ErrorOperacion) as t_malo:
            self.backend.historia_por_instante(5000)
        self.assertIn("entre 0 y", str(t_malo.exception))
        with self.assertRaises(ErrorOperacion) as k_malo:
            self.backend.historia_por_accion(7)
        self.assertIn("entre 1 y 1", str(k_malo.exception))

    def test_sin_partida_es_un_error_de_operacion(self):
        sin_partida = crear_backend(os.path.join(self.carpeta, "otra"))
        with self.assertRaises(ErrorOperacion):
            sin_partida.historia_por_instante(0)


if __name__ == "__main__":
    unittest.main()
