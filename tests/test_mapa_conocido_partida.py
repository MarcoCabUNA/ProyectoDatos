"""
Pruebas de la historia 4 en Logic (feature 002, integrante 2): con el HistorialRetroceso real, el pergamino deja el
mapa exactamente como antes de la acción (FR-222, NFR-203), sin copiar el mapa.

Excepción documentada al «falla primero» (Principio X, T023): estos escenarios usan código que ya llegó en T012 (la
reversión por casilla), T015 y T021, así que pueden pasar desde que se escriben.

T031: la variante con el motor (leer un pergamino); falla hasta T033.
T040: guardar y cargar el mapa con PartidaGuardada (H4-3) y los puntos de control con su mapa; fallan hasta T040.
T041: el replay da el mismo mapa (H4-5) y la misma partida da el mismo mapa en cada acción (SC-205). Excepción
documentada al «falla primero»: pasan por el código de T033 y T040, así que pueden pasar desde que se escriben.
T042: `historia #4` muestra el mapa de ese instante (H4-4), con guarda hasta T118 del integrante 3.
"""
import dataclasses
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from Data import GuardadoBinario  # noqa: E402
from DTO.CriptaDTO import CriptaDTO  # noqa: E402
from DTO.ObjetoDTO import ObjetoDTO  # noqa: E402
from Logic.Efectos import Antorcha  # noqa: E402
from Logic.HistorialRetroceso import HistorialRetroceso  # noqa: E402
from Logic.PartidaGuardada import PartidaGuardada  # noqa: E402
from tests.ayudas_mapa import (A, B, C, D, E, ESTE, NORTE, SUR, cripta_mapa, entrar_a, estados,  # noqa: E402
                               mapa_de_prueba, motor_con_inventario, salida)
from tests.ayudas_terreno import LLAVE_FINAL, salidas_con_costos  # noqa: E402

# Constantes del mapa con sus valores de data-model §1.
DESCONOCIDA, AVISTADA, EXPLORADA = 0, 1, 2
SIN_OBSERVAR, ABIERTA, CERRADA = 0, 1, 2


SALIDAS_H4 = [salida(A, ESTE, B), salida(A, SUR, D), salida(B, SUR, C), salida(B, NORTE, D), salida(C, ESTE, E)]


def cripta_h4():
    """A –E– B, A –S– D, B –S– C, B –N– D, C –E– E. Salas 1..5."""
    return cripta_mapa(5, SALIDAS_H4)


