"""
Pruebas de la historia 3 de la feature 001: la búsqueda compartida de los cazadores (RutasHaciaJugador)
decide siempre lo mismo que un cálculo desde cero (FR-114, SC-102), aunque reutilice la búsqueda entre turnos.

- TestEscenariosH3: escenarios H3-1 a H3-5 de spec.md (H3-1 es el caso 5 del Apéndice B).
- TestEquivalenciaAleatoria: partidas sintéticas con semilla (puertas, cierres automáticos, movimientos,
  muertes, velocidades y pergaminos); antes de cada decisión de cada cazador se compara con paso_desde_cero.
- TestHistorial: la búsqueda se descarta al deshacer con un pergamino (R4).

    python -m unittest tests.test_rutas_equivalencia -v
"""
import os
import random
import sys
import unittest
from dataclasses import replace

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.CriptaDTO import CriptaDTO  # noqa: E402
from DTO.Direcciones import E, N, O, S  # noqa: E402
from DTO.ObjetoDTO import ObjetoDTO  # noqa: E402
from Logic.BusquedaCostoMinimo import paso_desde_cero  # noqa: E402
from Logic.GrafoEsqueleto import GrafoEsqueleto  # noqa: E402
from Logic.HistorialRetroceso import HistorialRetroceso  # noqa: E402
from Logic.Inventario import Inventario  # noqa: E402
from Logic.Mazmorra import CierrePuerta, Mazmorra  # noqa: E402
from Logic.RutasHaciaJugador import RutasHaciaJugador  # noqa: E402
from Logic.jugador import Jugador  # noqa: E402
from Logic.motorJuego import Motor  # noqa: E402
from tests.ayudas_terreno import (LLAVE_FINAL, OPUESTA, cuadricula_con_costos, ficha_cazador,  # noqa: E402
                                  ficha_errante, mazmorra_con_costos, motor_con, poner_enemigo, salida)

LLAVE = "llave_x"                 # abre todas las puertas cerradas de las partidas sintéticas
ID_PERGAMINO = "itm_pergamino"


def cazador_en(motor, sala: int, rango: int, instancia: str = "e-1", velocidad: int = 100, numero: int = 1):
    return poner_enemigo(motor, sala, ficha_cazador(rango, velocidad), instancia, numero=numero)


def desde_cero(motor, cazador):
    """La decisión de referencia (sin reutilizar nada) para el cazador en este instante."""
    return paso_desde_cero(motor.grafo, motor.jugador.Sala_Actual, cazador.Sala_Actual, cazador.ficha.rango)


def cerrar(motor, sala: int, direccion: int) -> None:
    """Cierra las dos caras de la puerta como un cierre automático (CierrePuerta.activar)."""
    salida_viva = motor.mazmorra.salida(sala, direccion)
    vuelta = motor.mazmorra.salida(salida_viva.destino, OPUESTA[direccion])
    CierrePuerta([salida_viva, vuelta]).activar(motor, None)


