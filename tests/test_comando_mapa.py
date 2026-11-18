"""
Pruebas del comando `mapa` y de su dibujo (feature 002, integrante 3; FR-219, FR-220; T048 puntos 1, 2 y 4).

- Controles y backend reales sobre una cuadrícula sin enemigos: el comando abre y cierra el panel, no consume tiempo, no es
  una acción y no se anota en partida.log ni en la línea de tiempo (H5-4), y el DTO no trae ids de salas no exploradas.
- Vista sin ventana: la disposición (función pura) y el dibujo sobre una superficie que no es la pantalla.
- De punta a punta: el ControladorPygame real pone el MapaConocidoDTO en PantallaDTO.mapa y la VistaPygame lo dibuja.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame, tecla  # noqa: E402  (fija SDL_VIDEODRIVER=dummy antes de importar pygame)
from ayudas_vista import ENTER, ESC, Recorrido  # noqa: E402
from ayudas_controladores import crear_backend  # noqa: E402

import View.Componentes as c  # noqa: E402
import View.MapaJuego as mapa_juego  # noqa: E402
from DTO.Direcciones import E as ESTE, N as NORTE, O as OESTE, S as SUR  # noqa: E402
from DTO.MapaConocidoDTO import (ABIERTA, CERRADA, SIN_OBSERVAR, MapaConocidoDTO, SalaConocidaDTO,  # noqa: E402
                                 SalidaConocidaDTO)
from Logic.Efectos import Antorcha  # noqa: E402
from UIController.ControlesJuego import PIDE_PAUSA, ControlesJuego  # noqa: E402
from View.VistaPygame import VistaPygame  # noqa: E402
from tests.ayudas_ir_a import servicio_partida_cuadricula  # noqa: E402
from tests.ayudas_mapa import estados  # noqa: E402


def foto(backend):
    contexto = backend._contexto
    with open(contexto.bitacora.ruta(), encoding="utf-8", newline="") as archivo:
        log = archivo.read()
    return (contexto.motor.reloj, contexto.jugador.acciones, log, len(contexto.linea.acciones),
            contexto.motor.historial.cantidad(), estados(contexto.motor.mapa), contexto.jugador.Sala_Actual)


def ids_en(mapa):
    ids = []
    for sala in mapa.salas:
        ids.append(sala.id)
        for salida in sala.salidas:
            if salida is not None and salida.destino is not None:
                ids.append(salida.destino)
    return ids


class ConPartida(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(self.carpeta.cleanup)
        self.backend = crear_backend(self.carpeta.name, partida=servicio_partida_cuadricula(self.carpeta.name))
        self.estado = self.backend.iniciar("cuadricula", "Ana")
        self.controles = ControlesJuego(self.backend, self.estado)

    def pulsar(self, codigo):
        return self.controles.procesar_evento(tecla(codigo))


class PruebasComando(ConPartida):

    def test_fr219_comando_valido_abre_y_se_cierra_con_el_mismo_comando_o_con_esc(self):
        self.controles.procesar_comando("mapa")
        self.assertIsInstance(self.controles.mapa, MapaConocidoDTO)
        self.assertEqual([sala.id for sala in self.controles.mapa.salas], [1])
        self.assertIsNone(self.controles.aviso)
        self.controles.procesar_comando("  MAPA ")                     # el mismo comando lo cierra
        self.assertIsNone(self.controles.mapa)
        self.controles.procesar_comando("mapa")
        self.assertIsNone(self.pulsar(ESC))                           # Esc cierra el panel y NO pide la pausa
        self.assertIsNone(self.controles.mapa)
        self.assertEqual(self.pulsar(ESC), PIDE_PAUSA)                # con el panel cerrado, Esc sigue pidiendo la pausa

    def test_fr219_comando_con_la_linea_de_comandos_de_teclado(self):
        self.pulsar(ENTER)
        for caracter in "mapa":
            self.controles.procesar_evento(tecla(ord(caracter), 0, caracter))
        self.pulsar(ENTER)
        self.assertIsNotNone(self.controles.mapa)
        self.assertIsNone(self.controles.linea)

    def test_fr219_comando_mal_formado_no_abre_nada(self):
        for texto in ("mapa 3", "mapas", "ver mapa"):
            with self.subTest(texto=texto):
                self.controles.procesar_comando(texto)
                self.assertIsNone(self.controles.mapa)
                self.assertIsNotNone(self.controles.aviso)

    def test_una_accion_nueva_cierra_el_panel(self):
        self.controles.procesar_comando("mapa")
        self.pulsar(pygame.K_d)                                        # mover al este: el mapa mostrado ya no es el de ahora
        self.assertIsNone(self.controles.mapa)
        self.assertEqual(self.controles.estado.sala.id, 2)

    def test_h5_4_a12_fr220_ver_el_mapa_no_gasta_tiempo_ni_se_registra(self):
        self.pulsar(pygame.K_d)
        antes = foto(self.backend)
        self.controles.procesar_comando("mapa")
        self.controles.procesar_comando("mapa")
        self.controles.procesar_comando("mapa")
        self.pulsar(ESC)
        self.assertEqual(foto(self.backend), antes)               # reloj, acciones, partida.log, línea, historial y mapa
        self.assertEqual(self.controles.estado.reloj, antes[0])

    def test_h5_4_a12_fr220_la_prueba_detecta_un_comando_que_se_registra(self):
        original = type(self.backend).ver_mapa
        self.addCleanup(setattr, type(self.backend), "ver_mapa", original)

        def registra(este):
            este._contexto.bitacora.anexar_comentario("mapa")
            return original(este)

        type(self.backend).ver_mapa = registra
        antes = foto(self.backend)
        self.controles.procesar_comando("mapa")
        self.assertNotEqual(foto(self.backend), antes)             # la comparación de arriba habría fallado

    def test_h5_4_a12_fr220_la_prueba_detecta_un_comando_que_gasta_tiempo(self):
        original = type(self.backend).ver_mapa
        self.addCleanup(setattr, type(self.backend), "ver_mapa", original)

        def gasta(este):
            este.esperar()
            return original(este)

        type(self.backend).ver_mapa = gasta
        antes = foto(self.backend)
        self.controles.procesar_comando("mapa")
        self.assertNotEqual(foto(self.backend), antes)

    def test_ver_mapa_no_descarta_un_viaje_en_curso(self):
        self.pulsar(pygame.K_d)
        self.backend.ir_a("Sala 1")
        self.controles.procesar_comando("mapa")
        paso = self.backend.dar_paso_viaje()
        self.assertEqual(paso.estado.sala.id, 1)

    def test_fr217_fr219_el_mapa_no_revela_ids_de_salas_no_exploradas(self):
        mapa = self.backend._contexto.motor.mapa
        x = 7
        for paso in range(60):
            if paso == 30:
                self.backend._contexto.motor.efectos.aplicar(Antorcha(self.backend._contexto.jugador, 10 ** 7))
            dto = self.backend.ver_mapa()
            self.assertEqual(ids_en(dto), [i for i in ids_en(dto) if mapa.es_explorada(i)])
            for sala in dto.salas:
                for salida in sala.salidas:
                    if salida is not None and salida.destino is None:
                        self.assertTrue(salida.estado_puerta in (ABIERTA, CERRADA, SIN_OBSERVAR))
            x = (x * 1103515245 + 12345) % (1 << 32)
            estado = self.backend.estado()
            abiertas = [d for d in range(4) if estado.sala.salidas[d] is not None]
            self.backend.mover(abiertas[(x >> 16) % len(abiertas)])
        self.assertGreater(len(self.backend.ver_mapa().salas), 5)

    def test_con_la_partida_terminada_el_comando_no_esta_disponible_pero_ver_mapa_no_falla(self):
        import dataclasses
        terminado = dataclasses.replace(self.estado, terminado=True, resultado="victoria")
        controles = ControlesJuego(self.backend, terminado)
        self.assertIsNone(controles.procesar_evento(tecla(ENTER)))             # la línea no se abre
        self.assertIsNone(controles.linea)
        self.assertIsNone(controles.mapa)
        self.assertIsInstance(self.backend.ver_mapa(), MapaConocidoDTO)         # el backend no mira si terminó

    def test_fr219_ver_mapa_sin_partida_es_error_de_operacion(self):
        from UIController.ControladorBackend import ErrorOperacion
        with self.assertRaises(ErrorOperacion):
            crear_backend(self.carpeta.name).ver_mapa()


def sala(id_sala, nombre, **salidas):
    lista = [None] * 4
    for direccion, (destino, estado, costo) in salidas.items():
        lista["NSEO".index(direccion)] = SalidaConocidaDTO(costo, estado, destino)
    return SalaConocidaDTO(id_sala, nombre, lista)


class PruebasDisposicion(unittest.TestCase):

    def test_las_salas_se_ponen_hacia_donde_apunta_su_salida_y_lo_avistado_es_una_celda_hueca(self):
        mapa = MapaConocidoDTO([sala(1, "A", E=(2, ABIERTA, 100), S=(None, SIN_OBSERVAR, 150)),
                                sala(2, "B", O=(1, ABIERTA, 100), N=(None, CERRADA, 90))])
        disp = mapa_juego.disposicion(mapa, 1)
        celdas = {(celda.tipo, celda.sala): (celda.x, celda.y) for celda in disp.celdas if celda.sala is not None}
        a, b = celdas[(mapa_juego.ACTUAL, 1)], celdas[(mapa_juego.EXPLORADA, 2)]
        self.assertEqual((b[0] - a[0], b[1] - a[1]), (1, 0))                   # B está al este de A
        huecas = [celda for celda in disp.celdas if celda.tipo == mapa_juego.SIN_EXPLORAR]
        self.assertEqual(len(huecas), 2)
        self.assertTrue(all(celda.sala is None and celda.nombre == "" for celda in huecas))     # sin id ni nombre
        self.assertEqual({(celda.x - a[0], celda.y - a[1]) for celda in huecas}, {(0, 1), (1, -1)})
        self.assertEqual(disp.desplazadas, 0)

    def test_dos_salidas_hacia_la_misma_avistada_son_dos_celdas_huecas(self):
        mapa = MapaConocidoDTO([sala(1, "A", E=(None, ABIERTA, 100), S=(None, ABIERTA, 100))])
        disp = mapa_juego.disposicion(mapa, 1)
        self.assertEqual(len([celda for celda in disp.celdas if celda.tipo == mapa_juego.SIN_EXPLORAR]), 2)

    def test_una_sala_que_no_cabe_junto_a_su_vecina_se_pone_mas_lejos_sin_pisar_otra(self):
        mapa = MapaConocidoDTO([sala(1, "A", E=(2, ABIERTA, 1), S=(3, ABIERTA, 1)),
                                sala(2, "B", S=(4, ABIERTA, 1)),
                                sala(3, "C", E=(4, ABIERTA, 1)),
                                sala(4, "D")])
        disp = mapa_juego.disposicion(mapa, 1)
        posiciones = [(celda.x, celda.y) for celda in disp.celdas if celda.sala is not None]
        self.assertEqual(len(posiciones), 4)
        self.assertEqual(len(set(posiciones)), 4)                                # ninguna sobre otra
        self.assertEqual(len(disp.conexiones), 4)

    def test_el_mapa_vacio_no_rompe(self):
        self.assertEqual(mapa_juego.disposicion(MapaConocidoDTO([]), 1).celdas, [])

    def test_trescientas_salas_en_cuadricula_caben_sin_recorte(self):
        mapa = _cuadricula(18, 17)
        disp = mapa_juego.disposicion(mapa, 1)
        area = (c.HUD_MAPA.width - 2 * c.HUD_RELLENO, c.HUD_MAPA.height - 72)
        lado = mapa_juego.lado_de_celda(disp, *area)
        self.assertGreaterEqual(lado, mapa_juego.CELDA_MINIMA)
        minx, miny, maxx, maxy = mapa_juego.limites(disp)
        self.assertLessEqual((maxx - minx + 1) * lado, area[0])
        self.assertLessEqual((maxy - miny + 1) * lado, area[1])
        self.assertEqual(len([celda for celda in disp.celdas if celda.sala is not None]), 307)       # 18 x 17 y la sala suelta

    def test_trescientas_salas_en_fila_se_recortan_alrededor_de_la_sala_actual(self):
        salas = []
        for i in range(1, 301):
            salidas = {}
            if i > 1:
                salidas["O"] = (i - 1, ABIERTA, 10)
            if i < 300:
                salidas["E"] = (i + 1, ABIERTA, 10)
            salas.append(sala(i, f"Sala {i}", **salidas))
        mapa = MapaConocidoDTO(salas)
        disp = mapa_juego.disposicion(mapa, 150)
        area = (c.HUD_MAPA.width - 2 * c.HUD_RELLENO, c.HUD_MAPA.height - 72)
        lado = mapa_juego.lado_de_celda(disp, *area)
        self.assertEqual(lado, mapa_juego.CELDA_MINIMA)                         # no baja de la celda mínima
        columnas, filas = area[0] // lado, area[1] // lado
        x0, y0 = mapa_juego.ventana(disp, columnas, filas, 150)
        actual = [celda for celda in disp.celdas if celda.tipo == mapa_juego.ACTUAL][0]
        self.assertTrue(x0 <= actual.x < x0 + columnas)                         # la sala actual queda dentro de la ventana
        minx, _, maxx, _ = mapa_juego.limites(disp)
        self.assertTrue(minx <= x0 and x0 + columnas - 1 <= maxx)


def _cuadricula(filas, columnas):
    salas = []
    for f in range(filas):
        for col in range(columnas):
            i = f * columnas + col + 1
            salidas = {}
            if f > 0:
                salidas["N"] = (i - columnas, ABIERTA, 10)
            if f < filas - 1:
                salidas["S"] = (i + columnas, ABIERTA, 10)
            if col < columnas - 1:
                salidas["E"] = (i + 1, ABIERTA, 10)
            if col > 0:
                salidas["O"] = (i - 1, ABIERTA, 10)
            salas.append(sala(i, f"Sala {i}", **salidas))
    salas.append(sala(len(salas) + 1, "Lejos", O=(None, SIN_OBSERVAR, 5)))
    return MapaConocidoDTO(salas)


class PruebasDibujo(unittest.TestCase):

    def setUp(self):
        pygame.font.init()
        self.fuentes = c.Fuentes()
        self.panel = mapa_juego.PanelMapa(self.fuentes)
        self.fondo = (7, 9, 11)

    def dibujar(self, mapa, sala_actual):
        superficie = pygame.Surface((c.ANCHO, c.ALTO))
        superficie.fill(self.fondo)
        self.panel.dibujar(superficie, mapa, sala_actual)
        return superficie

    def contar(self, superficie, color):
        return pygame.mask.from_threshold(superficie, color, (1, 1, 1, 255)).count()

    def test_dibuja_solo_dentro_de_su_marco_y_con_los_colores_de_las_puertas_recordadas(self):
        mapa = MapaConocidoDTO([sala(1, "A", E=(2, ABIERTA, 100), S=(None, SIN_OBSERVAR, 150), N=(None, CERRADA, 5)),
                                sala(2, "B", O=(1, ABIERTA, 100))])
        superficie = self.dibujar(mapa, 1)
        self.assertEqual(superficie.get_at((2, 2))[:3], self.fondo)                 # fuera del marco: intacto
        self.assertEqual(superficie.get_at((c.ANCHO - 3, c.ALTO - 3))[:3], self.fondo)
        for color in (mapa_juego.COLOR_ABIERTA, mapa_juego.COLOR_CERRADA, mapa_juego.COLOR_SIN_OBSERVAR,
                      mapa_juego.COLOR_VACIA, c.ORO):
            self.assertGreater(self.contar(superficie, color), 0, color)

    def test_el_mapa_dibujado_cambia_con_la_sala_actual(self):
        mapa = MapaConocidoDTO([sala(1, "A", E=(2, ABIERTA, 100)), sala(2, "B", O=(1, ABIERTA, 100))])
        uno, dos = self.dibujar(mapa, 1), self.dibujar(mapa, 2)
        self.assertNotEqual(uno.get_buffer().raw, dos.get_buffer().raw)

    def test_un_mapa_enorme_se_dibuja_recortado_sin_salirse_del_marco(self):
        salas = []
        for i in range(1, 301):
            salidas = {}
            if i > 1:
                salidas["O"] = (i - 1, ABIERTA, 10)
            if i < 300:
                salidas["E"] = (i + 1, ABIERTA, 10)
            salas.append(sala(i, f"Sala {i}", **salidas))
        superficie = self.dibujar(MapaConocidoDTO(salas), 150)
        self.assertEqual(superficie.get_at((2, 2))[:3], self.fondo)
        self.assertEqual(superficie.get_at((c.ANCHO - 3, c.ALTO - 3))[:3], self.fondo)
        self.assertGreater(self.contar(superficie, c.AVISO), 0)                     # el rótulo «Recortado: …»
        self.assertGreater(self.contar(superficie, c.ORO), 0)                       # la sala actual está en el recorte


class PruebasDeLaPuntaALaPunta(unittest.TestCase):

    def test_el_dto_del_mapa_llega_a_la_vista_y_se_dibuja_sin_cambiar_la_partida(self):
        vista = VistaPygame()
        vista.abrir()
        try:
            with Recorrido(vista) as r:
                r.pulsar(ENTER, ENTER)
                r.escribir("Ana")
                r.pulsar(ENTER)
                antes = r.dibujar()
                self.assertIsNone(antes.mapa)
                reloj = antes.estado.reloj
                r.pulsar(ENTER)
                r.escribir("mapa")
                r.pulsar(ENTER)
                con_mapa = r.dibujar()
                self.assertIsInstance(con_mapa.mapa, MapaConocidoDTO)
                self.assertEqual([sala.id for sala in con_mapa.mapa.salas], [con_mapa.estado.sala.id])
                self.assertEqual(con_mapa.pantalla, "juego")
                self.assertEqual(con_mapa.estado.reloj, reloj)
                self.assertGreater(self.contar(vista, mapa_juego.COLOR_VACIA), 0)           # las vecinas, como huecos
                r.pulsar(ESC)
                despues = r.dibujar()
                self.assertIsNone(despues.mapa)
                self.assertEqual(despues.pantalla, "juego")                                  # Esc cerró el panel, no pausó
                self.assertEqual(despues.estado.reloj, reloj)
        finally:
            vista.cerrar()

    @staticmethod
    def contar(vista, color):
        return pygame.mask.from_threshold(vista._superficie, color, (1, 1, 1, 255)).count()


if __name__ == "__main__":
    unittest.main()
