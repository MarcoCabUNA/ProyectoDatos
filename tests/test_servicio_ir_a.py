"""
Pruebas del servicio de «ir a» (feature 002, integrante 3): T107, T108 y T114, más el controlador (T112).

El motor, el mapa, el reloj y los servicios son los reales. Los escenarios con letras (A = 1 … G = 7) se arman a mano
con tests/ayudas_ir_a.py (sin red ni carpetas); los del controlador usan una partida real sobre una cuadrícula sin
enemigos (servicio_partida_cuadricula). Las salas de la cuadrícula se llaman «Sala 1» … «Sala 25».
"""
import dataclasses
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import Service.ServicioIrA as modulo_servicio  # noqa: E402
from DTO.AccionDTO import AccionDTO  # noqa: E402
from DTO.Direcciones import E as ESTE_DIR  # noqa: E402
from DTO.ObjetoDTO import ObjetoDTO  # noqa: E402
from DTO.ViajeDTO import (AMBIGUO, DANO, DESTINO_INVALIDO, ENEMIGOS, INTERRUMPIDO, LLEGO, PASO_RECHAZADO,  # noqa: E402
                          SIN_RUTA, TERMINADA, YA_AQUI)
from Logic.BusquedaCostoMinimo import paso_desde_cero  # noqa: E402
from Logic.Efectos import Regeneracion, Veneno, Antorcha  # noqa: E402
from Logic.EventoPorg import EventoProgramado  # noqa: E402
from Logic.GrafoMapaConocido import GrafoMapaConocido  # noqa: E402
from Logic.Mazmorra import TrampaViva  # noqa: E402
from DTO.FichaTrampaDTO import FichaTrampaDTO  # noqa: E402
from Service.ArmadorEstado import ArmadorEstado  # noqa: E402
from Service.ServicioIrA import ServicioIrA  # noqa: E402
from Service.ServicioLineaTiempo import ServicioLineaTiempo  # noqa: E402
from tests.ayudas_controladores import crear_backend  # noqa: E402
from tests.ayudas_ir_a import (BitacoraPrueba, contexto_de_prueba, dar_pergaminos_a, poner_dormido,  # noqa: E402
                               servicio_partida_cuadricula)
from tests.ayudas_mapa import A, B, C, D, E, ESTE, NORTE, SUR, estados, salida  # noqa: E402
from tests.ayudas_terreno import ficha_errante, poner_enemigo  # noqa: E402
from UIController.ControladorBackend import ErrorOperacion  # noqa: E402

F, G = 6, 7


def rombo(costo_bd=100):
    """A –E– B –S– D y A –S– C –E– D (por B cuesta 100 + costo_bd; por C, 400), y D –E– E."""
    return [salida(A, ESTE, B, 100), salida(B, SUR, D, costo_bd), salida(A, SUR, C, 200), salida(C, ESTE, D, 200),
            salida(D, ESTE, E, 100)]


def correr(servicio, contexto, nombre, limite=20):
    """Pide el viaje y da pasos hasta que se detiene: (lista de pasos, sala y reloj después de cada uno)."""
    inicio = servicio.iniciar(contexto, nombre)
    assert inicio.viaje is not None, inicio.motivos
    viaje, pasos, huellas = inicio.viaje, [], []
    for _ in range(limite):
        paso = servicio.dar_paso(contexto, viaje)
        pasos.append(paso)
        huellas.append((contexto.jugador.Sala_Actual, contexto.motor.reloj))
        viaje = paso.viaje
        if viaje is None:
            return pasos, huellas
    raise AssertionError("el viaje no se detuvo")


def foto(contexto):
    """Lo que no puede cambiar si una orden no da ningún paso."""
    return (contexto.motor.reloj, contexto.jugador.acciones, contexto.jugador.Sala_Actual,
            estados(contexto.motor.mapa), None if contexto.bitacora is None else list(contexto.bitacora.lineas))