class TestEscenariosH3(unittest.TestCase):
    """Historia 3: la decisión sigue siendo correcta cuando el mapa cambia (escenarios H3-1 a H3-5)."""

    def test_h3_1_apendiceB_caso5_fr114_puerta_se_cierra_entre_turnos(self):
        # 1-2 y 2-4 cuestan 100; 1-3 y 3-4 cuestan 150. Cazador en 1 (rango 600), jugador en 4.
        m = mazmorra_con_costos(4, [salida(1, E, 2, 100), salida(2, S, 4, 100),
                                    salida(1, S, 3, 150), salida(3, E, 4, 150)])
        motor, _ = motor_con(m, 4)
        cazador = cazador_en(motor, 1, 600)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 2)
        cerrar(motor, 2, S)                                            # se cierra 2-4
        self.assertEqual(desde_cero(motor, cazador), (1, 100))         # 2-1, 1-3, 3-4: d = 400 <= 600
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 1)
        self.assertEqual(cazador.Evento_pendiente.tiempo, 100)         # se movió con costo 100

    def test_h3_2_fr114_jugador_cambia_de_sala(self):
        # Línea 1-2-3-4. Cazador en 2, jugador en 4: va a 3. Luego el jugador pasa a la 1: vuelve a 2.
        m = mazmorra_con_costos(4, [salida(1, E, 2), salida(2, E, 3), salida(3, E, 4)])
        motor, _ = motor_con(m, 4)
        cazador = cazador_en(motor, 2, 1000)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 3)
        recalculos = motor.rutas.recalculos
        motor.jugador.Sala_Actual = 1
        self.assertEqual(desde_cero(motor, cazador), (2, 100))
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 2)                       # hacia la sala actual, no la anterior
        self.assertEqual(motor.rutas.recalculos, recalculos + 1)       # otra sala del jugador: búsqueda nueva

    def test_h3_3_fr114_se_abre_una_puerta_y_crea_ruta(self):
        # 1-2 (400) y 2-3 (300): d = 700 > 600, espera. Al abrir 1-3 (200) hay ruta de 200.
        m = mazmorra_con_costos(3, [salida(1, E, 2, 400), salida(2, E, 3, 300),
                                    salida(1, S, 3, 200, cerrada=True)])
        m.salida(1, S).llave = LLAVE
        m.salida(3, N).llave = LLAVE
        motor, _ = motor_con(m, 3)
        cazador = cazador_en(motor, 1, 600)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 1)                       # esperó
        motor.iniciar()
        motor.avanzar_hasta_jugador()
        self.assertEqual(motor.abrir_puerta(N, lambda llave: llave == LLAVE), "ok")
        self.assertEqual(desde_cero(motor, cazador), (3, 200))
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 3)

    def test_h3_4_fr114_cierre_lejano_no_cambia_la_decision(self):
        # Línea 1-2-3 (jugador en 3) y una rama lejana 1-4 (300), 4-5: al decidir desde la 1, la búsqueda
        # resuelve 3, 2 y 1, pero no 4 ni 5. Cerrar 4-5 no la descarta (R4).
        m = mazmorra_con_costos(5, [salida(1, E, 2), salida(2, E, 3), salida(1, S, 4, 300), salida(4, E, 5)])
        motor, _ = motor_con(m, 3)
        cazador = cazador_en(motor, 1, 1000)
        motor.turno_enemigo(cazador)
        self.assertEqual(cazador.Sala_Actual, 2)
        recalculos = motor.rutas.recalculos
        cerrar(motor, 4, E)
        esperado = desde_cero(motor, cazador)
        motor.turno_enemigo(cazador)
        self.assertEqual((cazador.Sala_Actual, cazador.Evento_pendiente.tiempo), esperado)
        self.assertEqual(motor.rutas.recalculos, recalculos)           # se reutilizó la misma búsqueda
        self.assertTrue(motor.rutas.valida)

    def test_h3_5_fr114_muerte_movimiento_y_velocidad_no_invalidan(self):
        # Línea 1-2-3-4-5 con el jugador en 5. Otro cazador se mueve, otro muere y uno cambia de velocidad.
        m = mazmorra_con_costos(5, [salida(1, E, 2), salida(2, E, 3), salida(3, E, 4), salida(4, E, 5)])
        motor, _ = motor_con(m, 5)
        a = cazador_en(motor, 1, 1000, "e-1", numero=1)
        b = cazador_en(motor, 2, 1000, "e-2", numero=2)
        c = cazador_en(motor, 3, 1000, "e-3", numero=3)
        motor.turno_enemigo(a)
        recalculos = motor.rutas.recalculos
        motor.turno_enemigo(b)                                         # otro actor cambia de sala
        motor.morir(c)                                                 # otro actor muere
        motor.cambiar_velocidad(a, 150)                                # cambia una velocidad
        esperado = desde_cero(motor, a)
        motor.turno_enemigo(a)
        self.assertEqual(a.Sala_Actual, esperado[0])
        self.assertEqual(motor.rutas.recalculos, recalculos)