class PruebasPergamino(unittest.TestCase):

    def setUp(self):
        self.mazmorra = cripta_h4()
        self.historial = HistorialRetroceso()
        self.mapa, self.jugador = mapa_de_prueba(self.mazmorra, A, self.historial)
        self.mapa.iniciar(A)
        self.historial.descartar_intervalo_abierto()       # como la preparación del motor

    def test_h4_1_apendiceB_caso5_fr222_pergamino_revierte_entrada_con_antorcha(self):
        self.assertEqual(self.mapa.estado_sala(B), AVISTADA)
        self.assertEqual(self.mapa.estado_sala(C), DESCONOCIDA)
        self.assertEqual(self.mapa.estado_sala(D), AVISTADA)
        antes = estados(self.mapa)
        entrar_a(self.mapa, self.jugador, B, True)
        for sala in (B, C, D):
            self.assertEqual(self.mapa.estado_sala(sala), EXPLORADA)
        self.historial.cerrar_intervalo()
        self.assertTrue(self.historial.deshacer())
        self.assertEqual(self.mapa.estado_sala(B), AVISTADA)
        self.assertEqual(self.mapa.estado_sala(C), DESCONOCIDA)
        self.assertEqual(self.mapa.estado_sala(D), AVISTADA)
        self.assertEqual(estados(self.mapa), antes)

    def test_h4_2_a8_fr222_pergamino_revierte_la_observacion(self):
        entrar_a(self.mapa, self.jugador, B)
        self.historial.cerrar_intervalo()
        entrar_a(self.mapa, self.jugador, A)
        self.historial.cerrar_intervalo()
        self.assertEqual(self.mapa.estado_cara(B, SUR), ABIERTA)
        self.mazmorra.salida(B, SUR).cerrada = True             # se cierra lejos del jugador
        self.mazmorra.salida(C, NORTE).cerrada = True
        entrar_a(self.mapa, self.jugador, B)
        self.assertEqual(self.mapa.estado_cara(B, SUR), CERRADA)
        self.historial.cerrar_intervalo()
        self.historial.deshacer()
        self.assertEqual(self.mapa.estado_cara(B, SUR), ABIERTA)
        self.assertEqual(self.mapa.estado_cara(C, NORTE), ABIERTA)

    def test_fr222_pergaminos_seguidos(self):
        inicial = estados(self.mapa)
        entrar_a(self.mapa, self.jugador, B)
        self.historial.cerrar_intervalo()
        despues_de_b = estados(self.mapa)
        entrar_a(self.mapa, self.jugador, C, True)
        self.historial.cerrar_intervalo()
        self.assertEqual(self.mapa.estado_sala(E), EXPLORADA)
        self.historial.deshacer()
        self.assertEqual(estados(self.mapa), despues_de_b)
        self.historial.deshacer()
        self.assertEqual(estados(self.mapa), inicial)

    def test_fr222_pergamino_sin_cambios_del_mapa(self):
        entrar_a(self.mapa, self.jugador, B)
        self.historial.cerrar_intervalo()
        entrar_a(self.mapa, self.jugador, A)                   # ya explorada y puertas iguales: no cambia nada
        self.historial.cerrar_intervalo()
        antes = estados(self.mapa)
        self.assertTrue(self.historial.deshacer())
        self.assertEqual(estados(self.mapa), antes)

    def test_fr222_iniciar_no_se_deshace(self):
        self.assertFalse(self.historial.deshacer())             # el conocimiento inicial se descartó
        self.assertEqual(self.mapa.estado_sala(A), EXPLORADA)
        entrar_a(self.mapa, self.jugador, B)
        self.historial.cerrar_intervalo()
        self.assertTrue(self.historial.deshacer())
        self.assertFalse(self.historial.deshacer())
        self.assertEqual(self.mapa.estado_sala(A), EXPLORADA)
        self.assertEqual(self.mapa.estado_sala(B), AVISTADA)
        self.assertEqual(self.mapa.estado_cara(A, ESTE), ABIERTA)
        self.assertEqual(self.mapa.estado_sala(C), DESCONOCIDA)


ANTORCHA, PERGAMINO = "itm_antorcha", "itm_pergamino"


class PruebasPergaminoConMotor(unittest.TestCase):
    """T031, historia 4 con el motor: leer un pergamino revierte el mapa junto con la posición y el reloj."""

    def test_h4_1_apendiceB_caso5_fr222_motor_leer_pergamino(self):
        objetos = [ObjetoDTO(ANTORCHA, "Antorcha", "antorcha", 1, 5, duracion=1000),
                   ObjetoDTO(PERGAMINO, "Pergamino", "pergamino_retroceso", 1, 5)]
        motor, _ = motor_con_inventario(cripta_h4(), A, objetos)
        motor.iniciar()
        motor.avanzar_hasta_jugador()
        self.assertEqual(motor.usar(ANTORCHA), "ok")
        motor.avanzar_hasta_jugador()
        antes = (estados(motor.mapa), motor.jugador.Sala_Actual, motor.reloj)
        self.assertEqual(motor.mapa.estado_sala(C), DESCONOCIDA)
        self.assertEqual(motor.mover_jugador(ESTE), "ok")        # entra a B con la antorcha encendida
        motor.avanzar_hasta_jugador()
        for sala in (B, C, D):
            self.assertEqual(motor.mapa.estado_sala(sala), EXPLORADA, f"sala {sala}")
        self.assertEqual(motor.usar(PERGAMINO), "ok")
        self.assertEqual((estados(motor.mapa), motor.jugador.Sala_Actual, motor.reloj), antes)
        self.assertEqual(motor.mapa.estado_sala(B), AVISTADA)
        self.assertEqual(motor.mapa.estado_sala(C), DESCONOCIDA)


