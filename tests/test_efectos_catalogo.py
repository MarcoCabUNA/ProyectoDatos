"""
Tests de los efectos que declara el catálogo (§2.10): lectura tolerante de la ficha (DTO/EfectoFichaDTO.py),
conservación en la caché en disco y su simulación en Lógica (veneno al golpear o por trampa, regeneración,
cambio de velocidad), incluidos retroceso y guardado.

Ejecutar desde la raiz del proyecto:
    python3 -m unittest tests.test_efectos_catalogo -v
"""
import os
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from Data.AlmacenCatalogo import AlmacenCatalogo
from Data.FuenteJson import FuenteJson
from DTO.CriptaDTO import CriptaDTO
from DTO.Direcciones import E
from DTO.EfectoFichaDTO import EfectoFichaDTO, leer_efectos
from DTO.FichaEnemigoDTO import FichaEnemigoDTO
from DTO.FichaTrampaDTO import FichaTrampaDTO
from DTO.ObjetoDTO import ObjetoDTO
from DTO.SalaDTO import SalaDTO, SalidaDTO
from Logic.Enemigo import Enemigo
from Logic.Inventario import Inventario
from Logic.jugador import Jugador
from Logic.Mazmorra import Mazmorra, TrampaViva
from Logic.motorJuego import Motor
from Logic.PartidaGuardada import PartidaGuardada


# ---------- Fabricas de datos de prueba

def json_enemigo(**extra):
    d = {"id": "ent_arana", "clase": "enemigo", "nombre": "Araña", "vida_max": 10, "ataque": 4,
         "defensa": 0, "velocidad": 100, "comportamiento": "guardián", "suelta": None}
    d.update(extra)
    return d


def json_trampa(**extra):
    d = {"id": "trp_aguja", "clase": "trampa", "nombre": "Aguja", "daño": 3, "rearme": None}
    d.update(extra)
    return d


def enemigo_desde(d):
    return FichaEnemigoDTO.desde_diccionario(d)


def trampa_desde(d):
    return FichaTrampaDTO.desde_diccionario(d)


def crear_cripta():
    return CriptaDTO(id="c1", version="1", salas_total=2, paginas=1, salas_por_pagina=2,
                     sala_inicial=0, sala_salida=1, llave_salida="llave_final",
                     presupuesto_solicitudes=10, inventario_max=5, jugador_vida_max=30,
                     jugador_ataque=5, jugador_defensa=0, jugador_velocidad=100)


def esqueleto():
    """0 <-E/O-> 1, abierta."""
    return [SalaDTO(0, "Entrada", [None, None, SalidaDTO(1), None], "1"),
            SalaDTO(1, "Pasillo", [None, None, None, SalidaDTO(0)], "1")]


def crear_motor(enemigo_en_0=None, vida_enemigo=None, trampa_en_1=None):
    """Motor iniciado y detenido en la primera decisión del jugador (t=0)."""
    mazmorra = Mazmorra(1, "llave_final")
    mazmorra.cargar_esqueleto(esqueleto())
    for i in (0, 1):
        mazmorra.sala(i).contenido_cargado = True
    if enemigo_en_0 is not None:
        mazmorra.sala(0).enemigos.append(Enemigo(enemigo_en_0, "e-1", vida_enemigo, 1, 0))
    if trampa_en_1 is not None:
        mazmorra.sala(1).trampas.append(TrampaViva("t-1", trampa_en_1))
    mensajes = []
    motor = Motor(7, Jugador(crear_cripta()), mazmorra, mensajes.append, Inventario(5))
    motor.iniciar()
    motor.avanzar_hasta_jugador()
    return motor, mensajes


def deshacer(motor):
    """Lo mismo que hace el pergamino (Motor._usar_pergamino) sin necesitar uno en el inventario."""
    motor.historial.descartar_intervalo_abierto()
    return motor.historial.deshacer()


def esperar_hasta(motor, tiempo):
    while not motor.terminado and motor.reloj < tiempo:
        motor.esperar()
        motor.avanzar_hasta_jugador()


# ---------- Lectura tolerante de la ficha

