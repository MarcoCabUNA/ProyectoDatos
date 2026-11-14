"""
Pruebas de la feature 001: terreno con costo por salida y enemigo cazador.

Una prueba por escenario de aceptación de spec.md, con el escenario y el FR en el nombre (Principio X).

    python -m unittest tests.test_terreno_cazador -v
"""
import copy
import os
import random
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.Direcciones import E, N, O, S  # noqa: E402
from DTO.ObjetoDTO import ObjetoDTO  # noqa: E402
from Data.ValidacionDatos import ErrorDatos  # noqa: E402
from DTO.AccionDTO import AccionDTO  # noqa: E402
from DTO.ConfiguracionDTO import ConfiguracionDTO  # noqa: E402
from Logic.BusquedaCostoMinimo import paso_desde_cero  # noqa: E402
from Logic.Comportamientos import Cazador, Errante, crear_comportamiento  # noqa: E402
from Logic.Enemigo import Enemigo  # noqa: E402
from Logic.Inventario import Inventario  # noqa: E402
from Logic.Mazmorra import CierrePuerta, Mazmorra  # noqa: E402
from Service.ServicioAccionJugador import ServicioAccionJugador  # noqa: E402
from Service.ServicioPartida import ServicioPartida  # noqa: E402
from tests.TestValidacionDatos import CAZADOR, SIN_RANGO, api_con_cazador, api_con_costos  # noqa: E402
from tests.Utilidades import ID_CRIPTA, ApiFalsa, fuente_red, pagina_real  # noqa: E402
from tests.ayudas_terreno import (ID_CAZADOR_SIN_RANGO, ID_ENEMIGO_BOTIN_INVALIDO,  # noqa: E402
                                  ID_OBJETO_DURACION_INVALIDA, LLAVE_FINAL, FuenteConBotinInvalido,
                                  FuenteConFichaInvalida, FuenteConObjetoInvalido,
                                  cuadricula_con_costos, ficha_cazador, ficha_errante, ficha_rastreador,
                                  mazmorra_con_costos, motor_con, poner_enemigo, salida)


def turno_del_jugador(motor):
    """Inicia la partida y avanza hasta el primer turno del jugador (t = 0)."""
    motor.iniciar()
    motor.avanzar_hasta_jugador()
    return motor


def siguiente_accion(actor) -> int:
    """El instante de la siguiente acción programada del actor."""
    assert actor.Evento_pendiente is not None
    return actor.Evento_pendiente.tiempo


class TestTerreno(unittest.TestCase):
    """Historia 1: el terreno cuesta distinto (escenarios H1-1 a H1-9)."""

    def test_h1_1_fr102_salida_costo_250(self):
        motor, _ = motor_con(mazmorra_con_costos(2, [salida(1, E, 2, 250)]), 1)
        turno_del_jugador(motor)
        self.assertEqual(motor.mover_jugador(E), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 250)

    def test_h1_2_fr101_salida_sin_costo_vale_100(self):
        motor, _ = motor_con(mazmorra_con_costos(2, [salida(1, E, 2)]), 1)
        turno_del_jugador(motor)
        self.assertEqual(motor.mover_jugador(E), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 100)

    def test_h1_3_fr101_mismo_costo_en_ambos_sentidos(self):
        motor, _ = motor_con(mazmorra_con_costos(2, [salida(1, E, 2, 250)]), 2)
        turno_del_jugador(motor)
        self.assertEqual(motor.mover_jugador(O), "ok")
        self.assertEqual(motor.jugador.Sala_Actual, 1)
        self.assertEqual(siguiente_accion(motor.jugador), 250)

    def test_h1_4_apendiceB_caso6_fr102_intervalo_minimo_1(self):
        motor, _ = motor_con(mazmorra_con_costos(2, [salida(1, E, 2, 1)]), 1)
        motor.jugador.velocidad = 300
        turno_del_jugador(motor)
        self.assertEqual(motor.mover_jugador(E), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 1)     # max(1, 1 * 100 // 300) = 1, nunca 0

    def test_h1_5_apendiceB_caso7_fr105_cambio_de_velocidad(self):
        motor, _ = motor_con(mazmorra_con_costos(2, [salida(1, E, 2, 400)]), 1)
        turno_del_jugador(motor)
        self.assertEqual(motor.mover_jugador(E), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 400)
        motor.reloj = 100                                        # el reloj llega a t = 100 (P1 §2.3)
        motor.cambiar_velocidad(motor.jugador, 200)
        # max(1, (400 - 100) * 100 // 200) = 150 -> t = 250
        self.assertEqual(siguiente_accion(motor.jugador), 250)

    def test_h1_6_fr103_otras_acciones_conservan_costo(self):
        salidas_caras = [salida(1, E, 2, 400), (1, O, 3, 300, 300, False)]

        motor, _ = motor_con(mazmorra_con_costos(3, salidas_caras), 1)
        poner_enemigo(motor, 1, ficha_errante(comportamiento="guardián", id="guardian", vida_max=50))
        turno_del_jugador(motor)
        self.assertEqual(motor.atacar_enemigo("e-1"), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 100)

        motor, _ = motor_con(mazmorra_con_costos(3, salidas_caras), 1)
        turno_del_jugador(motor)
        self.assertEqual(motor.esperar(), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 100)

        motor, _ = motor_con(mazmorra_con_costos(3, salidas_caras), 1)
        motor.inventario = Inventario(5)
        motor.inventario.historial = motor.historial
        motor.inventario.recoger(ObjetoDTO("pocion", "Poción", "pocion", 1, 1, cura=5))
        turno_del_jugador(motor)
        self.assertEqual(motor.usar("pocion"), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 50)

    def test_h1_7_fr104_errante_paga_la_salida_sorteada(self):
        # La única salida abierta de la sala 1 cuesta 300; el jugador está lejos, en la sala 3 (aislada).
        motor, _ = motor_con(mazmorra_con_costos(3, [salida(1, E, 2, 300)]), 3)
        errante = poner_enemigo(motor, 1, ficha_errante())
        motor.turno_enemigo(errante)                             # en t = 0
        self.assertEqual(errante.Sala_Actual, 2)
        self.assertEqual(siguiente_accion(errante), 300)

    def test_h1_8_fr101_costo_declarado_en_un_solo_lado(self):
        # Solo el lado de la sala 1 declara 250; el jugador va de 2 a 1.
        motor, _ = motor_con(mazmorra_con_costos(2, [(1, E, 2, 250, None, False)]), 2)
        turno_del_jugador(motor)
        self.assertEqual(motor.mover_jugador(O), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 250)

    def _motor_con_inventario(self):
        """Sala 1 con salidas de costo 400 (E) y 300 (O, cerrada con llave), y un inventario vacío."""
        m = mazmorra_con_costos(3, [salida(1, E, 2, 400), salida(1, O, 3, 300, cerrada=True)])
        m.salida(1, O).llave = "llave_x"
        m.salida(3, E).llave = "llave_x"
        motor, _ = motor_con(m, 1)
        motor.inventario = Inventario(5)
        motor.inventario.historial = motor.historial
        return motor

    def test_h1_9_fr103_equipar_recoger_soltar_abrir_conservan_costo(self):
        """Escenario H1-9 (FR-103): equipar 50, recoger 25, soltar 25 y abrir con llave 50, como en P1."""
        espada = ObjetoDTO("espada", "Espada", "arma", 3, 10, ataque_bonus=4)

        motor = self._motor_con_inventario()
        motor.inventario.recoger(espada)
        turno_del_jugador(motor)
        self.assertEqual(motor.equipar("espada"), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 50)

        motor = self._motor_con_inventario()
        motor.mazmorra.sala(1).objetos.append("espada")
        turno_del_jugador(motor)
        self.assertEqual(motor.recoger("espada", lambda _id: espada), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 25)

        motor = self._motor_con_inventario()
        motor.inventario.recoger(espada)
        turno_del_jugador(motor)
        self.assertEqual(motor.soltar("espada"), "ok")
        self.assertEqual(siguiente_accion(motor.jugador), 25)

        motor = self._motor_con_inventario()
        turno_del_jugador(motor)
        self.assertEqual(motor.abrir_puerta(O, lambda llave: llave == "llave_x"), "ok")
        self.assertFalse(motor.mazmorra.salida(1, O).cerrada)
        self.assertEqual(siguiente_accion(motor.jugador), 50)


