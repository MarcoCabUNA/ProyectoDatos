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
from DTO.SalaDTO import SalidaDTO  # noqa: E402
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

    def test_h4_1_fr116_sc106_una_direccion_sin_salida_no_dibuja_costo(self):
        estado = estado_base(3, N=salida(100), E=salida(250, True))
        registro = self.dibujar(estado)
        marcos = escena.marcos_de(c.FONDO_REGULAR)
        self.assertEqual(escena.etiquetas_de_costo(estado), [(N, "100"), (E, "250")])
        for direccion in (S, O):
            for _, rectangulo in self.costos(registro):
                self.assertFalse(self.cerca_del_marco(rectangulo, marcos[direccion]), direccion)
        self.assertEqual(len(self.costos(registro)), 2)
        self.assertEqual(self.costos(self.dibujar(estado_base(3))), [])        # sin ninguna salida, ninguno

    def test_h4_1_fr116_sc106_el_costo_no_tapa_al_protagonista_ni_a_los_enemigos(self):
        fuente = self.vista._fuentes.pie
        for fondo in c.FONDOS_CONOCIDOS:
            marcos = escena.marcos_de(fondo)
            for direccion in DIRECCIONES:
                punto, ancla = escena.posicion_de_costo(marcos[direccion], direccion)
                texto = fuente.render("300", True, c.ORO)
                rectangulo = texto.get_rect(**{ancla: punto})
                self.assertFalse(rectangulo.colliderect(c.SUELO), (fondo, direccion))     # allí pisan todos
                for panel in c.HUD_PANELES:
                    self.assertFalse(rectangulo.colliderect(panel), (fondo, direccion, panel))
                self.assertTrue(pygame.Rect(0, 0, c.ANCHO, c.ALTO).contains(rectangulo), (fondo, direccion))

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