class TestLecturaDeEfectos(unittest.TestCase):

    def test_ficha_sin_efectos(self):
        self.assertEqual(enemigo_desde(json_enemigo()).efectos, ())
        self.assertEqual(trampa_desde(json_trampa()).efectos, ())

    def test_formas_aceptadas_del_veneno(self):
        esperado = (EfectoFichaDTO("veneno", 2),)
        for extra in ({"veneno": 2}, {"veneno": "2"}, {"veneno": 2.0}, {"Veneno": 2},
                      {"veneno": {"daño": 2}}, {"veneno": {"cantidad": 2}}, {"daño_veneno": 2},
                      {"efectos": [{"tipo": "veneno", "valor": 2}]},
                      {"efectos": [{"efecto": "Envenenamiento", "daño": 2}]}):
            with self.subTest(extra=extra):
                self.assertEqual(enemigo_desde(json_enemigo(**extra)).efectos, esperado)

    def test_veneno_con_duracion_del_catalogo(self):
        f = enemigo_desde(json_enemigo(veneno={"daño": 2, "duracion": 240}))
        self.assertEqual(f.efectos, (EfectoFichaDTO("veneno", 2, 240),))

    def test_regeneracion_con_y_sin_tilde(self):
        for extra in ({"regeneracion": 3}, {"regeneración": 3}, {"Regeneración": {"cantidad": 3}}):
            with self.subTest(extra=extra):
                self.assertEqual(enemigo_desde(json_enemigo(**extra)).efectos, (EfectoFichaDTO("regeneracion", 3),))

    def test_velocidad_exige_duracion(self):
        self.assertEqual(enemigo_desde(json_enemigo(modificador_velocidad=-30)).efectos, ())
        f = enemigo_desde(json_enemigo(modificador_velocidad=-30, duracion=300))
        self.assertEqual(f.efectos, (EfectoFichaDTO("velocidad", -30, 300),))

    def test_valores_invalidos_se_ignoran_sin_caerse(self):
        for extra in ({"veneno": "mucho"}, {"veneno": True}, {"veneno": None}, {"veneno": 0},
                      {"veneno": -2}, {"regeneracion": [1, 2]}, {"efectos": "veneno"},
                      {"efectos": [None, 3, {"tipo": "veneno"}]}):
            with self.subTest(extra=extra):
                self.assertEqual(enemigo_desde(json_enemigo(**extra)).efectos, ())

    def test_un_tipo_repetido_gana_la_primera_aparicion(self):
        f = enemigo_desde(json_enemigo(efectos=[{"tipo": "veneno", "valor": 5}], veneno=1))
        self.assertEqual(f.efectos, (EfectoFichaDTO("veneno", 5),))

    def test_varios_efectos_en_orden(self):
        d = json_enemigo(efectos=[{"tipo": "regeneracion", "valor": 1},
                                  {"tipo": "velocidad", "valor": -20, "duracion": 200}], veneno=2)
        tipos = [e.tipo for e in enemigo_desde(d).efectos]
        self.assertEqual(tipos, ["regeneracion", "velocidad", "veneno"])

    def test_tipo_desconocido_se_conserva_con_su_nombre(self):
        f = enemigo_desde(json_enemigo(efectos=[{"tipo": "Ceguera", "valor": 1}]))
        self.assertEqual(f.efectos, (EfectoFichaDTO("ceguera", 1),))

    def test_trampa_de_veneno_sin_valor_usa_su_dano_como_pulso(self):
        t = trampa_desde(json_trampa(efecto="veneno"))
        self.assertEqual(t.efectos, (EfectoFichaDTO("veneno", 3),))
        self.assertEqual(t.dano_al_activarse(), 0)

    def test_trampa_de_veneno_con_valor_conserva_el_dano_inmediato(self):
        t = trampa_desde(json_trampa(efecto="veneno", valor=1))
        self.assertEqual(t.efectos, (EfectoFichaDTO("veneno", 1),))
        self.assertEqual(t.dano_al_activarse(), 3)

    def test_trampa_con_efecto_dano_es_una_trampa_comun(self):
        t = trampa_desde(json_trampa(efecto="daño"))
        self.assertEqual((t.efectos, t.dano_al_activarse()), ((), 3))

    def test_trampa_sin_dano_y_rearme_invalido(self):
        d = json_trampa(veneno=2, rearme="nunca")
        del d["daño"]
        t = trampa_desde(d)
        self.assertEqual((t.danio, t.rearme, t.efectos), (0, 300, (EfectoFichaDTO("veneno", 2),)))

    def test_construir_sin_efectos_sigue_funcionando(self):
        """Las fichas creadas a mano (pruebas, bench) no tienen que dar efectos ni extras."""
        self.assertEqual(FichaTrampaDTO("t", "T", 4, 300).dano_al_activarse(), 4)
        self.assertEqual(leer_efectos({}), ())


