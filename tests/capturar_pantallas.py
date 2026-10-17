"""
Guarda una captura PNG de cada pantalla de la Vista en capturas/ (no es una prueba; capturas/ está en .gitignore).
Conduce el controlador real con servicios reales y eventos simulados. Uso: python tests/capturar_pantallas.py
"""
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402
from ayudas_vista import Recorrido, las_ocho_pantallas  # noqa: E402

from ayudas_controladores import RAIZ  # noqa: E402
from DTO.PantallaDTO import PantallaDTO  # noqa: E402
from DTO.PuntajeDTO import PuntajeDTO  # noqa: E402
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
            vistas = las_ocho_pantallas(recorrido, guardar)
            # Pruebas de estrés de la lista de criptas (la partida real solo trae una): criptas inventadas.
            ayuda = ["Arriba / Abajo o ratón: elegir", "Enter o clic: aceptar", "Esc: volver"]
            for cantidad, seleccion, aviso in ((14, 2, "Aviso de prueba: la red no responde"), (40, 17, "")):
                opciones = [f"Cripta de prueba {i + 1} - {6 + i} salas, dificultad {1 + i % 3}"
                            for i in range(cantidad)] + ["Volver"]
                vista.dibujar(PantallaDTO("criptas", "Elige una cripta", opciones, seleccion, aviso=aviso, ayuda=ayuda))
                guardar(f"criptas_{cantidad}", None)
            # Pausa con un aviso largo (hasta tres líneas), sobre la pausa real.
            pausa = next(p for nombre, p in vistas if nombre == "pausa")
            aviso_largo = ("No se pudo guardar la partida: la carpeta de partidas no se puede escribir y el archivo "
                           "anterior se conservó sin cambios. Revisa los permisos de la carpeta saves e inténtalo de "
                           "nuevo; si el problema continúa, sal al menú y vuelve a cargar la última partida guardada.")
            vista.dibujar(replace(pausa, aviso=aviso_largo))
            guardar("pausa_aviso_largo", None)
            # Victoria y derrota en los casos extremos (a mano): sin puntaje y con aviso; nombre de 16 caracteres,
            # cifras grandes, presupuesto desconocido y partida online.
            victoria = next(p for nombre, p in vistas if nombre == "victoria")
            vista.dibujar(replace(victoria, puntaje=None, aviso="No se pudo guardar el puntaje: la carpeta de "
                                  "puntajes no se puede escribir. La partida terminó bien, pero no quedó registrada."))
            guardar("victoria_sin_puntaje", None)
            extremo = PuntajeDTO("W" * 16, "cripta-con-un-nombre-muy-largo-de-prueba", "abcdef0123456789",
                                 12345678901, 98765432, 10 ** 12)
            vista.dibujar(replace(victoria, puntaje=extremo, reporte=replace(victoria.reporte, solicitudes_realizadas=
                                  2 * 10 ** 9, presupuesto=None, aciertos_cache=987654321, fallos_cache=10 ** 11,
                                  offline=False)))
            guardar("victoria_extrema", None)
    finally:
        vista.cerrar()


if __name__ == "__main__":
    principal()
