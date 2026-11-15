"""
Pruebas de la historia 5 en Logic (feature 002, integrante 2, T045): MapaConocido.a_dto(), el único DTO que la
interfaz y el resumen usan para el mapa (FR-217, FR-219, FR-220; contrato (b)), y la comprobación automática de SC-202.

Fallan hasta T046 (a_dto). El comando de ver el mapa y el dibujo son del integrante 3 (T048).

Guardas, con su motivo:
- test_h5_7_a40_…: Service/ServicioResolubilidad.py de la 003 todavía no existe; se quita cuando exista.
- test_sc202_…: la parte del EstadoJuegoDTO espera el H-2 del integrante 3 (T116); la quita T050.

También está aquí test_h1_4_a14_… (historia 1), que T045 pone en tests/test_mapa_conocido_estados.py: ese archivo no
estaba entre los permitidos de este lote. Se puede mover sin cambiarla.
"""
import dataclasses
import importlib.util
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.MapaConocidoDTO import MapaConocidoDTO, SalaConocidaDTO, SalidaConocidaDTO  # noqa: E402
from Logic.Efectos import Antorcha  # noqa: E402
from Logic.HistorialRetroceso import HistorialRetroceso  # noqa: E402
from tests.ayudas_mapa import (A, B, C, D, E, ESTE, F, J, NORTE, OESTE, SUR, EsqueletoPrueba,  # noqa: E402
                               cripta_mapa, cuadricula_mapa, entrar_a, estados, mapa_de_prueba, motor_con,
                               motor_con_inventario, salida)

# Constantes del mapa con sus valores de data-model §1.
DESCONOCIDA, AVISTADA, EXPLORADA = 0, 1, 2
SIN_OBSERVAR, ABIERTA, CERRADA = 0, 1, 2


def cripta_h5():
    """A –E– B, A –S– C, B –S– D, B –E– E, D –E– F. Seis salas."""
    return cripta_mapa(6, [salida(A, ESTE, B), salida(A, SUR, C), salida(B, SUR, D), salida(B, ESTE, E),
                           salida(D, ESTE, F)])


def ids_en(dto: MapaConocidoDTO) -> list[int]:
    """Todos los ids que aparecen en el DTO: los de las salas y los destinos que no son None."""
    ids = []
    for sala in dto.salas:
        ids.append(sala.id)
        for s in sala.salidas:
            if s is not None and s.destino is not None:
                ids.append(s.destino)
    return ids


def sala_del_dto(dto: MapaConocidoDTO, id_sala: int) -> SalaConocidaDTO:
    for sala in dto.salas:
        if sala.id == id_sala:
            return sala
    raise AssertionError(f"la sala {id_sala} no está en el DTO")


def revisar_dto(prueba: unittest.TestCase, mapa, dto) -> None:
    """
    SC-202 sobre un MapaConocidoDTO: solo salas exploradas, en orden creciente de id, con su nombre, sus 4 salidas con
    el costo igualado y el estado RECORDADO de su cara; el destino es el id solo si está explorado (si no, None); nunca
    aparece una sala desconocida ni el id de una avistada.
    """
    prueba.assertIsInstance(dto, MapaConocidoDTO)
    exploradas = []
    for sala in range(len(mapa.estado)):
        if mapa.estado[sala] == EXPLORADA:
            exploradas.append(sala)
    prueba.assertEqual([s.id for s in dto.salas], exploradas)
    for sala_dto in dto.salas:
        viva = mapa.mazmorra.sala(sala_dto.id)
        prueba.assertEqual(sala_dto.nombre, viva.nombre)
        prueba.assertEqual(len(sala_dto.salidas), 4)
        for d in range(4):
            s = viva.salidas[d]
            salida_dto = sala_dto.salidas[d]
            if s is None:
                prueba.assertIsNone(salida_dto)
                continue
            prueba.assertNotEqual(mapa.estado[s.destino], DESCONOCIDA)      # nunca una desconocida
            prueba.assertEqual(salida_dto.costo, s.costo)
            prueba.assertEqual(salida_dto.estado_puerta, mapa.caras[sala_dto.id * 4 + d])
            if mapa.estado[s.destino] == EXPLORADA:
                prueba.assertEqual(salida_dto.destino, s.destino)
            else:
                prueba.assertIsNone(salida_dto.destino)                     # avistada: sin id
    for id_sala in ids_en(dto):
        prueba.assertEqual(mapa.estado[id_sala], EXPLORADA)