# ---------- La caché en disco no pierde lo que manda el API

class TestCamposExtraEnDisco(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.mkdtemp()
        self.almacen = AlmacenCatalogo("v1", self.temp)
        self.almacen.preparar()

    def tearDown(self):
        shutil.rmtree(self.temp)

    def ida_y_vuelta(self, d):
        ficha = FuenteJson.ficha_desde_diccionario(d)
        self.almacen.guardar(ficha)
        return ficha, self.almacen.leer(ficha.id)

    def test_enemigo_conserva_efectos_y_campos_desconocidos(self):
        original, leida = self.ida_y_vuelta(json_enemigo(veneno={"daño": 2}, regeneración=1, aura="roja"))
        self.assertEqual(leida.efectos, original.efectos)
        self.assertEqual(leida.a_diccionario(), original.a_diccionario())
        self.assertEqual(leida.a_diccionario()["aura"], "roja")

    def test_trampa_conserva_efecto(self):
        original, leida = self.ida_y_vuelta(json_trampa(efecto="veneno"))
        self.assertEqual((leida.efectos, leida.dano_al_activarse()), (original.efectos, 0))

    def test_objeto_conserva_campos_desconocidos(self):
        d = {"id": "itm_x", "clase": "pocion", "nombre": "X", "peso": 1, "valor": 2, "cura": 3, "rareza": "épica"}
        original, leida = self.ida_y_vuelta(d)
        self.assertEqual(leida.a_diccionario(), d)
        self.assertEqual(leida, original)

    def test_ficha_sin_campos_nuevos_queda_igual_que_antes(self):
        d = json_enemigo()
        d["suelta"] = []
        self.assertEqual(enemigo_desde(d).a_diccionario(), d)


# ---------- Simulación en Lógica

class TestEfectosEnElJuego(unittest.TestCase):

    def test_enemigo_venenoso_envenena_al_golpear(self):
        ficha = enemigo_desde(json_enemigo(veneno=2))
        motor, mensajes = crear_motor(enemigo_en_0=ficha)
        motor.esperar()
        motor.avanzar_hasta_jugador()                  # t=100: la araña golpea antes que el jugador
        self.assertTrue(motor.efectos.tiene(motor.jugador, "veneno"))
        self.assertTrue(any("envenena" in m for m in mensajes))

    def test_trampa_venenosa_pulsa_y_termina(self):
        motor, _ = crear_motor(trampa_en_1=trampa_desde(json_trampa(efecto="veneno")))
        motor.mover_jugador(E)                         # t=0: entra a la trampa, sin daño inmediato
        self.assertEqual(motor.jugador.vida, 30)
        self.assertTrue(motor.efectos.tiene(motor.jugador, "veneno"))
        motor.avanzar_hasta_jugador()
        esperar_hasta(motor, 500)
        self.assertEqual(motor.jugador.vida, 30 - 5 * 3)   # pulsos en 80, 160, 240, 320 y 400
        self.assertFalse(motor.efectos.tiene(motor.jugador, "veneno"))

    def test_trampa_que_ralentiza(self):
        trampa = trampa_desde(json_trampa(modificador_velocidad=-50, duracion=300))
        motor, _ = crear_motor(trampa_en_1=trampa)
        motor.mover_jugador(E)
        self.assertEqual(motor.jugador.velocidad, 50)
        self.assertEqual(motor.jugador.Evento_pendiente.tiempo, 200)   # costo 100 a velocidad 50 (§2.3)

    def test_regeneracion_cada_200_sin_pasar_de_vida_max(self):
        ficha = enemigo_desde(json_enemigo(regeneracion=3, ataque=0))
        motor, _ = crear_motor(enemigo_en_0=ficha, vida_enemigo=5)
        enemigo = motor.mazmorra.sala(0).enemigos[0]
        esperar_hasta(motor, 200)
        self.assertEqual(enemigo.vida, 8)
        esperar_hasta(motor, 400)
        self.assertEqual(enemigo.vida, 10)             # 11 se topa en vida_max

    def test_regeneracion_empieza_al_activarse(self):
        ficha = enemigo_desde(json_enemigo(regeneracion=3))
        mazmorra = Mazmorra(1, "llave_final")
        mazmorra.cargar_esqueleto(esqueleto())
        mazmorra.sala(1).enemigos.append(Enemigo(ficha, "e-9", 5, 1, 1))   # dormida en otra sala
        motor = Motor(7, Jugador(crear_cripta()), mazmorra, None, Inventario(5))
        motor.iniciar()
        self.assertEqual(motor.efectos.activos, [])

    def test_al_morir_se_cancela_la_regeneracion(self):
        ficha = enemigo_desde(json_enemigo(regeneracion=3, ataque=0, defensa=0))
        motor, _ = crear_motor(enemigo_en_0=ficha, vida_enemigo=1)
        motor.atacar_enemigo("e-1")
        self.assertEqual(motor.efectos.activos, [])
        motor.avanzar_hasta_jugador()
        esperar_hasta(motor, 600)
        self.assertEqual(motor.mazmorra.sala(0).enemigos[0].vida, 0)   # nunca revive regenerando

    def test_efecto_desconocido_avisa_y_no_rompe(self):
        ficha = enemigo_desde(json_enemigo(efectos=[{"tipo": "ceguera", "valor": 1}]))
        motor, mensajes = crear_motor(enemigo_en_0=ficha)
        self.assertTrue(any("desconocido" in m for m in mensajes))
        esperar_hasta(motor, 300)
        self.assertEqual(sum("desconocido" in m for m in mensajes), 1)    # solo al activarse

    def test_pergamino_deshace_el_envenenamiento_de_la_trampa(self):
        motor, _ = crear_motor(trampa_en_1=trampa_desde(json_trampa(efecto="veneno")))
        motor.mover_jugador(E)
        motor.avanzar_hasta_jugador()
        self.assertTrue(deshacer(motor))
        self.assertEqual(motor.jugador.Sala_Actual, 0)
        self.assertEqual(motor.efectos.activos, [])
        self.assertTrue(motor.mazmorra.sala(1).trampas[0].armada)
        esperar_hasta(motor, 600)                      # los pulsos deshechos no hacen daño
        self.assertEqual(motor.jugador.vida, 30)

    def test_misma_semilla_misma_partida(self):
        def jugar():
            ficha = enemigo_desde(json_enemigo(veneno=1, regeneracion=2))
            motor, mensajes = crear_motor(enemigo_en_0=ficha)
            for _ in range(4):
                motor.atacar_enemigo("e-1")
                motor.avanzar_hasta_jugador()
            return mensajes, motor.reloj, motor.jugador.vida
        self.assertEqual(jugar(), jugar())


# ---------- Guardado

class TestGuardadoConEfectos(unittest.TestCase):

    def test_guardar_y_cargar_conserva_regeneracion_y_veneno(self):
        ficha = enemigo_desde(json_enemigo(veneno=2, regeneracion=3))
        motor, _ = crear_motor(enemigo_en_0=ficha, vida_enemigo=4)
        motor.esperar()
        motor.avanzar_hasta_jugador()                  # t=100: ya envenenado
        partida, salas = PartidaGuardada.guardar(motor, crear_cripta(), "v1", 7)

        cargado = PartidaGuardada.cargar(partida, salas, crear_cripta(), esqueleto(), lambda _id: ficha)
        tipos = sorted(e.tipo for e in cargado.efectos.activos)
        self.assertEqual(tipos, ["regeneracion", "veneno"])

        for m in (motor, cargado):                     # el original y el cargado siguen igual
            esperar_hasta(m, 400)
        self.assertEqual(cargado.jugador.vida, motor.jugador.vida)
        self.assertEqual(cargado.mazmorra.sala(0).enemigos[0].vida, motor.mazmorra.sala(0).enemigos[0].vida)


if __name__ == "__main__":
    unittest.main()