class PruebasRechazoSinTocarNada(unittest.TestCase):

    def test_h6_1_apendiceB_caso1_fr251_rechazo_sin_tiempo_ni_accion_ni_log(self):
        salidas = rombo() + [salida(E, ESTE, F), salida(F, ESTE, G)]
        contexto = contexto_de_prueba(G, salidas, A, [], BitacoraPrueba())
        self.assertEqual(contexto.motor.mapa.estado_sala(B), 1)                # B avistada
        self.assertEqual(contexto.motor.mapa.estado_sala(G), 0)                # G desconocida
        antes = foto(contexto)
        servicio = ServicioIrA()
        for nombre in ("Sala 2", "Sala 7", "Sala 99"):
            inicio = servicio.iniciar(contexto, nombre)
            self.assertIsNone(inicio.viaje)
            self.assertEqual(inicio.motivos, [DESTINO_INVALIDO], nombre)
            self.assertEqual(foto(contexto), antes, nombre)

    def test_fr251_ambiguo_sin_tiempo(self):
        contexto = contexto_de_prueba(5, rombo(), A, [B, C, D], BitacoraPrueba())
        contexto.mazmorra.sala(C).nombre = "Sala 2"                            # dos exploradas con el mismo nombre
        antes = foto(contexto)
        inicio = ServicioIrA().iniciar(contexto, "sala 2")
        self.assertEqual((inicio.viaje, inicio.motivos), (None, [AMBIGUO]))
        self.assertEqual(foto(contexto), antes)

    def test_h6_8_a30_fr251_ya_aqui_sin_pasos_ni_tiempo(self):
        contexto = contexto_de_prueba(5, rombo(), A, [B, C, D], BitacoraPrueba())
        antes = foto(contexto)
        inicio = ServicioIrA().iniciar(contexto, "Sala 1")
        self.assertEqual((inicio.viaje, inicio.motivos), (None, [YA_AQUI]))
        self.assertEqual(foto(contexto), antes)

    def test_iniciar_con_destino_valido_no_da_ningun_paso(self):
        contexto = contexto_de_prueba(5, rombo(), A, [B, C, D], BitacoraPrueba())
        antes = foto(contexto)
        inicio = ServicioIrA().iniciar(contexto, "  SALA 4 ")
        self.assertEqual(inicio.motivos, [])
        self.assertEqual((inicio.viaje.destino, inicio.viaje.nombre_destino, inicio.viaje.pasos_dados), (D, "Sala 4", 0))
        self.assertEqual(inicio.viaje.acciones_esperadas, contexto.jugador.acciones)
        self.assertEqual(foto(contexto), antes)


