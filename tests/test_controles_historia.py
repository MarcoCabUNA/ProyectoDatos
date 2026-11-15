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
from UIController.ControlesJuego import (LARGO_MAXIMO_LINEA, MENSAJE_USO_HISTORIA, PIDE_PAUSA,  # noqa: E402
                                         ControlesJuego)
from test_controlador_pygame import Entorno  # noqa: E402

JUGADOR = ActorDTO("jugador", "jugador", "J", 30, 30, 5, 1, 100, 1)


def resumen(reloj=10, instante=10):
    return ResumenHistoriaDTO(reloj=reloj, sala_id=1, sala_nombre="Sala", jugador=JUGADOR, inventario=[],
                              arma_equipada=None, armadura_equipada=None, efectos=[], enemigos=[],
                              instante_pedido=instante)


class BackendQueAnota:
    """Anota las consultas de historia; devuelve un resumen o falla con el mensaje que se le pida."""

    def __init__(self):
        self.llamadas = []
        self.otras = []
        self.falla_con = None

    def __getattr__(self, nombre):
        """Cualquier otra llamada (mover, esperar, retroceder...) se anota en `otras`: con la línea abierta no debe haber."""
        def otra(*argumentos):
            self.otras.append((nombre, argumentos))
            raise ErrorOperacion(f"no debería llamarse a {nombre}")
        return otra

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


def _teclas(controles, *eventos):
    return [controles.procesar_evento(evento) for evento in eventos]


def _escribir(controles, texto):
    for caracter in texto:
        controles.procesar_evento(tecla(ord(caracter.lower()), caracter=caracter))