class TestTerrenoComportamientos(unittest.TestCase):
    """FR-102 y FR-104: errantes, rastreadores y guardianes deciden como en P1 y pagan el costo de la salida."""

    def _sala_con_dos_salidas_a_la_misma_vecina(self):
        # Sala 1: N -> 2 (costo 300), E -> 2 (costo 100), S -> 3 (sin costo). El jugador queda aislado en la 4.
        return mazmorra_con_costos(4, [salida(1, N, 2, 300), salida(1, E, 2, 100), salida(1, S, 3)])

    def test_fr104_errante_sortea_por_salida_igual_que_p1(self):
        for semilla in range(1, 30):
            motor_p1, _ = motor_con(self._sala_con_dos_salidas_a_la_misma_vecina(), 4, semilla)
            motor_nuevo, _ = motor_con(self._sala_con_dos_salidas_a_la_misma_vecina(), 4, semilla)
            errante_p1 = poner_enemigo(motor_p1, 1, ficha_errante())
            errante_nuevo = poner_enemigo(motor_nuevo, 1, ficha_errante())
            destino = Errante().decidir(errante_p1, motor_p1)
            paso = Errante().decidir_paso(errante_nuevo, motor_nuevo)
            # Mismo índice sorteado, mismo destino y el generador queda en el mismo estado (Principio IV).
            opciones = motor_nuevo.mazmorra.salidas_abiertas_con_costo(1)
            indice = random.Random(semilla).randint(0, len(opciones) - 1)
            self.assertEqual(paso, opciones[indice])
            self.assertEqual(paso[0], destino)
            self.assertEqual(motor_nuevo.azar.getstate(), motor_p1.azar.getstate())

    def test_fr104_errante_paga_el_costo_de_la_salida_sorteada(self):
        costos_vistos = []
        for semilla in range(1, 30):
            motor, _ = motor_con(self._sala_con_dos_salidas_a_la_misma_vecina(), 4, semilla)
            errante = poner_enemigo(motor, 1, ficha_errante())
            opciones = motor.mazmorra.salidas_abiertas_con_costo(1)
            destino, costo = opciones[random.Random(semilla).randint(0, len(opciones) - 1)]
            motor.turno_enemigo(errante)
            self.assertEqual(errante.Sala_Actual, destino)
            self.assertEqual(siguiente_accion(errante), costo)
            costos_vistos.append(costo)
        # Con 29 semillas salen las dos salidas hacia la sala 2 (100 y 300), no solo la más barata.
        self.assertIn(100, costos_vistos)
        self.assertIn(300, costos_vistos)

    def test_fr104_rastreador_usa_la_salida_mas_barata(self):
        """Escenario H1-10 (FR-104): el rastreador va a la sala del rastro por la salida más barata."""
        # Dos salidas de 1 a 2 (costos 300 y 120); el rastro de la sala 2 está fresco.
        motor, _ = motor_con(mazmorra_con_costos(4, [salida(1, N, 2, 300), salida(1, E, 2, 120)]), 4)
        rastreador = poner_enemigo(motor, 1, ficha_rastreador())
        motor.rastro.marcar(2, 0)
        motor.turno_enemigo(rastreador)
        self.assertEqual(rastreador.Sala_Actual, 2)
        self.assertEqual(siguiente_accion(rastreador), 120)

    def test_fr104_guardian_no_se_mueve(self):
        """Escenario H1-11 (FR-104): el guardián no se mueve, como en P1, y espera con costo 100."""
        motor, _ = motor_con(mazmorra_con_costos(3, [salida(1, E, 2, 250)]), 3)
        guardian = poner_enemigo(motor, 1, ficha_errante(comportamiento="guardián", id="guardian"))
        self.assertIsNone(guardian.estrategia.decidir_paso(guardian, motor))
        motor.turno_enemigo(guardian)
        self.assertEqual(guardian.Sala_Actual, 1)
        self.assertEqual(siguiente_accion(guardian), 100)        # esperar cuesta 100 (FR-103)

    def test_fr102_enemigo_programa_con_costo_de_salida(self):
        # Errante de velocidad 50 por la única salida (costo 250): max(1, 250 * 100 // 50) = 500.
        motor, _ = motor_con(mazmorra_con_costos(3, [salida(1, E, 2, 250)]), 3)
        errante = poner_enemigo(motor, 1, ficha_errante(velocidad=50))
        motor.turno_enemigo(errante)
        self.assertEqual(errante.Sala_Actual, 2)
        self.assertEqual(siguiente_accion(errante), 500)


