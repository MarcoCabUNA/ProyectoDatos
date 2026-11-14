"""
Pruebas de la Vista con `historia` (feature 004, T055, FR-423, FR-406): el panel de solo lectura que muestra el
ResumenHistoriaDTO y la línea de comandos. La Vista no calcula nada: solo muestra lo que trae el DTO. SDL_VIDEODRIVER=dummy.
"""
import sys
import unittest
from dataclasses import fields, replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402,F401  (fija SDL_VIDEODRIVER=dummy antes de importar pygame)
from test_vista_hud import VistaMedida, _pantalla  # noqa: E402

import View.Componentes as c  # noqa: E402
from DTO.ActorDTO import ActorDTO  # noqa: E402
from DTO.EfectoDTO import EfectoDTO  # noqa: E402
from DTO.ResumenHistoriaDTO import ResumenHistoriaDTO  # noqa: E402
from View.HudJuego import lineas_del_resumen  # noqa: E402

JUGADOR = ActorDTO("jugador", "jugador", "Ana", 18, 30, 6, 2, 100, 2)
RATA = ActorDTO("e-201", "enemigo", "Rata gigante #1", 7, 12, 3, 0, 100, 2, "agresivo")


def un_resumen(**cambios):
    base = dict(reloj=450, sala_id=2, sala_nombre="Pasillo de las urnas", jugador=JUGADOR,
                inventario=["itm_antorcha", "itm_daga_oxidada"], arma_equipada="itm_daga_oxidada",
                armadura_equipada=None, efectos=[EfectoDTO("veneno", 12, 3)], enemigos=[RATA], instante_pedido=450)
    base.update(cambios)
    return ResumenHistoriaDTO(**base)


def dentro_del_panel(m, rectangulo):
    return [texto for texto, r, _ in m.textos() if rectangulo.contains(r)]


class PruebasVistaHistoria(unittest.TestCase):

    def test_h1_11_fr423_la_vista_muestra_el_resumen(self):
        pantalla = replace(_pantalla(), resumen=un_resumen())
        with VistaMedida() as m:
            m.dibujar(pantalla)
            texto = "\n".join(dentro_del_panel(m, c.HUD_HISTORIA))
        self.assertIn("450", texto)                                            # el reloj
        self.assertIn("Pasillo de las urnas", texto)                           # la sala
        self.assertIn("18/30", texto)                                          # la vida
        self.assertIn("itm_antorcha", texto)                                   # el inventario (ids, en su orden)
        self.assertIn("itm_daga_oxidada", texto)
        self.assertLess(texto.index("itm_antorcha"), texto.index("itm_daga_oxidada"))
        self.assertIn("Veneno", texto)                                         # los efectos
        self.assertIn("12", texto)
        self.assertIn("Rata gigante #1", texto)                                # los enemigos
        self.assertIn("7/12", texto)
        self.assertNotIn("cursor", texto.casefold())                           # el inventario no trae cursor (FR-406)

    def test_la_vista_dice_si_la_partida_termino_antes_de_t(self):
        resumen = un_resumen(reloj=900, instante_pedido=1500, terminada_antes=True)
        lineas = lineas_del_resumen(resumen)
        self.assertTrue(any("terminó antes" in linea and "1500" in linea for linea in lineas), lineas)
        self.assertFalse(any("terminó antes" in linea for linea in lineas_del_resumen(un_resumen())))

    def test_sin_resumen_no_hay_panel(self):
        with VistaMedida() as m:
            m.dibujar(_pantalla())
            self.assertEqual(dentro_del_panel(m, c.HUD_HISTORIA), [])

    def test_fr406_la_vista_no_muestra_mensajes_del_juego_en_el_resumen(self):
        mensajes = ["[t=450] Veneno te hace 3 de daño", "[t=300] Entras a Pasillo de las urnas"]
        pantalla = replace(_pantalla(mensajes=mensajes), resumen=un_resumen())
        with VistaMedida() as m:
            m.dibujar(pantalla)
            en_el_panel = "\n".join(dentro_del_panel(m, c.HUD_HISTORIA))
            en_total = m.lista()
        for mensaje in mensajes:
            self.assertNotIn(mensaje, en_el_panel)                            # el panel del resumen no lleva mensajes
            self.assertIn(mensaje, en_total)                                  # el panel de Mensajes del HUD sigue igual
        self.assertNotIn("mensajes", [campo.name for campo in fields(ResumenHistoriaDTO)])
        self.assertFalse(any("[t=" in linea for linea in lineas_del_resumen(un_resumen())))

    def test_fr423_la_linea_de_comandos_se_ve_con_su_texto(self):
        with VistaMedida() as m:
            m.dibujar(replace(_pantalla(), linea_comandos="historia #3"))
            visto = "\n".join(dentro_del_panel(m, c.HUD_LINEA))
            m.dibujar(_pantalla())
            cerrada = dentro_del_panel(m, c.HUD_LINEA)
        self.assertIn("historia #3", visto)
        self.assertEqual(cerrada, [])                                          # cerrada: no se dibuja nada

    def test_fr423_la_linea_abierta_y_vacia_se_ve_y_los_dos_paneles_caben_en_pantalla(self):
        with VistaMedida() as m:
            m.dibujar(replace(_pantalla(), linea_comandos="", resumen=un_resumen()))
            self.assertTrue(dentro_del_panel(m, c.HUD_LINEA), "la línea abierta y vacía muestra al menos su indicación")
        pantalla = pygame.Rect(0, 0, c.ANCHO, c.ALTO)
        self.assertTrue(pantalla.contains(c.HUD_HISTORIA) and pantalla.contains(c.HUD_LINEA))
        self.assertFalse(c.HUD_HISTORIA.colliderect(c.HUD_LINEA))
        for panel in c.HUD_PANELES:
            self.assertFalse(c.HUD_HISTORIA.colliderect(panel), panel)         # no tapa los paneles fijos del HUD
            self.assertFalse(c.HUD_LINEA.colliderect(panel), panel)


if __name__ == "__main__":
    unittest.main()