class PruebasVistaMapaConocido(unittest.TestCase):

    def test_h5_1_a11_fr219_muestra_exploradas_y_avistadas_sin_desconocidas(self):
        mapa, jugador = mapa_de_prueba(cripta_h5(), A)
        mapa.iniciar(A)
        entrar_a(mapa, jugador, B)
        dto = mapa.a_dto()
        self.assertEqual([s.id for s in dto.salas], [A, B])
        sala_a, sala_b = dto.salas
        self.assertEqual((sala_a.nombre, sala_b.nombre), ("Sala 1", "Sala 2"))
        self.assertEqual(sala_a.salidas[ESTE], SalidaConocidaDTO(100, ABIERTA, B))
        self.assertEqual(sala_a.salidas[SUR], SalidaConocidaDTO(100, ABIERTA, None))       # C avistada
        self.assertIsNone(sala_a.salidas[NORTE])
        self.assertIsNone(sala_a.salidas[OESTE])
        self.assertEqual(sala_b.salidas[OESTE], SalidaConocidaDTO(100, ABIERTA, A))
        self.assertEqual(sala_b.salidas[SUR], SalidaConocidaDTO(100, ABIERTA, None))       # D avistada
        self.assertEqual(sala_b.salidas[ESTE], SalidaConocidaDTO(100, ABIERTA, None))      # E avistada
        for oculta in (C, D, E, F):
            self.assertNotIn(oculta, ids_en(dto))
        self.assertEqual(mapa.estado_sala(F), DESCONOCIDA)
        revisar_dto(self, mapa, dto)

    def test_h5_2_a21_fr208_fr219_muestra_el_recordado_no_el_real(self):
        mazmorra = cripta_h5()
        mapa, jugador = mapa_de_prueba(mazmorra, A)
        mapa.iniciar(A)
        entrar_a(mapa, jugador, B)
        entrar_a(mapa, jugador, A)
        mazmorra.salida(B, SUR).cerrada = True                  # B–D se cierra lejos del jugador
        mazmorra.salida(D, NORTE).cerrada = True
        mapa.puerta_cambio(B, D)                                # el aviso llega, pero el jugador está en A
        salida_b = sala_del_dto(mapa.a_dto(), B).salidas[SUR]
        self.assertEqual(salida_b.estado_puerta, ABIERTA)       # el recordado, no el real
        self.assertTrue(mazmorra.salida(B, SUR).cerrada)

    def test_h5_3_a22_fr211_fr212_fr219_explorada_por_antorcha_sin_contenido_y_sin_observar(self):
        mazmorra = cripta_mapa(10, [salida(A, ESTE, B), salida(B, ESTE, C), salida(C, SUR, J)])
        mazmorra.sala(C).objetos.append("itm_oculto")           # contenido que no debe aparecer
        mapa, jugador = mapa_de_prueba(mazmorra, A)
        mapa.iniciar(A)
        entrar_a(mapa, jugador, B, True)                        # C explorada por la antorcha
        dto = mapa.a_dto()
        sala_c = sala_del_dto(dto, C)
        self.assertEqual(sala_c.nombre, "Sala 3")
        self.assertEqual(sala_c.salidas[OESTE], SalidaConocidaDTO(100, ABIERTA, B))   # la cara hacia B, observada
        self.assertEqual(sala_c.salidas[SUR], SalidaConocidaDTO(100, SIN_OBSERVAR, None))  # C→J nunca observada
        self.assertEqual([f.name for f in dataclasses.fields(MapaConocidoDTO)], ["salas"])
        self.assertEqual([f.name for f in dataclasses.fields(SalaConocidaDTO)], ["id", "nombre", "salidas"])
        self.assertEqual([f.name for f in dataclasses.fields(SalidaConocidaDTO)],
                         ["costo", "estado_puerta", "destino"])           # sin campos de contenido ni estado real
        self.assertNotIn("itm_oculto", repr(dto))
        revisar_dto(self, mapa, dto)

    def test_h5_4_a12_fr220_ver_el_mapa_no_altera_la_partida(self):
        historial = HistorialRetroceso()
        mapa, jugador = mapa_de_prueba(cripta_h5(), A, historial)
        mapa.iniciar(A)
        historial.descartar_intervalo_abierto()
        entrar_a(mapa, jugador, B)
        antes = (estados(mapa), historial.cantidad(), len(historial._abierto))
        primero = mapa.a_dto()
        segundo = mapa.a_dto()
        self.assertEqual(primero, segundo)
        self.assertEqual((estados(mapa), historial.cantidad(), len(historial._abierto)), antes)
        historial.cerrar_intervalo()
        historial.deshacer()                                    # deshace solo la entrada a B
        self.assertEqual(mapa.estado_sala(B), AVISTADA)

    def test_h5_4_a12_fr220_motor_reloj_sin_cambios(self):
        motor, _ = motor_con(cripta_h5(), A)
        motor.iniciar()
        motor.avanzar_hasta_jugador()
        for direccion in (ESTE, OESTE, ESTE):                   # tres salidas de costo 100 a velocidad 100
            self.assertEqual(motor.mover_jugador(direccion), "ok")
            motor.avanzar_hasta_jugador()
        self.assertEqual(motor.reloj, 300)
        antes = (estados(motor.mapa), motor.historial.cantidad(), len(motor.historial._abierto),
                 motor.jugador.Sala_Actual)
        dto = motor.mapa.a_dto()
        self.assertEqual(motor.reloj, 300)
        self.assertEqual((estados(motor.mapa), motor.historial.cantidad(), len(motor.historial._abierto),
                          motor.jugador.Sala_Actual), antes)
        revisar_dto(self, motor.mapa, dto)

    def test_h5_5_a23_fr204_fr219_dos_salidas_a_la_misma_avistada(self):
        mapa, jugador = mapa_de_prueba(cripta_mapa(3, [salida(A, NORTE, C), salida(A, ESTE, C)]), A)
        mapa.iniciar(A)
        sala_a = mapa.a_dto().salas[0]
        self.assertIsNotNone(sala_a.salidas[NORTE])
        self.assertIsNotNone(sala_a.salidas[ESTE])
        self.assertIsNone(sala_a.salidas[NORTE].destino)
        self.assertIsNone(sala_a.salidas[ESTE].destino)
        self.assertNotIn(C, ids_en(mapa.a_dto()))
        entrar_a(mapa, jugador, C)
        sala_a = sala_del_dto(mapa.a_dto(), A)
        self.assertEqual(sala_a.salidas[NORTE].destino, C)
        self.assertEqual(sala_a.salidas[ESTE].destino, C)

    def test_h5_6_a39_fr205_fr219_costo_igualado(self):
        # A–B: solo la cara de B declara 150; A–C: ninguna cara declara costo (100).
        mazmorra = cripta_mapa(3, [(A, ESTE, B, None, 150, False), (A, SUR, C, None, None, False)])
        mapa, jugador = mapa_de_prueba(mazmorra, A)
        mapa.iniciar(A)
        entrar_a(mapa, jugador, B)
        dto = mapa.a_dto()
        self.assertEqual(sala_del_dto(dto, A).salidas[ESTE].costo, 150)
        self.assertEqual(sala_del_dto(dto, B).salidas[OESTE].costo, 150)
        self.assertEqual(sala_del_dto(dto, A).salidas[SUR].costo, 100)

    def test_h5_7_a40_fr202_fr217_reporte_con_forzar_no_cambia_el_mapa(self):
        if importlib.util.find_spec("Service.ServicioResolubilidad") is None:
            self.skipTest("pendiente: Service/ServicioResolubilidad.py de la 003 todavía no existe")
        import tempfile
        from tests.ayudas_linea_tiempo import ID_CRIPTA, partida_de_prueba
        from Service.ServicioResolubilidad import ServicioResolubilidad
        with tempfile.TemporaryDirectory() as carpeta:
            partida, _ = partida_de_prueba(carpeta)
            ctx = ServicioResolubilidad(partida).iniciar_partida_nueva(ID_CRIPTA, "Ana", True)
            inicial = ctx.jugador.Sala_Actual
            nuevo, _ = mapa_de_prueba(ctx.mazmorra, inicial)
            nuevo.iniciar(inicial)
            self.assertEqual(estados(ctx.motor.mapa), estados(nuevo))   # igual que sin reporte
            self.assertEqual([s.id for s in ctx.motor.mapa.a_dto().salas], [inicial])

    def test_sc202_doscientas_acciones_sin_datos_de_desconocidas(self):
        from DTO import EstadoJuegoDTO as modulo_estado
        h2_listo = hasattr(modulo_estado, "SIN_EXPLORAR")
        hay_resumen = importlib.util.find_spec("Service.ArmadorResumen") is not None
        lado = 15
        mazmorra, salas = cuadricula_mapa(lado, 2026)
        esqueleto = EsqueletoPrueba(salas)
        motor, mensajes = motor_con_inventario(mazmorra, 1)
        motor.iniciar()
        motor.avanzar_hasta_jugador()
        contexto = _contexto_de_prueba(motor, esqueleto, mensajes, lado)
        x = 2026
        acciones = 0
        con_antorcha = [False, False]
        while acciones < 220:
            if acciones == 110:                                 # la segunda mitad, con la antorcha encendida
                motor.efectos.aplicar(Antorcha(motor.jugador, 10 ** 7))
            x = (x * 1103515245 + 12345) % (1 << 32)
            abiertas = []
            for d in range(4):
                s = motor.mazmorra.salida(motor.jugador.Sala_Actual, d)
                if s is not None and not s.cerrada:
                    abiertas.append(d)
            con_antorcha[motor.efectos.tiene(motor.jugador, "antorcha")] = True
            self.assertEqual(motor.mover_jugador(abiertas[(x >> 16) % len(abiertas)]), "ok")
            motor.avanzar_hasta_jugador()
            acciones += 1
            try:
                revisar_dto(self, motor.mapa, motor.mapa.a_dto())
                if hay_resumen:
                    from Service.ArmadorResumen import ArmadorResumen
                    resumen = ArmadorResumen.armar(motor, esqueleto, motor.reloj, False, False,
                                                   mapa_conocido=motor.mapa.a_dto())
                    self.assertEqual(motor.mapa.estado[resumen.sala_id], EXPLORADA)
                    revisar_dto(self, motor.mapa, resumen.mapa_conocido)
                if h2_listo:
                    from Service.ArmadorEstado import ArmadorEstado
                    estado = ArmadorEstado().armar_estado(contexto)
                    for s in estado.sala.salidas:
                        if s is not None and s.sala_destino != modulo_estado.SIN_EXPLORAR:
                            self.assertTrue(motor.mapa.es_explorada(s.sala_destino))
                    if estado.sala_salida is not None:
                        self.assertTrue(motor.mapa.es_explorada(estado.sala_salida))
            except AssertionError as error:
                self.fail(f"acción {acciones}: {error}")
        self.assertFalse(motor.terminado)
        self.assertEqual(con_antorcha, [True, True])            # acciones sin y con antorcha
        self.assertIn(DESCONOCIDA, motor.mapa.estado[1:])       # quedaron salas desconocidas que no debían aparecer
        self.assertIn(AVISTADA, motor.mapa.estado)
        if not h2_listo:
            self.skipTest("pendiente: H-2 del integrante 3 (sala_destino de destinos no explorados en EstadoJuegoDTO)")