def cazador_en(motor, sala: int, rango: int | None, velocidad: int = 100, instancia: str = "c-1"):
    """Coloca y activa un cazador en 'sala'."""
    return poner_enemigo(motor, sala, ficha_cazador(rango, velocidad), instancia)


class TestCazador(unittest.TestCase):
    """Historia 2: el cazador persigue por la ruta más barata (escenarios H2-1 a H2-8)."""

    def test_h2_1_apendiceB_caso1_fr109_sin_ruta_abierta_espera(self):
        # Todas las rutas de 1 a 4 pasan por una puerta cerrada.
        m = mazmorra_con_costos(4, [salida(1, E, 2), salida(2, S, 4, cerrada=True),
                                    salida(1, S, 3), salida(3, E, 4, cerrada=True)])
        motor, _ = motor_con(m, 4)
        cazador = cazador_en(motor, 1, 10000)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 1)
        self.assertEqual(siguiente_accion(cazador), 100)

    def test_h2_2_apendiceB_caso2_fr109_d700_mayor_que_rango600_espera(self):
        motor, _ = motor_con(mazmorra_con_costos(3, [salida(1, E, 2, 400), salida(2, E, 3, 300)]), 3)
        cazador = cazador_en(motor, 1, 600)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 1)
        self.assertEqual(siguiente_accion(cazador), 100)

    def test_h2_3_apendiceB_caso3_fr110_ruta_de_mas_salas_y_menor_costo(self):
        # 1-4 directa (500) frente a 1-2, 2-3, 3-4 (100 cada una, total 300).
        m = mazmorra_con_costos(4, [salida(1, O, 4, 500), salida(1, E, 2, 100),
                                    salida(2, E, 3, 100), salida(3, S, 4, 100)])
        motor, _ = motor_con(m, 4)
        cazador = cazador_en(motor, 1, 1000)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 2)
        self.assertEqual(siguiente_accion(cazador), 100)

    def test_h2_4_apendiceB_caso4_fr111_desempate_menor_id(self):
        # Dos rutas de 200: 1-7-5 y 1-4-5. En la sala 1, la salida hacia 7 (N) aparece antes que la de 4 (S).
        m = mazmorra_con_costos(7, [salida(1, N, 7), salida(1, S, 4), salida(7, E, 5), salida(4, S, 5)])
        self.assertEqual(m.salidas_abiertas(1), [7, 4])
        motor, _ = motor_con(m, 5)
        cazador = cazador_en(motor, 1, 1000)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 4)

    def test_h2_5_fr107_misma_sala_ataca_y_no_se_mueve(self):
        motor, _ = motor_con(mazmorra_con_costos(2, [salida(1, E, 2)]), 1)
        cazador = cazador_en(motor, 1, 1000)
        vida = motor.jugador.vida
        motor.turno_enemigo(cazador)
        self.assertLess(motor.jugador.vida, vida)
        self.assertEqual(cazador.Sala_Actual, 1)
        self.assertEqual(siguiente_accion(cazador), 100)

    def test_h2_6_fr110_d_igual_a_rango_se_mueve(self):
        motor, _ = motor_con(mazmorra_con_costos(3, [salida(1, E, 2, 250), salida(2, E, 3, 350)]), 3)
        cazador = cazador_en(motor, 1, 600)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 2)
        self.assertEqual(siguiente_accion(cazador), 250)

    def test_h2_7_fr102_velocidad_120_costo_250_intervalo_208(self):
        motor, _ = motor_con(mazmorra_con_costos(3, [salida(1, E, 2, 250), salida(2, E, 3)]), 3)
        cazador = cazador_en(motor, 1, 1000, velocidad=120)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 2)
        self.assertEqual(siguiente_accion(cazador), 208)          # max(1, 250 * 100 // 120)

    def test_h2_8_fr112_ignora_contenido_no_descargado(self):
        m = mazmorra_con_costos(3, [salida(1, E, 2), salida(2, E, 3)])
        m.sala(2).contenido_cargado = False                       # la sala intermedia, nunca vista
        motor, _ = motor_con(m, 3)
        cazador = cazador_en(motor, 1, 1000)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 2)
        self.assertEqual(siguiente_accion(cazador), 100)


