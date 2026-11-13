"""
Pruebas de Motor.avanzar_hasta(t) (feature 004, T011/T012; contrato §3, FR-401, FR-402).

Usan el motor sintético de tests/ayudas_terreno.py con los eventos programados a mano en t = 300 (o 400):
dos salas conectadas por una puerta, el jugador en la sala 1 y, según la prueba, un enemigo errante que
ataca, una puerta que se cierra sola, un efecto que expira o un veneno.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ayudas_terreno import ficha_errante, mazmorra_con_costos, motor_con, poner_enemigo, salida
from Logic.Efectos import Antorcha, Veneno
from Logic.EventoPorg import EventoProgramado
from Logic.Mazmorra import CierrePuerta
from Logic.motorJuego import Motor


def _escenario(semilla: int = 1) -> Motor:
    """Dos salas (1 al oeste de 2) unidas por una puerta; el jugador en la sala 1 con el control en t = 0."""
    mazmorra = mazmorra_con_costos(2, [salida(1, 2, 2, 100)])
    motor, _mensajes = motor_con(mazmorra, 1, semilla)
    motor.iniciar()
    motor.avanzar_hasta_jugador()
    return motor


def _en(motor: Motor, tiempo: int, tipo: str, dueno: object) -> EventoProgramado:
    """Programa a mano un evento en el instante `tiempo`."""
    return motor.cola.programar(EventoProgramado(tiempo, tipo, dueno))


def _enemigo_en(motor: Motor, tiempo: int):
    """Un enemigo errante en la sala del jugador cuya primera acción cae exactamente en `tiempo`."""
    enemigo = poner_enemigo(motor, 1, ficha_errante())
    enemigo.Evento_pendiente.cancelar()
    enemigo.Evento_pendiente = _en(motor, tiempo, "accion_actor", enemigo)
    return enemigo


def _puerta(motor: Motor) -> list:
    """Las dos caras de la puerta entre las salas 1 y 2."""
    return [motor.mazmorra.sala(1).salidas[2], motor.mazmorra.sala(2).salidas[3]]


class PruebasAvanzarHasta(unittest.TestCase):

    def test_h1_2_apendiceB_caso3_fr402(self):
        motor = _escenario()
        motor.programar_accion(motor.jugador, 500)                    # la próxima decisión del jugador es en 500
        _enemigo_en(motor, 300)                                       # un enemigo ataca en 300
        caras = _puerta(motor)
        _en(motor, 300, "cierre_puerta", CierrePuerta(caras))         # una puerta se cierra sola en 300
        motor.efectos.aplicar(Antorcha(motor.jugador, 300))           # un efecto expira en 300
        vida_antes = motor.jugador.vida
        self.assertFalse(motor.avanzar_hasta(300))                    # sin decisión del jugador en 300
        self.assertEqual(motor.reloj, 300)
        self.assertLess(motor.jugador.vida, vida_antes)               # el estado es el posterior a todos los eventos
        self.assertTrue(caras[0].cerrada and caras[1].cerrada)
        self.assertFalse(motor.efectos.tiene(motor.jugador, "antorcha"))
        self.assertIsNotNone(motor.jugador.Evento_pendiente)          # la decisión de 500 sigue pendiente

    def test_fr402_un_instante_anterior_a_los_eventos_no_cambia_nada(self):
        motor = _escenario()
        motor.programar_accion(motor.jugador, 500)
        _enemigo_en(motor, 300)
        caras = _puerta(motor)
        _en(motor, 300, "cierre_puerta", CierrePuerta(caras))
        vida_antes = motor.jugador.vida
        self.assertFalse(motor.avanzar_hasta(299))
        self.assertEqual((motor.reloj, motor.jugador.vida), (0, vida_antes))
        self.assertFalse(caras[0].cerrada or caras[1].cerrada)
        self.assertFalse(motor.avanzar_hasta(0))                      # t igual al reloj actual: tampoco hace nada

    def test_h1_9_fr402_decision_del_jugador_en_t(self):
        motor = _escenario()
        enemigo = _enemigo_en(motor, 300)                             # el enemigo ataca y luego le toca al jugador
        motor.programar_accion(motor.jugador, 300)
        vida_antes = motor.jugador.vida
        self.assertTrue(motor.avanzar_hasta(300))                     # se detuvo en una decisión del jugador
        self.assertEqual(motor.reloj, 300)
        self.assertLess(motor.jugador.vida, vida_antes)               # incluye el ataque anterior a la decisión
        self.assertIsNone(motor.jugador.Evento_pendiente)             # la decisión todavía no se tomó
        self.assertTrue(enemigo.Evento_pendiente.esta_valido())       # el enemigo ya programó su siguiente acción

    def test_fr402_el_orden_del_mismo_instante_es_el_de_la_cola(self):
        motor = _escenario()
        motor.programar_accion(motor.jugador, 300)                    # esta vez el jugador va primero en 300
        _enemigo_en(motor, 300)
        vida_antes = motor.jugador.vida
        self.assertTrue(motor.avanzar_hasta(300))
        self.assertEqual(motor.jugador.vida, vida_antes)              # el ataque quedó para después de la decisión

    def test_h1_12_fr402_fr405_partida_terminada_en_t(self):
        motor = _escenario()
        motor.jugador.vida = 5
        veneno = Veneno(motor.jugador, 10)
        veneno.primer_retraso = 400                                   # el primer pulso mata al jugador en t = 400
        motor.efectos.aplicar(veneno)                                 # va primero en la cola de t = 400
        motor.programar_accion(motor.jugador, 600)
        enemigo = _enemigo_en(motor, 400)                             # los demás eventos de t = 400
        caras = _puerta(motor)
        _en(motor, 400, "cierre_puerta", CierrePuerta(caras))
        self.assertFalse(motor.avanzar_hasta(400))
        self.assertTrue(motor.terminado)
        self.assertFalse(motor.jugador.Vivo())
        self.assertEqual(motor.reloj, 400)
        self.assertFalse(caras[0].cerrada or caras[1].cerrada)        # los demás eventos de t = 400 no se ejecutaron
        self.assertTrue(enemigo.Evento_pendiente.esta_valido())
        self.assertFalse(motor.avanzar_hasta(900))                    # con la partida terminada no avanza más
        self.assertEqual(motor.reloj, 400)

    def test_fr402_eventos_cancelados_no_cuentan(self):
        motor = _escenario()
        motor.programar_accion(motor.jugador, 500)
        caras = _puerta(motor)
        _en(motor, 200, "cierre_puerta", CierrePuerta(caras)).cancelar()
        self.assertFalse(motor.avanzar_hasta(300))
        self.assertFalse(caras[0].cerrada or caras[1].cerrada)
        self.assertEqual(motor.reloj, 0)                              # el cancelado no adelantó el reloj

    def test_fr402_avanzar_hasta_no_cambia_avanzar_hasta_jugador(self):
        def preparar() -> Motor:
            motor = _escenario(semilla=7)
            _enemigo_en(motor, 300)
            motor.programar_accion(motor.jugador, 500)
            return motor

        clasico, nuevo = preparar(), preparar()
        self.assertTrue(clasico.avanzar_hasta_jugador())              # el comportamiento de siempre
        self.assertEqual(clasico.reloj, 500)
        self.assertIsNone(clasico.jugador.Evento_pendiente)
        self.assertTrue(nuevo.avanzar_hasta(500))                     # el nuevo llega al mismo estado
        self.assertEqual((nuevo.reloj, nuevo.jugador.vida), (clasico.reloj, clasico.jugador.vida))
        self.assertEqual(nuevo.azar.getstate(), clasico.azar.getstate())
        self.assertIsNone(nuevo.jugador.Evento_pendiente)


if __name__ == "__main__":
    unittest.main()