class PruebasPasosDelViaje(unittest.TestCase):

    def test_h6_2_a24_fr250_fr253_fr254_dos_pasos_cada_uno_con_el_tiempo_de_su_salida(self):
        bitacora = BitacoraPrueba()
        contexto = contexto_de_prueba(5, rombo(150), A, [B, C, D], bitacora)
        pasos, huellas = correr(ServicioIrA(), contexto, "Sala 4")
        self.assertEqual(huellas, [(B, 100), (D, 250)])                       # 100 de A–B y 150 de B–D
        self.assertEqual([p.motivos for p in pasos], [[], [LLEGO]])
        self.assertEqual((pasos[0].viaje.pasos_dados, pasos[0].viaje.acciones_esperadas), (1, 1))
        self.assertIsNone(pasos[1].viaje)
        self.assertEqual(pasos[1].estado.reloj, 250)
        movimientos = [a for tipo, a in bitacora.lineas if tipo == "accion"]
        self.assertEqual([m.tipo for m in movimientos], ["mover", "mover"])   # FR-250: solo `mover`
        self.assertEqual([m.direccion for m in movimientos], [ESTE, SUR])

    def test_h6_3_a25_fr253_primer_paso_a_la_vecina_de_menor_id(self):
        salidas = [salida(A, ESTE, B, 100), salida(A, SUR, C, 100), salida(B, SUR, D, 100), salida(C, ESTE, D, 100),
                   salida(D, ESTE, E, 100)]
        contexto = contexto_de_prueba(5, salidas, A, [B, C, D])
        pasos, huellas = correr(ServicioIrA(), contexto, "Sala 4")
        self.assertEqual(huellas, [(B, 100), (D, 200)])

    def test_h6_4_a26_fr252_fr257_fr259_no_abre_puertas_con_la_llave(self):
        for con_otra_ruta in (True, False):
            salidas = [salida(A, ESTE, B, 100), salida(B, SUR, D, 100, True), salida(D, ESTE, E, 100)]
            if con_otra_ruta:
                salidas += [salida(A, SUR, C, 200), salida(C, ESTE, D, 200)]
            bitacora = BitacoraPrueba()
            contexto = contexto_de_prueba(5, salidas, A, [B, C, D] if con_otra_ruta else [B, D], bitacora)
            contexto.mazmorra.salida(B, SUR).llave = "itm_llave_x"
            contexto.inventario.recoger(ObjetoDTO(id="itm_llave_x", nombre="Llave", clase="llave", peso=1, valor=1,
                                                  abre="itm_llave_x"))
            self.assertEqual(contexto.motor.mapa.estado_cara(B, SUR), 2)           # B recuerda la cara CERRADA
            pasos, huellas = correr(ServicioIrA(), contexto, "Sala 4")
            self.assertTrue(contexto.mazmorra.salida(B, SUR).cerrada)
            self.assertTrue(contexto.inventario.tiene_objeto("itm_llave_x"))
            if con_otra_ruta:
                self.assertEqual(huellas, [(C, 200), (D, 400)])
                self.assertEqual([a.tipo for t, a in bitacora.lineas if t == "accion"], ["mover", "mover"])
            else:
                self.assertEqual([p.motivos for p in pasos], [[SIN_RUTA]])
                self.assertEqual((contexto.motor.reloj, contexto.jugador.acciones, bitacora.lineas), (0, 0, []))

    def test_h6_5_a27_fr212_fr252_sin_observar_no_se_usa(self):
        contexto = contexto_de_prueba(5, rombo(), A, [B, C, D])
        contexto.motor.mapa.caras[A * 4 + ESTE] = 0                           # la cara de A hacia B sin observar
        pasos, huellas = correr(ServicioIrA(), contexto, "Sala 4")
        self.assertEqual(huellas, [(C, 200), (D, 400)])

    def test_h6_6_a28_fr217_fr252_solo_salas_exploradas(self):
        contexto = contexto_de_prueba(5, rombo(), A, [D])                      # B y C solo avistadas
        antes = foto(contexto)
        pasos, _ = correr(ServicioIrA(), contexto, "Sala 4")
        self.assertEqual([p.motivos for p in pasos], [[SIN_RUTA]])
        self.assertEqual(foto(contexto), antes)

    def test_h6_7_a29_fr254_cierre_automatico_entre_pasos_en_su_instante(self):
        contexto = contexto_de_prueba(5, rombo(), B, [A, C, D])
        puerta = contexto.mazmorra.salida(B, SUR)
        puerta.cerrada, puerta.llave, puerta.cierre_automatico = True, "itm_x", 150
        contexto.mazmorra.salida(D, NORTE).cerrada = True
        contexto.mazmorra.salida(D, NORTE).llave = "itm_x"
        contexto.motor.mapa.caras[B * 4 + SUR] = 1                             # B la recuerda abierta
        self.assertEqual(contexto.motor.abrir_puerta(SUR, lambda llave: True), "ok")
        contexto.motor.avanzar_hasta_jugador()                                # t = 50
        self.assertEqual(contexto.motor.mapa.estado_cara(B, SUR), 1)
        servicio_linea = ServicioLineaTiempo()
        servicio_linea.ejecutar(contexto, AccionDTO("esperar"))               # t = 150: se cierra en su instante
        self.assertTrue(puerta.cerrada)
        self.assertEqual(contexto.motor.mapa.estado_cara(B, SUR), 2)           # el jugador está en B: lo ve cerrar
        pasos, huellas = correr(ServicioIrA(), contexto, "Sala 4")
        self.assertEqual([sala for sala, _ in huellas], [A, C, D])             # recalcula: por B ya no se puede

    def test_h6_9_a31_fr264_paso_con_antorcha_enemigos_y_trampas(self):
        recorrido = []
        for modo in ("viaje", "a_mano"):
            contexto = contexto_de_prueba(5, rombo(), A, [B, D])
            motor = contexto.motor
            motor.efectos.aplicar(Antorcha(contexto.jugador, 2000))
            contexto.mazmorra.sala(B).trampas.append(TrampaViva("t-1", FichaTrampaDTO("pinchos", "Pinchos", 4, 300)))
            poner_dormido(motor, B, ficha_errante(), "e-b")
            if modo == "viaje":
                pasos, _ = correr(ServicioIrA(), contexto, "Sala 4")
                self.assertEqual(len(pasos), 1)
                self.assertEqual(pasos[0].motivos, [ENEMIGOS, DANO])
            else:
                ServicioLineaTiempo().ejecutar(contexto, AccionDTO("mover", direccion=ESTE))
            recorrido.append((motor.reloj, contexto.jugador.Sala_Actual, contexto.jugador.vida,
                              contexto.jugador.danio_recibido, estados(motor.mapa), list(contexto.mensajes),
                              [e.activo for e in contexto.mazmorra.sala(B).enemigos]))
        self.assertEqual(recorrido[0], recorrido[1])                           # igual a un `mover` hecho a mano
        self.assertEqual(recorrido[0][6], [True])                              # el dormido se activó
        self.assertGreater(recorrido[0][3], 0)                                 # la trampa hizo daño

    def test_sc251_cada_paso_igual_a_paso_desde_cero(self):
        escenarios = [(rombo(), "Sala 4"), (rombo(150), "Sala 5"),
                      ([salida(A, ESTE, B, 100), salida(A, SUR, C, 100), salida(B, SUR, D, 100),
                        salida(C, ESTE, D, 100), salida(D, ESTE, E, 100)], "Sala 4")]
        for salidas, nombre in escenarios:
            contexto = contexto_de_prueba(5, salidas, A, [B, C, D, E])
            servicio = ServicioIrA()
            viaje = servicio.iniciar(contexto, nombre).viaje
            while viaje is not None:
                esperado = paso_desde_cero(GrafoMapaConocido(contexto.motor.mapa), viaje.destino,
                                           contexto.jugador.Sala_Actual, None)
                reloj = contexto.motor.reloj
                paso = servicio.dar_paso(contexto, viaje)
                self.assertEqual((contexto.jugador.Sala_Actual, contexto.motor.reloj - reloj), esperado)
                viaje = paso.viaje