class TestCazadorBordes(unittest.TestCase):
    """Casos borde del cazador (FR-106, FR-108, FR-113, FR-115, FR-119 a FR-121, FR-123; H2-10 a H2-16)."""

    def test_fr113_no_abre_puertas(self):
        # La única ruta pasa por una puerta con llave; la llave está en la sala del cazador.
        m = mazmorra_con_costos(2, [salida(1, E, 2, cerrada=True)])
        m.sala(1).objetos.append("itm_llave")
        motor, _ = motor_con(m, 2)
        cazador = cazador_en(motor, 1, 1000)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 1)
        self.assertTrue(m.salida(1, E).cerrada)
        self.assertEqual(siguiente_accion(cazador), 100)

    def test_fr119_dos_salidas_misma_vecina_paga_la_mas_barata(self):
        """Escenario H2-10 (FR-119): con dos salidas hacia la sala 2 (300 y 120), d = 220 y paga 120."""
        motor, _ = motor_con(mazmorra_con_costos(3, [salida(1, N, 2, 300), salida(1, E, 2, 120),
                                                     salida(2, E, 3)]), 3)
        cazador = cazador_en(motor, 1, 1000)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 2)
        self.assertEqual(siguiente_accion(cazador), 120)

    def test_fr120_otros_actores_no_bloquean(self):
        """Escenario H2-11 (FR-120): un guardián y otro cazador en la sala 2 no le bloquean el paso."""
        motor, _ = motor_con(mazmorra_con_costos(3, [salida(1, E, 2), salida(2, E, 3)]), 3)
        poner_enemigo(motor, 2, ficha_errante(comportamiento="guardián", id="guardian"), "g-1")
        poner_enemigo(motor, 2, ficha_cazador(1000), "c-2")
        cazador = cazador_en(motor, 1, 1000)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 2)

    def test_fr121_entra_a_la_sala_y_no_ataca_en_ese_turno(self):
        """Escenario H2-12 (FR-121): entra a la sala del jugador y ataca recién en su siguiente turno."""
        motor, _ = motor_con(mazmorra_con_costos(2, [salida(1, E, 2)]), 2)
        cazador = cazador_en(motor, 1, 1000)
        vida = motor.jugador.vida
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 2)
        self.assertEqual(motor.jugador.vida, vida)                # moverse fue su acción del turno
        motor.turno_enemigo(cazador)
        self.assertLess(motor.jugador.vida, vida)                 # ataca en el siguiente

    def test_fr123_dormido_no_actua_hasta_activarse(self):
        """Escenario H2-13 (FR-123): dormido no actúa; al entrar el jugador, su primera acción queda a 100."""
        motor, _ = motor_con(mazmorra_con_costos(3, [salida(1, E, 2), salida(2, E, 3)]), 1)
        cazador = Enemigo(ficha_cazador(1000), "c-1", None, 1, 3)
        motor.mazmorra.sala(3).enemigos.append(cazador)          # colocado, sin activar
        turno_del_jugador(motor)
        for _ in range(3):
            motor.esperar()
            motor.avanzar_hasta_jugador()
        self.assertFalse(cazador.activo)
        self.assertEqual(cazador.Sala_Actual, 3)
        self.assertIsNone(cazador.Evento_pendiente)
        self.assertEqual(motor.mover_jugador(E), "ok")
        motor.avanzar_hasta_jugador()
        self.assertEqual(motor.mover_jugador(E), "ok")            # entra a la sala 3: se activa (P1 §2.4)
        self.assertTrue(cazador.activo)
        self.assertEqual(siguiente_accion(cazador), motor.reloj + 100)

    def test_rango_0_solo_ataca_en_la_misma_sala(self):
        motor, _ = motor_con(mazmorra_con_costos(2, [salida(1, E, 2, 1)]), 2)
        cazador = cazador_en(motor, 1, 0)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 1)                  # toda ruta cuesta al menos 1
        motor.jugador.Sala_Actual = 1
        vida = motor.jugador.vida
        motor.turno_enemigo(cazador)
        self.assertLess(motor.jugador.vida, vida)

    def test_fr115_decidir_no_consume_el_generador(self):
        """Escenario H2-14, primera parte (FR-115): moverse o esperar no consume el generador."""
        # Se mueve:
        motor, _ = motor_con(mazmorra_con_costos(3, [salida(1, E, 2), salida(2, E, 3)]), 3)
        cazador = cazador_en(motor, 1, 1000)
        antes = motor.azar.getstate()
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 2)
        self.assertEqual(motor.azar.getstate(), antes)
        # Espera:
        motor, _ = motor_con(mazmorra_con_costos(3, [salida(1, E, 2), salida(2, E, 3)]), 3)
        cazador = cazador_en(motor, 1, 100)
        antes = motor.azar.getstate()
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 1)
        self.assertEqual(motor.azar.getstate(), antes)

    def test_h2_14_fr115_ataque_usa_la_formula_de_p1(self):
        """
        Escenario H2-14, segunda parte (FR-115, P1 §2.6): el ataque del cazador consume el generador igual que
        el de cualquier enemigo. Con la misma semilla, el daño y el estado del generador son los mismos que los
        de un errante con los mismos atributos, y dos partidas iguales dan el mismo daño.
        """
        resultados = []
        for ficha in (ficha_cazador(1000), ficha_errante(), ficha_cazador(1000)):
            motor, _ = motor_con(mazmorra_con_costos(2, [salida(1, E, 2)]), 1, semilla=7)
            enemigo = poner_enemigo(motor, 1, ficha)
            antes = motor.azar.getstate()
            vida = motor.jugador.vida
            motor.turno_enemigo(enemigo)
            self.assertNotEqual(motor.azar.getstate(), antes)      # el ataque sí usa el generador
            resultados.append((vida - motor.jugador.vida, motor.azar.getstate()))
        cazador, errante, cazador_otra_vez = resultados
        self.assertGreaterEqual(cazador[0], 1)                     # max(1, ...) de la fórmula de P1
        self.assertEqual(cazador, errante)
        self.assertEqual(cazador, cazador_otra_vez)

    def test_h2_15_fr108_puerta_abierta_con_llave_cuenta_como_abierta(self):
        """Escenario H2-15 (FR-108): una puerta que el jugador abrió con llave forma parte de la ruta."""
        m = mazmorra_con_costos(2, [salida(1, E, 2, cerrada=True)])
        m.salida(1, E).llave = "llave_x"
        m.salida(2, O).llave = "llave_x"
        motor, _ = motor_con(m, 2)
        cazador = cazador_en(motor, 1, 1000)
        self.assertIsNone(cazador.estrategia.decidir_paso(cazador, motor))   # antes de abrir: espera
        turno_del_jugador(motor)
        self.assertEqual(motor.abrir_puerta(O, lambda llave: llave == "llave_x"), "ok")
        self.assertEqual(paso_desde_cero(motor.grafo, 2, 1, 1000), (2, 100))
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 2)

    def test_fr106_crear_comportamiento_cazador(self):
        self.assertIsInstance(crear_comportamiento("cazador"), Cazador)

    def _cierre_en_el_mismo_instante(self, cierre_primero: bool):
        # Cazador en 1, jugador en 3; la única ruta es 1-2-3. Un cierre automático de 1-2 en t = 100,
        # el mismo instante del primer turno del cazador.
        m = mazmorra_con_costos(3, [salida(1, E, 2), salida(2, E, 3)])
        motor, _ = motor_con(m, 3)
        turno_del_jugador(motor)
        cierre = CierrePuerta([m.salida(1, E), m.salida(2, O)])
        if cierre_primero:
            motor.programar_efecto(100, "cierre_puerta", cierre)
            cazador = cazador_en(motor, 1, 1000)
        else:
            cazador = cazador_en(motor, 1, 1000)
            motor.programar_efecto(100, "cierre_puerta", cierre)
        esperado_antes = paso_desde_cero(motor.grafo, 3, 1, 1000)
        motor.esperar()
        motor.avanzar_hasta_jugador()                            # t = 100: cierre, cazador y jugador
        return motor, cazador, esperado_antes

    def test_fr108_cierre_automatico_en_el_mismo_instante(self):
        """
        Escenario H2-16 (FR-108): cierre automático y turno del cazador en el mismo t se atienden en el orden
        en que se programaron. Cierre programado antes: espera. Programado después: se mueve.
        """
        # El cierre va primero en el orden de eventos de P1 §2.3: al decidir, la puerta ya está cerrada.
        motor, cazador, _ = self._cierre_en_el_mismo_instante(cierre_primero=True)
        self.assertEqual(motor.reloj, 100)
        self.assertEqual(cazador.Sala_Actual, 1)
        self.assertIsNone(paso_desde_cero(motor.grafo, 3, 1, 1000))
        # El cierre va después: al decidir, la puerta seguía abierta.
        motor, cazador, esperado_antes = self._cierre_en_el_mismo_instante(cierre_primero=False)
        self.assertEqual(esperado_antes, (2, 100))
        self.assertEqual(cazador.Sala_Actual, 2)
        self.assertTrue(motor.mazmorra.salida(1, E).cerrada)


