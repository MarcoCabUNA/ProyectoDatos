"""
Pruebas de la vista del reporte de resolubilidad (feature 003, T055 (vista); FR-311, FR-312, FR-313, FR-301).

ControladorPygame y VistaPygame reales sobre una fuente falsa con una cripta resoluble o con un ciclo de llaves
(tests/test_resolubilidad_cli.py). El reporte llega a la vista como PantallaDTO.reporte_resolubilidad (líneas ya con el
formato de TextoResolubilidad) y la vista solo lo dibuja.
"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import letra, pygame, tecla  # noqa: E402  (fija SDL_VIDEODRIVER=dummy antes de importar pygame)
from ayudas_vista import ENTER  # noqa: E402
from ayudas_controladores import crear_backend  # noqa: E402
from ayudas_resolubilidad import FuenteConLlaves  # noqa: E402
import test_resolubilidad_cli as criptas  # noqa: E402

import UIController.ControladorPygame as modulo  # noqa: E402
import View.Componentes as c  # noqa: E402
import View.ReporteResolubilidad as reporte_vista  # noqa: E402
from DTO.ConfiguracionDTO import ConfiguracionDTO  # noqa: E402
from DTO.ReporteResolubilidadDTO import RESOLUBLE  # noqa: E402
from Service.ServicioPartida import ServicioPartida  # noqa: E402
from UIController.ControladorPygame import ControladorPygame  # noqa: E402
from View.VistaPygame import VistaPygame  # noqa: E402


class Entorno:

    def __init__(self, cripta, forzar=False):
        self.carpeta = tempfile.mkdtemp()
        self.dto, self.salas, self.ubicaciones = cripta
        self.ruta_original = modulo.RUTA_GUARDADO
        modulo.RUTA_GUARDADO = os.path.join(self.carpeta, "saves", "partida.sav")
        self.vista = VistaPygame()
        self.vista.abrir()
        self.backends = []
        self.controlador = ControladorPygame(self.vista, ConfiguracionDTO(offline=True, forzar=forzar), self._fabrica)

    def _fabrica(self, config):
        partida = ServicioPartida(config, fuente=FuenteConLlaves(self.dto, self.salas, self.ubicaciones),
                                  carpeta_cache=os.path.join(self.carpeta, "cache"),
                                  carpeta_logs=os.path.join(self.carpeta, "logs"))
        backend = crear_backend(self.carpeta, config, partida=partida)
        self.backends.append(backend)
        return backend

    def cerrar(self):
        modulo.RUTA_GUARDADO = self.ruta_original
        self.vista.cerrar()
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def pulsar(self, *codigos, mod=0):
        for codigo in codigos:
            self.controlador.procesar_evento(tecla(codigo, mod))

    def empezar(self):
        self.pulsar(ENTER, ENTER)
        for caracter in "Ana":
            self.controlador.procesar_evento(letra(caracter))
        self.pulsar(ENTER)
        return self.controlador.pantalla()


class ConEntorno(unittest.TestCase):

    def entorno(self, cripta, forzar=False):
        entorno = Entorno(cripta, forzar)
        self.addCleanup(entorno.cerrar)
        return entorno


class PruebasReporteAlIniciar(ConEntorno):

    def test_h1_9_fr313_reporte_resoluble_visible_antes_de_la_primera_accion(self):
        e = self.entorno(criptas.cripta_resoluble())
        pantalla = e.empezar()
        self.assertEqual(pantalla.pantalla, "juego")
        self.assertIn("RESOLUBLE", pantalla.reporte_resolubilidad[0])
        self.assertEqual(pantalla.reporte_resolubilidad[1], "Orden de obtención de llaves: A, B, S")
        self.assertFalse(pantalla.reporte_advertencia)
        e.vista.dibujar(pantalla)                                                  # la vista lo dibuja sin romperse
        self.assertEqual(pantalla.estado.reloj, 0)

    def test_el_reporte_se_oculta_con_la_primera_accion_y_no_con_una_rechazada(self):
        e = self.entorno(criptas.cripta_resoluble())
        e.empezar()
        e.pulsar(pygame.K_w)                                                       # sin salida al norte: se rechaza
        self.assertEqual(e.controlador.pantalla().estado.reloj, 0)
        self.assertIsNotNone(e.controlador.pantalla().reporte_resolubilidad)
        e.pulsar(pygame.K_z)                                                       # esperar: la primera acción
        pantalla = e.controlador.pantalla()
        self.assertGreater(pantalla.estado.reloj, 0)
        self.assertIsNone(pantalla.reporte_resolubilidad)
        e.pulsar(pygame.K_z)
        self.assertIsNone(e.controlador.pantalla().reporte_resolubilidad)

    def test_h4_2_fr312_fr313_con_forzar_el_reporte_no_resoluble_es_una_advertencia(self):
        e = self.entorno(criptas.cripta_ciclo(), forzar=True)
        pantalla = e.empezar()
        self.assertEqual(pantalla.pantalla, "juego")
        self.assertTrue(pantalla.reporte_advertencia)
        self.assertIn("NO RESOLUBLE", pantalla.reporte_resolubilidad[0])
        e.vista.dibujar(pantalla)
        self.assertGreater(pygame.mask.from_threshold(e.vista._superficie, c.ROJO_VIVO, (1, 1, 1, 255)).count(), 0)

    def test_h4_3_fr312_forzar_con_cripta_resoluble_no_cambia_nada(self):
        sin = self.entorno(criptas.cripta_resoluble()).empezar()
        con = self.entorno(criptas.cripta_resoluble(), forzar=True).empezar()
        self.assertEqual((con.reporte_resolubilidad, con.reporte_advertencia),
                         (sin.reporte_resolubilidad, sin.reporte_advertencia))


def dibujar_y_anotar(e, pantalla):
    """Dibuja con la Vista real y devuelve los textos que se pusieron (con c.texto_en anotando)."""
    textos = []
    original = c.texto_en

    def anotando(superficie, fuente, texto, *args, **kwargs):
        textos.append(texto)
        return original(superficie, fuente, texto, *args, **kwargs)

    c.texto_en = anotando
    try:
        e.vista.dibujar(pantalla)
    finally:
        c.texto_en = original
    return textos


def borde_del_panel(e, marco):
    return tuple(e.vista._superficie.get_at((marco.x, marco.centery)))[:3]


class PruebasTituloDelPanel(ConEntorno):

    def test_fr313_la_partida_que_inicia_resoluble_dice_verificacion_y_no_advertencia(self):
        e = self.entorno(criptas.cripta_resoluble())
        pantalla = e.empezar()
        textos = dibujar_y_anotar(e, pantalla)
        self.assertIn("Verificación de resolubilidad", textos)
        self.assertNotIn("Advertencia: la cripta no es resoluble", textos)
        self.assertEqual(borde_del_panel(e, c.HUD_REPORTE_JUEGO), c.ORO)           # borde dorado

    def test_fr312_la_partida_que_inicia_con_forzar_dice_advertencia_en_rojo(self):
        e = self.entorno(criptas.cripta_ciclo(), forzar=True)
        pantalla = e.empezar()
        self.assertEqual(pantalla.pantalla, "juego")
        textos = dibujar_y_anotar(e, pantalla)
        self.assertIn("Advertencia: la cripta no es resoluble", textos)
        self.assertNotIn("La partida no inició: la cripta no es resoluble", textos)
        self.assertEqual(borde_del_panel(e, c.HUD_REPORTE_JUEGO), c.ROJO_VIVO)

    def test_fr311_la_partida_que_no_inicia_dice_que_no_inicio_y_no_es_advertencia(self):
        e = self.entorno(criptas.cripta_ciclo())
        pantalla = e.empezar()
        self.assertEqual(pantalla.pantalla, "nombre")
        textos = dibujar_y_anotar(e, pantalla)
        self.assertIn("La partida no inició: la cripta no es resoluble", textos)
        self.assertNotIn("Advertencia: la cripta no es resoluble", textos)
        self.assertEqual(borde_del_panel(e, c.HUD_REPORTE_MENU), c.ORO)            # sin el rojo de la advertencia


class PruebasPartidaQueNoInicia(ConEntorno):

    def test_h4_1_fr311_si_no_inicia_el_menu_muestra_el_reporte_completo(self):
        e = self.entorno(criptas.cripta_ciclo())
        pantalla = e.empezar()
        self.assertEqual(pantalla.pantalla, "nombre")                              # sigue en el menú: no hay partida
        self.assertFalse(pantalla.reporte_advertencia)                             # la advertencia es de la partida que SÍ inició
        texto = "\n".join(pantalla.reporte_resolubilidad)
        self.assertIn("NO RESOLUBLE", texto)
        self.assertIn("A está en la sala 6 → la puerta 2–6 requiere B → B está en la sala 7", texto)   # el ciclo, completo
        self.assertIn("Frontera bloqueada", texto)
        self.assertFalse(e.backends[0].hay_partida())

    def test_el_aviso_corto_cabe_y_el_reporte_se_lee_completo_en_el_panel(self):
        e = self.entorno(criptas.cripta_ciclo())
        pantalla = e.empezar()
        caja, lineas = e.vista._menus.caja_del_aviso(pantalla)
        self.assertLessEqual(len(lineas), c.AVISO_MAX_LINEAS)
        self.assertFalse(lineas[-1].endswith("..."))                               # el aviso no se corta…
        self.assertNotIn("A está en la sala 6", pantalla.aviso)                    # …pero tampoco trae el ciclo
        superficie = pygame.Surface((c.ANCHO, c.ALTO))
        dibujadas = reporte_vista.dibujar(superficie, e.vista._fuentes, pantalla, c.HUD_REPORTE_MENU, "")
        self.assertEqual(len(dibujadas), len(pantalla.reporte_resolubilidad))      # ninguna línea cortada ni «... y N más»
        self.assertFalse(any(linea.startswith("...") for linea in dibujadas))
        self.assertTrue(any("requiere B" in linea and "sala 6" in linea for linea in dibujadas))
        self.assertFalse(any("→" in linea for linea in dibujadas))                 # la fuente no tiene la flecha
        e.vista.dibujar(pantalla)

    def test_un_reporte_mas_largo_que_el_panel_se_corta_y_dice_cuantas_lineas_faltan(self):
        pygame.font.init()
        fuentes = c.Fuentes()
        lineas = [f"línea {i}" for i in range(40)]
        capacidad = 12
        dibujadas = reporte_vista.lineas_a_dibujar(fuentes.ayuda_juego, lineas, 600, capacidad)
        self.assertEqual(len(dibujadas), capacidad)
        self.assertIn("29 líneas más", dibujadas[-1])
        self.assertEqual(reporte_vista.lineas_a_dibujar(fuentes.ayuda_juego, lineas[:5], 600, capacidad), lineas[:5])

    def test_un_nuevo_intento_o_volver_al_menu_quita_el_reporte(self):
        e = self.entorno(criptas.cripta_ciclo())
        e.empezar()
        e.pulsar(pygame.K_ESCAPE)                                                  # volver al menú
        self.assertEqual(e.controlador.pantalla().pantalla, "menu")
        self.assertIsNone(e.controlador.pantalla().reporte_resolubilidad)


class PruebasCargarYReplay(ConEntorno):

    def test_h4_4_fr301_al_cargar_no_se_muestra_el_reporte(self):
        e = self.entorno(criptas.cripta_ciclo(), forzar=True)
        con_reporte = e.empezar()
        self.assertIsNotNone(con_reporte.reporte_resolubilidad)
        e.pulsar(pygame.K_s, mod=pygame.KMOD_CTRL)                                 # guardar
        e.pulsar(pygame.K_l, mod=pygame.KMOD_CTRL)                                 # cargar: otra partida, sin verificar
        pantalla = e.controlador.pantalla()
        self.assertEqual(pantalla.pantalla, "juego")
        self.assertIsNone(pantalla.reporte_resolubilidad)
        self.assertFalse(pantalla.reporte_advertencia)
        self.assertIsNone([b for b in e.backends if b.hay_partida()][-1].resolubilidad())

    def test_h4_4_fr301_en_replay_no_hay_reporte_que_mostrar(self):
        e = self.entorno(criptas.cripta_ciclo(), forzar=True)
        e.empezar()
        e.pulsar(pygame.K_z)
        ruta = [b for b in e.backends if b.hay_partida()][-1]._contexto.bitacora.ruta()
        otro = e._fabrica(ConfiguracionDTO(offline=True))
        resultado = otro.reproducir(ruta)
        self.assertEqual(resultado.acciones_reproducidas, 1)
        self.assertIsNone(otro.resolubilidad())


if __name__ == "__main__":
    unittest.main()