class PruebasRecalculoYParadas(unittest.TestCase):

    def cerrar_bd_de_verdad(self, contexto):
        contexto.mazmorra.salida(B, SUR).cerrada = True
        contexto.mazmorra.salida(D, NORTE).cerrada = True

    def test_h7_1_apendiceB_caso2b_fr255_fr256_recalcula_y_sigue_por_otra_ruta(self):
        contexto = contexto_de_prueba(5, rombo(), A, [B, C, D])
        self.cerrar_bd_de_verdad(contexto)                                    # el mapa la recuerda abierta
        pasos, huellas = correr(ServicioIrA(), contexto, "Sala 4")
        self.assertEqual([sala for sala, _ in huellas], [B, A, C, D])          # en B se entera y rodea
        self.assertEqual(pasos[-1].motivos, [LLEGO])

    def test_h7_2_apendiceB_caso2b_fr256_fr259_fr260_sin_ruta_se_detiene_en_b_sin_tiempo(self):
        salidas = [salida(A, ESTE, B, 100), salida(B, SUR, D, 100), salida(D, ESTE, E, 100)]
        bitacora = BitacoraPrueba()
        contexto = contexto_de_prueba(5, salidas, A, [B, D], bitacora)
        self.cerrar_bd_de_verdad(contexto)
        pasos, huellas = correr(ServicioIrA(), contexto, "Sala 4")
        self.assertEqual([p.motivos for p in pasos], [[], [SIN_RUTA]])
        self.assertEqual(huellas, [(B, 100), (B, 100)])                        # el reloj queda donde lo dejó el paso
        self.assertEqual(contexto.jugador.acciones, 1)
        self.assertEqual(pasos[1].estado.reloj, 100)

    def test_h7_3_apendiceB_caso3_fr258_fr260_enemigo_dormido_se_activa_y_para(self):
        contexto = contexto_de_prueba(5, rombo(), A, [B, C, D])
        dormido = poner_dormido(contexto.motor, B, ficha_errante(velocidad=10), "e-b")       # lento: no alcanza a golpear
        pasos, huellas = correr(ServicioIrA(), contexto, "Sala 4")
        self.assertEqual([p.motivos for p in pasos], [[ENEMIGOS]])
        self.assertIsNone(pasos[0].viaje)
        self.assertTrue(dormido.activo)
        self.assertEqual(huellas, [(B, 100)])

    def test_i3_4_la_sala_de_partida_con_enemigos_permite_el_primer_paso(self):
        contexto = contexto_de_prueba(5, rombo(), A, [B, C, D])
        poner_enemigo(contexto.motor, A, dataclasses.replace(ficha_errante(), comportamiento="guardián"), "e-a")
        pasos, huellas = correr(ServicioIrA(), contexto, "Sala 4")
        self.assertEqual(huellas[0][0], B)
        self.assertEqual(pasos[-1].motivos, [LLEGO])

    def test_h7_4_a33_fr258_fr260_enemigo_activo_en_el_destino_dos_motivos(self):
        ficha = dataclasses.replace(ficha_errante(), comportamiento="guardián")
        for activo in (False, True):
            contexto = contexto_de_prueba(5, rombo(), A, [B, C, D])
            if activo:
                poner_enemigo(contexto.motor, D, ficha, "e-d")
            else:
                poner_dormido(contexto.motor, D, ficha, "e-d")
            pasos, _ = correr(ServicioIrA(), contexto, "Sala 4")
            self.assertEqual(pasos[-1].motivos[:2], [LLEGO, ENEMIGOS], activo)

    def test_h7_5_a34_fr258_fr260_veneno_detiene_antes_del_siguiente_paso(self):
        contexto = contexto_de_prueba(5, rombo(), A, [B, C, D])
        contexto.motor.efectos.aplicar(Veneno(contexto.jugador, 3))            # pulsa a los 80: cae dentro del paso
        pasos, huellas = correr(ServicioIrA(), contexto, "Sala 4")
        self.assertEqual([p.motivos for p in pasos], [[DANO]])
        self.assertEqual(huellas, [(B, 100)])                                  # no dio el segundo paso
        self.assertGreater(contexto.jugador.danio_recibido, 0)

    def test_h7_6_a35_fr258_fr260_llego(self):
        contexto = contexto_de_prueba(5, rombo(), A, [B, C, D])
        pasos, _ = correr(ServicioIrA(), contexto, "Sala 2")
        self.assertEqual([p.motivos for p in pasos], [[LLEGO]])
        self.assertIsNone(pasos[0].viaje)

    def test_i3_6_fr258_paso_rechazado_para_sin_tiempo_ni_comentario(self):
        bitacora = BitacoraPrueba()
        contexto = contexto_de_prueba(5, rombo(), A, [B, C, D], bitacora)
        armador = ArmadorEstado()

        class Rechaza:
            def ejecutar(self, contexto, accion):
                return armador.armar_estado(contexto, "No hay salida en esa dirección.")

        servicio = ServicioIrA()
        servicio._acciones = Rechaza()
        pasos, _ = correr(servicio, contexto, "Sala 4")
        self.assertEqual([p.motivos for p in pasos], [[PASO_RECHAZADO]])
        self.assertEqual((pasos[0].viaje, contexto.motor.reloj, contexto.jugador.acciones), (None, 0, 0))
        self.assertEqual(bitacora.lineas, [])

    def test_i3_7_fr258_terminada_junto_con_dano_o_llego(self):
        contexto = contexto_de_prueba(5, rombo(), A, [B, C, D])
        contexto.jugador.vida = 1
        poner_dormido(contexto.motor, B, ficha_errante(), "e-b")
        pasos, _ = correr(ServicioIrA(), contexto, "Sala 2")
        self.assertTrue(contexto.motor.terminado)
        self.assertEqual(pasos[0].motivos, [LLEGO, ENEMIGOS, DANO, TERMINADA])
        otro = contexto_de_prueba(5, rombo(), A, [B, C, D, E], salida_abierta=True)
        pasos, _ = correr(ServicioIrA(), otro, "Sala 5")                     # llega a la salida y la partida termina
        self.assertEqual(pasos[-1].motivos, [LLEGO, TERMINADA])
        self.assertTrue(otro.motor.terminado)

    def test_dar_paso_con_la_partida_terminada_para_con_terminada(self):
        contexto = contexto_de_prueba(5, rombo(), A, [B, C, D, E], salida_abierta=True)
        servicio = ServicioIrA()
        viaje = servicio.iniciar(contexto, "Sala 5").viaje
        while viaje is not None and not contexto.motor.terminado:
            viaje = servicio.dar_paso(contexto, viaje).viaje
        contexto_b = contexto_de_prueba(5, rombo(), A, [B, C, D, E])
        contexto_b.motor.terminado = True
        viaje_b = servicio.iniciar(contexto_b, "Sala 2").viaje
        paso = servicio.dar_paso(contexto_b, viaje_b)
        self.assertEqual((paso.viaje, paso.motivos), (None, [TERMINADA]))
        self.assertEqual(contexto_b.jugador.acciones, 0)

    def test_dar_paso_con_la_partida_cambiada_por_fuera_para_con_interrumpido(self):
        contexto = contexto_de_prueba(5, rombo(), A, [B, C, D])
        servicio = ServicioIrA()
        viaje = servicio.iniciar(contexto, "Sala 4").viaje
        ServicioLineaTiempo().ejecutar(contexto, AccionDTO("esperar"))
        reloj = contexto.motor.reloj
        paso = servicio.dar_paso(contexto, viaje)
        self.assertEqual((paso.viaje, paso.motivos, contexto.motor.reloj), (None, [INTERRUMPIDO], reloj))