class TestDatosInvalidos(unittest.TestCase):
    """FR-122, escenarios H2-9 y H2-17 a H2-22: datos inválidos de terreno, de cazador, de objeto y de botín."""

    def test_h2_9_fr122_ficha_invalida_rechaza_entrar(self):
        """
        Escenario H2-9 (FR-122, T054). Con FuenteConFichaInvalida (devuelve la ficha del cazador de una sala sin
        `rango`, no lanza el error: Data la rechaza con ErrorDatos y recuerda la sala) y
        ServicioPartida(..., fuente=esa_fuente):
          1. la precarga llega y la partida sigue: el jugador actúa en otras salas y el cazador no se activa;
          2. intentar entrar a esa sala se rechaza con un mensaje que nombra la ficha y el campo `rango`,
             el jugador sigue en su sala y el reloj no avanza;
          3. la partida sigue: el jugador puede hacer otra acción;
          4. ese `mover` no queda en partida.log;
          5. un segundo intento da el mismo mensaje sin una solicitud nueva.
        """
        # Cuadrícula de 3 x 3: la sala inicial es la 1; la 2 (la del cazador sin `rango`) queda al este y la 4 al sur.
        fuente = FuenteConFichaInvalida(3, sala_cazador=2)
        acciones = ServicioAccionJugador()
        with tempfile.TemporaryDirectory() as carpeta:
            partida = ServicioPartida(ConfiguracionDTO(), fuente=fuente,
                                      carpeta_cache=os.path.join(carpeta, "cache"),
                                      carpeta_logs=os.path.join(carpeta, "logs"))
            ctx = partida.iniciar_partida("cuadricula", "Ana", semilla=1)

            # 1. La precarga trajo la sala 2 y la ficha del cazador, y la partida sigue: el jugador actúa en otras
            #    salas y el cazador no se activa (no está en ninguna sala del juego).
            self.assertTrue(any(2 in lote for lote in fuente.lotes))
            self.assertTrue(any(ID_CAZADOR_SIN_RANGO in lote for lote in fuente.catalogos))
            for direccion, destino in ((S, 4), (N, 1)):
                estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=direccion))
                self.assertIsNone(estado.resultado)
                self.assertEqual(estado.sala.id, destino)
            self.assertFalse(any(e.ficha.id == ID_CAZADOR_SIN_RANGO
                                 for sala in ctx.mazmorra.salas if sala is not None for e in sala.enemigos))

            # 2. Entrar a la sala 2 se rechaza con el error de datos (ficha y campo `rango`), no con el de red;
            #    el jugador sigue en la sala 1 y el reloj no avanza.
            reloj, escritas = ctx.motor.reloj, ctx.bitacora.acciones_escritas()
            lotes, catalogos = len(fuente.lotes), len(fuente.catalogos)
            estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=E))
            mensaje = estado.resultado
            self.assertIsNotNone(mensaje)
            self.assertIn(ID_CAZADOR_SIN_RANGO, mensaje)
            self.assertIn("rango", mensaje)
            self.assertFalse(mensaje.startswith("Sin conexión"))
            self.assertEqual(estado.sala.id, 1)
            self.assertEqual(estado.reloj, reloj)

            # 5. Un segundo intento da el mismo mensaje sin una solicitud nueva (ni de contenido ni de catálogo).
            estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=E))
            self.assertEqual(estado.resultado, mensaje)
            self.assertEqual(estado.sala.id, 1)
            self.assertEqual(estado.reloj, reloj)
            self.assertEqual((len(fuente.lotes), len(fuente.catalogos)), (lotes, catalogos))

            # 3. La partida sigue: el jugador puede hacer otra acción.
            estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=S))
            self.assertIsNone(estado.resultado)
            self.assertEqual(estado.sala.id, 4)

            # 4. Ninguno de los dos `mover` hacia la sala 2 quedó en partida.log; sí los tres que se hicieron (S, N, S).
            self.assertEqual(ctx.bitacora.acciones_escritas(), escritas + 1)
            with open(ctx.bitacora.ruta(), encoding="utf-8") as log:
                lineas = log.read().splitlines()
            self.assertNotIn(AccionDTO("mover", direccion=E).a_linea(), lineas)
            self.assertEqual(lineas.count(AccionDTO("mover", direccion=S).a_linea()), 2)

    def test_h2_17_fr122_costo_invalido_no_inicia(self):
        """
        Escenario H2-17 (FR-122): un esqueleto con una salida de costo 0, "250" o true no deja iniciar la partida;
        el error indica la sala, la dirección y el campo `costo`, y el programa no se cae.
        """
        for costo in (0, "250", True):
            with self.subTest(costo=costo):
                error = _no_inicia(self, api_con_costos([(2, "N", costo)]))
                for texto in ("sala 2", "salida N", "costo", repr(costo)):
                    self.assertIn(texto, error)

    def test_h2_18_fr122_costos_distintos_entre_caras_no_inicia(self):
        """
        Escenario H2-18 (FR-101, FR-122): la salida 1-2 con 100 del lado de la sala 1 y 250 del lado de la sala 2
        no deja iniciar la partida; el error indica esa salida y el campo `costo`.
        """
        # En cripta-01, la salida N de la sala 1 y la S de la sala 2 son las dos caras de la misma puerta.
        error = _no_inicia(self, api_con_costos([(1, "N", 100), (2, "S", 250)]))
        for texto in ("sala 1", "salida N", "100", "sala 2", "salida S", "250", "costo"):
            self.assertIn(texto, error)

    def test_h2_19_fr122_ficha_invalida_en_la_sala_inicial_no_inicia(self):
        """
        Escenario H2-19 (FR-122): la ficha de un cazador de la sala inicial sin `rango` o con `rango` -1 no deja
        iniciar la partida; el error indica esa ficha y el campo `rango`.
        """
        for rango in (SIN_RANGO, -1):
            with self.subTest(rango=rango):
                error = _no_inicia(self, api_con_cazador(1, rango))    # la sala 1 es la inicial de cripta-01
                self.assertIn(CAZADOR, error)
                self.assertIn("rango", error)

    def test_h2_20_fr122_cierre_automatico_invalido_no_inicia(self):
        """
        Escenario H2-20 (FR-122, T056): un esqueleto con una salida cuyo `cierre_automatico` es 0, -5, "10" o true
        no deja iniciar la partida; el error indica la sala, la dirección y el campo, y el programa no se cae.
        La parte de `--forzar` (003 FR-323) se agrega cuando exista la spec 003, como en H3-7.
        """
        for cierre in (0, -5, "10", True):
            with self.subTest(cierre_automatico=cierre):
                error = _no_inicia(self, _api_con_cierre_automatico(2, "N", cierre))
                for texto in ("sala 2", "salida N", "cierre_automatico", repr(cierre)):
                    self.assertIn(texto, error)

    def test_h2_21_fr122_duracion_invalida_deja_la_sala_sin_contenido(self):
        """
        Escenario H2-21 (FR-122, T056): con FuenteConObjetoInvalido (una poción con `duracion` 0, -5, "10" o true en
        la sala 2, que no es la inicial), la partida inicia y entrar a la sala 2 se rechaza con un mensaje que nombra
        la ficha y el campo `duracion`; el jugador sigue en la sala 1, el reloj no avanza y la partida sigue.
        """
        for duracion in (0, -5, "10", True):
            with self.subTest(duracion=duracion):
                fuente = FuenteConObjetoInvalido(3, sala_objeto=2, duracion=duracion)
                acciones = ServicioAccionJugador()
                with tempfile.TemporaryDirectory() as carpeta:
                    partida = ServicioPartida(ConfiguracionDTO(), fuente=fuente,
                                              carpeta_cache=os.path.join(carpeta, "cache"),
                                              carpeta_logs=os.path.join(carpeta, "logs"))
                    ctx = partida.iniciar_partida("cuadricula", "Ana", semilla=1)
                    reloj = ctx.motor.reloj

                    estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=E))
                    mensaje = estado.resultado
                    self.assertIsNotNone(mensaje)
                    self.assertIn(ID_OBJETO_DURACION_INVALIDA, mensaje)
                    self.assertIn("duracion", mensaje)
                    self.assertFalse(mensaje.startswith("Sin conexión"))
                    self.assertEqual(estado.sala.id, 1)
                    self.assertEqual(estado.reloj, reloj)

                    # La partida sigue: el jugador puede moverse a otra sala.
                    estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=S))
                    self.assertIsNone(estado.resultado)
                    self.assertEqual(estado.sala.id, 4)

    def test_h2_22_fr122_botin_invalido_deja_la_sala_sin_contenido(self):
        """
        Escenario H2-22 (FR-122, T057): con FuenteConBotinInvalido, un errante cuya `suelta` trae una poción con
        `duracion` 0, -5, "10" o true. En la sala 2 (no inicial), la partida inicia y entrar a la sala 2 se rechaza
        con un mensaje que nombra la ficha del enemigo, el campo `suelta` y la ficha rechazada; el jugador sigue
        en la sala 1, el reloj no avanza y la partida sigue. En la sala 1 (la inicial), la partida no inicia.
        """
        self.skipTest("pendiente de T057 (integrante 2): Data todavía no rechaza un enemigo por su suelta")
        acciones = ServicioAccionJugador()
        for duracion in (0, -5, "10", True):
            with self.subTest(sala="no inicial", duracion=duracion):
                with tempfile.TemporaryDirectory() as carpeta:
                    partida = _partida_con(FuenteConBotinInvalido(3, sala_enemigo=2, duracion=duracion), carpeta)
                    ctx = partida.iniciar_partida("cuadricula", "Ana", semilla=1)
                    reloj = ctx.motor.reloj

                    estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=E))
                    mensaje = estado.resultado
                    self.assertIsNotNone(mensaje)
                    for texto in (ID_ENEMIGO_BOTIN_INVALIDO, "suelta", ID_OBJETO_DURACION_INVALIDA):
                        self.assertIn(texto, mensaje)
                    self.assertFalse(mensaje.startswith("Sin conexión"))
                    self.assertEqual(estado.sala.id, 1)
                    self.assertEqual(estado.reloj, reloj)

                    estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=S))
                    self.assertIsNone(estado.resultado)
                    self.assertEqual(estado.sala.id, 4)

            with self.subTest(sala="inicial", duracion=duracion):
                with tempfile.TemporaryDirectory() as carpeta:
                    partida = _partida_con(FuenteConBotinInvalido(3, sala_enemigo=1, duracion=duracion), carpeta)
                    with self.assertRaises(ErrorDatos) as error:
                        partida.iniciar_partida("cuadricula", "Ana", semilla=1)
                    for texto in (ID_ENEMIGO_BOTIN_INVALIDO, "suelta", ID_OBJETO_DURACION_INVALIDA):
                        self.assertIn(texto, str(error.exception))
                    self.assertFalse(os.path.isdir(os.path.join(carpeta, "logs")))    # no se creó partida.log