def cripta_dto_h4(sala_inicial: int) -> CriptaDTO:
    """El CriptaDTO de cripta_h4, con los mismos datos que motor_con, para guardar y cargar con PartidaGuardada."""
    return CriptaDTO(id="c-mapa", version="1", salas_total=5, paginas=1, salas_por_pagina=50,
                     sala_inicial=sala_inicial, sala_salida=E, llave_salida=LLAVE_FINAL, presupuesto_solicitudes=10,
                     inventario_max=5, jugador_vida_max=30, jugador_ataque=5, jugador_defensa=2,
                     jugador_velocidad=100)


def cargar_h4(partida, salas):
    """PartidaGuardada.cargar sobre el esqueleto de cripta_h4 (no hay fichas que pedir)."""
    return PartidaGuardada.cargar(partida, salas, cripta_dto_h4(A), salidas_con_costos(5, SALIDAS_H4),
                                  lambda id_ficha: None)


class PruebasGuardadoConMotor(unittest.TestCase):
    """T040: PartidaGuardada guarda y carga el mapa (FR-221) y los puntos de control lo llevan (FR-223)."""

    def motor_h4(self):
        motor, _ = motor_con_inventario(cripta_h4(), A)
        motor.iniciar()
        motor.avanzar_hasta_jugador()
        return motor

    def mover(self, motor, direccion):
        self.assertEqual(motor.mover_jugador(direccion), "ok")
        motor.avanzar_hasta_jugador()

    def test_h4_3_a7_fr221_guardar_y_cargar_conserva_el_mapa(self):
        motor = self.motor_h4()
        motor.efectos.aplicar(Antorcha(motor.jugador, 1000))
        self.mover(motor, ESTE)                                  # B por entrada; C y D por la antorcha
        self.mover(motor, 3)                                     # de vuelta a A
        motor.mazmorra.salida(B, SUR).cerrada = True             # B–C se cierra lejos del jugador
        motor.mazmorra.salida(C, NORTE).cerrada = True
        self.assertEqual(motor.mapa.estado_cara(B, SUR), ABIERTA)    # recordada distinta del real
        original = estados(motor.mapa)
        partida, salas = PartidaGuardada.guardar(motor, cripta_dto_h4(A), "cat-1", 1)
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "partida.sav")
            GuardadoBinario.guardar(ruta, partida, salas)
            cargado = cargar_h4(GuardadoBinario.cargar(ruta), GuardadoBinario.cargar_salas(ruta))
        self.assertEqual(estados(cargado.mapa), original)       # casilla por casilla
        for sala in (A, B, C, D):
            self.assertEqual(cargado.mapa.estado_sala(sala), EXPLORADA, f"sala {sala}")
        self.assertTrue(cargado.mazmorra.salida(B, SUR).cerrada)
        self.assertEqual(cargado.mapa.estado_cara(B, SUR), ABIERTA)
        self.assertEqual(cargado.historial.cantidad(), 0)

    def test_fr221_cargar_con_mapa_none_deja_el_mapa_inicial_desde_la_sala_del_jugador(self):
        motor = self.motor_h4()
        self.mover(motor, ESTE)                                  # el jugador queda en B (la «sala X»)
        partida, salas = PartidaGuardada.guardar(motor, cripta_dto_h4(A), "cat-1", 1)
        partida = dataclasses.replace(partida, mapa=None)        # un DTO armado a mano, sin mapa (riesgo R-9)
        cargado = cargar_h4(partida, salas)                      # no lanza error
        nuevo, _ = mapa_de_prueba(cargado.mazmorra, B)
        nuevo.iniciar(B)
        self.assertEqual(estados(cargado.mapa), estados(nuevo))  # como FR-202 con B como sala de inicio
        self.assertEqual(cargado.mapa.estado_sala(B), EXPLORADA)
        for sala in (A, C, D):                                   # A estaba explorada: ahora solo avistada
            self.assertEqual(cargado.mapa.estado_sala(sala), AVISTADA, f"sala {sala}")
        self.assertEqual(cargado.mapa.estado_sala(E), DESCONOCIDA)
        for d in (NORTE, SUR, 3):
            self.assertEqual(cargado.mapa.estado_cara(B, d), ABIERTA)
        antes = estados(cargado.mapa)
        self.assertFalse(cargado.historial.deshacer())           # deshacer no lo revierte
        self.assertEqual(estados(cargado.mapa), antes)

    def test_fr223_punto_de_control_lleva_el_mapa(self):
        carpeta_tests = os.path.join(RAIZ, "tests")
        if carpeta_tests not in sys.path:
            sys.path.insert(0, carpeta_tests)
        from test_servicios import _crear, _elegir_accion
        from Service.ReconstructorEstado import ReconstructorEstado
        from Service.ServicioLineaTiempo import ServicioLineaTiempo
        with tempfile.TemporaryDirectory() as carpeta:
            servicio, _, ctx = _crear(carpeta, semilla=11, reforzar=True)
            ctx.linea.puntos = []                                # reforzar cambió al jugador después del punto 0:
            ServicioLineaTiempo.tomar_punto(ctx)                 # se vuelve a tomar, para que la re-simulación coincida
            linea = ServicioLineaTiempo()
            mapas = [ctx.motor.mapa.a_guardado()]                # el mapa con k acciones hechas, en mapas[k]
            estado = servicio.estado(ctx)
            x = 11
            while len(mapas) <= 3 * ctx.linea.k and not estado.terminado:
                x = (x * 1103515245 + 12345) % 2147483648
                antes = ctx.jugador.acciones
                estado = linea.ejecutar(ctx, _elegir_accion(estado, x))
                if ctx.jugador.acciones == antes + 1:
                    mapas.append(ctx.motor.mapa.a_guardado())
            self.assertGreaterEqual(len(ctx.linea.puntos), 2)
            for punto in ctx.linea.puntos:
                with self.subTest(punto=punto.acciones_completadas):
                    self.assertIsNotNone(punto.partida.mapa)
                    self.assertEqual(punto.partida.mapa, mapas[punto.acciones_completadas])
            for k in range(1, len(mapas)):                       # un Motor rearmado desde un punto trae ese mapa
                with self.subTest(accion=k):
                    motor = ReconstructorEstado(ctx).hasta_accion(k)
                    self.assertEqual(motor.mapa.a_guardado(), mapas[k - 1])
            self.assertTrue(any(m != mapas[0] for m in mapas))   # el mapa sí cambió en el camino


