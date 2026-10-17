"""
Ayudas para probar la Vista de Pygame (no es una prueba). La Vista es la real; el Controlador y los servicios también
(paquete offline, carpetas temporales): nada se escribe en cache/, logs/ ni saves/. Necesita pygame.
"""
import os
import shutil
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_controladores import CONFIG_OFFLINE  # noqa: E402
from ayudas_pygame import clic, crear_fabrica, letra, movimiento, pygame, tecla  # noqa: E402

import UIController.ControladorPygame as modulo  # noqa: E402
from UIController.ControladorPygame import DERROTA, JUEGO, ControladorPygame  # noqa: E402

ENTER, ESC = pygame.K_RETURN, pygame.K_ESCAPE
ARRIBA, ABAJO = pygame.K_UP, pygame.K_DOWN


class Recorrido:
    """ControladorPygame real + vista real + servicios reales, en una carpeta temporal. Úsalo con 'with'."""

    def __init__(self, vista):
        self.vista = vista
        self.carpeta = tempfile.mkdtemp()
        self._ruta_original = modulo.RUTA_GUARDADO
        modulo.RUTA_GUARDADO = os.path.join(self.carpeta, "saves", "partida.sav")
        ruta_puntajes = os.path.join(self.carpeta, "puntajes.jsonl")
        self.controlador = ControladorPygame(vista, CONFIG_OFFLINE, crear_fabrica(self.carpeta, ruta_puntajes))

    def __enter__(self):
        return self

    def __exit__(self, *_):
        modulo.RUTA_GUARDADO = self._ruta_original
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def pulsar(self, *codigos):
        for codigo in codigos:
            self.controlador.procesar_evento(tecla(codigo))

    def escribir(self, texto):
        for caracter in texto:
            self.controlador.procesar_evento(letra(caracter))

    def pantalla(self):
        return self.controlador.pantalla()

    def dibujar(self):
        """Dibuja el cuadro actual con la vista real y devuelve el PantallaDTO."""
        pantalla = self.pantalla()
        self.vista.dibujar(pantalla)
        return pantalla

    def centro_del_boton(self, indice):
        """Dibuja el cuadro actual y devuelve el centro de la zona que la Vista registró para el botón 'indice'."""
        self.dibujar()
        for rectangulo, elemento in zip(self.vista._zonas._rectangulos, self.vista._zonas._elementos):
            if elemento.tipo == "boton" and elemento.indice == indice:
                return rectangulo.center
        raise AssertionError(f"la Vista no registró el botón {indice}")

    def clic_en_boton(self, indice):
        self.controlador.procesar_evento(clic(self.centro_del_boton(indice)))

    def pasar_el_raton_por(self, indice):
        self.controlador.procesar_evento(movimiento(self.centro_del_boton(indice)))

    def perder(self):
        """Entra a la sala de las ratas y espera: en el paquete de pruebas la partida se pierde."""
        self.pulsar(ARRIBA)
        for _ in range(100):
            if self.pantalla().pantalla == DERROTA:
                return
            self.pulsar(pygame.K_z)
        raise AssertionError("la partida no terminó")


def las_ocho_pantallas(recorrido, al_dibujar=None):
    """Conduce el controlador por las 8 pantallas y dibuja cada una. Devuelve la lista de (nombre, PantallaDTO).
    La victoria real depende de la llave y del azar: se arma a mano a partir de la derrota real."""
    vistas = []

    def ver(nombre, pantalla=None):
        pantalla = recorrido.dibujar() if pantalla is None else pantalla
        if al_dibujar is not None:
            al_dibujar(nombre, pantalla)
        vistas.append((nombre, pantalla))

    ver("menu")
    recorrido.pulsar(ENTER)
    ver("criptas")
    recorrido.pulsar(ENTER)
    recorrido.escribir("Ana")
    ver("nombre")
    recorrido.pulsar(ENTER)
    assert recorrido.pantalla().pantalla == JUEGO
    ver("juego")
    recorrido.pulsar(ESC)
    ver("pausa")
    recorrido.pulsar(ESC)
    recorrido.perder()
    ver("derrota")
    derrota = recorrido.pantalla()
    victoria = replace(derrota, pantalla="victoria", estado=replace(derrota.estado, resultado="victoria"))
    recorrido.vista.dibujar(victoria)
    if al_dibujar is not None:
        al_dibujar("victoria", victoria)
    vistas.append(("victoria", victoria))
    recorrido.pulsar(ABAJO, ENTER)
    ver("puntajes")
    return vistas
