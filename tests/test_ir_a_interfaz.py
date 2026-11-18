"""
«ir a» de punta a punta con la interfaz (feature 002, integrante 3; FR-250, FR-258, FR-260 a FR-262): la línea de comandos de
ControlesJuego, el ControladorPygame real (con un reloj propio que fija cuándo se da cada paso) y la VistaPygame real dibujando
cada cuadro, sobre una partida real de una cuadrícula de 5 × 5 salas sin enemigos («Sala 1» … «Sala 25»).
"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import letra, pygame, tecla  # noqa: E402  (fija SDL_VIDEODRIVER=dummy antes de importar pygame)
from ayudas_vista import ENTER, ESC  # noqa: E402
from ayudas_controladores import crear_backend  # noqa: E402

import UIController.ControladorPygame as modulo  # noqa: E402
from Data.BitacoraReplayIO import BitacoraReplayIO  # noqa: E402
from DTO.ConfiguracionDTO import ConfiguracionDTO  # noqa: E402
from Service.ServicioAccionJugador import ServicioAccionJugador  # noqa: E402
from Service.ServicioReplay import ServicioReplay  # noqa: E402
from UIController.ControladorPygame import PASO_VIAJE_MS, ControladorPygame  # noqa: E402
from UIController.ControlesJuego import MENSAJE_USO_IR_A, ControlesJuego  # noqa: E402
from View.HudJuego import lineas_de_mensajes  # noqa: E402
from View.VistaPygame import VistaPygame  # noqa: E402
from tests.ayudas_ir_a import servicio_partida_cuadricula  # noqa: E402
from tests.ayudas_mapa import estados  # noqa: E402

ESTE, SUR, OESTE, NORTE = pygame.K_d, pygame.K_s, pygame.K_a, pygame.K_w


class Reloj:
    def __init__(self):
        self.ahora = 0

    def leer(self):
        return self.ahora


class Entorno:

    def __init__(self):
        self.carpeta = tempfile.mkdtemp()
        self.ruta_original = modulo.RUTA_GUARDADO
        modulo.RUTA_GUARDADO = os.path.join(self.carpeta, "saves", "partida.sav")
        self.vista = VistaPygame()
        self.vista.abrir()
        self.reloj = Reloj()
        self.backends = []
        self.controlador = ControladorPygame(self.vista, ConfiguracionDTO(offline=True, forzar=True), self._fabrica,
                                             reloj_ms=self.reloj.leer)
        for codigo in (ENTER, ENTER):
            self.pulsar(codigo)
        self.escribir("Ana")
        self.pulsar(ENTER)

    def _fabrica(self, config):
        partida = servicio_partida_cuadricula(self.carpeta)
        backend = crear_backend(self.carpeta, config, partida=partida)
        self.backends.append(backend)
        return backend

    def cerrar(self):
        modulo.RUTA_GUARDADO = self.ruta_original
        self.vista.cerrar()
        shutil.rmtree(self.carpeta, ignore_errors=True)

    @property
    def backend(self):
        return [b for b in self.backends if b.hay_partida()][-1]

    @property
    def contexto(self):
        return self.backend._contexto

    def pulsar(self, *codigos):
        for codigo in codigos:
            self.controlador.procesar_evento(tecla(codigo))

    def escribir(self, texto):
        for caracter in texto:
            self.controlador.procesar_evento(letra(caracter))

    def comando(self, texto):
        self.pulsar(ENTER)
        self.escribir(texto)
        self.pulsar(ENTER)

    def pantalla(self):
        return self.controlador.pantalla()

    def sala(self):
        return self.pantalla().estado.sala.id

    def tick(self):
        self.reloj.ahora += PASO_VIAJE_MS
        self.controlador.avanzar_viaje()
        pantalla = self.pantalla()
        self.vista.dibujar(pantalla)
        return pantalla

    def viajar(self, maximo=40):
        salas = []
        for _ in range(maximo):
            if not self.controlador._juego.viajando:
                return salas
            salas.append(self.tick().estado.sala.id)
        raise AssertionError("el viaje no se detuvo")

    def mensajes(self):
        return lineas_de_mensajes(self.pantalla().estado.mensajes)


class ConEntorno(unittest.TestCase):

    def setUp(self):
        self.e = Entorno()
        self.addCleanup(self.e.cerrar)

    def caminar_hasta_la_sala_25(self):
        self.e.pulsar(*([ESTE] * 4 + [SUR] * 4))
        self.assertEqual(self.e.sala(), 25)


class PruebasElViajeSeVe(ConEntorno):

    def test_ir_a_lleva_a_la_sala_un_paso_por_cuadro_y_el_motivo_queda_en_el_panel(self):
        self.caminar_hasta_la_sala_25()
        reloj = self.e.pantalla().estado.reloj
        self.e.comando("ir a Sala 1")
        self.assertTrue(self.e.controlador._juego.viajando)
        self.assertEqual(self.e.sala(), 25)                                     # la orden no da ningún paso por sí sola
        self.assertEqual(self.e.pantalla().estado.reloj, reloj)
        self.e.controlador.avanzar_viaje()                                      # el primer paso sale en el primer cuadro
        primero = self.e.sala()
        self.assertNotEqual(primero, 25)
        self.e.controlador.avanzar_viaje()                                      # sin pasar el tiempo entre pasos, no hay otro
        self.assertEqual(self.e.sala(), primero)
        salas = [primero] + self.e.viajar()
        self.assertEqual(len(salas), 8)                                         # ocho salas, de una en una
        self.assertEqual(salas[-1], 1)
        for anterior, siguiente in zip([25] + salas, salas):
            self.assertEqual(abs(anterior - siguiente) in (1, 5), True)         # cada paso cambia a una sala vecina
        self.assertEqual(self.e.pantalla().estado.reloj, reloj + 800)           # cada paso gastó el tiempo de su salida
        self.assertIn("Llegaste a Sala 1.", self.e.mensajes()[-1])
        self.assertFalse(self.e.controlador._juego.viajando)
        self.e.comando("IR   A  sala 25")                                       # mayúsculas y espacios sobrantes valen
        self.assertEqual(self.e.viajar()[-1], 25)
        self.assertIn("Llegaste a Sala 25.", self.e.mensajes()[-1])

    def test_las_ordenes_rechazadas_se_muestran_como_aviso_y_no_gastan_tiempo(self):
        self.e.pulsar(ESTE)
        antes = (self.e.pantalla().estado.reloj, self.e.sala(), self.e.contexto.jugador.acciones)
        avisos = []
        for texto in ("ir a Sala 99", "ir a Sala 3", "ir a Sala 2", "ir a", "ir a    "):
            self.e.comando(texto)
            pantalla = self.e.pantalla()
            avisos.append(pantalla.aviso)
            self.assertIsNotNone(pantalla.aviso, texto)
            self.assertFalse(self.e.controlador._juego.viajando, texto)
            self.assertEqual((pantalla.estado.reloj, pantalla.estado.sala.id, self.e.contexto.jugador.acciones), antes, texto)
        self.assertEqual(avisos[0], avisos[1])                                  # inexistente y avistada: el mismo mensaje
        self.assertNotEqual(avisos[0], avisos[2])                               # «ya estás aquí» es otro
        self.assertEqual(avisos[3], MENSAJE_USO_IR_A)
        self.assertNotIn("# ir a", self._log())

    def _log(self):
        with open(self.e.contexto.bitacora.ruta(), encoding="utf-8", newline="") as archivo:
            return archivo.read()

    def test_sin_ruta_conocida_el_viaje_se_detiene_y_lo_dice(self):
        self.e.pulsar(*([ESTE] * 4))                                            # solo la fila 1 explorada
        mazmorra = self.e.contexto.mazmorra
        mazmorra.salida(3, 2).cerrada = True                                    # la puerta 3–4 se cierra «a escondidas»
        mazmorra.salida(4, 3).cerrada = True
        self.e.comando("ir a Sala 1")
        salas = self.e.viajar()
        self.assertEqual(salas, [4, 4])                                         # llega a 4; el cuadro siguiente ve la puerta y para
        self.assertIn("sin ruta conocida a Sala 1", self.e.mensajes()[-1])
        self.assertEqual(self.e.contexto.jugador.acciones, 5)

    def test_con_una_puerta_cerrada_recordada_rodea_por_otra_ruta(self):
        self.e.pulsar(*([ESTE] * 4 + [SUR] + [OESTE] * 4))                      # filas 1 y 2 exploradas; termina en la Sala 6
        self.assertEqual(self.e.sala(), 6)
        mazmorra = self.e.contexto.mazmorra
        mazmorra.salida(3, 2).cerrada = True
        mazmorra.salida(4, 3).cerrada = True
        self.e.comando("ir a Sala 5")
        salas = self.e.viajar()
        self.assertEqual(salas[:3], [1, 2, 3])                                  # empieza por la vecina de menor id
        self.assertEqual(salas[3:], [8, 9, 4, 5])                               # en la 3 ve la puerta cerrada y rodea por la fila 2
        self.assertEqual(salas.index(8), salas.index(3) + 1)                    # de la 3 a la 8, no de la 3 a la 4
        self.assertIn("Llegaste a Sala 5.", self.e.mensajes()[-1])


class PruebasElBucle(ConEntorno):

    def test_el_bucle_principal_da_un_paso_por_intervalo_hasta_llegar(self):
        self.caminar_hasta_la_sala_25()
        self.e.comando("ir a Sala 1")
        salas = []
        llamadas = [0]

        def eventos():
            llamadas[0] += 1
            salas.append(self.e.sala())
            self.e.reloj.ahora += PASO_VIAJE_MS
            if not self.e.controlador._juego.viajando or llamadas[0] > 60:
                return [pygame.event.Event(pygame.QUIT)]
            return []

        self.e.controlador.ejecutar(eventos)
        self.assertEqual(self.e.sala(), 1)
        cambios = [b for a, b in zip(salas, salas[1:]) if a != b]
        self.assertEqual(len(cambios), 8)                                       # una sala distinta por intervalo
        self.assertIn("Llegaste a Sala 1.", self.e.mensajes()[-1])


class PruebasInterrumpirElViaje(ConEntorno):

    def empezar(self):
        self.caminar_hasta_la_sala_25()
        self.e.comando("ir a Sala 1")
        self.e.tick()
        self.e.tick()
        self.assertTrue(self.e.controlador._juego.viajando)
        return self.e.sala()

    def test_esc_corta_el_viaje_sin_pausar_el_juego(self):
        donde = self.empezar()
        reloj = self.e.pantalla().estado.reloj
        self.e.pulsar(ESC)
        pantalla = self.e.pantalla()
        self.assertEqual(pantalla.pantalla, "juego")                            # Esc cortó el viaje, no abrió la pausa
        self.assertFalse(self.e.controlador._juego.viajando)
        self.assertIn("Viaje interrumpido.", self.e.mensajes()[-1])
        for _ in range(3):
            self.e.tick()
        self.assertEqual((self.e.sala(), self.e.pantalla().estado.reloj), (donde, reloj))
        self.assertIsNone(self.e.backend._viaje)
        self.e.pulsar(ESC)
        self.assertEqual(self.e.pantalla().pantalla, "pausa")                   # sin viaje, Esc vuelve a pedir la pausa

    def test_otra_orden_corta_el_viaje_y_se_ejecuta(self):
        donde = self.empezar()
        reloj = self.e.pantalla().estado.reloj
        self.e.pulsar(pygame.K_z)                                               # esperar
        self.assertFalse(self.e.controlador._juego.viajando)
        self.assertEqual(self.e.pantalla().estado.reloj, reloj + 100)           # la orden sí se ejecutó
        self.assertIn("Viaje interrumpido.", self.e.mensajes()[-1])
        for _ in range(3):
            self.e.tick()
        self.assertEqual(self.e.sala(), donde)

    def test_un_movimiento_a_mano_corta_el_viaje_y_se_mueve(self):
        donde = self.empezar()
        self.e.pulsar(ESTE if donde % 5 != 0 else OESTE)
        self.assertFalse(self.e.controlador._juego.viajando)
        self.assertNotEqual(self.e.sala(), donde)
        despues = self.e.sala()
        self.e.tick()
        self.assertEqual(self.e.sala(), despues)


class PruebasElRegistro(ConEntorno):

    def test_el_log_trae_el_comentario_y_se_reproduce_igual(self):
        self.caminar_hasta_la_sala_25()
        self.e.comando("ir a Sala 1")
        self.e.viajar()
        self.e.comando("ir a Sala 25")
        self.e.viajar()
        ruta = self.e.contexto.bitacora.ruta()
        with open(ruta, encoding="utf-8", newline="") as archivo:
            lineas = archivo.read().split("\n")
        self.assertEqual([l for l in lineas if l.startswith("# ")], ["# ir a Sala 1", "# ir a Sala 25"])
        leido = BitacoraReplayIO.leer(ruta)
        self.assertEqual(len(leido.acciones), 8 + 8 + 8)                        # los pasos, uno por uno; la orden no cuenta
        self.assertTrue(all(accion.tipo == "mover" for accion in leido.acciones))
        vivo = self.e.contexto
        esperado = (vivo.motor.reloj, vivo.jugador.Sala_Actual, estados(vivo.motor.mapa), vivo.jugador.a_dto())
        resultado = ServicioReplay(servicio_partida_cuadricula(self.e.carpeta)).reproducir(ruta)
        self.assertEqual((resultado.estado_final.reloj, resultado.estado_final.sala.id), (esperado[0], esperado[1]))
        replay = servicio_partida_cuadricula(self.e.carpeta).iniciar_partida(
            "cuadricula", "Replay", semilla=leido.encabezado.semilla, registrar_bitacora=False)
        servicio = ServicioAccionJugador()
        for accion in leido.acciones:
            servicio.ejecutar(replay, accion)
        self.assertEqual((replay.motor.reloj, replay.jugador.Sala_Actual, estados(replay.motor.mapa),
                          replay.jugador.a_dto()), esperado)


class PruebasLosControles(unittest.TestCase):

    def test_solo_ir_a_con_un_destino_es_el_comando(self):
        from UIController.ControlesJuego import _destino_de_ir_a
        self.assertEqual(_destino_de_ir_a("ir a Sala 25"), "Sala 25")
        self.assertEqual(_destino_de_ir_a("  IR A   Pasillo  de las urnas "), "Pasillo  de las urnas")   # no colapsa espacios
        self.assertEqual(_destino_de_ir_a("ir a"), "")
        for texto in ("irA sala", "ir al norte", "ir", "historia 3", "mapa", "ira a", "", "a ir Sala"):
            self.assertIsNone(_destino_de_ir_a(texto), texto)


if __name__ == "__main__":
    unittest.main()
