"""
Capturas de las animaciones (Etapa 9) con un reloj falso: así cada instante se puede repetir. Escribe en capturas/ (anim_f1_*.png).
Se ejecuta desde cualquier carpeta:  python tests/capturar_animaciones.py
"""
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402
from ayudas_vista import cerrada, con_enemigos, con_objetos, estado_base  # noqa: E402
from ayudas_controladores import RAIZ  # noqa: E402

import View.Animaciones as anim  # noqa: E402
import View.Componentes as c  # noqa: E402
from DTO.ElementoDTO import ElementoDTO  # noqa: E402
from DTO.PantallaDTO import PantallaDTO  # noqa: E402
from View.VistaPygame import VistaPygame  # noqa: E402

CARPETA = RAIZ / "capturas"


class Reloj:
    def __init__(self):
        self.ahora = 0

    def __call__(self):
        return self.ahora


def guardar(nombre, superficie=None):
    ruta = CARPETA / f"{nombre}.png"
    pygame.image.save(superficie if superficie is not None else pygame.display.get_surface(), str(ruta))
    print(ruta)


def juego(estado, bajo=None):
    return PantallaDTO("juego", "", ["Esperar"], -1, estado=estado, objetivo="enemigo-1", ayuda=["Esc: menú"],
                       elemento_bajo_el_raton=bajo)


