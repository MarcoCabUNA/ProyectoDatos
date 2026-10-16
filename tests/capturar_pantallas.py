"""
Guarda una captura PNG de cada pantalla de la Vista en capturas/ (no es una prueba; capturas/ está en .gitignore).
Conduce el controlador real con servicios reales y eventos simulados. Uso: python tests/capturar_pantallas.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402
from ayudas_vista import Recorrido, las_ocho_pantallas  # noqa: E402

from ayudas_controladores import RAIZ  # noqa: E402
from View.VistaPygame import VistaPygame  # noqa: E402

CARPETA = RAIZ / "capturas"


def principal():
    CARPETA.mkdir(exist_ok=True)
    vista = VistaPygame()
    vista.abrir()
    try:
        with Recorrido(vista) as recorrido:
            def guardar(nombre, _pantalla):
                ruta = CARPETA / f"{nombre}.png"
                pygame.image.save(pygame.display.get_surface(), str(ruta))
                print(ruta)
            las_ocho_pantallas(recorrido, guardar)
    finally:
        vista.cerrar()


if __name__ == "__main__":
    principal()