def _partida_con(fuente, carpeta: str) -> ServicioPartida:
    """Un ServicioPartida con esa fuente y la caché y los logs dentro de 'carpeta' (H2-22)."""
    return ServicioPartida(ConfiguracionDTO(), fuente=fuente, carpeta_cache=os.path.join(carpeta, "cache"),
                           carpeta_logs=os.path.join(carpeta, "logs"))


def _api_con_cierre_automatico(id_sala: int, direccion: str, cierre):
    """La cripta real con un `cierre_automatico` en la salida 'direccion' de la sala 'id_sala' (H2-20)."""
    pagina = copy.deepcopy(pagina_real())
    for sala in pagina["salas"]:
        if sala["id"] == id_sala:
            sala["salidas"][direccion]["cierre_automatico"] = cierre
    return ApiFalsa(paginas={ID_CRIPTA: [pagina]})


def _no_inicia(prueba: unittest.TestCase, api) -> str:
    """Intenta iniciar cripta-01 con esa ApiFalsa; comprueba que no inicia con ErrorDatos y devuelve el mensaje."""
    with tempfile.TemporaryDirectory() as carpeta:
        partida = ServicioPartida(ConfiguracionDTO(), fuente=fuente_red(api),
                                  carpeta_cache=os.path.join(carpeta, "cache"),
                                  carpeta_logs=os.path.join(carpeta, "logs"))
        with prueba.assertRaises(ErrorDatos) as ctx:
            partida.iniciar_partida(ID_CRIPTA, "Ana", semilla=1)
        prueba.assertFalse(os.path.isdir(os.path.join(carpeta, "logs")))    # no se creó ningún partida.log
    return str(ctx.exception)


