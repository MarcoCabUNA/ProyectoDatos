"""
Pruebas del contador ActorBase.danio_recibido (plan de «ir a», tarea nueva antes de T111; FR-258 c, I3-3, R-I3-7).

El contador sube en Recibir_Dannio solo cuando el daño final es > 0. Es lo que «ir a» compara antes y después de cada
paso para saber si el jugador recibió daño de cualquier origen (ataque de enemigo, veneno o trampa), aunque una curación del
mismo paso le devuelva la vida. NO va al historial de retroceso ni a PartidaGuardada.
"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ayudas_terreno import ficha_errante, mazmorra_con_costos, motor_con, poner_enemigo, salida
from DTO.FichaTrampaDTO import FichaTrampaDTO
from Logic.Efectos import Veneno
from Logic.Inventario import Inventario
from Logic.EventoPorg import EventoProgramado
from Logic.Mazmorra import TrampaViva
from Logic.PartidaGuardada import PartidaGuardada
from Logic.motorJuego import Motor


def _escenario(semilla: int = 1) -> tuple[Motor, list]:
    """Dos salas unidas (1 al oeste de 2), el jugador en la 1 con el control en t = 0. Devuelve (motor, mensajes)."""
    motor, mensajes = motor_con(mazmorra_con_costos(2, [salida(1, 2, 2, 100)]), 1, semilla)
    motor.iniciar()
    motor.avanzar_hasta_jugador()
    return motor, mensajes


def _enemigo_en(motor: Motor, tiempo: int):
    """Un enemigo errante en la sala del jugador cuya primera acción cae exactamente en `tiempo`."""
    enemigo = poner_enemigo(motor, 1, ficha_errante())
    enemigo.Evento_pendiente.cancelar()
    enemigo.Evento_pendiente = motor.cola.programar(EventoProgramado(tiempo, "accion_actor", enemigo))
    return enemigo


def _trampa_en_2(motor: Motor, danio: int) -> None:
    motor.mazmorra.sala(2).trampas.append(TrampaViva("t-1", FichaTrampaDTO("pinchos", "Pinchos", danio, 300)))


class PruebasContadorDeDanio(unittest.TestCase):

    def test_el_contador_nace_en_cero_en_el_jugador_y_en_los_enemigos(self):
        motor, _ = _escenario()
        enemigo = poner_enemigo(motor, 1, ficha_errante())
        self.assertEqual(motor.jugador.danio_recibido, 0)
        self.assertEqual(enemigo.danio_recibido, 0)                      # ActorBase lo comparte; nadie lo lee en ellos
        self.assertIsInstance(motor.jugador.danio_recibido, int)

    def test_ataque_de_enemigo_lo_sube_con_el_dano_final_fr258(self):
        motor, mensajes = _escenario()
        _enemigo_en(motor, 50)
        vida = motor.jugador.vida
        motor.esperar()                                                  # el enemigo ataca antes de la próxima decisión
        motor.avanzar_hasta_jugador()
        perdida = vida - motor.jugador.vida
        self.assertGreater(perdida, 0)
        self.assertEqual(motor.jugador.danio_recibido, perdida)

    def test_cant_ya_es_el_dano_final_despues_de_la_defensa_fr258(self):
        """Recibir_Dannio recibe el daño ya calculado (ataque + azar - defensa, mínimo 1): el contador suma ese número."""
        textos = []
        for defensa in (2, 500):                                         # la defensa alta deja el golpe en el mínimo (1)
            motor, mensajes = _escenario()
            motor.jugador.defensa = defensa
            _enemigo_en(motor, 50)
            motor.esperar()
            motor.avanzar_hasta_jugador()
            golpes = [int(re.search(r": (\d+) de daño", m).group(1)) for m in mensajes if " ataca a Jugador" in m]
            self.assertGreaterEqual(len(golpes), 1)
            self.assertEqual(motor.jugador.danio_recibido, sum(golpes), f"defensa {defensa}")
            textos.append(golpes)
        self.assertTrue(all(g == 1 for g in textos[1]))                  # defensa 500: cada golpe hace 1, no el ataque bruto
        self.assertGreater(textos[0][0], 1)

    def test_veneno_lo_sube_en_cada_pulso_fr258(self):
        motor, _ = _escenario()
        motor.efectos.aplicar(Veneno(motor.jugador, 3))
        motor.programar_accion(motor.jugador, 400)
        vida = motor.jugador.vida
        motor.avanzar_hasta(400)
        self.assertGreater(motor.jugador.danio_recibido, 0)
        self.assertEqual(motor.jugador.danio_recibido % 3, 0)            # solo pulsos de 3
        self.assertEqual(motor.jugador.danio_recibido, vida - motor.jugador.vida)

    def test_trampa_lo_sube_fr258(self):
        motor, _ = _escenario()
        _trampa_en_2(motor, 4)
        self.assertEqual(motor.mover_jugador(2), "ok")
        self.assertEqual(motor.jugador.danio_recibido, 4)

    def test_un_dano_de_cero_no_lo_sube(self):
        motor, _ = _escenario()
        vida = motor.jugador.vida
        for cant in (0, -3):
            motor.jugador.Recibir_Dannio(cant)                           # la guarda de ActorBase: sin daño no hay nada
        self.assertEqual((motor.jugador.danio_recibido, motor.jugador.vida), (0, vida))
        _trampa_en_2(motor, 0)                                           # una trampa de daño 0 tampoco
        self.assertEqual(motor.mover_jugador(2), "ok")
        self.assertEqual(motor.jugador.danio_recibido, 0)

    def test_una_curacion_no_lo_baja_y_se_sigue_viendo_el_dano_r_i3_7(self):
        motor, _ = _escenario()
        motor.jugador.Recibir_Dannio(7)
        motor.jugador.Curacion(100)                                      # la vida vuelve al máximo...
        self.assertEqual(motor.jugador.vida, motor.jugador.vida_Max)
        self.assertEqual(motor.jugador.danio_recibido, 7)                # ...pero el daño recibido sigue contado
        motor.jugador.Recibir_Dannio(2)
        self.assertEqual(motor.jugador.danio_recibido, 9)                # y se acumula

    def test_el_pergamino_no_cambia_la_comparacion_antes_y_despues_de_un_paso_fr262(self):
        """Deshacer una acción (lo que hace el pergamino) no baja el contador: restaura la vida, no el daño ya contado."""
        motor, _ = _escenario()
        _enemigo_en(motor, 50)
        motor.esperar()
        motor.avanzar_hasta_jugador()                                    # esa acción recibió daño
        contado = motor.jugador.danio_recibido
        self.assertGreater(contado, 0)
        vida_con_dano = motor.jugador.vida
        antes = motor.jugador.danio_recibido                             # lo que Service lee antes del «paso» (un pergamino)
        self.assertTrue(motor.historial.deshacer())
        self.assertGreater(motor.jugador.vida, vida_con_dano)            # la vida sí volvió
        self.assertEqual(motor.jugador.danio_recibido, contado)          # el contador no
        self.assertFalse(motor.jugador.danio_recibido > antes)           # así que el pergamino no parece daño

    def test_no_va_a_partida_guardada(self):
        motor, _ = _escenario()
        motor.inventario = Inventario(5)                                 # PartidaGuardada.guardar lo necesita
        motor.jugador.Recibir_Dannio(5)
        partida, salas = PartidaGuardada.guardar(motor, _cripta_de(motor), "catalogo-1", 1)
        texto = repr(partida.a_diccionario()) + repr([sala.a_diccionario() for sala in salas])
        self.assertNotIn("danio_recibido", texto)


def _cripta_de(motor: Motor):
    """La CriptaDTO mínima que PartidaGuardada.guardar necesita (la misma de motor_con)."""
    from DTO.CriptaDTO import CriptaDTO
    return CriptaDTO(id="c-terreno", version="1", salas_total=len(motor.mazmorra.salas) - 1, paginas=1,
                     salas_por_pagina=50, sala_inicial=1, sala_salida=motor.mazmorra.sala_salida,
                     llave_salida=motor.mazmorra.llave_salida, presupuesto_solicitudes=10, inventario_max=5,
                     jugador_vida_max=30, jugador_ataque=5, jugador_defensa=2, jugador_velocidad=100)


if __name__ == "__main__":
    unittest.main()
