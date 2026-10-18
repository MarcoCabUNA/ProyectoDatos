"""
Maqueta del HUD (Etapa 7): solo rectángulos rotulados, sin contenido, sobre la escena más pesada (12 enemigos y 12 objetos),
con las medidas REALES de View/Componentes.py (c.HUD_*). Genera una captura "limpia" y otra con las zonas prohibidas (puertas,
c.SUELO y el sitio del protagonista en sus cinco posiciones) para ver que ningún panel pisa lo que no debe, e imprime la
comprobación numérica. Se ejecuta desde cualquier carpeta.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402
from ayudas_vista import cerrada, con_enemigos, con_objetos, estado_base  # noqa: E402
from ayudas_controladores import RAIZ  # noqa: E402

import View.Componentes as c  # noqa: E402
from DTO.PantallaDTO import PantallaDTO  # noqa: E402
from View.EscenaJuego import repartir_escena  # noqa: E402
from View.HudJuego import casillas_del_inventario  # noqa: E402
from View.VistaPygame import VistaPygame  # noqa: E402

R = pygame.Rect
CARPETA = RAIZ / "capturas"

ALTERNATIVA_A = [          # los paneles reales, con su rótulo
    ("ESTADISTICAS + RELOJ", c.HUD_ESTADISTICAS), ("EFECTOS", c.HUD_EFECTOS), ("MENSAJES (20 lineas)", c.HUD_MENSAJES),
    ("INVENTARIO", c.HUD_INVENTARIO), ("BOTON ESPERAR", c.HUD_ESPERAR), ("AVISO", c.HUD_AVISO),
    ("AYUDA (11 lineas)", c.HUD_AYUDA),
]


def casillas_de(panel, _alternativa):
    """Las 10 casillas del inventario y los subrectángulos de texto, dentro de 'panel'."""
    casillas = casillas_del_inventario(10)
    criterio = R(panel.x + 9, panel.y + 6, 150, 20)
    contador = R(panel.right - 70, panel.y + 6, 60, 20)
    detalle = R(panel.x + 9, casillas[-1].bottom + 12, panel.width - 18, panel.bottom - casillas[-1].bottom - 20)
    return casillas, criterio, contador, detalle


def rotulado(superficie, fuente, rectangulo, texto, color=(236, 230, 218), relleno=(16, 11, 16, 215)):
    capa = pygame.Surface(rectangulo.size, pygame.SRCALPHA)
    capa.fill(relleno)
    superficie.blit(capa, rectangulo)
    pygame.draw.rect(superficie, (190, 36, 42), rectangulo, 2)
    imagen = fuente.render(texto, True, color)
    superficie.blit(imagen, imagen.get_rect(midtop=(rectangulo.centerx, rectangulo.y + 4)) if rectangulo.height > 60
                    else imagen.get_rect(center=rectangulo.center))


def dibujar_maqueta(superficie, fuente, alternativa, paneles):
    for rotulo, rectangulo in paneles:
        rotulado(superficie, fuente, rectangulo, "" if rotulo.startswith("INVENTARIO") else rotulo)
        if rotulo.startswith("INVENTARIO"):
            casillas, criterio, contador, detalle = casillas_de(rectangulo, alternativa)
            for i, casilla in enumerate(casillas):
                pygame.draw.rect(superficie, (150, 112, 48), casilla, 1)
                superficie.blit(fuente.render(str(i + 1), True, (170, 160, 150)), casilla.move(4, 3))
            for sub, texto in ((criterio, "criterio: Orden"), (contador, "n/10"), (detalle, "datos del objeto bajo el cursor")):
                pygame.draw.rect(superficie, (120, 28, 32), sub, 1)
                superficie.blit(fuente.render(texto, True, (170, 160, 150)), sub.move(4, 3))


def zonas_prohibidas(vista):
    """(rótulo, rectángulo): las zonas de puerta de los tres fondos (las dos clases de puerta), c.SUELO y el sitio que
    reserva el protagonista en sus cinco posiciones."""
    prohibidas = [("SUELO", c.SUELO)]
    for id_sala in (1, 3, 6):
        for cierre in (cerrada(), cerrada(6)):
            vista._escena.olvidar_la_sala()
            vista._zonas.limpiar()
            vista.dibujar(PantallaDTO("juego", "", [], 0, estado=estado_base(id_sala, N=cierre, S=cierre,
                                                                                    E=cierre, O=cierre)))
            for direccion, rectangulo in enumerate(vista._zonas._rectangulos):
                prohibidas.append((f"puerta {'NSEO'[direccion]}", R(rectangulo)))
    for i, pies in enumerate([c.PIES_CENTRO] + list(c.PIES_PUERTA)):
        ancho, alto = c.JUGADOR_OCUPA
        prohibidas.append((f"protagonista {i}", R(pies[0] - ancho // 2, pies[1] - alto, ancho, alto)))
    return prohibidas


def tocan(paneles, prohibidas):
    return [(rotulo, nombre, rectangulo, otro) for rotulo, rectangulo in paneles for nombre, otro in prohibidas
            if rectangulo.colliderect(otro)]


def principal():
    CARPETA.mkdir(exist_ok=True)
    vista = VistaPygame()
    vista.abrir()
    try:
        fuente = pygame.font.Font(None, 22)
        vista._hud.dibujar = lambda *_: None                      # la maqueta es sin contenido: el HUD real no se dibuja
        prohibidas = zonas_prohibidas(vista)
        vista._escena.olvidar_la_sala()
        pesada = con_objetos(con_enemigos(estado_base(3, N=cerrada(), S=cerrada(), E=cerrada(), O=cerrada()), 12), 12)
        vista.dibujar(PantallaDTO("juego", "", [], 0, estado=pesada))
        escena = pygame.display.get_surface().copy()
        for letra, paneles in (("final", ALTERNATIVA_A),):
            limpia = escena.copy()
            dibujar_maqueta(limpia, fuente, letra, paneles)
            pygame.image.save(limpia, str(CARPETA / f"hud_maqueta_{letra}.png"))
            con_zonas = escena.copy()
            for nombre, rectangulo in prohibidas:
                color = (60, 120, 255) if nombre == "SUELO" else (60, 220, 90) if nombre.startswith("prota") else (255, 70, 70)
                pygame.draw.rect(con_zonas, color, rectangulo, 1)
            dibujar_maqueta(con_zonas, fuente, letra, paneles)
            pygame.image.save(con_zonas, str(CARPETA / f"hud_maqueta_{letra}_zonas.png"))
            choques = tocan(paneles, [z for z in prohibidas if z[0] != "SUELO"])
            print(f"Maqueta {letra}: {len(paneles)} paneles, {len(choques)} choques con puertas o con el protagonista")
            pisados = [p for p in (c.HUD_MENSAJES, c.HUD_ESPERAR, c.HUD_AVISO, c.HUD_AYUDA) if p.colliderect(c.SUELO)]
            print(f"   paneles que entran en SUELO (se reparten como zonas ocupadas): {len(pisados)}")
            for pies in [c.PIES_CENTRO] + list(c.PIES_PUERTA):
                reparto = repartir_escena(vista._escena._almacen, vista._fuentes, pesada.enemigos, pesada.objetos_suelo,
                                          pesada.sala.salidas, pies)
                zonas = reparto.enemigos + reparto.objetos
                bajo_un_panel = [z for z in zonas if any(z.colliderect(p) for _, p in paneles)]
                print(f"   protagonista en {pies}: {len(zonas)} zonas de enemigos y objetos, {len(bajo_un_panel)} bajo un panel")
            for choque in choques:
                print("   CHOCA:", choque)
            for rotulo, rectangulo in paneles:
                print(f"   {rotulo:45s} {tuple(rectangulo)}  bajo el borde: {rectangulo.bottom <= c.ALTO and rectangulo.right <= c.ANCHO}")
    finally:
        vista.cerrar()


if __name__ == "__main__":
    principal()
