"""
Pruebas de la escena de juego con el terreno y el cazador (feature 001, T041; H4-1 y H4-2; FR-116, FR-117, SC-106), con la
Vista REAL (SDL_VIDEODRIVER=dummy): el costo junto a cada salida, también las cerradas, y el comportamiento junto al nombre de
cada enemigo, con un marcador solo para el cazador. Lo que se dibuja se mide con lo que la escena le pide a Componentes
(texto_sombreado) y a pygame.draw.polygon, no con el color de un píxel.
"""
import sys
import unittest
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402  (fija SDL_VIDEODRIVER=dummy antes de importar pygame)
from ayudas_vista import cerrada, con_objetos, estado_base  # noqa: E402

import View.Componentes as c  # noqa: E402
import View.EscenaJuego as escena  # noqa: E402
from DTO.ActorDTO import ActorDTO  # noqa: E402
from DTO.Direcciones import E, N, O, S  # noqa: E402
from types import SimpleNamespace  # noqa: E402
from DTO.SalaDTO import SalidaDTO  # noqa: E402
from Logic.Mazmorra import Mazmorra  # noqa: E402
from Service.ArmadorEstado import ArmadorEstado  # noqa: E402
from tests.ayudas_terreno import salida as salida_declarada, salidas_con_costos  # noqa: E402
from View.VistaPygame import VistaPygame  # noqa: E402

COMPORTAMIENTOS = ["errante", "guardián", "rastreador", "cazador"]
DIRECCIONES = [N, S, E, O]


def salida(costo, cerrada_=False):
    return replace(cerrada(), costo=costo) if cerrada_ else SalidaDTO(1, costo=costo)


def enemigos(cantidad, comportamientos=COMPORTAMIENTOS, sala=3):
    lista = []
    for i in range(cantidad):
        lista.append(ActorDTO(f"enemigo-{i + 1}", "ent_rata_gigante", f"Rata gigante #{i + 1}", 8, 12, 3, 1, 100, sala,
                              comportamiento=comportamientos[i % len(comportamientos)]))
    return lista


class Registro:
    # lo que la escena dibuja con texto_sombreado (texto, color, rectángulo) y los rombos de pygame.draw.polygon

    def __init__(self):
        self.textos = []
        self.poligonos = []


@contextmanager
def espiando():
    registro = Registro()
    texto_original, poligono_original = c.texto_sombreado, pygame.draw.polygon

    def texto(superficie, fuente, texto_, color, posicion, ancla="center"):
        rectangulo = texto_original(superficie, fuente, texto_, color, posicion, ancla)
        registro.textos.append((texto_, color, rectangulo.copy()))
        return rectangulo

    def poligono(superficie, color, puntos, ancho=0):
        registro.poligonos.append((color, list(puntos), ancho))
        return poligono_original(superficie, color, puntos, ancho)

    c.texto_sombreado, pygame.draw.polygon = texto, poligono
    try:
        yield registro
    finally:
        c.texto_sombreado, pygame.draw.polygon = texto_original, poligono_original


class ConVista(unittest.TestCase):

    def setUp(self):
        self.vista = VistaPygame()
        self.vista.abrir()
        self.addCleanup(self.vista.cerrar)
        self.lienzo = pygame.Surface((c.ANCHO, c.ALTO))

    def dibujar(self, estado):
        with espiando() as registro:
            self.vista._escena.dibujar(self.lienzo, estado, None, True, None)
        return registro

    def costos(self, registro):
        # los textos que son un costo (solo dígitos): el nombre y los comportamientos nunca lo son
        return [(t, r) for t, _, r in registro.textos if t.isdigit()]


