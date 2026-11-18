"""
Pruebas de la escena de juego con el terreno y el cazador (feature 001, T041; H4-1 y H4-2; FR-116, FR-117, SC-106), con la
escena REAL (SDL_VIDEODRIVER=dummy): el costo junto a cada salida, también las cerradas, y el comportamiento junto al nombre de
cada enemigo, con un marcador solo para el cazador. Lo que se dibuja se mide con lo que la escena le pide a Componentes
(texto_sombreado) y a pygame.draw.polygon, no con el color de un píxel.

La Vista recibe la sala ya igualada (contrato de PantallaDTO): aquí se arma a mano, salvo el escenario literal de H4-1, que
viene de tests/ayudas_terreno.py (el mismo montaje que usa test_dto_terreno.py). Solo se usa lo público de View: la escena
(EscenaJuego), sus funciones puras (repartir_escena, posicion_del_protagonista...) y las medidas de Componentes.
"""
import sys
import unittest
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402  (fija SDL_VIDEODRIVER=dummy antes de importar pygame)
from ayudas_vista import cerrada, estado_base  # noqa: E402

import View.Componentes as c  # noqa: E402
import View.EscenaJuego as escena  # noqa: E402
from DTO.ActorDTO import ActorDTO  # noqa: E402
from DTO.Direcciones import E, N, O, S  # noqa: E402
from DTO.SalaDTO import SalidaDTO  # noqa: E402
from Logic.Comportamientos import COMPORTAMIENTOS as CLASES_DE_COMPORTAMIENTO  # noqa: E402
from tests.ayudas_terreno import sala_del_escenario_h4_1  # noqa: E402
from View.AlmacenSprites import AlmacenSprites  # noqa: E402
from View.ZonasClic import ZonasClic  # noqa: E402

COMPORTAMIENTOS = [clase.NOMBRE for clase in CLASES_DE_COMPORTAMIENTO]      # los que existen, tal cual los define Lógica
DIRECCIONES = [N, S, E, O]
FONDOS = ((c.FONDO_REGULAR, 3), (c.FONDO_INICIAL, 1), (c.FONDO_FINAL, 6))   # (fondo, id de sala): la inicial es la 1 y la de salida la 6
DESTINOS = {N: 11, S: 12, E: 13, O: 14}                                     # de qué sala se viene al entrar por cada puerta
RUTA_ASSETS = str(Path(__file__).resolve().parent.parent / "assets")
DIGITOS_PROBADOS = 5            # la spec no fija un máximo de costo (FR-122 solo pide un entero >= 1): hasta cinco dígitos se prueban
COSTO_MAS_LARGO = "9" * DIGITOS_PROBADOS
# Costos de 4 dígitos (9999, 8888, 7777, 6666) en la prueba de choques: con 5, en fondo_inicial, la etiqueta de la puerta E u O
# pisa 7 u 8 px el sprite del protagonista que entra por ella (limitación conocida, DECISIONES.md)
COSTO_DE_CHOQUES = 9999
pygame.font.init()
# Hasta dónde llega una etiqueta de costo desde su marco: la distancia de FR-116 más lo más grande que mide la etiqueta más larga
CERCA_DEL_MARCO = c.COSTO_DISTANCIA + max(pygame.font.Font(None, c.TAM_PIE).size(COSTO_MAS_LARGO))


def salida(costo, cerrada_=False, destino=1):
    """Una salida hacia 'destino' con ese costo, cerrada (con llave) o abierta."""
    return replace(cerrada(destino), costo=costo) if cerrada_ else SalidaDTO(destino, costo=costo)


def enemigos(cantidad, comportamientos=COMPORTAMIENTOS, sala=3):
    """'cantidad' ratas con nombre «Rata gigante #n», que reparten entre sí los comportamientos dados."""
    lista = []
    for i in range(cantidad):
        lista.append(ActorDTO(f"enemigo-{i + 1}", "ent_rata_gigante", f"Rata gigante #{i + 1}", 8, 12, 3, 1, 100, sala,
                              comportamiento=comportamientos[i % len(comportamientos)]))
    return lista


