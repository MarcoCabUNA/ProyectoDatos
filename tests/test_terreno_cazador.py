"""
Pruebas de la feature 001: terreno con costo por salida y enemigo cazador.

Una prueba por escenario de aceptación de spec.md, con el escenario y el FR en el nombre (Principio X).

    python -m unittest tests.test_terreno_cazador -v
"""
import os
import random
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.Direcciones import E, N, O, S  # noqa: E402
from DTO.ObjetoDTO import ObjetoDTO  # noqa: E402
from Logic.BusquedaCostoMinimo import paso_desde_cero  # noqa: E402
from Logic.Comportamientos import Cazador, Errante, crear_comportamiento  # noqa: E402
from Logic.Enemigo import Enemigo  # noqa: E402
from Logic.Inventario import Inventario  # noqa: E402
from Logic.Mazmorra import CierrePuerta  # noqa: E402
from tests.ayudas_terreno import (ficha_cazador, ficha_errante, ficha_rastreador,  # noqa: E402
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
    """Historia 1: el terreno cuesta distinto (escenarios H1-1 a H1-8)."""

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
        # Dos salidas de 1 a 2 (costos 300 y 120); el rastro de la sala 2 está fresco.
        motor, _ = motor_con(mazmorra_con_costos(4, [salida(1, N, 2, 300), salida(1, E, 2, 120)]), 4)
        rastreador = poner_enemigo(motor, 1, ficha_rastreador())
        motor.rastro.marcar(2, 0)
        motor.turno_enemigo(rastreador)
        self.assertEqual(rastreador.Sala_Actual, 2)
        self.assertEqual(siguiente_accion(rastreador), 120)

    def test_fr104_guardian_no_se_mueve(self):
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
    """Casos borde del cazador (FR-106, FR-108, FR-113, FR-115, FR-119 a FR-121, FR-123)."""

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
        motor, _ = motor_con(mazmorra_con_costos(3, [salida(1, N, 2, 300), salida(1, E, 2, 120),
                                                     salida(2, E, 3)]), 3)
        cazador = cazador_en(motor, 1, 1000)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 2)
        self.assertEqual(siguiente_accion(cazador), 120)

    def test_fr120_otros_actores_no_bloquean(self):
        motor, _ = motor_con(mazmorra_con_costos(3, [salida(1, E, 2), salida(2, E, 3)]), 3)
        poner_enemigo(motor, 2, ficha_errante(comportamiento="guardián", id="guardian"), "g-1")
        poner_enemigo(motor, 2, ficha_cazador(1000), "c-2")
        cazador = cazador_en(motor, 1, 1000)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 2)

    def test_fr121_entra_a_la_sala_y_no_ataca_en_ese_turno(self):
        motor, _ = motor_con(mazmorra_con_costos(2, [salida(1, E, 2)]), 2)
        cazador = cazador_en(motor, 1, 1000)
        vida = motor.jugador.vida
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 2)
        self.assertEqual(motor.jugador.vida, vida)                # moverse fue su acción del turno
        motor.turno_enemigo(cazador)
        self.assertLess(motor.jugador.vida, vida)                 # ataca en el siguiente

    def test_fr123_dormido_no_actua_hasta_activarse(self):
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


if __name__ == "__main__":
    unittest.main()
