"""
Tests de Logic/PartidaGuardada.py: el Motor se guarda en los DTOs y se vuelve a armar igual.

Ejecutar desde la raiz del proyecto:
    python3 -m unittest discover -s tests -p "*.py" -v     # "*.py": tambien los Test*.py
"""
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from Data import GuardadoBinario
from DTO.CriptaDTO import CriptaDTO
from DTO.Direcciones import E, O
from DTO.FichaEnemigoDTO import FichaEnemigoDTO
from DTO.FichaTrampaDTO import FichaTrampaDTO
from DTO.ObjetoDTO import ObjetoDTO
from DTO.SalaDTO import SalaDTO, SalidaDTO, EnemigoEnSalaDTO, TrampaEnSalaDTO
from Logic.Efectos import Veneno
from Logic.Inventario import Inventario
from Logic.jugador import Jugador
from Logic.Mazmorra import Mazmorra
from Logic.motorJuego import Motor
from Logic.PartidaGuardada import PartidaGuardada


# ---------- Fabricas de datos de prueba

FICHAS = {
    "rata": FichaEnemigoDTO(id="rata", nombre="Rata", vida_max=10, ataque=3, defensa=1, velocidad=100,
                            comportamiento="rastreador", suelta=["queso"]),
    "pinchos": FichaTrampaDTO("pinchos", "Pinchos", 4, 300),
    "daga": ObjetoDTO("daga", "Daga", "arma", 1, 5, ataque_bonus=2),
    "cota": ObjetoDTO("cota", "Cota", "armadura", 5, 10, defensa_bonus=3),
    "llave_k": ObjetoDTO("llave_k", "Llave", "llave", 1, 1, abre="k"),
    "pocion_vel": ObjetoDTO("pocion_vel", "Pocion rapida", "pocion", 1, 3, modificador_velocidad=25, duracion=600),
    "antorcha": ObjetoDTO("antorcha", "Antorcha", "antorcha", 1, 1, duracion=700),
    "queso": ObjetoDTO("queso", "Queso", "pocion", 1, 1, cura=2),
}


def fn_ficha(id_ficha):
    return FICHAS[id_ficha]


def crear_cripta():
    return CriptaDTO(id="c1", version="1", salas_total=3, paginas=1, salas_por_pagina=3,
                     sala_inicial=0, sala_salida=2, llave_salida="llave_final",
                     presupuesto_solicitudes=10, inventario_max=6, jugador_vida_max=30,
                     jugador_ataque=5, jugador_defensa=2, jugador_velocidad=100)


def esqueleto():
    """0 <-E/O-> 1 <-E/O-> 2 (salida). La puerta 0-1 se abre con "llave_k" y se cierra sola a los 500."""
    return [
        SalaDTO(0, "Entrada", [None, None, SalidaDTO(1, True, "llave_k", 500), None], "1"),
        SalaDTO(1, "Pasillo", [None, None, SalidaDTO(2, True, "llave_final"), SalidaDTO(0, True, "llave_k", 500)], "1"),
        SalaDTO(2, "Salida", [None, None, None, SalidaDTO(1, True, "llave_final")], "1"),
    ]


def contenido(id_sala):
    sala = esqueleto()[id_sala]
    if id_sala == 0:
        objetos = ["daga", "daga", "cota", "llave_k", "pocion_vel", "antorcha"]
        return SalaDTO(sala.id, sala.nombre, sala.salidas, "1", True, [], objetos, [])
    return SalaDTO(sala.id, sala.nombre, sala.salidas, "1", True,
                   [EnemigoEnSalaDTO("r-1", "rata")], [], [TrampaEnSalaDTO("t-1", "pinchos")])


def crear_motor(mensajes):
    cripta = crear_cripta()
    mazmorra = Mazmorra(cripta.sala_salida, cripta.llave_salida)
    mazmorra.cargar_esqueleto(esqueleto())
    mazmorra.cargar_contenido(contenido(0), fn_ficha)
    mazmorra.cargar_contenido(contenido(1), fn_ficha)       # la sala 2 queda sin contenido
    motor = Motor(7, Jugador(cripta), mazmorra, mensajes.append, Inventario(cripta.inventario_max))
    motor.iniciar()
    motor.avanzar_hasta_jugador()
    return motor


def partida_a_media(mensajes):
    """Deja vivos todos los tipos de evento: accion_actor, veneno, velocidad, antorcha,
    rearme_trampa y cierre_puerta; y dos dagas iguales con la equipada en la posición 1."""
    motor = crear_motor(mensajes)
    acciones = [
        lambda: motor.recoger("daga", fn_ficha),
        lambda: motor.recoger("daga", fn_ficha),
        lambda: motor.recoger("cota", fn_ficha),
        lambda: motor.recoger("llave_k", fn_ficha),
        lambda: motor.recoger("pocion_vel", fn_ficha),
        lambda: motor.recoger("antorcha", fn_ficha),
        lambda: motor.equipar("daga"),
        lambda: motor.equipar("cota"),
        lambda: motor.usar("pocion_vel"),
        lambda: motor.usar("antorcha"),
        lambda: motor.abrir_puerta(E, motor.inventario.tiene_objeto),
        lambda: motor.mover_jugador(E),
        motor.esperar,                                     # la rata ataca: el azar avanza
        motor.esperar,
    ]
    for accion in acciones:
        assert accion() == "ok"
        motor.avanzar_hasta_jugador()
    motor.efectos.aplicar(Veneno(motor.jugador, 1))
    return motor


