"""
Capturas del feedback de combate (Etapa 9, fase 2) con un reloj falso: escribe capturas/anim_f2_*.png.
Se ejecuta desde cualquier carpeta:  python tests/capturar_combate.py
"""
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402
from ayudas_vista import cerrada, con_enemigos, con_objetos, con_sala, estado_base  # noqa: E402
from ayudas_controladores import RAIZ  # noqa: E402
from test_vista_animaciones import _terminado  # noqa: E402
from test_vista_combate import con_vida_de, con_vida_del_jugador, siguiente  # noqa: E402

from DTO.PantallaDTO import PantallaDTO  # noqa: E402
from DTO.SalaDTO import SalidaDTO  # noqa: E402
from View.VistaPygame import VistaPygame  # noqa: E402

CARPETA = RAIZ / "capturas"
MENU = PantallaDTO("menu", "", ["Comenzar juego", "Modo: online", "Cargar partida", "Puntajes", "Salir"], 0)


class Reloj:
    def __init__(self):
        self.ahora = 0

    def __call__(self):
        return self.ahora


def guardar(nombre, superficie=None):
    ruta = CARPETA / f"{nombre}.png"
    pygame.image.save(superficie if superficie is not None else pygame.display.get_surface(), str(ruta))
    print(ruta)


def juego(estado):
    return PantallaDTO("juego", "", ["Esperar"], -1, estado=estado, objetivo="enemigo-1", ayuda=["Esc: menú"])


class Estudio:
    """Dibuja una escena 'tranquila' (sin cambios) y, un rato después, el estado con el cambio: así la Vista ve la diferencia."""

    def __init__(self, vista, reloj):
        self.vista, self.reloj, self.t = vista, reloj, 100000

    def preparar(self, antes):
        self.reloj.ahora = self.t
        self.vista.dibujar(MENU)                                  # reinicia la memoria: lo que sigue es una partida nueva
        self.reloj.ahora = self.t + 10
        self.vista.dibujar(juego(antes))
        self.reloj.ahora = self.t + 500                           # (el fundido de entrada a la sala ya pasó)
        self.vista.dibujar(juego(antes))

    def despues(self, estado, ms):
        """Dibuja 'estado' 'ms' después del instante del cambio (t + 600) y devuelve la superficie de la pantalla."""
        self.reloj.ahora = self.t + 600 + ms
        self.vista.dibujar(juego(estado))
        return pygame.display.get_surface()

    def terminar(self):
        self.t += 20000


def principal():
    CARPETA.mkdir(exist_ok=True)
    reloj = Reloj()
    vista = VistaPygame(animaciones=True, reloj=reloj)
    vista.abrir()
    try:
        estudio = Estudio(vista, reloj)
        cerradas = dict(N=cerrada(), S=cerrada(), E=cerrada(), O=cerrada())
        # 1. golpes, curación y daño al protagonista en el mismo instante
        antes = con_vida_de(con_enemigos(estado_base(3, **cerradas), 3), "enemigo-2", 6)
        estudio.preparar(antes)
        cambio = con_vida_del_jugador(con_vida_de(con_vida_de(siguiente(antes), "enemigo-1", 7), "enemigo-2", 10), 13)
        guardar("anim_f2_numeros_destello_y_borde", estudio.despues(cambio, 50).copy())
        estudio.terminar()

        # 2. el golpe mortal al protagonista, durante la demora del fin: números, borde y el protagonista cayendo
        antes = con_vida_del_jugador(con_enemigos(estado_base(3, **cerradas), 2), 6)
        estudio.preparar(antes)
        mortal = siguiente(_terminado(antes, "derrota"))
        guardar("anim_f2_golpe_mortal_en_la_demora", estudio.despues(mortal, 0).copy())
        guardar("anim_f2_golpe_mortal_en_la_demora_150ms", estudio.despues(mortal, 150).copy())
        estudio.terminar()

        # 3. la muerte de una rata (se encoge) y de un guardián (sus 4 fotogramas), en 4 instantes
        antes = con_enemigos(estado_base(3, **cerradas), 3)
        estudio.preparar(antes)
        muertos = siguiente(replace(antes, enemigos=[antes.enemigos[1]]))              # mueren la rata 1 y el guardián
        zona = pygame.Rect(280, 160, 820, 470)
        tomas = []
        for ms in (0, 130, 260, 400):
            tomas.append((ms, estudio.despues(muertos, ms).subsurface(zona).copy()))
        fuente = pygame.font.Font(None, 28)
        hoja = pygame.Surface((zona.width, zona.height))
        hoja.fill((0, 0, 0))
        for k, (ms, toma) in enumerate(tomas):
            reducida = pygame.transform.smoothscale(toma, (zona.width // 2, zona.height // 2))
            x, y = (k % 2) * (zona.width // 2), (k // 2) * (zona.height // 2)
            hoja.blit(reducida, (x, y))
            hoja.blit(fuente.render(f"+{ms} ms", True, (255, 255, 255)), (x + 6, y + 6))
        guardar("anim_f2_muerte_de_rata_y_guardian_4_instantes", hoja)
        estudio.terminar()

        # 4. un objeto recogido
        antes = con_objetos(estado_base(3, **cerradas), 3)
        estudio.preparar(antes)
        recogido = siguiente(replace(antes, objetos_suelo=antes.objetos_suelo[1:]))
        guardar("anim_f2_objeto_recogido", estudio.despues(recogido, 100).copy())
        estudio.terminar()

        # 5. dos puertas que se abren a la vez: la normal solo se desvanece; la final (hacia la sala de salida) además brilla
        antes = estado_base(3, N=cerrada(99), E=cerrada(6))
        estudio.preparar(antes)
        abiertas = siguiente(con_sala(antes, N=SalidaDTO(99), E=SalidaDTO(6)))
        guardar("anim_f2_puertas_se_abren_la_final_brilla", estudio.despues(abiertas, 90).copy())
        estudio.terminar()
    finally:
        vista.cerrar()


if __name__ == "__main__":
    principal()
