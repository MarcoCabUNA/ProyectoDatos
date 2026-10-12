"""
Tests basicos de la capa de Logica.

Ejecutar desde la raiz del proyecto:
    python3 -m unittest discover -s tests -p "*.py" -v     # "*.py": tambien los Test*.py
"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from DTO.CriptaDTO import CriptaDTO
from DTO.FichaEnemigoDTO import FichaEnemigoDTO
from DTO.FichaTrampaDTO import FichaTrampaDTO
from DTO.ObjetoDTO import ObjetoDTO
from DTO.SalaDTO import SalaDTO, SalidaDTO, EnemigoEnSalaDTO, TrampaEnSalaDTO, ContenidoSalaDTO

from Logic.ActorBase import ActorBase
from Logic.ColaEventos import ColaEventos
from Logic.Comportamientos import Guardian, Errante, Rastreador, crear_comportamiento
from Logic.Efectos import Veneno, Velocidad, Antorcha
from Logic.Enemigo import Enemigo
from Logic.EventoPorg import EventoProgramado
from Logic.jugador import Jugador
from Logic.Mazmorra import Mazmorra, TrampaViva
from Logic.motorJuego import Motor
from Logic.RastroSalas import RastroSalas

from DTO.Direcciones import N, E, O


# ---------- Fabricas de datos de prueba

def crear_cripta(**cambios):
    datos = dict(id="c1", version="1", salas_total=3, paginas=1, salas_por_pagina=3,
                 sala_inicial=0, sala_salida=2, llave_salida="llave_final",
                 presupuesto_solicitudes=10, inventario_max=5, jugador_vida_max=30,
                 jugador_ataque=5, jugador_defensa=2, jugador_velocidad=100)
    datos.update(cambios)
    return CriptaDTO(**datos)


def crear_ficha(comportamiento="guardián", **cambios):
    datos = dict(id="rata", nombre="Rata", vida_max=10, ataque=3, defensa=1,
                 velocidad=100, comportamiento=comportamiento, suelta=["itm_queso"])
    datos.update(cambios)
    return FichaEnemigoDTO(**datos)


def salas_lineales():
    """0 <-E/O-> 1 <-E/O-> 2 (salida). La puerta 1->2 esta cerrada con llave_final."""
    return [
        SalaDTO(0, "Entrada", [None, None, SalidaDTO(1), None], "1"),
        SalaDTO(1, "Pasillo", [None, None, SalidaDTO(2, True, "llave_final"), SalidaDTO(0)], "1"),
        SalaDTO(2, "Salida", [None, None, None, SalidaDTO(1, True, "llave_final")], "1"),
    ]


def crear_mazmorra(cargadas=None):
    m = Mazmorra(sala_salida=2, llave_salida="llave_final")
    m.cargar_esqueleto(salas_lineales())
    if cargadas is None:
        cargadas = [0, 1, 2]
    for i in cargadas:
        m.sala(i).contenido_cargado = True
    return m


def poner_enemigo(mazmorra, sala, instancia="e-1", ficha=None, vida=None, numero=1):
    enemigo = Enemigo(ficha or crear_ficha(), instancia, vida, numero, sala)
    mazmorra.sala(sala).enemigos.append(enemigo)
    return enemigo


def crear_motor(mazmorra=None, semilla=1):
    mensajes = []
    motor = Motor(semilla, Jugador(crear_cripta()), mazmorra or crear_mazmorra(), mensajes.append)
    return motor, mensajes


class ActorDePrueba(ActorBase):
    def tipo(self):
        return "prueba"

    def nombre_visible(self):
        return "Prueba"


# ---------- EventoProgramado y ColaEventos

class TestEventoProgramado(unittest.TestCase):
    def test_orden_por_tiempo(self):
        a = EventoProgramado(5, "x", None)
        b = EventoProgramado(10, "x", None)
        self.assertTrue(a < b)
        self.assertFalse(b < a)

    def test_desempate_por_secuencia(self):
        a = EventoProgramado(5, "x", None)
        b = EventoProgramado(5, "x", None)
        a.secuencia = 0
        b.secuencia = 1
        self.assertTrue(a < b)

    def test_cancelar(self):
        e = EventoProgramado(1, "x", None)
        self.assertTrue(e.esta_valido())
        e.cancelar()
        self.assertFalse(e.esta_valido())
        self.assertIn("cancelado", repr(e))


class TestColaEventos(unittest.TestCase):
    def test_vacia(self):
        cola = ColaEventos()
        self.assertTrue(cola.esta_vacia())
        self.assertIsNone(cola.obtener_siguiente())
        self.assertIsNone(cola.ver_siguiente())

    def test_extrae_en_orden_de_tiempo(self):
        cola = ColaEventos()
        tiempos = [50, 3, 99, 0, 17, 17, 42, 8, 1, 75]
        for t in tiempos:
            cola.programar(EventoProgramado(t, "x", None))
        sacados = []
        while not cola.esta_vacia():
            sacados.append(cola.obtener_siguiente().tiempo)
        self.assertEqual(sacados, sorted(tiempos))

    def test_empates_salen_en_orden_de_llegada(self):
        cola = ColaEventos()
        eventos = [cola.programar(EventoProgramado(10, "x", i)) for i in range(6)]
        self.assertEqual([cola.obtener_siguiente().dueno for _ in eventos], list(range(6)))

    def test_descarta_cancelados(self):
        cola = ColaEventos()
        a = cola.programar(EventoProgramado(1, "x", "a"))
        cola.programar(EventoProgramado(2, "x", "b"))
        a.cancelar()
        self.assertEqual(cola.ver_siguiente().dueno, "b")
        self.assertEqual(cola.obtener_siguiente().dueno, "b")
        self.assertTrue(cola.esta_vacia())

    def test_ver_siguiente_no_extrae(self):
        cola = ColaEventos()
        cola.programar(EventoProgramado(1, "x", "a"))
        cola.ver_siguiente()
        self.assertFalse(cola.esta_vacia())


# ---------- Actores

class TestActorBase(unittest.TestCase):
    def setUp(self):
        self.actor = ActorDePrueba("a", 20, 30, 5, 2, 100, 0)

    def test_intervalo_segun_velocidad(self):
        self.assertEqual(self.actor.Calcu_de_Intervalo(100), 100)
        self.actor.velocidad = 200
        self.assertEqual(self.actor.Calcu_de_Intervalo(100), 50)
        self.actor.velocidad = 100000
        self.assertEqual(self.actor.Calcu_de_Intervalo(100), 1)  # minimo 1

    def test_dano_no_baja_de_cero(self):
        self.actor.Recibir_Dannio(50)
        self.assertEqual(self.actor.vida, 0)
        self.assertFalse(self.actor.Vivo())

    def test_dano_exacto_mata(self):
        self.actor.Recibir_Dannio(20)
        self.assertFalse(self.actor.Vivo())

    def test_curacion_topada_en_maximo(self):
        self.actor.Curacion(100)
        self.assertEqual(self.actor.vida, 30)

    def test_curacion_no_revive(self):
        self.actor.Recibir_Dannio(20)
        self.actor.Curacion(10)
        self.assertEqual(self.actor.vida, 0)

    def test_dano_negativo_no_cura(self):
        self.actor.Recibir_Dannio(-15)
        self.assertLessEqual(self.actor.vida, self.actor.vida_Max)

    def test_metodos_abstractos(self):
        base = ActorBase("a", 1, 1, 1, 1, 1, 0)
        with self.assertRaises(NotImplementedError):
            base.tipo()
        with self.assertRaises(NotImplementedError):
            base.a_dto()


class TestJugador(unittest.TestCase):
    def test_creado_desde_cripta(self):
        j = Jugador(crear_cripta())
        self.assertEqual([j.vida, j.vida_Max, j.ataque, j.defensa, j.velocidad, j.Sala_Actual],
                         [30, 30, 5, 2, 100, 0])
        self.assertEqual(j.acciones, 0)

    def test_equipar_suma_bonus(self):
        j = Jugador(crear_cripta())
        j.equipar(ObjetoDTO("espada", "Espada", "arma", 3, 10, ataque_bonus=4))
        j.equipar(ObjetoDTO("cota", "Cota", "armadura", 5, 10, defensa_bonus=3))
        self.assertEqual(j.ataque_efectivo(), 9)
        self.assertEqual(j.defensa_efectiva(), 5)

    def test_equipar_objeto_no_equipable_se_ignora(self):
        j = Jugador(crear_cripta())
        j.equipar(ObjetoDTO("pocion", "Pocion", "pocion", 1, 1, cura=5))
        self.assertIsNone(j.arma)
        self.assertIsNone(j.armadura)

    def test_a_dto(self):
        j = Jugador(crear_cripta())
        j.equipar(ObjetoDTO("espada", "Espada", "arma", 3, 10, ataque_bonus=4))
        dto = j.a_dto()
        self.assertEqual(dto.id, "jugador")
        self.assertEqual(dto.tipo, "jugador")
        self.assertEqual(dto.ataque, 9)
        self.assertEqual(dto.sala_actual, 0)


class TestEnemigo(unittest.TestCase):
    def test_vida_none_usa_vida_max(self):
        self.assertEqual(Enemigo(crear_ficha(), "e-1", None, 1, 0).vida, 10)

    def test_vida_explicita(self):
        self.assertEqual(Enemigo(crear_ficha(), "e-1", 4, 1, 0).vida, 4)

    def test_nombre_y_tipo(self):
        e = Enemigo(crear_ficha(), "e-1", None, 3, 0)
        self.assertEqual(e.nombre_visible(), "Rata #3")
        self.assertEqual(e.tipo(), "rata")
        self.assertEqual(e.objetos_que_suelta(), ["itm_queso"])
        self.assertFalse(e.activo)

    def test_estrategia_segun_ficha(self):
        self.assertIsInstance(Enemigo(crear_ficha("guardián"), "e", None, 1, 0).estrategia, Guardian)
        self.assertIsInstance(Enemigo(crear_ficha("errante"), "e", None, 1, 0).estrategia, Errante)
        self.assertIsInstance(Enemigo(crear_ficha("rastreador"), "e", None, 1, 0).estrategia, Rastreador)

    def test_comportamiento_desconocido(self):
        with self.assertRaises(ValueError):
            crear_comportamiento("volador")

    def test_a_dto(self):
        dto = Enemigo(crear_ficha(), "e-1", 7, 1, 2).a_dto()
        self.assertEqual([dto.id, dto.tipo, dto.vida, dto.vida_max, dto.sala_actual],
                         ["e-1", "rata", 7, 10, 2])


# ---------- Rastro y comportamientos

class TestRastroSalas(unittest.TestCase):
    def test_sala_no_marcada(self):
        r = RastroSalas()
        self.assertIsNone(r.obtener(7))
        self.assertFalse(r.es_fresco(7, 0))

    def test_frescura(self):
        r = RastroSalas()
        r.marcar(3, 100)
        self.assertEqual(r.obtener(3), 100)
        self.assertTrue(r.es_fresco(3, 499))
        self.assertFalse(r.es_fresco(3, 500))  # 400 de antiguedad ya no es fresco


class TestComportamientos(unittest.TestCase):
    def test_guardian_no_se_mueve(self):
        motor, _ = crear_motor()
        enemigo = poner_enemigo(motor.mazmorra, 1, ficha=crear_ficha("guardián"))
        self.assertIsNone(enemigo.estrategia.decidir(enemigo, motor))

    def test_errante_elige_salida_abierta(self):
        motor, _ = crear_motor()
        enemigo = poner_enemigo(motor.mazmorra, 1, ficha=crear_ficha("errante"))
        for _ in range(20):
            self.assertEqual(enemigo.estrategia.decidir(enemigo, motor), 0)  # 1->2 esta cerrada

    def test_errante_sin_salidas(self):
        motor, _ = crear_motor()
        enemigo = poner_enemigo(motor.mazmorra, 2, ficha=crear_ficha("errante"))
        self.assertIsNone(enemigo.estrategia.decidir(enemigo, motor))

    def test_rastreador_sigue_rastro_fresco(self):
        motor, _ = crear_motor()
        enemigo = poner_enemigo(motor.mazmorra, 1, ficha=crear_ficha("rastreador"))
        self.assertIsNone(enemigo.estrategia.decidir(enemigo, motor))  # sin rastro
        motor.rastro.marcar(0, 0)
        self.assertEqual(enemigo.estrategia.decidir(enemigo, motor), 0)
        motor.reloj = 400
        self.assertIsNone(enemigo.estrategia.decidir(enemigo, motor))  # rastro viejo


# ---------- Mazmorra

class TestMazmorra(unittest.TestCase):
    def test_cargar_esqueleto(self):
        m = crear_mazmorra(cargadas=[])
        self.assertEqual(m.sala(1).nombre, "Pasillo")
        self.assertFalse(m.contenido_cargado(1))
        self.assertEqual(m.salidas_abiertas(1), [0])

    def test_llave_requerida(self):
        m = crear_mazmorra()
        self.assertEqual(m.llave_requerida(1, E), "llave_final")
        self.assertIsNone(m.llave_requerida(1, O))   # abierta
        self.assertIsNone(m.llave_requerida(1, N))   # no existe

    def test_abrir_puerta_abre_ambas_caras(self):
        motor, _ = crear_motor()
        m = motor.mazmorra
        m.abrir_puerta(1, E, motor)
        self.assertFalse(m.salida(1, E).cerrada)
        self.assertFalse(m.salida(2, O).cerrada)
        self.assertTrue(m.salida_abierta)

    def test_cierre_automatico(self):
        m = Mazmorra(sala_salida=1, llave_salida="x")
        m.cargar_esqueleto([
            SalaDTO(0, "A", [None, None, SalidaDTO(1, True, "k", cierre_automatico=30), None], "1"),
            SalaDTO(1, "B", [None, None, None, SalidaDTO(0, True, "k")], "1"),
        ])
        m.sala(0).contenido_cargado = m.sala(1).contenido_cargado = True
        motor, _ = crear_motor(m)
        m.abrir_puerta(0, E, motor)
        self.assertFalse(m.salida(0, E).cerrada)
        evento = motor.cola.obtener_siguiente()
        self.assertEqual([evento.tiempo, evento.tipo], [30, "cierre_puerta"])
        evento.dueno.activar(motor, evento)
        self.assertTrue(m.salida(0, E).cerrada)
        self.assertTrue(m.salida(1, O).cerrada)

    def test_abrir_puerta_hacia_sala_sin_esqueleto(self):
        # Esqueleto paginado: la sala destino todavia no se descargo.
        m = Mazmorra(sala_salida=9, llave_salida="x")
        m.cargar_esqueleto([SalaDTO(0, "A", [None, None, SalidaDTO(9, True, "k"), None], "1")])
        motor, _ = crear_motor(m)
        m.abrir_puerta(0, E, motor)
        self.assertFalse(m.salida(0, E).cerrada)

    def test_mover_enemigo(self):
        m = crear_mazmorra()
        e = poner_enemigo(m, 1)
        m.mover_enemigo(e, 0)
        self.assertEqual(e.Sala_Actual, 0)
        self.assertEqual(m.enemigos_vivos(0), [e])
        self.assertEqual(m.enemigos_vivos(1), [])

    def test_enemigos_vivos_dormidos_y_buscar(self):
        m = crear_mazmorra()
        a = poner_enemigo(m, 1, "e-1")
        b = poner_enemigo(m, 1, "e-2")
        b.activo = True
        c = poner_enemigo(m, 1, "e-3")
        c.Recibir_Dannio(100)
        self.assertEqual(m.enemigos_vivos(1), [a, b])
        self.assertEqual(m.enemigos_dormidos(1), [a])
        self.assertIs(m.buscar_enemigo(1, "e-2"), b)
        self.assertIsNone(m.buscar_enemigo(1, "e-3"))

    def test_soltar_y_recoger_objeto(self):
        m = crear_mazmorra()
        m.soltar_objeto(0, "itm_a")
        self.assertTrue(m.recoger_objeto(0, "itm_a"))
        self.assertFalse(m.recoger_objeto(0, "itm_a"))

    def test_trampas_armadas(self):
        m = crear_mazmorra()
        t = TrampaViva("t-1", FichaTrampaDTO("pinchos", "Pinchos", 4, 300))
        m.sala(1).trampas.append(t)
        self.assertEqual(m.trampas_armadas(1), [t])
        t.armada = False
        self.assertEqual(m.trampas_armadas(1), [])

    def test_cargar_contenido_con_dto_real(self):
        """SalaDTO.enemigos/trampas son dataclasses, no tuplas."""
        m = crear_mazmorra(cargadas=[])
        sala = salas_lineales()[1].con_contenido(ContenidoSalaDTO(
            1, [EnemigoEnSalaDTO("e-1", "rata"), EnemigoEnSalaDTO("e-2", "rata", 3)],
            ["itm_a"], [TrampaEnSalaDTO("t-1", "pinchos")]))
        fichas = {"rata": crear_ficha(), "pinchos": FichaTrampaDTO("pinchos", "Pinchos", 4, 300)}
        m.cargar_contenido(sala, fichas.__getitem__)
        enemigos = m.enemigos_vivos(1)
        self.assertEqual([e.nombre_visible() for e in enemigos], ["Rata #1", "Rata #2"])
        self.assertEqual(enemigos[1].vida, 3)
        self.assertEqual(m.sala(1).objetos, ["itm_a"])
        self.assertEqual(len(m.trampas_armadas(1)), 1)
        self.assertTrue(m.contenido_cargado(1))


# ---------- Efectos

class TestEfectos(unittest.TestCase):
    def setUp(self):
        self.motor, self.mensajes = crear_motor()
        self.jugador = self.motor.jugador

    def correr_hasta(self, tiempo):
        while not self.motor.cola.esta_vacia() and self.motor.cola.ver_siguiente().tiempo <= tiempo:
            evento = self.motor.cola.obtener_siguiente()
            self.motor.reloj = evento.tiempo
            if evento.dueno is not self.jugador:
                evento.dueno.activar(self.motor, evento)

    def test_veneno_pulsa_cinco_veces(self):
        self.motor.efectos.aplicar(Veneno(self.jugador, 2))
        self.assertTrue(self.motor.efectos.tiene(self.jugador, "veneno"))
        self.correr_hasta(1000)
        self.assertEqual(self.jugador.vida, 30 - 5 * 2)  # pulsos en 80,160,240,320,400
        self.assertFalse(self.motor.efectos.tiene(self.jugador, "veneno"))

    def test_veneno_unico_reemplaza_al_anterior(self):
        self.motor.efectos.aplicar(Veneno(self.jugador, 2))
        self.motor.efectos.aplicar(Veneno(self.jugador, 3))
        self.assertEqual(len(self.motor.efectos.activos), 1)
        self.correr_hasta(80)
        self.assertEqual(self.jugador.vida, 27)

    def test_veneno_puede_matar(self):
        self.jugador.vida = 2
        self.motor.efectos.aplicar(Veneno(self.jugador, 5))
        self.correr_hasta(1000)
        self.assertFalse(self.jugador.Vivo())
        self.assertTrue(self.motor.terminado)
        self.assertEqual(self.motor.efectos.activos, [])

    def test_antorcha_expira(self):
        self.motor.efectos.aplicar(Antorcha(self.jugador, 150))
        self.assertEqual(self.motor.efectos.visibles(self.jugador)[0].restante, 150)
        self.correr_hasta(150)
        self.assertFalse(self.motor.efectos.tiene(self.jugador, "antorcha"))
        self.assertTrue(any("antorcha se apaga" in m for m in self.mensajes))

    def test_velocidad_se_aplica_y_revierte(self):
        self.motor.efectos.aplicar(Velocidad(self.jugador, 50, 200))
        self.assertEqual(self.jugador.velocidad, 150)
        self.correr_hasta(200)
        self.assertEqual(self.jugador.velocidad, 100)

    def test_velocidad_no_baja_de_uno(self):
        self.motor.efectos.aplicar(Velocidad(self.jugador, -500, 200))
        self.assertEqual(self.jugador.velocidad, 1)
        self.correr_hasta(200)
        self.assertEqual(self.jugador.velocidad, 100)

    def test_cancelar_efecto_inexistente(self):
        self.assertFalse(self.motor.efectos.cancelar(self.jugador, "veneno"))


# ---------- Motor

class TestMotor(unittest.TestCase):
    def test_iniciar_da_turno_al_jugador_y_activa_enemigos(self):
        m = crear_mazmorra()
        e = poner_enemigo(m, 0)
        motor, _ = crear_motor(m)
        motor.iniciar()
        self.assertTrue(e.activo)
        self.assertTrue(motor.avanzar_hasta_jugador())
        self.assertEqual(motor.reloj, 0)

    def test_mover_resultados(self):
        motor, _ = crear_motor(crear_mazmorra(cargadas=[0]))
        motor.iniciar()
        motor.avanzar_hasta_jugador()
        self.assertEqual(motor.mover_jugador(N), "sin_salida")
        self.assertEqual(motor.mover_jugador(E), "pendiente")
        motor.mazmorra.sala(1).contenido_cargado = True
        self.assertEqual(motor.mover_jugador(E), "ok")
        self.assertEqual(motor.jugador.Sala_Actual, 1)
        self.assertEqual(motor.jugador.acciones, 1)
        motor.avanzar_hasta_jugador()
        self.assertEqual(motor.reloj, 100)
        self.assertEqual(motor.mover_jugador(E), "cerrada")

    def test_abrir_puerta_y_ganar(self):
        motor, _ = crear_motor()
        motor.jugador.Sala_Actual = 1
        motor.iniciar()
        motor.avanzar_hasta_jugador()
        self.assertEqual(motor.abrir_puerta(O, lambda _: True), "nada_que_abrir")
        self.assertEqual(motor.abrir_puerta(E, lambda _: False), "sin_llave")
        self.assertEqual(motor.abrir_puerta(E, lambda llave: llave == "llave_final"), "ok")
        motor.avanzar_hasta_jugador()
        self.assertEqual(motor.reloj, 50)  # abrir cuesta 50
        self.assertEqual(motor.mover_jugador(E), "ok")
        self.assertTrue(motor.terminado)
        self.assertTrue(motor.victoria)

    def test_ataque_hace_al_menos_uno(self):
        motor, _ = crear_motor()
        defensor = ActorDePrueba("d", 100, 100, 0, 999, 100, 0)
        motor.atacar(motor.jugador, defensor)
        self.assertEqual(defensor.vida, 99)

    def test_ataque_en_rango(self):
        motor, _ = crear_motor()
        for _ in range(50):
            defensor = ActorDePrueba("d", 100, 100, 0, 2, 100, 0)
            motor.atacar(motor.jugador, defensor)  # 5 + [0..4] - 2
            self.assertIn(100 - defensor.vida, range(3, 8))

    def test_matar_enemigo_suelta_objetos(self):
        m = crear_mazmorra()
        e = poner_enemigo(m, 0, vida=1)
        motor, _ = crear_motor(m)
        motor.iniciar()
        motor.avanzar_hasta_jugador()
        self.assertEqual(motor.atacar_enemigo("e-1"), "ok")
        self.assertFalse(e.Vivo())
        self.assertFalse(e.Evento_pendiente.esta_valido())
        self.assertEqual(motor.enemigos_derrotados, 1)
        self.assertEqual(m.sala(0).objetos, ["itm_queso"])
        self.assertEqual(motor.atacar_enemigo("e-1"), "sin_objetivo")

    def test_enemigo_ataca_y_mata_al_jugador(self):
        m = crear_mazmorra()
        poner_enemigo(m, 0, ficha=crear_ficha(ataque=100, velocidad=1000))
        motor, _ = crear_motor(m)
        motor.iniciar()
        motor.avanzar_hasta_jugador()
        motor.esperar()
        self.assertFalse(motor.avanzar_hasta_jugador())
        self.assertTrue(motor.terminado)
        self.assertFalse(motor.victoria)
        self.assertFalse(motor.jugador.Vivo())

    def test_rastreador_persigue_al_jugador(self):
        m = crear_mazmorra()
        e = poner_enemigo(m, 1, ficha=crear_ficha("rastreador", ataque=0))
        e.activo = True
        motor, _ = crear_motor(m)
        motor.iniciar()
        motor.programar_accion(e, 100)
        motor.avanzar_hasta_jugador()
        motor.esperar()
        motor.avanzar_hasta_jugador()
        self.assertEqual(e.Sala_Actual, 0)

    def test_trampa_hace_dano_al_entrar(self):
        m = crear_mazmorra()
        m.sala(1).trampas.append(TrampaViva("t-1", FichaTrampaDTO("pinchos", "Pinchos", 4, 300)))
        motor, _ = crear_motor(m)
        motor.iniciar()
        motor.avanzar_hasta_jugador()
        motor.mover_jugador(E)
        self.assertEqual(motor.jugador.vida, 26)
        self.assertEqual(m.trampas_armadas(1), [])

    def test_pocion_velocidad_no_da_turno_extra(self):
        motor, _ = crear_motor()
        motor.iniciar()
        motor.avanzar_hasta_jugador()          # turno del jugador en t=0
        motor.efectos.aplicar(Velocidad(motor.jugador, 100, 500))
        motor.esperar()                        # velocidad 200 -> siguiente turno en t=50
        motor.avanzar_hasta_jugador()
        self.assertEqual(motor.reloj, 50)

    def test_errante_no_entra_a_sala_sin_esqueleto(self):
        m = Mazmorra(sala_salida=9, llave_salida="x")
        m.cargar_esqueleto([SalaDTO(0, "A", [None, None, SalidaDTO(5), None], "1"),
                            SalaDTO(1, "B", [None, None, None, None], "1")])
        m.sala(0).contenido_cargado = m.sala(1).contenido_cargado = True
        e = poner_enemigo(m, 0, ficha=crear_ficha("errante"))
        e.activo = True
        motor, _ = crear_motor(m)
        motor.jugador.Sala_Actual = 1
        motor.turno_enemigo(e)
        self.assertEqual(e.Sala_Actual, 0)

    def test_ordenar_enemigos_por_id_al_activar(self):
        m = crear_mazmorra()
        b = poner_enemigo(m, 0, "e-2")
        a = poner_enemigo(m, 0, "e-1")
        motor, _ = crear_motor(m)
        motor.iniciar()
        self.assertLess(a.Evento_pendiente.secuencia, b.Evento_pendiente.secuencia)


if __name__ == "__main__":
    unittest.main()