class PartidaAleatoria:
    """
    Una partida sintética determinista por semilla: cuadrícula con costos, algunas puertas cerradas con llave y
    cierre automático, de 5 a 20 cazadores con rangos distintos y dos errantes. El jugador tiene la llave,
    vida de sobra y pergaminos. Cada decisión de cazador se compara con paso_desde_cero en ese instante.
    """

    def __init__(self, semilla: int):
        self.azar = random.Random(semilla)
        n = self.azar.randint(5, 8)
        salas = cuadricula_con_costos(n, self.azar)
        self._poner_puertas(salas)
        mazmorra = Mazmorra(sala_salida=n * n, llave_salida=LLAVE_FINAL)
        mazmorra.cargar_esqueleto(salas)
        for sala in salas:
            mazmorra.sala(sala.id).contenido_cargado = True
        cripta = CriptaDTO(id="c-rutas", version="1", salas_total=n * n, paginas=1, salas_por_pagina=50,
                           sala_inicial=1, sala_salida=n * n, llave_salida=LLAVE_FINAL,
                           presupuesto_solicitudes=10, inventario_max=50, jugador_vida_max=100000,
                           jugador_ataque=8, jugador_defensa=2, jugador_velocidad=100)
        inventario = Inventario(cripta.inventario_max)
        for _ in range(40):
            inventario.recoger(ObjetoDTO(ID_PERGAMINO, "Pergamino", Motor.PERGAMINO, 1, 1))
        self.motor = Motor(semilla, Jugador(cripta), mazmorra, None, inventario)
        self.motor.iniciar()
        self.enemigos = []
        for i in range(self.azar.randint(5, 20)):
            rango = self.azar.choice([100, 250, 400, 600, 1000, 3000])
            velocidad = self.azar.choice([80, 100, 120, 150])
            sala = self.azar.randint(2, n * n)
            self.enemigos.append(cazador_en(self.motor, sala, rango, f"e-{i + 1}", velocidad, numero=i + 1))
        for j in range(2):
            numero = len(self.enemigos) + 1
            self.enemigos.append(poner_enemigo(self.motor, self.azar.randint(2, n * n), ficha_errante(),
                                               f"e-{numero}", numero=numero))
        self.decisiones = 0
        self.diferencias: list[str] = []
        self._decidir = self.motor.rutas.decidir
        self.motor.rutas.decidir = self._comparar

    def _poner_puertas(self, salas) -> None:
        """Cierra con LLAVE alrededor de un cuarto de los pares de salas; algunas se cierran solas."""
        for sala in salas:
            for direccion in range(4):
                cara = sala.salidas[direccion]
                if cara is None or cara.sala_destino < sala.id or self.azar.random() >= 0.25:
                    continue
                cierre = self.azar.choice([None, 150, 400])
                sala.salidas[direccion] = replace(cara, cerrada=True, llave=LLAVE, cierre_automatico=cierre)

    def _comparar(self, sala_cazador, sala_jugador, rango):
        esperado = paso_desde_cero(self.motor.grafo, sala_jugador, sala_cazador, rango)
        obtenido = self._decidir(sala_cazador, sala_jugador, rango)
        self.decisiones += 1
        if obtenido != esperado:
            self.diferencias.append(f"t={self.motor.reloj} cazador en {sala_cazador}, jugador en {sala_jugador}, "
                                    f"rango {rango}: {obtenido} != {esperado}")
        return obtenido

    def jugar(self, acciones: int) -> None:
        motor = self.motor
        motor.avanzar_hasta_jugador()
        for _ in range(acciones):
            if motor.terminado:
                return
            tipo = self.azar.random()
            if tipo < 0.2 and motor.historial.cantidad() > 0:
                motor.usar(ID_PERGAMINO)                       # no es una acción: el jugador vuelve a decidir
                continue
            if tipo < 0.3:
                vivos = [e for e in self.enemigos if e.Vivo()]
                if vivos:
                    motor.cambiar_velocidad(self.azar.choice(vivos), self.azar.choice([80, 100, 130]))
            resultado = self._accion_del_jugador()
            if resultado != "ok":
                motor.esperar()
            motor.avanzar_hasta_jugador()

    def _accion_del_jugador(self) -> str:
        motor = self.motor
        tipo = self.azar.random()
        enemigos_aqui = [e for e in self.enemigos if e.Vivo() and e.Sala_Actual == motor.jugador.Sala_Actual]
        if enemigos_aqui and tipo < 0.5:
            return motor.atacar_enemigo(enemigos_aqui[0].id)
        if tipo < 0.65:
            return motor.abrir_puerta(self.azar.randrange(4), lambda llave: llave == LLAVE)
        if tipo < 0.9:
            return motor.mover_jugador(self.azar.randrange(4))
        return motor.esperar()


class TestEquivalenciaAleatoria(unittest.TestCase):
    """FR-114, SC-102: cada decisión de cada cazador coincide con paso_desde_cero en ese instante."""

    def test_fr114_sc102_cada_decision_igual_a_paso_desde_cero(self):
        reutilizaciones = 0
        for semilla in range(1, 13):
            with self.subTest(semilla=semilla):
                partida = PartidaAleatoria(semilla)
                partida.jugar(300)
                self.assertEqual(partida.diferencias, [])
                self.assertGreater(partida.decisiones, 0)
                reutilizaciones += partida.motor.rutas.reutilizaciones
        self.assertGreater(reutilizaciones, 0)                          # sí se reutiliza la búsqueda