def caja(puntos):
    """El rectángulo que envuelve a una lista de vértices."""
    xs, ys = [x for x, _ in puntos], [y for _, y in puntos]
    return pygame.Rect(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


class Registro:
    """Lo que la escena dibuja con texto_sombreado (texto, color, rectángulo) y los polígonos de pygame.draw.polygon."""

    def __init__(self):
        self.textos = []
        self.poligonos = []
        self.barras = []        # (rectángulo, vida, vida_max) de cada barra de vida

    def costos(self):
        """(texto, rectángulo) de los textos que son un costo (solo dígitos): un nombre o un comportamiento nunca lo es."""
        return [(t, r) for t, _, r in self.textos if t.isdigit()]

    def rombos(self):
        """Los vértices de cada rombo del cazador: cuatro puntos, rojo vivo y relleno (no su contorno)."""
        return [p for color, p, ancho in self.poligonos if len(p) == 4 and color == c.ROJO_VIVO and ancho == 0]


@contextmanager
def espiando():
    """Anota lo que se dibuje con c.texto_sombreado y pygame.draw.polygon, y siempre los deja como estaban."""
    registro = Registro()
    texto_original, poligono_original, barra_original = c.texto_sombreado, pygame.draw.polygon, c.barra_de_vida

    def texto(superficie, fuente, texto_, color, posicion, ancla="center"):
        rectangulo = texto_original(superficie, fuente, texto_, color, posicion, ancla)
        registro.textos.append((texto_, color, rectangulo.copy()))
        return rectangulo

    def poligono(superficie, color, puntos, ancho=0):
        registro.poligonos.append((color, list(puntos), ancho))
        return poligono_original(superficie, color, puntos, ancho)

    def barra(superficie, fuentes, rectangulo, vida, vida_max):
        registro.barras.append((rectangulo.copy(), vida, vida_max))
        return barra_original(superficie, fuentes, rectangulo, vida, vida_max)

    c.texto_sombreado, pygame.draw.polygon, c.barra_de_vida = texto, poligono, barra
    try:
        yield registro
    finally:
        c.texto_sombreado, pygame.draw.polygon, c.barra_de_vida = texto_original, poligono_original, barra_original


class ConEscena(unittest.TestCase):

    def setUp(self):
        pygame.display.init()
        pygame.font.init()
        pygame.display.set_mode((c.ANCHO, c.ALTO))
        self.addCleanup(pygame.quit)
        self.fuentes = c.Fuentes()
        self.almacen = AlmacenSprites(RUTA_ASSETS)
        self.escena = escena.EscenaJuego(self.almacen, self.fuentes, ZonasClic())
        self.lienzo = pygame.Surface((c.ANCHO, c.ALTO))

    def dibujar(self, estado, desde=None):
        """Dibuja la sala y devuelve lo que se pintó. Con 'desde' (el id de la sala anterior), antes dibuja un cuadro de esa
        sala, así que el protagonista entra por la puerta que lleva a ella."""
        self.escena.olvidar_la_sala()
        if desde is not None:
            self.escena.dibujar(self.lienzo, estado_base(desde), None)
        with espiando() as registro:
            self.escena.dibujar(self.lienzo, estado, None)
        return registro

    def repartir(self, estado, pies):
        """El reparto de la escena (función pura) con el protagonista pisando en 'pies'."""
        return escena.repartir_escena(self.almacen, self.fuentes, estado.enemigos, estado.objetos_suelo,
                                      estado.sala.salidas, pies)

    def protagonista_pintado(self, estado, registro, pies):
        """Los rectángulos que de verdad se pintan del protagonista: su sprite, su barra de vida y su nombre, con la sombra del
        texto. JUGADOR_OCUPA no sirve para esto: es la reserva que repartir_escena le deja al protagonista para colocar
        enemigos y objetos, y es más ancha (120 x 130) que lo pintado (91 x 90 de sprite)."""
        jugador = estado.jugador
        sprite = self.almacen.actor_a_altura(jugador.tipo, c.ALTURA_JUGADOR, nombre=jugador.nombre).fotogramas[0]
        barra = [r for r, vida, vida_max in registro.barras if (vida, vida_max) == (jugador.vida, jugador.vida_max)]
        nombre = [r.inflate(2, 2) for t, _, r in registro.textos if t == jugador.nombre]
        self.assertEqual((len(barra), len(nombre)), (1, 1))
        return [sprite.get_rect(midbottom=pies), barra[0], nombre[0]]

    def pies_sin_sala_anterior(self, estado):
        return escena.posicion_del_protagonista(estado.sala.salidas, None)


class PruebasCostoDeLasSalidas(ConEscena):

    def cerca_del_marco(self, rectangulo, marco):
        return rectangulo.colliderect(marco.inflate(2 * CERCA_DEL_MARCO, 2 * CERCA_DEL_MARCO))

    def test_h4_1_fr116_sc106_escenario_literal_muestra_100_250_100_y_300_junto_a_cada_salida(self):
        # Escenario H4-1 tal cual: costos 100, 250, una sin costo declarado y una cerrada de 300 -> se muestran 100, 250, 100 y 300
        sala = sala_del_escenario_h4_1()
        self.assertTrue(sala.salidas[O].cerrada)                            # la de 300 es la cerrada
        for fondo, id_sala in FONDOS:
            estado = replace(estado_base(id_sala), sala=replace(sala, id=id_sala))
            costos = self.dibujar(estado).costos()
            marcos = escena.marcos_de(fondo)
            self.assertEqual(sorted(t for t, _ in costos), ["100", "100", "250", "300"], fondo)
            for direccion, texto in ((N, "100"), (S, "250"), (E, "100"), (O, "300")):
                cerca = [r for t, r in costos if t == texto and self.cerca_del_marco(r, marcos[direccion])]
                self.assertEqual(len(cerca), 1, (fondo, direccion, texto))     # junto a SU puerta, también la cerrada

    def test_h4_1_fr116_sc106_cada_salida_tambien_las_cerradas_muestra_su_costo(self):
        for fondo, id_sala in FONDOS:
            estado = estado_base(id_sala, N=salida(100), E=salida(250, True), O=salida(60), S=salida(330, True))
            costos = self.dibujar(estado).costos()
            marcos = escena.marcos_de(fondo)
            self.assertEqual(sorted(t for t, _ in costos), ["100", "250", "330", "60"], fondo)
            for direccion, texto in ((N, "100"), (E, "250"), (O, "60"), (S, "330")):
                cerca = [r for t, r in costos if t == texto and self.cerca_del_marco(r, marcos[direccion])]
                self.assertEqual(len(cerca), 1, (fondo, direccion, texto))      # junto a SU puerta, cerrada o no

    def test_h4_1_fr116_sc106_la_lista_de_etiquetas_trae_texto_y_rectangulo_de_cada_salida(self):
        fuente = self.fuentes.pie
        marcos = escena.marcos_de(c.FONDO_REGULAR)
        estado = estado_base(3, N=salida(100), E=salida(250, True))
        etiquetas = escena.etiquetas_de_costo(estado, marcos, fuente)
        self.assertEqual([(d, t) for d, t, _ in etiquetas], [(N, "100"), (E, "250")])    # la cerrada también; S y O no tienen salida
        for direccion, texto, rectangulo in etiquetas:
            self.assertIsInstance(rectangulo, pygame.Rect)
            self.assertTrue(self.cerca_del_marco(rectangulo, marcos[direccion]), (direccion, texto))
        self.assertEqual(escena.etiquetas_de_costo(estado_base(3), marcos, fuente), [])      # sin ninguna salida, ninguna
        dibujados = self.dibujar(estado).costos()
        self.assertEqual(sorted((t, tuple(r)) for t, r in dibujados),                      # y la escena dibuja exactamente esas,
                         sorted((t, tuple(r)) for _, t, r in etiquetas))                   # cada una en su rectángulo

    def test_h4_1_fr116_sc106_la_etiqueta_con_su_sombra_cabe_en_pantalla_sin_pisar_el_hud_ni_el_suelo(self):
        for fondo in c.FONDOS_CONOCIDOS:
            marcos = escena.marcos_de(fondo)
            for digitos in range(1, DIGITOS_PROBADOS + 1):
                costo = int("9" * digitos)
                estado = estado_base(3, N=salida(costo), S=salida(costo, True), E=salida(costo), O=salida(costo))
                etiquetas = escena.etiquetas_de_costo(estado, marcos, self.fuentes.pie)
                self.assertEqual(len(etiquetas), 4)
                for direccion, texto, rectangulo in etiquetas:
                    pintado = rectangulo.inflate(2, 2)                            # lo que ocupa con la sombra de texto_sombreado
                    contexto = (fondo, digitos, direccion)
                    self.assertTrue(escena.PANTALLA.contains(pintado), contexto)
                    self.assertEqual(pintado.collidelist(c.HUD_PANELES), -1, contexto)
                    self.assertFalse(pintado.colliderect(c.SUELO), contexto)

    def test_h4_1_fr116_sc106_el_costo_no_choca_con_enemigos_protagonista_ni_otras_salidas(self):
        # El protagonista entra por CADA puerta (viniendo de una sala distinta por cada una) y está donde dicen PIES_PUERTA;
        # la etiqueta no toca lo que se pinta de él (sprite, barra y nombre), ni a los enemigos
        for fondo, id_sala in FONDOS:
            marcos = escena.marcos_de(fondo)
            for cantidad in (1, 6, 12):                          # el peor caso: costos de 4 dígitos y varios enemigos
                estado = replace(estado_base(id_sala, N=salida(COSTO_DE_CHOQUES, destino=DESTINOS[N]),
                                             S=salida(8888, True, DESTINOS[S]), E=salida(7777, destino=DESTINOS[E]),
                                             O=salida(6666, destino=DESTINOS[O])), enemigos=enemigos(cantidad))
                etiquetas = escena.etiquetas_de_costo(estado, marcos, self.fuentes.pie)
                self.assertEqual(len(etiquetas), 4)
                for entrada in DIRECCIONES:
                    pies = escena.posicion_del_protagonista(estado.sala.salidas, DESTINOS[entrada])
                    self.assertEqual(pies, c.PIES_PUERTA[entrada], (fondo, cantidad, entrada))     # entró de verdad por esa puerta
                    zonas = self.repartir(estado, pies).enemigos
                    registro = self.dibujar(estado, desde=DESTINOS[entrada])
                    protagonista = self.protagonista_pintado(estado, registro, pies)
                    for enemigo, zona in zip(estado.enemigos, zonas):           # la escena colocó a los enemigos con esos pies
                        dentro = [t for t, _, r in registro.textos if zona.contains(r) and t == f"{enemigo.vida}/{enemigo.vida_max}"]
                        self.assertEqual(len(dentro), 1, (fondo, cantidad, entrada))
                    for direccion, texto, rectangulo in etiquetas:
                        contexto = (fondo, cantidad, entrada, direccion)
                        pintado = rectangulo.inflate(2, 2)
                        self.assertEqual(pintado.collidelist(zonas + protagonista), -1, contexto)
                        for otra, marco in enumerate(marcos):
                            if otra != direccion:
                                self.assertFalse(pintado.colliderect(marco), contexto + (otra,))
                        for otra, _, otro_rectangulo in etiquetas:
                            if otra != direccion:
                                self.assertFalse(pintado.colliderect(otro_rectangulo.inflate(2, 2)), contexto + (otra,))

    def test_h4_1_fr116_sc106_el_reparto_de_enemigos_no_cambia_con_los_costos(self):
        base = estado_base(3, N=salida(100), E=salida(250, True), O=salida(60), S=salida(330))
        for cantidad in (1, 6, 12):
            con = replace(base, enemigos=enemigos(cantidad))
            sin = replace(con, sala=replace(con.sala, salidas=[replace(s, costo=None) for s in con.sala.salidas]))
            fichas_con = [(t, tuple(r)) for t, _, r in self.dibujar(con).textos if not t.isdigit()]
            fichas_sin = [(t, tuple(r)) for t, _, r in self.dibujar(sin).textos if not t.isdigit()]
            self.assertEqual(fichas_con, fichas_sin)


class PruebasComportamientoDelEnemigo(ConEscena):

    def estado(self, cantidad, comportamientos=COMPORTAMIENTOS):
        return replace(estado_base(3, N=salida(100), S=salida(100), E=salida(100), O=salida(100)),
                       enemigos=enemigos(cantidad, comportamientos))

    def zonas(self, estado):
        return self.repartir(estado, self.pies_sin_sala_anterior(estado)).enemigos

    def ficha_de(self, registro, zona, enemigo):
        """(texto, rectángulo) de la ficha de un enemigo: el único texto dibujado dentro de su zona, aparte del número de
        su barra de vida."""
        dentro = [(t, r) for t, _, r in registro.textos if zona.contains(r) and t != f"{enemigo.vida}/{enemigo.vida_max}"]
        self.assertEqual(len(dentro), 1, (zona, dentro))
        return dentro[0]

    def rombos_en(self, registro, zona):
        """Las cajas de los rombos dibujados dentro de la zona de un enemigo."""
        return [caja(r) for r in registro.rombos() if zona.contains(caja(r))]

    def test_h4_2_fr117_sc106_cada_enemigo_muestra_su_comportamiento_junto_a_su_nombre(self):
        for cantidad in (1, 4, 12):
            estado = self.estado(cantidad)
            registro = self.dibujar(estado)
            for enemigo, zona in zip(estado.enemigos, self.zonas(estado)):
                texto, _ = self.ficha_de(registro, zona, enemigo)           # cabe en la zona de su enemigo
                self.assertTrue(texto.endswith(f"({enemigo.comportamiento})"), (cantidad, texto))
                if cantidad == 1:
                    self.assertTrue(texto.startswith("Rata"), texto)       # el nombre, aunque cortado, sigue ahí

    def test_h4_2_fr117_sc106_solo_el_cazador_lleva_marcador(self):
        lado, hueco = c.MARCADOR_CAZADOR, c.MARCADOR_SEPARACION
        for cantidad in (1, 4, 12):
            estado = self.estado(cantidad)
            registro = self.dibujar(estado)
            self.assertEqual(len(registro.rombos()), sum(e.comportamiento == "cazador" for e in estado.enemigos), cantidad)
            for i, (enemigo, zona) in enumerate(zip(estado.enemigos, self.zonas(estado))):
                _, texto = self.ficha_de(registro, zona, enemigo)
                rombos = self.rombos_en(registro, zona)
                if enemigo.comportamiento != "cazador":
                    self.assertEqual(rombos, [], (cantidad, i))             # ni el errante, ni el guardián, ni el rastreador
                    continue
                self.assertEqual(len(rombos), 1, (cantidad, i))
                rombo = rombos[0]
                self.assertEqual(texto.left - rombo.right, hueco, (cantidad, i))        # el rombo a la izquierda del texto, con su hueco
                self.assertEqual(rombo.centery, texto.centery, (cantidad, i))           # a la altura del texto
                self.assertLessEqual(rombo.width + hueco + texto.width, zona.width, (cantidad, i))   # rombo + hueco + texto caben
                self.assertLessEqual(abs(rombo.left + texto.right - 2 * zona.centerx), 1, (cantidad, i))   # y van centrados juntos
                self.assertEqual(rombo.width, lado)
        sin_cazador = self.estado(4, ["errante", "guardián", "rastreador"])
        self.assertEqual(self.dibujar(sin_cazador).rombos(), [])

    def test_h4_2_fr117_el_marcador_sale_del_comportamiento_no_del_id_ni_del_nombre(self):
        sabueso = ActorDTO("enemigo-1", "ent_sabueso_oseo", "Sabueso óseo #1", 8, 12, 3, 1, 100, 3, comportamiento="errante")
        rata_1 = ActorDTO("enemigo-2", "ent_rata_gigante", "Rata gigante #2", 8, 12, 3, 1, 100, 3, comportamiento="cazador")
        rata_2 = ActorDTO("enemigo-3", "ent_rata_gigante", "Rata gigante #3", 8, 12, 3, 1, 100, 3, comportamiento="cazador")
        estado = replace(self.estado(3), enemigos=[sabueso, rata_1, rata_2])
        registro = self.dibujar(estado)
        zonas = self.zonas(estado)
        self.assertEqual(len(registro.rombos()), 2)                          # los dos cazadores, aunque no se llamen ni sean «sabueso»
        self.assertEqual(self.rombos_en(registro, zonas[0]), [])             # el sabueso errante: ningún rombo
        for indice in (1, 2):
            self.assertEqual(len(self.rombos_en(registro, zonas[indice])), 1, indice)

    def test_h4_2_fr117_sc106_un_errante_y_un_cazador_se_distinguen_en_pantalla(self):
        errante, cazador = self.estado(1, ["errante"]), self.estado(1, ["cazador"])
        registro_e = self.dibujar(errante)
        imagen_e = pygame.image.tobytes(self.lienzo, "RGB")
        registro_c = self.dibujar(cazador)
        imagen_c = pygame.image.tobytes(self.lienzo, "RGB")
        self.assertNotEqual(imagen_e, imagen_c)
        self.assertEqual(self.ficha_de(registro_e, self.zonas(errante)[0], errante.enemigos[0])[0].split()[-1], "(errante)")
        self.assertEqual(self.ficha_de(registro_c, self.zonas(cazador)[0], cazador.enemigos[0])[0].split()[-1], "(cazador)")
        self.assertEqual(registro_e.rombos(), [])
        self.assertEqual(len(registro_c.rombos()), 1)

    def test_h4_2_fr117_el_texto_de_la_ficha_conserva_el_comportamiento_y_cabe(self):
        fuente = self.fuentes.pie
        self.assertEqual(escena.texto_de_ficha(fuente, "Rata", None, 200), "Rata")                   # el jugador no lo lleva
        self.assertEqual(escena.texto_de_ficha(fuente, "Rata", "errante", 200), "Rata (errante)")
        largo = escena.texto_de_ficha(fuente, "Rata gigante #12", "rastreador", 120)
        self.assertTrue(largo.endswith("(rastreador)") and "..." in largo, largo)
        self.assertLessEqual(fuente.size(largo)[0], 120)
        solo = escena.texto_de_ficha(self.fuentes.chico, "Rata gigante #12", "cazador", c.FICHA_ANCHO_MIN)
        self.assertEqual(solo, "(cazador)")                       # en la ficha estrecha, sin sitio para el nombre
        self.assertLessEqual(self.fuentes.chico.size(solo)[0], c.FICHA_ANCHO_MIN)
        self.assertTrue(escena.lleva_marcador("cazador"))
        for otro in ("errante", "guardián", "rastreador", None):
            self.assertFalse(escena.lleva_marcador(otro), otro)

    def test_h4_2_fr117_el_sufijo_cabe_completo_con_el_ancho_real_de_cada_comportamiento(self):
        # El peor ancho que recibe una ficha es FICHA_ANCHO_MIN (con la fuente chica, que es la que se usa ahí); al cazador
        # le quita el rombo y su hueco. El comportamiento nunca se corta, ni el más largo.
        con_marcador = c.FICHA_ANCHO_MIN - (c.MARCADOR_CAZADOR + c.MARCADOR_SEPARACION)
        self.assertIn("cazador", COMPORTAMIENTOS)
        for comportamiento in COMPORTAMIENTOS:
            ancho = con_marcador if escena.lleva_marcador(comportamiento) else c.FICHA_ANCHO_MIN
            texto = escena.texto_de_ficha(self.fuentes.chico, "Rata gigante #12", comportamiento, ancho)
            self.assertTrue(texto.endswith(f"({comportamiento})"), (comportamiento, texto))
            self.assertLessEqual(self.fuentes.chico.size(texto)[0], ancho, (comportamiento, texto))
        # Y con 12 enemigos la ficha sí llega a ser la estrecha: lo dibujado trae el sufijo completo de cada uno
        estado = self.estado(12)
        reparto = self.repartir(estado, self.pies_sin_sala_anterior(estado))
        self.assertTrue(reparto.fuente_chica)
        self.assertEqual(min(zona.width for zona in reparto.enemigos), c.FICHA_ANCHO_MIN)
        registro = self.dibujar(estado)
        for enemigo, zona in zip(estado.enemigos, reparto.enemigos):
            self.assertTrue(self.ficha_de(registro, zona, enemigo)[0].endswith(f"({enemigo.comportamiento})"), enemigo.comportamiento)


if __name__ == "__main__":
    unittest.main()