def guion_cripta_01():
    """
    Acciones de una partida de la cripta-01 del paquete offline (antorcha en la sala 1, llave de bronce en la 3,
    pergamino en la 5): 1 → 2 sin antorcha; la enciende en 2; 2 → 3 con antorcha; abre 2–5 y va a 5 por el
    pergamino; 5 → 2 → 3 → 4 (entrar a 4 con antorcha explora la 6); lee el pergamino (revierte esa entrada) y vuelve
    a entrar a 4.
    """
    from DTO.AccionDTO import AccionDTO
    norte, sur, este, oeste = 0, 1, 2, 3
    return [AccionDTO("recoger", objeto="itm_antorcha"), AccionDTO("mover", norte),
            AccionDTO("usar", objeto="itm_antorcha"), AccionDTO("mover", norte),
            AccionDTO("recoger", objeto="itm_llave_bronce"), AccionDTO("mover", sur), AccionDTO("abrir", este),
            AccionDTO("mover", este), AccionDTO("recoger", objeto="itm_pergamino_retroceso"),
            AccionDTO("mover", oeste), AccionDTO("mover", norte), AccionDTO("mover", norte),
            AccionDTO("retroceder"), AccionDTO("mover", norte), AccionDTO("esperar")]


def importar_ayudas_linea_tiempo():
    """tests/ayudas_linea_tiempo.py y tests/test_servicio_replay_hasta.py (de la 004) se importan sin el prefijo tests."""
    carpeta_tests = os.path.join(RAIZ, "tests")
    if carpeta_tests not in sys.path:
        sys.path.insert(0, carpeta_tests)
    import ayudas_linea_tiempo
    import test_servicio_replay_hasta
    return ayudas_linea_tiempo, test_servicio_replay_hasta