class PruebasCostoDeLasSalidas(ConVista):

    def cerca_del_marco(self, rectangulo, marco):
        return rectangulo.colliderect(marco.inflate(2 * 60, 2 * 60))

    def test_h4_1_fr116_sc106_cada_salida_tambien_las_cerradas_muestra_su_costo(self):
        for id_sala, fondo in ((3, c.FONDO_REGULAR), (1, c.FONDO_INICIAL), (6, c.FONDO_FINAL)):
            estado = estado_base(id_sala, N=salida(100), E=salida(250, True), O=salida(60), S=salida(330, True))
            registro = self.dibujar(estado)
            marcos = escena.marcos_de(fondo)
            costos = self.costos(registro)
            self.assertEqual(sorted(t for t, _ in costos), ["100", "250", "330", "60"], fondo)
            for direccion, texto in ((N, "100"), (E, "250"), (O, "60"), (S, "330")):
                cerca = [r for t, r in costos if t == texto and self.cerca_del_marco(r, marcos[direccion])]
                self.assertEqual(len(cerca), 1, (fondo, direccion, texto))      # junto a SU puerta, cerrada o no

    def test_h4_1_fr116_sc106_la_lista_de_etiquetas_trae_texto_y_rectangulo_de_cada_salida(self):
        fuente = self.vista._fuentes.pie
        marcos = escena.marcos_de(c.FONDO_REGULAR)
        estado = estado_base(3, N=salida(100), E=salida(250, True))
        etiquetas = escena.etiquetas_de_costo(estado, marcos, fuente)
        self.assertEqual([(d, t) for d, t, _ in etiquetas], [(N, "100"), (E, "250")])    # la cerrada también; S y O no tienen salida
        for direccion, texto, rectangulo in etiquetas:
            self.assertIsInstance(rectangulo, pygame.Rect)
            self.assertTrue(self.cerca_del_marco(rectangulo, marcos[direccion]), (direccion, texto))
        self.assertEqual(escena.etiquetas_de_costo(estado_base(3), marcos, fuente), [])      # sin ninguna salida, ninguna
        self.assertEqual(len(self.costos(self.dibujar(estado))), 2)                          # y la escena dibuja exactamente esas

    def test_h4_1_fr116_sc106_el_costo_no_choca_con_enemigos_protagonista_ni_otras_salidas(self):
        fuente = self.vista._fuentes.pie
        for fondo, id_sala in ((c.FONDO_REGULAR, 3), (c.FONDO_INICIAL, 1), (c.FONDO_FINAL, 6)):
            marcos = escena.marcos_de(fondo)
            for cantidad in (1, 6, 12):                              # el peor caso: costos de 4 dígitos y varios enemigos
                estado = replace(estado_base(id_sala, N=salida(9999), S=salida(8888, True), E=salida(7777), O=salida(6666)),
                                 enemigos=enemigos(cantidad))
                etiquetas = escena.etiquetas_de_costo(estado, marcos, fuente)
                self.assertEqual(len(etiquetas), 4)
                zonas = self.vista._escena._repartir(estado).enemigos + [self.vista._escena._rect_del_jugador(estado)]
                for direccion, texto, rectangulo in etiquetas:
                    contexto = (fondo, cantidad, direccion)
                    self.assertEqual(rectangulo.collidelist(zonas), -1, contexto)
                    for otra, marco in enumerate(marcos):
                        if otra != direccion:
                            self.assertFalse(rectangulo.colliderect(marco), contexto + (otra,))
                    for otra, _, otro_rectangulo in etiquetas:
                        if otra != direccion:
                            self.assertFalse(rectangulo.colliderect(otro_rectangulo), contexto + (otra,))

    def test_h4_1_fr116_sc106_se_muestra_el_costo_igualado_y_100_si_ninguna_cara_lo_declara(self):
        # Sala 1: N -> 2 sin costo en ninguna cara (100), S -> 3 (250 en las dos), O -> 5 (solo el lado de la sala 5 declara 300)
        esqueleto = salidas_con_costos(5, [salida_declarada(1, N, 2), salida_declarada(1, S, 3, 250), (1, O, 5, None, 300, False)])
        mazmorra = Mazmorra(sala_salida=5, llave_salida="llave_final")
        mazmorra.cargar_esqueleto(esqueleto)
        contexto = SimpleNamespace(esqueleto=SimpleNamespace(obtener_sala=lambda i: esqueleto[i - 1]), mazmorra=mazmorra,
                                   motor=SimpleNamespace(mapa=SimpleNamespace(es_explorada=lambda sala: True)))
        sala = ArmadorEstado()._sala_con_estado_actual(contexto, 1)
        self.assertIsNone(esqueleto[0].salidas[N].costo)                 # lo declarado por la cara de la sala 1: nada
        estado = replace(estado_base(1), sala=sala)
        etiquetas = escena.etiquetas_de_costo(estado, escena.marcos_de(c.FONDO_INICIAL), self.vista._fuentes.pie)
        self.assertEqual([(d, t) for d, t, _ in etiquetas], [(N, "100"), (S, "250"), (O, "300")])
        self.assertEqual(sorted(t for t, _ in self.costos(self.dibujar(estado))), ["100", "250", "300"])

    def test_h4_1_fr116_sc106_el_reparto_de_enemigos_no_cambia_con_los_costos(self):
        base = estado_base(3, N=salida(100), E=salida(250, True), O=salida(60), S=salida(330))
        for cantidad in (1, 6, 12):
            con = replace(base, enemigos=enemigos(cantidad))
            sin = replace(con, sala=replace(con.sala, salidas=[replace(s, costo=None) for s in con.sala.salidas]))
            self.assertEqual(self.vista._escena._repartir(con).enemigos, self.vista._escena._repartir(sin).enemigos)