class PruebasContadorDeDanioYRegeneracion(unittest.TestCase):

    def test_h7_5_a34_fr258_dano_compensado_por_regeneracion_detiene(self):
        contexto = contexto_de_prueba(5, rombo(), A, [B, C, D])
        motor, jugador = contexto.motor, contexto.jugador
        jugador.vida = jugador.vida_Max
        guardian = poner_enemigo(motor, B, dataclasses.replace(ficha_errante(), comportamiento="guardián"), "e-b")
        guardian.Evento_pendiente.cancelar()
        guardian.Evento_pendiente = motor.cola.programar(EventoProgramado(90, "accion_actor", guardian))
        regeneracion = Regeneracion(jugador, 20)
        regeneracion.primer_retraso = 95                                       # cura justo después del golpe
        motor.efectos.aplicar(regeneracion)
        vida_antes = jugador.vida
        pasos, _ = correr(ServicioIrA(), contexto, "Sala 4")
        self.assertEqual(jugador.vida, vida_antes)                             # la vida no baja…
        self.assertGreater(jugador.danio_recibido, 0)                          # …pero el contador sí sube
        self.assertIn(DANO, pasos[0].motivos)
        self.assertIsNone(pasos[0].viaje)

    def test_fr258_regeneracion_activa_sin_dano_el_viaje_sigue(self):
        contexto = contexto_de_prueba(5, rombo(), A, [B, C, D])
        motor, jugador = contexto.motor, contexto.jugador
        jugador.vida = 20
        motor.efectos.aplicar(Regeneracion(jugador, 5))                        # pulsa a los 200: dentro del 2.º paso
        pasos, huellas = correr(ServicioIrA(), contexto, "Sala 4")
        self.assertEqual([p.motivos for p in pasos], [[], [LLEGO]])
        self.assertEqual(jugador.danio_recibido, 0)                            # curarse no sube el contador
        self.assertEqual(jugador.vida, 25)