class PruebasReplayYMismaPartida(unittest.TestCase):
    """T041: H4-5 (FR-224) y SC-205. No necesitan código nuevo: pasan por el mismo motor (research R6)."""

    def jugar_guion(self, ctx):
        """
        Juega guion_cripta_01 por ServicioLineaTiempo (como el Controlador). Devuelve (por_accion, linea): el mapa
        después de cada acción hecha, en el orden del log, y la línea de tiempo vigente [(reloj, mapa)], que
        empieza en el instante 0 y pierde la entrada que revierte el pergamino.
        """
        from Service.ServicioLineaTiempo import ServicioLineaTiempo
        servicio = ServicioLineaTiempo()
        por_accion = []
        linea = [(ctx.motor.reloj, estados(ctx.motor.mapa))]
        hubo_antorcha = [False, False]
        for accion in guion_cripta_01():
            if accion.tipo == "mover":
                hubo_antorcha[ctx.motor.efectos.tiene(ctx.jugador, "antorcha")] = True
            estado = servicio.ejecutar(ctx, accion)
            self.assertIsNone(estado.resultado, f"{accion} fue rechazada")
            por_accion.append(estados(ctx.motor.mapa))
            if accion.tipo == "retroceder":
                revertida = linea.pop()
                self.assertNotEqual(revertida[1], linea[-1][1])  # el pergamino sí revierte un cambio del mapa
                self.assertEqual((ctx.motor.reloj, estados(ctx.motor.mapa)), linea[-1])
            else:
                linea.append((ctx.motor.reloj, estados(ctx.motor.mapa)))
        self.assertEqual(hubo_antorcha, [True, True])            # entradas sin y con antorcha
        return por_accion, linea

    def test_h4_5_a10_fr224_replay_da_el_mismo_mapa(self):
        from unittest import mock
        from DTO.ConfiguracionDTO import ConfiguracionDTO
        from Service.ArmadorResumen import ArmadorResumen
        from Service.ServicioPartida import ServicioPartida
        from Service.ServicioReplay import ServicioReplay
        ayudas, replay_hasta = importar_ayudas_linea_tiempo()

        def prueba(carpeta):
            _, ctx = ayudas.partida_de_prueba(os.path.join(carpeta, "origen"), semilla=7)
            por_accion, linea = self.jugar_guion(ctx)
            ruta = replay_hasta.con_comentarios_ir_a(ctx.bitacora.ruta())     # con líneas «# ir a <sala>»
            with open(ruta, encoding="utf-8") as archivo:
                self.assertIn("# ir a", archivo.read())

            # --replay: ServicioReplay completo, mirando el mapa del motor reproducido después de cada acción
            partida = ServicioPartida(ConfiguracionDTO(offline=True),
                                      fuente=ayudas.FuenteReforzada(os.path.join(RAIZ, "paquete")),
                                      carpeta_cache=os.path.join(carpeta, "c"), carpeta_logs=os.path.join(carpeta, "l"))
            contextos = []
            iniciar = partida.iniciar_partida

            def iniciar_y_anotar(*args, **kwargs):
                contexto = iniciar(*args, **kwargs)
                contextos.append(contexto)
                return contexto
            partida.iniciar_partida = iniciar_y_anotar
            reproducidos = []
            ServicioReplay(partida).reproducir(
                ruta, al_avanzar=lambda numero, accion, estado: reproducidos.append(estados(contextos[0].motor.mapa)))
            self.assertEqual(reproducidos, por_accion)

            # --replay … --hasta t: el motor que arma el resumen de cada instante de la línea vigente
            servicio = replay_hasta.servicio_para_reproducir(os.path.join(carpeta, "replay"), reforzado=True)
            armar = ArmadorResumen.armar
            vistos = []

            def armar_y_anotar(motor, *args, **kwargs):
                vistos.append(estados(motor.mapa))
                return armar(motor, *args, **kwargs)
            with mock.patch.object(ArmadorResumen, "armar", staticmethod(armar_y_anotar)):
                for t, mapa in linea:
                    with self.subTest(t=t):
                        servicio.reproducir_hasta(ruta, t)
                        self.assertEqual(vistos[-1], mapa)
        ayudas._correr(prueba)

    def test_sc205_misma_partida_mismo_mapa_en_cada_accion(self):
        ayudas, _ = importar_ayudas_linea_tiempo()

        def prueba(carpeta):
            ejecuciones = []
            for i in range(2):                                   # misma cripta, semilla y acciones
                _, ctx = ayudas.partida_de_prueba(os.path.join(carpeta, str(i)), semilla=7)
                por_accion, _ = self.jugar_guion(ctx)
                mapas = list(por_accion)
                ayudas.jugar(ctx, 40, al_decidir=lambda estado: mapas.append(estados(ctx.motor.mapa)))
                mapas.append(estados(ctx.motor.mapa))
                ejecuciones.append(mapas)
            self.assertGreater(len(ejecuciones[0]), len(guion_cripta_01()) + 10)   # el guion y varias más
            self.assertEqual(len(ejecuciones[0]), len(ejecuciones[1]))
            for i in range(len(ejecuciones[0])):                 # casilla por casilla, en cada acción
                self.assertEqual(ejecuciones[0][i], ejecuciones[1][i], f"acción {i}")
        ayudas._correr(prueba)


