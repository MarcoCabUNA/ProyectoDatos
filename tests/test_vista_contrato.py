"""
Pruebas del contrato de la Vista de Pygame (Etapa 2): abrir, dibujar, cerrar y elemento_en, con la Vista real, el
ControladorPygame real y servicios reales (paquete offline). Se ejecuta desde cualquier carpeta.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402  (fija SDL_VIDEODRIVER=dummy antes de importar pygame)
from ayudas_vista import ESC, Recorrido, las_ocho_pantallas  # noqa: E402

from DTO.PantallaDTO import PantallaDTO  # noqa: E402
from UIController.ControladorPygame import ControladorPygame  # noqa: E402
from ayudas_controladores import CONFIG_OFFLINE  # noqa: E402
from View.VistaPygame import ALTO, ANCHO, VistaPygame  # noqa: E402

PANTALLAS = ["menu", "criptas", "nombre", "juego", "pausa", "derrota", "victoria", "puntajes"]


def probar_abrir_dibujar_y_cerrar():
    vista = VistaPygame()
    vista.abrir()
    try:
        assert pygame.display.get_surface().get_size() == (ANCHO, ALTO)
        assert pygame.display.get_caption()[0] == "Cripta"
        assert pygame.display.get_init() and pygame.font.get_init()
        assert pygame.mixer.get_init() is None            # solo video y fuentes: sin audio (no pygame.init())
        vista.dibujar(PantallaDTO("menu", "CRIPTA", ["Comenzar juego"], 0))
    finally:
        vista.cerrar()
    assert not pygame.display.get_init() and not pygame.mixer.get_init()


def probar_cerrar_es_seguro_sin_abrir_y_dos_veces():
    vista = VistaPygame()
    vista.cerrar()
    vista.cerrar()


def probar_elemento_en_antes_del_primer_dibujo_devuelve_none():
    vista = VistaPygame()
    assert vista.elemento_en((10, 10)) is None
    vista.abrir()
    try:
        assert vista.elemento_en((10, 10)) is None
    finally:
        vista.cerrar()


def probar_dibujar_las_ocho_pantallas_reales():
    vista = VistaPygame()
    vista.abrir()
    try:
        with Recorrido(vista) as recorrido:
            vistas = las_ocho_pantallas(recorrido)
    finally:
        vista.cerrar()
    assert [nombre for nombre, _ in vistas] == PANTALLAS
    for nombre, pantalla in vistas:
        assert pantalla.pantalla == nombre, (nombre, pantalla.pantalla)
    assert vistas[3][1].estado.sala_inicial is not None            # la Etapa 1 llega a la Vista


def probar_el_bucle_real_termina_con_quit_y_cierra_la_vista():
    class VistaVigilada(VistaPygame):
        def __init__(self):
            super().__init__()
            self.cuadros = 0
            self.cierres = 0

        def dibujar(self, pantalla):
            self.cuadros += 1
            super().dibujar(pantalla)

        def cerrar(self):
            self.cierres += 1
            super().cerrar()

    vista = VistaVigilada()
    with Recorrido(vista) as recorrido:
        controlador = ControladorPygame(vista, CONFIG_OFFLINE, recorrido.controlador._fabrica)
        cuadros = [[], [pygame.event.Event(pygame.QUIT)]]
        controlador.ejecutar(lambda: cuadros.pop(0) if cuadros else [])
    assert vista.cuadros >= 1 and vista.cierres == 1 and not controlador.activo()


def probar_el_bucle_cierra_la_vista_aunque_falle():
    class VistaQueFalla(VistaPygame):
        cierres = 0

        def dibujar(self, pantalla):
            raise RuntimeError("fallo a propósito")

        def cerrar(self):
            VistaQueFalla.cierres += 1
            super().cerrar()

    vista = VistaQueFalla()
    with Recorrido(vista) as recorrido:
        controlador = ControladorPygame(vista, CONFIG_OFFLINE, recorrido.controlador._fabrica)
        try:
            controlador.ejecutar(lambda: [])
        except RuntimeError:
            pass
        else:
            raise AssertionError("el error debía propagarse")
    assert VistaQueFalla.cierres == 1


def probar_la_vista_no_importa_capas_prohibidas_ni_toca_el_teclado():
    for ruta in (Path(__file__).resolve().parent.parent / "View").glob("*.py"):
        codigo = ruta.read_text(encoding="utf-8")
        for prohibido in ("UIController", "Service", "Logic", "Data", "Estructuras"):
            assert f"import {prohibido}" not in codigo and f"from {prohibido}" not in codigo, (ruta.name, prohibido)
        for prohibido in ("event.get", "event.poll", "event.pump", "get_mods", "mouse.get_pos", "set_repeat",
                          "pygame.init()"):
            assert prohibido not in codigo, (ruta.name, prohibido)


if __name__ == "__main__":
    probar_abrir_dibujar_y_cerrar()
    probar_cerrar_es_seguro_sin_abrir_y_dos_veces()
    probar_elemento_en_antes_del_primer_dibujo_devuelve_none()
    probar_dibujar_las_ocho_pantallas_reales()
    probar_el_bucle_real_termina_con_quit_y_cierra_la_vista()
    probar_el_bucle_cierra_la_vista_aunque_falle()
    probar_la_vista_no_importa_capas_prohibidas_ni_toca_el_teclado()
    print("OK: todas las pruebas del contrato de la Vista pasaron")