class PruebasGrafoUnaVezPorViaje(unittest.TestCase):

    def setUp(self):
        self.construidos = []
        original = modulo_servicio.GrafoMapaConocido
        construidos = self.construidos

        class Contador(original):
            def __init__(self, mapa):
                super().__init__(mapa)
                construidos.append(mapa)

        modulo_servicio.GrafoMapaConocido = Contador
        self.addCleanup(setattr, modulo_servicio, "GrafoMapaConocido", original)

    def test_el_grafo_se_arma_una_vez_por_viaje(self):
        contexto = contexto_de_prueba(5, rombo(), A, [B, C, D, E])
        servicio = ServicioIrA()
        pasos, _ = correr(servicio, contexto, "Sala 5")
        self.assertEqual(len(pasos), 3)
        self.assertEqual(len(self.construidos), 1)
        self.assertIs(self.construidos[0], contexto.motor.mapa)
        correr(servicio, contexto, "Sala 1")                                  # otro viaje: otro grafo
        self.assertEqual(len(self.construidos), 2)

    def test_viaje_tras_cargar_toma_el_mapa_del_motor_nuevo_y_arma_un_grafo_nuevo(self):
        with tempfile.TemporaryDirectory() as carpeta:
            servicio_partida = servicio_partida_cuadricula(carpeta)
            from Service.ServicioGuardado import ServicioGuardado
            guardado = ServicioGuardado(servicio_partida)
            contexto = servicio_partida.iniciar_partida("cuadricula", "Ana", semilla=7)
            lineas = ServicioLineaTiempo()
            for _ in range(3):
                lineas.ejecutar(contexto, AccionDTO("mover", direccion=ESTE_DIR))
            servicio = ServicioIrA()
            viaje = servicio.iniciar(contexto, "Sala 1").viaje
            viaje = servicio.dar_paso(contexto, viaje).viaje                  # un paso antes de guardar
            self.assertEqual(len(self.construidos), 1)
            ruta = os.path.join(carpeta, "guardada.sav")
            guardado.guardar(contexto, ruta)
            cargado = guardado.cargar(ruta, "Ana")
            self.assertIsNot(cargado.motor, contexto.motor)
            self.assertIsNot(cargado.motor.mapa, contexto.motor.mapa)
            nuevo = servicio.iniciar(cargado, "Sala 1").viaje                 # el mismo servicio, otra partida
            self.assertIsNotNone(nuevo)
            while nuevo is not None:
                nuevo = servicio.dar_paso(cargado, nuevo).viaje
            self.assertEqual(len(self.construidos), 2)
            self.assertIs(self.construidos[1], cargado.motor.mapa)
            self.assertEqual(cargado.jugador.Sala_Actual, 1)