class PruebasHistoriaConMapa(unittest.TestCase):
    """T042: el resumen de `historia #k` trae el mapa conocido de ese instante (FR-223; 004 FR-405)."""

    def test_h4_4_a9_fr223_historia_muestra_el_mapa_de_ese_instante(self):
        from DTO.AccionDTO import AccionDTO
        from DTO.MapaConocidoDTO import MapaConocidoDTO
        from Service.ServicioLineaTiempo import ServicioLineaTiempo
        ayudas, _ = importar_ayudas_linea_tiempo()
        norte = 0
        sala_a, sala_b = 1, 2                                    # en la cripta-01: A = la entrada (1), B = la 2

        def prueba(carpeta):
            _, ctx = ayudas.partida_de_prueba(carpeta, semilla=7)
            ayudas.dar_pergaminos(ctx, 1)
            servicio = ServicioLineaTiempo()
            # La acción 4 primero entra a B y el pergamino la revierte: no debe aparecer en la historia.
            for accion in (AccionDTO("recoger", objeto="itm_antorcha"), AccionDTO("esperar"), AccionDTO("esperar"),
                           AccionDTO("mover", norte), AccionDTO("retroceder"),
                           AccionDTO("esperar"), AccionDTO("esperar"), AccionDTO("mover", norte)):
                self.assertIsNone(servicio.ejecutar(ctx, accion).resultado, f"{accion} fue rechazada")
            self.assertEqual(ctx.jugador.acciones, 6)
            self.assertTrue(ctx.motor.mapa.es_explorada(sala_b))      # en la acción 6 explora B
            from Service.ReconstructorEstado import ReconstructorEstado
            antes_de_la_4 = ReconstructorEstado(ctx).hasta_accion(4)     # el motor aparte de `historia #4`
            self.assertFalse(antes_de_la_4.mapa.es_explorada(sala_b))    # ya sin guarda: el mapa de ese instante
            resumen = servicio.consultar_por_accion(ctx, 4)
            if resumen.mapa_conocido is None:
                self.skipTest("pendiente: T118 del integrante 3 (ServicioLineaTiempo pasa motor.mapa.a_dto())")
            self.assertEqual(resumen.sala_id, sala_a)                # en la acción 4 el jugador está en A
            mapa = resumen.mapa_conocido
            self.assertIsInstance(mapa, MapaConocidoDTO)
            self.assertEqual([s.id for s in mapa.salas], [sala_a])   # B no está entre las exploradas
            self.assertIsNone(mapa.salas[0].salidas[norte].destino)  # la salida hacia B: avistada, sin id
        ayudas._correr(prueba)


if __name__ == "__main__":
    unittest.main()
