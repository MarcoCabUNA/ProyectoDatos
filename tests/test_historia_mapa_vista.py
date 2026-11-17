"""
Pruebas del mapa en el panel de `historia` (feature 002, FR-223): la Vista dibuja el mapa conocido que trae el resumen
(el de ese instante), no el de la partida viva. Vista real sin ventana (SDL_VIDEODRIVER=dummy) y resúmenes reales de
ServicioLineaTiempo sobre una cuadrícula sin enemigos.
"""
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402,F401  (fija SDL_VIDEODRIVER=dummy antes de importar pygame)
from test_vista_hud import VistaMedida, _pantalla  # noqa: E402

import View.Componentes as c  # noqa: E402
from DTO.AccionDTO import AccionDTO  # noqa: E402
from DTO.Direcciones import E as ESTE  # noqa: E402
from Service.ServicioLineaTiempo import ServicioLineaTiempo  # noqa: E402
from tests.ayudas_ir_a import dar_pergaminos_a, servicio_partida_cuadricula  # noqa: E402


def nombres(mapa):
    return [sala.nombre for sala in mapa.salas]


def en_el_marco(m, marco):
    return [texto for texto, rectangulo, _ in m.textos() if marco.contains(rectangulo)]


def sobrante(m, pantalla):
    """Los textos que la pantalla pone en el marco del mapa de más respecto de la misma pantalla sin resumen ni mapa
    (la escena trae sus propios rótulos en esa zona)."""
    m.dibujar(_pantalla())
    base = en_el_marco(m, c.HUD_MAPA)
    m.dibujar(pantalla)
    resto = en_el_marco(m, c.HUD_MAPA)
    for texto in base:
        resto.remove(texto)
    return resto


def dibujar_historia(resumen):
    with VistaMedida() as m:
        return sobrante(m, replace(_pantalla(), resumen=resumen))


class PruebasHistoriaMapaVista(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(self.carpeta.cleanup)

    def partida(self, pasos: int, pergaminos: int = 0):
        contexto = servicio_partida_cuadricula(self.carpeta.name).iniciar_partida("cuadricula", "Ana", semilla=5)
        if pergaminos:
            dar_pergaminos_a(contexto, pergaminos)
        lineas = ServicioLineaTiempo()
        for _ in range(pasos):
            lineas.ejecutar(contexto, AccionDTO("mover", direccion=ESTE))
        return contexto, lineas

    def test_fr223_historia_temprana_dibuja_menos_salas_que_el_mapa_vivo(self):
        contexto, lineas = self.partida(3)                                    # Sala 1 → Sala 4
        resumen = lineas.consultar_por_accion(contexto, 2)                    # antes de la 2.ª acción: conocía 1 y 2
        vivo = contexto.motor.mapa.a_dto()
        self.assertEqual(len(resumen.mapa_conocido.salas), 2)
        self.assertEqual(len(vivo.salas), 4)
        textos = dibujar_historia(resumen)
        for nombre in nombres(resumen.mapa_conocido):
            self.assertIn(nombre, textos)
        for nombre in nombres(vivo)[2:]:                                      # las salas conocidas solo en acciones posteriores
            self.assertNotIn(nombre, textos)
        self.assertIn("Mapa conocido: 2 salas exploradas", textos)

    def test_fr223_con_un_pergamino_usado_el_mapa_de_historia_no_trae_lo_revertido(self):
        contexto, lineas = self.partida(3, pergaminos=1)
        sala_revertida = nombres(contexto.motor.mapa.a_dto())[-1]             # la última que se conoció (Sala 4)
        lineas.ejecutar(contexto, AccionDTO("retroceder"))                    # revierte el 3.er paso: la Sala 4 se desconoce
        resumen = lineas.consultar_por_instante(contexto, contexto.motor.reloj)
        self.assertEqual(len(resumen.mapa_conocido.salas), 3)
        self.assertNotIn(sala_revertida, nombres(resumen.mapa_conocido))
        textos = dibujar_historia(resumen)
        for nombre in nombres(resumen.mapa_conocido):
            self.assertIn(nombre, textos)
        self.assertNotIn(sala_revertida, textos)

    def test_sin_mapa_conocido_el_panel_de_historia_no_falla_ni_dibuja_el_mapa(self):
        contexto, lineas = self.partida(2)
        resumen = replace(lineas.consultar_por_accion(contexto, 2), mapa_conocido=None)
        with VistaMedida() as m:
            self.assertEqual(sobrante(m, replace(_pantalla(), resumen=resumen)), [])
            self.assertTrue(en_el_marco(m, c.HUD_HISTORIA))                   # el texto del resumen sigue ahí

    def test_el_comando_mapa_no_cambio_su_titulo_ni_su_cierre(self):
        contexto, lineas = self.partida(2)
        mapa = contexto.motor.mapa.a_dto()
        with VistaMedida() as m:
            textos = sobrante(m, replace(_pantalla(), mapa=mapa))
        self.assertIn("Mapa conocido: 3 salas exploradas", textos)
        self.assertIn("Esc o `mapa`: cerrar", textos)
        self.assertNotIn("Historia: el mapa de ese instante", textos)

    def test_el_titulo_del_panel_del_mapa_usa_el_singular_con_una_sala(self):
        contexto, _ = self.partida(0)
        with VistaMedida() as m:
            uno = sobrante(m, replace(_pantalla(), mapa=contexto.motor.mapa.a_dto()))
        self.assertIn("Mapa conocido: 1 sala explorada", uno)
        self.assertNotIn("Mapa conocido: 1 salas exploradas", uno)
        contexto, _ = self.partida(1)
        with VistaMedida() as m:
            dos = sobrante(m, replace(_pantalla(), mapa=contexto.motor.mapa.a_dto()))
        self.assertIn("Mapa conocido: 2 salas exploradas", dos)


if __name__ == "__main__":
    unittest.main()