def principal():
    CARPETA.mkdir(exist_ok=True)
    reloj = Reloj()
    vista = VistaPygame(animaciones=True, reloj=reloj)
    vista.abrir()
    try:
        estado = con_objetos(con_enemigos(estado_base(3, N=cerrada(), S=cerrada(), E=cerrada(), O=cerrada()), 3), 3)
        pantalla = juego(estado)
        reloj.ahora = -2000
        vista.dibujar(pantalla)                                           # la sala nueva: su fundido ya terminó en t = 0
        recortes = []
        zona = pygame.Rect(400, 230, 560, 390)                           # el protagonista, una rata y objetos
        for ms in (0, 400, 700):
            reloj.ahora = ms
            vista.dibujar(pantalla)
            guardar(f"anim_f1_t{ms}")
            recortes.append((ms, pygame.display.get_surface().subsurface(zona).copy()))
        reloj.ahora = 400
        vista.dibujar(juego(estado, ElementoDTO("objeto_suelo", 1)))
        guardar("anim_f1_t400_raton_sobre_el_objeto_2")
        recortes.append(("400 + ratón", pygame.display.get_surface().subsurface(zona).copy()))
        hoja = pygame.Surface((zona.width * 2, zona.height * 2 + 30))
        fuente = pygame.font.Font(None, 28)
        for k, (ms, recorte) in enumerate(recortes):
            x, y = (k % 2) * zona.width, (k // 2) * (zona.height + 15)
            hoja.blit(recorte, (x, y + 15))
            hoja.blit(fuente.render(f"t = {ms}", True, (255, 255, 255)), (x + 4, y))
        guardar("anim_f1_recortes_comparados", hoja)

        # el fundido de entrada a una sala: a mitad de camino (140 de 280 ms)
        reloj.ahora = 10000
        vista.dibujar(juego(estado_base(4, N=cerrada())))
        reloj.ahora = 10140
        vista.dibujar(juego(estado_base(4, N=cerrada())))
        guardar("anim_f1_fundido_de_sala_a_la_mitad")
        # y el de una pantalla de menú (90 de 180 ms)
        menu = PantallaDTO("menu", "", ["Comenzar juego", "Modo: online", "Cargar partida", "Puntajes", "Salir"], 0)
        reloj.ahora = 20000
        vista.dibujar(menu)
        reloj.ahora = 20090
        vista.dibujar(menu)
        guardar("anim_f1_fundido_de_menu_a_la_mitad")

        # el parpadeo de la luz: el instante más claro y el más oscuro del periodo (la escena, quieta salvo la capa)
        paso = c.PARPADEO_PERIODO_MS // len(c.PARPADEO)
        mas_oscuro = c.PARPADEO.index(max(c.PARPADEO)) * paso + 1
        mas_claro = c.PARPADEO.index(min(c.PARPADEO)) * paso + 1
        quieta = juego(estado_base(3, N=cerrada(), S=cerrada(), E=cerrada(), O=cerrada()))
        reloj.ahora = 40000
        vista.dibujar(quieta)
        imagenes = []
        for nombre, ms in (("claro", mas_claro), ("oscuro", mas_oscuro)):
            reloj.ahora = 40000 + 500 * 6 + ms - ms % 500                  # mismo fotograma de reposo en los dos
            reloj.ahora = 42500 + ms
            vista.dibujar(quieta)
            guardar(f"anim_f1_parpadeo_{nombre}")
            imagenes.append(pygame.display.get_surface().copy())
        diferencia = pygame.Surface(imagenes[0].get_size())
        for x in range(0, c.ANCHO, 2):
            for y in range(0, c.ALTO, 2):
                a, b = imagenes[0].get_at((x, y)), imagenes[1].get_at((x, y))
                nivel = min(255, 20 * max(abs(a[i] - b[i]) for i in range(3)))
                pygame.draw.rect(diferencia, (nivel, nivel, nivel), (x, y, 2, 2))
        guardar("anim_f1_parpadeo_diferencia_x20", diferencia)
        print(f"alfa de la capa: claro = {anim.alfa_parpadeo(mas_claro)}, oscuro = {anim.alfa_parpadeo(mas_oscuro)} (de 255)")

        # OPCIONAL (fase 1, punto 5), solo como propuesta: el protagonista entra desde el borde de la puerta sur en ~350 ms
        almacen = vista._escena._almacen
        caminar = almacen.actor_a_altura("jugador", c.ALTURA_JUGADOR, "caminar").fotogramas
        reloj.ahora = 60000
        vista.dibujar(quieta)
        reloj.ahora = 62000
        vista.dibujar(quieta)
        base = pygame.display.get_surface().copy()
        propuesta = base.copy()
        inicio, fin = (688, 700), c.PIES_PUERTA[1]
        for k, alfa in ((0, 110), (1, 160), (2, 210)):                       # tres instantes: 0, 175 y 350 ms
            t = k / 2
            pies = (round(inicio[0] + (fin[0] - inicio[0]) * t), round(inicio[1] + (fin[1] - inicio[1]) * t))
            sprite = caminar[k % len(caminar)].copy()
            sprite.set_alpha(alfa)
            propuesta.blit(sprite, sprite.get_rect(midbottom=pies))
        guardar("anim_f1_opcional_caminar_propuesta", propuesta)
        print(f"fotogramas de 'caminar' del protagonista: {len(caminar)}")

        # fase 2B: la muerte del protagonista (3 instantes de la derrota) y la sala final de la victoria
        perdida = replace(con_enemigos(estado_base(3, N=cerrada(), S=cerrada(), E=cerrada(), O=cerrada()), 2), terminado=True,
                          resultado="derrota", mensajes=["Rata gigante #1 ataca a Jugador y le hace 7 de daño.", "Jugador ha muerto."])
        perdida = replace(perdida, jugador=replace(perdida.jugador, vida=0))
        vivo = replace(perdida, terminado=False, resultado=None, jugador=replace(perdida.jugador, vida=3), mensajes=perdida.mensajes[:1])
        reloj.ahora = 100000
        vista.dibujar(juego(vivo))
        for ms, nombre in ((0, "0"), (250, "250"), (500, "500")):
            reloj.ahora = 105000 + ms
            if ms == 0:
                vista.dibujar(juego(vivo))
                reloj.ahora = 105000
            vista.dibujar(juego(perdida))
            guardar(f"anim_f2b_muerte_t{nombre}")
        ganada = replace(estado_base(6, N=cerrada(), S=cerrada(), E=cerrada(), O=cerrada()), terminado=True, resultado="victoria",
                         mensajes=["Has escapado de la cripta."])
        reloj.ahora = 110000
        vista.dibujar(juego(ganada))
        reloj.ahora = 112000
        vista.dibujar(juego(ganada))
        guardar("anim_f2b_victoria_sala_final")
    finally:
        vista.cerrar()


if __name__ == "__main__":
    principal()