class PruebasLineaDeComandos(unittest.TestCase):
    """T056: Enter abre la línea, Enter acepta, Esc la cierra sin pausar; y con la línea abierta las teclas del juego se
    escriben (no actúan). Se revisaron los controles de View/ y de ControladorPygame: Enter solo activa botones de los
    menús y acepta el nombre; en la partida no hacía nada. Esc sí choca: pedía la pausa (ver la última prueba)."""

    def test_fr423_enter_abre_y_acepta_y_esc_cierra_sin_pausar(self):
        backend = BackendQueAnota()
        controles = controles_con(backend)
        self.assertIsNone(controles.linea)
        controles.procesar_evento(tecla(pygame.K_RETURN))
        self.assertEqual(controles.linea, "")                                     # abierta y vacía
        _escribir(controles, "historia 7")
        self.assertEqual(controles.linea, "historia 7")
        self.assertIsNone(controles.procesar_evento(tecla(pygame.K_RETURN)))
        self.assertIsNone(controles.linea)                                        # aceptar la cierra
        self.assertEqual(backend.llamadas, [("instante", 7)])
        controles.procesar_evento(tecla(pygame.K_KP_ENTER))                       # el Enter del teclado numérico también
        self.assertEqual(controles.linea, "")
        self.assertIsNone(controles.procesar_evento(tecla(pygame.K_ESCAPE)))      # Esc cierra la línea: NO pide pausa
        self.assertIsNone(controles.linea)
        self.assertEqual(backend.llamadas, [("instante", 7)])                     # y no ejecuta nada
        self.assertEqual(backend.otras, [])

    def test_fr423_enter_con_la_linea_vacia_solo_la_cierra(self):
        backend = BackendQueAnota()
        controles = controles_con(backend)
        _teclas(controles, tecla(pygame.K_RETURN), tecla(pygame.K_RETURN))
        self.assertIsNone(controles.linea)
        self.assertIsNone(controles.aviso)
        self.assertEqual(backend.llamadas, [])

    def test_con_la_linea_abierta_las_teclas_del_juego_se_escriben_y_no_actuan(self):
        backend = BackendQueAnota()
        controles = controles_con(backend)
        controles.procesar_evento(tecla(pygame.K_RETURN))
        for caracter in "wasdezqugvx ":
            controles.procesar_evento(tecla(ord(caracter), caracter=caracter))
        controles.procesar_evento(tecla(pygame.K_TAB))
        controles.procesar_evento(tecla(pygame.K_UP))
        controles.procesar_evento(tecla(pygame.K_F5))
        controles.procesar_evento(tecla(pygame.K_z, mod=pygame.KMOD_CTRL))
        self.assertEqual(backend.otras, [], "ninguna tecla de juego debe llegar al backend con la línea abierta")
        self.assertEqual(controles.linea, "wasdezqugvx ")                          # lo imprimible quedó escrito

    def test_con_la_linea_abierta_retroceso_borra_y_no_lee_el_pergamino(self):
        backend = BackendQueAnota()
        controles = controles_con(backend)
        controles.procesar_evento(tecla(pygame.K_RETURN))
        _escribir(controles, "hist")
        ordenes = _teclas(controles, tecla(pygame.K_BACKSPACE), tecla(pygame.K_BACKSPACE))
        self.assertEqual(controles.linea, "hi")
        self.assertEqual(ordenes, [None, None])
        self.assertEqual(backend.otras, [])                                       # retroceder() nunca se llamó
        _teclas(controles, *[tecla(pygame.K_BACKSPACE)] * 5)                      # borrar de más no falla
        self.assertEqual(controles.linea, "")

    def test_la_linea_tiene_un_largo_maximo(self):
        controles = controles_con(BackendQueAnota())
        controles.procesar_evento(tecla(pygame.K_RETURN))
        _escribir(controles, "a" * 200)
        self.assertEqual(len(controles.linea), LARGO_MAXIMO_LINEA)

    def test_esc_cierra_primero_el_panel_de_historia_y_despues_pide_la_pausa(self):
        controles = controles_con(BackendQueAnota())
        controles.procesar_comando("historia 3")
        self.assertIsNotNone(controles.resumen)
        self.assertIsNone(controles.procesar_evento(tecla(pygame.K_ESCAPE)))      # cierra el panel: sin pausa
        self.assertIsNone(controles.resumen)
        self.assertEqual(controles.procesar_evento(tecla(pygame.K_ESCAPE)), PIDE_PAUSA)

    def test_una_accion_del_jugador_cierra_el_panel_y_la_consulta_no_toca_el_estado_vivo(self):
        controles = controles_con(BackendQueAnota())
        estado = controles.estado
        controles.procesar_comando("historia 3")
        self.assertIs(controles.estado, estado)                                    # el panel no toca el estado vivo
        controles._aplicar(estado)                                                 # una acción del jugador
        self.assertIsNone(controles.resumen)

    def test_fr423_en_el_controlador_de_pygame_la_linea_y_el_panel_llegan_a_la_vista(self):
        with Entorno() as e:
            e.al_juego()
            self.assertIsNone(e.pantalla().linea_comandos)
            e.pulsar(pygame.K_RETURN)
            self.assertEqual(e.pantalla().linea_comandos, "")
            activaciones = e.pantalla().activaciones
            e.escribir("historia 0")
            self.assertEqual(e.pantalla().linea_comandos, "historia 0")
            self.assertEqual(e.pantalla().activaciones, activaciones)             # escribir no cuenta como esperar ni suena
            e.pulsar(pygame.K_RETURN)
            pantalla = e.pantalla()
            self.assertIsNone(pantalla.linea_comandos)
            self.assertIsNotNone(pantalla.resumen)
            self.assertEqual((pantalla.resumen.reloj, pantalla.resumen.sala_id), (0, 1))
            self.assertEqual(pantalla.pantalla, "juego")
            e.pulsar(pygame.K_ESCAPE)                                              # cierra el panel
            self.assertIsNone(e.pantalla().resumen)
            self.assertEqual(e.pantalla().pantalla, "juego")                       # sin pausar
            e.pulsar(pygame.K_ESCAPE)
            self.assertEqual(e.pantalla().pantalla, "pausa")                       # el siguiente Esc sí

    def test_fr423_un_comando_mal_escrito_en_la_linea_deja_el_aviso_de_uso(self):
        with Entorno() as e:
            e.al_juego()
            e.pulsar(pygame.K_RETURN)
            e.escribir("historia abc")
            e.pulsar(pygame.K_RETURN)
            self.assertEqual(e.pantalla().aviso, MENSAJE_USO_HISTORIA)
            self.assertIsNone(e.pantalla().resumen)


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