class PruebasComportamientoDelEnemigo(ConVista):

    def estado(self, cantidad, comportamientos=COMPORTAMIENTOS):
        return replace(estado_base(3, N=salida(100), S=salida(100), E=salida(100), O=salida(100)),
                       enemigos=enemigos(cantidad, comportamientos))

    def fichas(self, estado, registro):
        # el texto de la ficha de cada enemigo, en orden: el que termina en «(comportamiento)» y está sobre su zona
        reparto = self.vista._escena._repartir(estado)
        resultado = []
        for i, enemigo in enumerate(estado.enemigos):
            sufijo = f"({enemigo.comportamiento})"
            hallados = [(t, r) for t, _, r in registro.textos if t.endswith(sufijo)
                        and abs(r.centerx - reparto.enemigos[i].centerx) <= c.MARCADOR_CAZADOR]
            resultado.append((enemigo, hallados, reparto.enemigos[i]))
        return resultado

    def test_h4_2_fr117_sc106_cada_enemigo_muestra_su_comportamiento_junto_a_su_nombre(self):
        for cantidad in (1, 4, 12):
            estado = self.estado(cantidad)
            registro = self.dibujar(estado)
            for enemigo, hallados, zona in self.fichas(estado, registro):
                self.assertTrue(hallados, (cantidad, enemigo.nombre, enemigo.comportamiento))
                texto, rectangulo = hallados[0]
                self.assertLessEqual(rectangulo.width, zona.width, (cantidad, texto))     # cabe en el ancho de la ficha
                if cantidad == 1:
                    self.assertTrue(texto.startswith("Rata"), texto)                      # el nombre, aunque cortado, sigue ahí

    def test_h4_2_fr117_sc106_solo_el_cazador_lleva_marcador(self):
        for cantidad in (1, 4, 12):
            estado = self.estado(cantidad)
            registro = self.dibujar(estado)
            rombos = [puntos for color, puntos, ancho in registro.poligonos if color == c.ROJO_VIVO and ancho == 0]
            cazadores = [i for i, e in enumerate(estado.enemigos) if e.comportamiento == "cazador"]
            self.assertEqual(len(rombos), len(cazadores), cantidad)
            fichas = self.fichas(estado, registro)
            for i in cazadores:                                       # el rombo está pegado al texto de SU cazador
                rectangulo = fichas[i][1][0][1]
                centros = [(sum(x for x, _ in r) / 4, sum(y for _, y in r) / 4) for r in rombos]
                cerca = [cx for cx, cy in centros if rectangulo.left - 2 * c.MARCADOR_CAZADOR <= cx < rectangulo.left
                         and rectangulo.top - 4 <= cy <= rectangulo.bottom + 4]
                self.assertEqual(len(cerca), 1, (cantidad, i))
        sin_cazador = self.estado(4, ["errante", "guardián", "rastreador"])
        self.assertEqual([p for col, p, ancho in self.dibujar(sin_cazador).poligonos if col == c.ROJO_VIVO and ancho == 0], [])

    def test_h4_2_fr117_el_marcador_sale_del_comportamiento_no_del_id_ni_del_nombre(self):
        sabueso = ActorDTO("enemigo-1", "ent_sabueso_oseo", "Sabueso óseo #1", 8, 12, 3, 1, 100, 3, comportamiento="errante")
        rata_1 = ActorDTO("enemigo-2", "ent_rata_gigante", "Rata gigante #2", 8, 12, 3, 1, 100, 3, comportamiento="cazador")
        rata_2 = ActorDTO("enemigo-3", "ent_rata_gigante", "Rata gigante #3", 8, 12, 3, 1, 100, 3, comportamiento="cazador")
        estado = replace(self.estado(3), enemigos=[sabueso, rata_1, rata_2])
        registro = self.dibujar(estado)
        fichas = self.fichas(estado, registro)
        rombos = [p for col, p, ancho in registro.poligonos if col == c.ROJO_VIVO and ancho == 0]
        self.assertEqual(len(rombos), 2)                                  # los dos cazadores, aunque no se llamen ni sean «sabueso»
        for indice in (1, 2):
            rectangulo = fichas[indice][1][0][1]
            self.assertEqual(len([r for r in rombos if rectangulo.left - 2 * c.MARCADOR_CAZADOR <= sum(x for x, _ in r) / 4
                                  < rectangulo.left]), 1, indice)
        rectangulo = fichas[0][1][0][1]                                    # el sabueso errante: ningún rombo a su lado
        self.assertEqual([r for r in rombos if rectangulo.left - 2 * c.MARCADOR_CAZADOR <= sum(x for x, _ in r) / 4
                          < rectangulo.left and abs(sum(y for _, y in r) / 4 - rectangulo.centery) <= rectangulo.height], [])

    def test_h4_2_fr117_sc106_un_errante_y_un_cazador_se_distinguen_en_pantalla(self):
        errante = self.estado(1, ["errante"])
        cazador = self.estado(1, ["cazador"])
        registro_e = self.dibujar(errante)
        imagen_e = pygame.image.tobytes(self.lienzo, "RGB")
        registro_c = self.dibujar(cazador)
        imagen_c = pygame.image.tobytes(self.lienzo, "RGB")
        self.assertNotEqual(imagen_e, imagen_c)
        textos_e = [t for t, _, _ in registro_e.textos if t.endswith("(errante)")]
        textos_c = [t for t, _, _ in registro_c.textos if t.endswith("(cazador)")]
        self.assertEqual((len(textos_e), len(textos_c)), (1, 1))
        self.assertEqual([p for col, p, a in registro_e.poligonos if col == c.ROJO_VIVO and a == 0], [])
        self.assertEqual(len([p for col, p, a in registro_c.poligonos if col == c.ROJO_VIVO and a == 0]), 1)

    def test_h4_2_fr117_el_texto_de_la_ficha_conserva_el_comportamiento_y_cabe(self):
        fuente = self.vista._fuentes.pie
        self.assertEqual(escena.texto_de_ficha(fuente, "Rata", None, 200), "Rata")                   # el jugador no lo lleva
        self.assertEqual(escena.texto_de_ficha(fuente, "Rata", "errante", 200), "Rata (errante)")
        largo = escena.texto_de_ficha(fuente, "Rata gigante #12", "rastreador", 120)
        self.assertTrue(largo.endswith("(rastreador)") and "..." in largo, largo)
        self.assertLessEqual(fuente.size(largo)[0], 120)
        solo = escena.texto_de_ficha(self.vista._fuentes.chico, "Rata gigante #12", "cazador", c.FICHA_ANCHO_MIN)
        self.assertEqual(solo, "(cazador)")                       # en la ficha estrecha, sin sitio para el nombre
        fuente = self.vista._fuentes.chico
        self.assertLessEqual(fuente.size(solo)[0], c.FICHA_ANCHO_MIN)
        self.assertTrue(escena.lleva_marcador("cazador"))
        for otro in ("errante", "guardián", "rastreador", None):
            self.assertFalse(escena.lleva_marcador(otro), otro)


if __name__ == "__main__":
    unittest.main()