class TestDeterminismo(unittest.TestCase):
    """FR-115, escenario H3-6 y SC-103: misma semilla y mismas acciones, misma partida."""

    def test_h3_6_fr115_misma_semilla_misma_partida(self):
        """
        Escenario H3-6 (FR-115): la misma cripta, la misma semilla y la misma secuencia de acciones, jugadas dos
        veces, dan los mismos mensajes y, después de cada acción, el mismo reloj y las mismas salas y vidas.
        """
        for semilla in (3, 11, 27):
            with self.subTest(semilla=semilla):
                primera = _partida_guionada(semilla, rango_cazadores=1000)
                self.assertEqual(primera, _partida_guionada(semilla, rango_cazadores=1000))
                mensajes, traza = primera
                self.assertTrue(any("ataca" in m for m in mensajes))      # hubo combate (consume el azar)
                self.assertNotEqual(traza[0][2], traza[-1][2])           # los enemigos se movieron

    def test_sc103_cazadores_no_cambian_lo_que_eligen_los_errantes(self):
        """
        SC-103 (FR-115): con cazadores que deciden en cada turno pero nunca atacan (rango 0, lejos del jugador,
        que solo espera), las salas que eligen los errantes son las mismas con y sin cazadores.
        """
        for semilla in (3, 11, 27):
            with self.subTest(semilla=semilla):
                _, sin = _partida_guionada(semilla, rango_cazadores=None, solo_esperar=True)
                _, con = _partida_guionada(semilla, rango_cazadores=0, solo_esperar=True)
                self.assertEqual([_errantes(paso) for paso in con], [_errantes(paso) for paso in sin])
                self.assertNotEqual(_errantes(sin[0]), _errantes(sin[-1]))   # los errantes sí se movieron