def _contexto_de_prueba(motor, esqueleto, mensajes, lado: int):
    """Lo que ArmadorEstado lee del contexto, armado sobre el motor de prueba (solo se usa cuando llega el H-2)."""
    from types import SimpleNamespace

    class Mensajes:
        def a_array(self):
            return list(mensajes)

    cripta = SimpleNamespace(sala_inicial=1, sala_salida=lado * lado)
    return SimpleNamespace(motor=motor, jugador=motor.jugador, mazmorra=motor.mazmorra, esqueleto=esqueleto,
                           inventario=motor.inventario, criterio_vista=None, mensajes=Mensajes(), cripta=cripta,
                           resolvedor=None)


class PruebasAvistadaEnLaVista(unittest.TestCase):
    """Historia 1, H1-4 (A14): una avistada solo muestra que existe (va en este archivo; ver el docstring)."""

    def test_h1_4_a14_fr204_fr217_avistada_solo_muestra_su_existencia(self):
        mazmorra = cripta_h5()
        mazmorra.sala(B).objetos.append("itm_de_b")
        mapa, _ = mapa_de_prueba(mazmorra, A)
        mapa.iniciar(A)
        self.assertEqual(mapa.estado_sala(B), AVISTADA)
        dto = mapa.a_dto()
        self.assertEqual([s.id for s in dto.salas], [A])         # B no es una sala del DTO
        self.assertEqual(dto.salas[0].salidas[ESTE], SalidaConocidaDTO(100, ABIERTA, None))  # solo su existencia
        self.assertNotIn(B, ids_en(dto))
        texto = repr(dto)
        self.assertNotIn("Sala 2", texto)                       # ni su nombre
        self.assertNotIn("itm_de_b", texto)                     # ni su contenido
        revisar_dto(self, mapa, dto)


if __name__ == "__main__":
    unittest.main()