def guardar(motor):
    return PartidaGuardada.guardar(motor, crear_cripta(), "cat-1", 7, "logs/p.log", motor.jugador.acciones)


def cargar(partida, salas, mensajes):
    return PartidaGuardada.cargar(partida, salas, crear_cripta(), esqueleto(), fn_ficha, mensajes.append)


def continuar(motor):
    """Las mismas acciones para la partida original y la cargada; devuelve los resultados."""
    resultados = []
    for accion in ["atacar", "esperar", "atacar", "esperar", "volver", "esperar", "atacar",
                   "esperar", "esperar", "esperar", "esperar", "esperar"]:
        if motor.terminado:
            break
        if accion == "atacar":
            resultados.append(motor.atacar_enemigo("r-1"))
        elif accion == "volver":
            resultados.append(motor.mover_jugador(O))
        else:
            resultados.append(motor.esperar())
        motor.avanzar_hasta_jugador()
    return resultados


# ---------- Tests

class TestPartidaGuardada(unittest.TestCase):
    def setUp(self):
        self.mensajes = []
        self.motor = partida_a_media(self.mensajes)
        self.partida, self.salas = guardar(self.motor)

    def test_guarda_todos_los_tipos_de_evento(self):
        tipos = [e.tipo for e in self.partida.eventos]
        for tipo in ["accion_actor", "veneno", "velocidad", "antorcha", "rearme_trampa", "cierre_puerta"]:
            self.assertIn(tipo, tipos)

    def test_guarda_el_equipo_por_posicion(self):
        inventario = self.partida.inventario
        self.assertEqual(["cota", "daga", "daga", "llave_k", "antorcha"], inventario.objetos)   # la antorcha no se gasta al usarla
        self.assertEqual(1, inventario.arma)
        self.assertEqual(0, inventario.armadura)

    def test_guarda_todas_las_salas(self):
        self.assertEqual([0, 1, 2], [s.id for s in self.salas])
        self.assertFalse(self.salas[2].contenido_cargado)
        self.assertFalse(self.salas[1].trampas[0].armada)
        self.assertEqual([False, False, False, False], self.salas[0].puertas_cerradas)

    def test_cargar_y_volver_a_guardar_da_lo_mismo(self):
        motor = cargar(self.partida, self.salas, [])
        self.assertEqual((self.partida, self.salas), guardar(motor))

    def test_cargar_rearma_el_motor(self):
        motor = cargar(self.partida, self.salas, [])
        self.assertEqual(self.motor.reloj, motor.reloj)
        self.assertEqual(1, motor.jugador.Sala_Actual)
        self.assertIs(motor.inventario.arma_equipada(), motor.jugador.arma)
        self.assertIs(motor.inventario.armadura_equipada(), motor.jugador.armadura)
        self.assertEqual(self.motor.jugador.ataque_efectivo(), motor.jugador.ataque_efectivo())
        rata = motor.mazmorra.buscar_enemigo(1, "r-1")
        self.assertTrue(rata.activo)
        self.assertTrue(rata.Evento_pendiente.esta_valido())
        for efecto in motor.efectos.activos:
            self.assertTrue(efecto.evento.esta_valido())
        self.assertFalse(motor.mazmorra.contenido_cargado(2))
        self.assertEqual(0, motor.historial.cantidad())

    def test_la_partida_cargada_sigue_igual_que_la_original(self):
        mensajes_cargada = []
        motor = cargar(self.partida, self.salas, mensajes_cargada)
        antes = len(self.mensajes)
        self.assertEqual(continuar(self.motor), continuar(motor))
        self.assertEqual(self.mensajes[antes:], mensajes_cargada)
        self.assertEqual(guardar(self.motor), guardar(motor))
        self.assertGreater(motor.enemigos_derrotados, 0)    # la continuación sí hizo algo

    def test_por_el_archivo_binario(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "partida.sav")
            GuardadoBinario.guardar(ruta, self.partida, self.salas)
            motor = cargar(GuardadoBinario.cargar(ruta), GuardadoBinario.cargar_salas(ruta), [])
        self.assertEqual((self.partida, self.salas), guardar(motor))
        self.assertEqual(continuar(self.motor), continuar(motor))
        self.assertEqual(guardar(self.motor), guardar(motor))

    def test_retroceso_despues_de_cargar(self):
        mensajes = []
        motor = cargar(self.partida, self.salas, mensajes)
        self.assertEqual("ok", motor.esperar())
        motor.avanzar_hasta_jugador()
        self.assertTrue(motor.historial.deshacer())
        self.assertEqual((self.partida, self.salas), guardar(motor))


if __name__ == "__main__":
    unittest.main()