class PruebasControlador(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(self.carpeta.cleanup)
        self.backend = crear_backend(self.carpeta.name, partida=servicio_partida_cuadricula(self.carpeta.name))
        self.backend.iniciar("cuadricula", "Ana")

    def caminar(self, pasos):
        for _ in range(pasos):
            self.backend.mover(ESTE_DIR)

    def test_h6_1_apendiceB_caso1_fr251_fr260_controlador_mismo_mensaje(self):
        estado = self.backend.estado()
        self.assertEqual(estado.sala.salidas[ESTE_DIR].sala_destino, 2)       # «Sala 2» está avistada
        mensajes = []
        for nombre in ("Sala 2", "Sala 20", "Nada de nada"):                    # avistada, desconocida, inexistente
            with self.assertRaises(ErrorOperacion) as contexto:
                self.backend.ir_a(nombre)
            mensajes.append(str(contexto.exception))
        self.assertEqual(len(set(mensajes)), 1)
        self.assertEqual(self.backend.estado().reloj, estado.reloj)

    def test_ya_aqui_y_ambiguo_tienen_mensaje_propio(self):
        with self.assertRaises(ErrorOperacion) as ya_aqui:
            self.backend.ir_a("Sala 1")
        with self.assertRaises(ErrorOperacion) as invalido:
            self.backend.ir_a("Sala 20")
        self.caminar(2)
        self.backend._contexto.mazmorra.sala(2).nombre = "Sala 3"
        with self.assertRaises(ErrorOperacion) as ambiguo:
            self.backend.ir_a("Sala 3 ")
        self.assertEqual(len({str(ya_aqui.exception), str(invalido.exception), str(ambiguo.exception)}), 3)

    def test_ir_a_valida_solo_la_forma_del_texto(self):
        for texto in ("", "   ", "Sala\n1", "Sala\r1", None, 7):
            with self.assertRaises(ErrorOperacion, msg=repr(texto)):
                self.backend.ir_a(texto)

    def test_ir_a_sin_partida_es_error_de_operacion(self):
        sin_partida = crear_backend(self.carpeta.name)
        with self.assertRaises(ErrorOperacion):
            sin_partida.ir_a("Sala 1")
        with self.assertRaises(ErrorOperacion):
            sin_partida.dar_paso_viaje()

    def test_ir_a_devuelve_el_viaje_y_los_pasos_lo_llevan_hasta_llegar(self):
        self.caminar(3)
        reloj = self.backend.estado().reloj
        viaje = self.backend.ir_a("sala 1")
        self.assertEqual((viaje.destino, viaje.nombre_destino, viaje.pasos_dados), (1, "Sala 1", 0))
        self.assertEqual(self.backend.estado().reloj, reloj)                   # la orden no gasta tiempo
        motivos = []
        for _ in range(10):
            paso = self.backend.dar_paso_viaje()
            if paso.viaje is None:
                motivos = paso.motivos
                break
        self.assertEqual(motivos, [LLEGO])
        self.assertEqual(paso.estado.sala.id, 1)
        self.assertEqual(self.backend.estado().reloj, reloj + 300)

    def test_r_i3_4_fr262_controlador_descarta_el_viaje_ante_otra_orden(self):
        for orden in ("esperar", "mover", "retroceder"):
            self.setUp()
            dar_pergaminos_a(self.backend._contexto, 1)
            self.caminar(3)
            self.backend.ir_a("Sala 1")
            primero = self.backend.dar_paso_viaje()
            self.assertEqual(primero.motivos, [], orden)
            if orden == "esperar":
                self.backend.esperar()
            elif orden == "mover":
                self.backend.mover(ESTE_DIR)
            else:
                self.backend.retroceder()
            antes = self.backend.estado()
            paso = self.backend.dar_paso_viaje()
            self.assertEqual((paso.viaje, paso.motivos), (None, [INTERRUMPIDO]), orden)
            despues = self.backend.estado()
            self.assertEqual((despues.reloj, despues.sala.id), (antes.reloj, antes.sala.id), orden)

    def test_cargar_otra_partida_descarta_el_viaje(self):
        self.caminar(3)
        self.backend.ir_a("Sala 1")
        ruta = os.path.join(self.carpeta.name, "p.sav")
        self.backend.guardar(ruta)
        self.backend.cargar(ruta, "Ana")
        paso = self.backend.dar_paso_viaje()
        self.assertEqual((paso.viaje, paso.motivos), (None, [INTERRUMPIDO]))

    def test_el_controlador_sabe_que_la_partida_termino_tras_un_paso(self):
        self.caminar(3)
        self.backend.ir_a("Sala 1")
        paso = self.backend.dar_paso_viaje()
        self.assertFalse(paso.estado.terminado)
        self.assertFalse(self.backend._terminada)


if __name__ == "__main__":
    unittest.main()