def _partida_guionada(semilla: int, rango_cazadores: int | None, solo_esperar: bool = False):
    """
    Cuadrícula de 5 x 5 con costos, el jugador en la 1, tres errantes y, si rango_cazadores no es None, tres
    cazadores con ese rango. 60 acciones del jugador sacadas de un generador propio del guion (no del motor).
    Devuelve (mensajes, traza): por acción, (reloj, sala del jugador, ((id, sala, vida) de cada enemigo)).
    """
    salas = cuadricula_con_costos(5, random.Random(semilla))
    mazmorra = Mazmorra(sala_salida=25, llave_salida=LLAVE_FINAL)
    mazmorra.cargar_esqueleto(salas)
    for sala in salas:
        mazmorra.sala(sala.id).contenido_cargado = True
    motor, mensajes = motor_con(mazmorra, 1, semilla)
    motor.jugador.vida = motor.jugador.vida_Max = 100000
    motor.iniciar()
    enemigos = [poner_enemigo(motor, sala, ficha_errante(), f"e-{i}", numero=i)
                for i, sala in ((1, 7), (2, 13), (3, 19))]
    if rango_cazadores is not None:
        enemigos += [poner_enemigo(motor, sala, ficha_cazador(rango_cazadores), f"e-{i}", numero=i)
                     for i, sala in ((4, 5), (5, 21), (6, 25))]
    guion = random.Random(1000 + semilla)
    traza = []
    motor.avanzar_hasta_jugador()
    for _ in range(60):
        if motor.terminado:
            break
        direccion = guion.randrange(5)
        if solo_esperar or direccion == 4 or motor.mover_jugador(direccion) != "ok":
            motor.esperar()
        motor.avanzar_hasta_jugador()
        traza.append((motor.reloj, motor.jugador.Sala_Actual,
                      tuple((e.id, e.Sala_Actual, e.vida) for e in enemigos)))
    return list(mensajes), traza


def _errantes(paso) -> tuple:
    """(id, sala) de los errantes (e-1 a e-3) en un paso de la traza."""
    return tuple((id_enemigo, sala) for id_enemigo, sala, _ in paso[2] if id_enemigo in ("e-1", "e-2", "e-3"))


class TestModosSinVista(unittest.TestCase):
    """FR-118, escenarios H3-7 y H3-8: las reglas de terreno y del cazador en los modos sin vista."""

    def test_h3_7_fr118_fr122_verificar_no_depende_de_costos_ni_cazadores(self):
        """
        Escenario H3-7 (FR-118, FR-122; 003 FR-302 y FR-314): `--verificar` carga un esqueleto con costos válidos
        sin error, y su veredicto y su orden de llaves no dependen de los costos ni de los cazadores. Con un error
        de datos de FR-122 (costo inválido o distinto entre caras), la verificación no concluye y el programa
        termina con código 1, sin caerse ni instanciar la vista.
        """
        self.skipTest("pendiente de la spec 003-resolubilidad: `--verificar` todavía no existe")

    def test_h3_8_fr118_bench_aplica_las_mismas_reglas(self):
        """
        Escenario H3-8 (FR-118): en `--bench`, con cuadrículas con costos y cazadores, cada decisión de cazador
        coincide con un cálculo desde cero y la medición corre sin vista.
        """
        import re
        import subprocess
        from Logic import BenchRutas

        # Las mediciones con cazadores comparan cada decisión con paso_desde_cero y fallan si alguna difiere.
        ciclo = BenchRutas.medir_ciclo_cazadores((4,), lado=8, otros=2, ciclos=3, ciclos_comprobados=40)
        for r in ciclo:
            comprobadas = int(re.search(r"(\d+) decisiones de cazador comprobadas contra paso_desde_cero",
                                        r.nota).group(1))
            self.assertGreater(comprobadas, 0, r.nota)
        for r in BenchRutas.medir_compartida((5,), lado=8, ciclos=10, repeticiones=1)[1:]:
            self.assertIn("decisiones iguales a paso_desde_cero", r.nota)
        for r in BenchRutas.medir_invalidacion(cazadores=5, lado=8, ciclos=20, repeticiones=1):
            self.assertIn("decisiones iguales a recalcular siempre", r.nota)

        # Sin vista: el bench de rutas no carga la Vista ni pygame (Principio V).
        codigo = ("import sys; from Logic import BenchLogica, BenchRutas; "
                  "BenchRutas.medir_ciclo_cazadores((2,), lado=6, otros=1, ciclos=2, ciclos_comprobados=2); "
                  "print(any(m == 'pygame' or m.startswith(('pygame.', 'View')) for m in sys.modules))")
        salida = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, capture_output=True, text=True, check=True)
        self.assertEqual(salida.stdout.strip(), "False")


if __name__ == "__main__":
    unittest.main()