class TestHistorial(unittest.TestCase):
    """R4: lo que deshace un pergamino descarta la búsqueda; un intervalo sin cambios de ruta la conserva."""

    def setUp(self):
        m = mazmorra_con_costos(4, [salida(1, E, 2), salida(2, E, 3), salida(3, E, 4)])
        self.historial = HistorialRetroceso()
        self.grafo = GrafoEsqueleto(m)
        self.rutas = RutasHaciaJugador(self.grafo, self.historial)

    def test_pergamino_descarta_la_busqueda(self):
        self.assertEqual(self.rutas.decidir(1, 4, 1000), (2, 100))     # crea la búsqueda en este intervalo
        self.historial.cerrar_intervalo()
        self.assertTrue(self.rutas.valida)
        self.assertTrue(self.historial.deshacer())
        self.assertFalse(self.rutas.valida)
        recalculos = self.rutas.recalculos
        self.assertEqual(self.rutas.decidir(1, 4, 1000), paso_desde_cero(self.grafo, 4, 1, 1000))
        self.assertEqual(self.rutas.recalculos, recalculos + 1)         # empieza desde cero

    def test_aviso_de_puerta_se_registra_en_el_historial(self):
        self.rutas.decidir(3, 4, 1000)                                  # resuelve solo 4 y 3
        self.historial.cerrar_intervalo()
        self.rutas.puerta_cambio(1, 1)                                  # la sala 1 no está resuelta
        self.assertTrue(self.rutas.valida)
        self.historial.cerrar_intervalo()
        self.assertTrue(self.historial.deshacer())                      # se deshace el cambio de esa puerta
        self.assertFalse(self.rutas.valida)

    def test_deshacer_un_intervalo_sin_cambios_de_ruta_la_conserva(self):
        self.rutas.decidir(1, 4, 1000)                                  # crea y resuelve 4, 3, 2 y 1
        self.historial.cerrar_intervalo()
        reutilizaciones = self.rutas.reutilizaciones
        self.assertEqual(self.rutas.decidir(2, 4, 1000), (3, 100))      # ya resuelta: no extiende
        self.assertEqual(self.rutas.reutilizaciones, reutilizaciones + 1)
        self.historial.cerrar_intervalo()
        self.assertTrue(self.historial.deshacer())
        self.assertTrue(self.rutas.valida)

    def test_pergamino_despues_de_abrir_una_puerta_sin_moverse(self):
        """
        FR-114: el jugador abre 1-2 sin cambiar de sala y la búsqueda se rehace con la puerta abierta; el
        pergamino la vuelve a cerrar sin avisar. La decisión siguiente usa la ruta larga, como desde cero.
        """
        m = mazmorra_con_costos(4, [salida(1, E, 2, 100, cerrada=True), salida(1, S, 3), salida(3, E, 4),
                                    salida(4, N, 2)])
        m.salida(1, E).llave = LLAVE
        m.salida(2, O).llave = LLAVE
        motor, _ = motor_con(m, 2)
        motor.inventario = Inventario(5)
        motor.inventario.historial = motor.historial
        motor.inventario.recoger(ObjetoDTO(ID_PERGAMINO, "Pergamino", Motor.PERGAMINO, 1, 1))
        motor.iniciar()
        motor.avanzar_hasta_jugador()
        self.assertEqual(motor.rutas.decidir(1, 2, 1000), (3, 100))     # con 1-2 cerrada: 1-3-4-2
        motor.esperar()
        motor.avanzar_hasta_jugador()
        self.assertEqual(motor.abrir_puerta(O, lambda llave: llave == LLAVE), "ok")
        self.assertEqual(motor.rutas.decidir(1, 2, 1000), (2, 100))     # con 1-2 abierta
        motor.avanzar_hasta_jugador()
        self.assertEqual(motor.usar(ID_PERGAMINO), "ok")                # deshace la apertura
        self.assertTrue(m.salida(1, E).cerrada)
        self.assertEqual(motor.rutas.decidir(1, 2, 1000), paso_desde_cero(motor.grafo, 2, 1, 1000))
        self.assertEqual(motor.rutas.decidir(1, 2, 1000), (3, 100))


if __name__ == "__main__":
    unittest.main()
