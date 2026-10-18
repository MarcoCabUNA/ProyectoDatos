"""
Guarda una captura PNG de cada pantalla de la Vista en capturas/ (no es una prueba; capturas/ está en .gitignore).
Conduce el controlador real con servicios reales y eventos simulados. Uso: python tests/capturar_pantallas.py
"""
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402
from ayudas_vista import (ARRIBA, ENTER, Recorrido, cerrada, con_enemigos, con_objetos, con_sala,  # noqa: E402
                          estado_base, las_ocho_pantallas)

from ayudas_controladores import RAIZ  # noqa: E402
from DTO.ElementoDTO import ElementoDTO  # noqa: E402
from DTO.EfectoDTO import EfectoDTO  # noqa: E402
from DTO.InventarioDTO import InventarioDTO  # noqa: E402
from DTO.ObjetoDTO import ObjetoDTO  # noqa: E402
from DTO.PantallaDTO import PantallaDTO  # noqa: E402
from DTO.PuntajeDTO import PuntajeDTO  # noqa: E402
from DTO.SalaDTO import SalidaDTO  # noqa: E402
import View.Componentes as c  # noqa: E402
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
            capturar_escenas(vista, recorrido, guardar)
            capturar_hud(vista, recorrido, guardar)
            def guardar_superficie(nombre, superficie):
                ruta = CARPETA / f"{nombre}.png"
                pygame.image.save(superficie, str(ruta))
                print(ruta)
            hojas_de_medicion(guardar_superficie)
    finally:
        vista.cerrar()


def capturar_hud(vista, recorrido, guardar):
    """El HUD de la partida: sobre el estado real de cripta-01 y variaciones armadas a mano con dataclasses.replace."""
    recorrido.pulsar(pygame.K_ESCAPE)                                     # de la pausa al menú
    recorrido.pulsar(ENTER)
    recorrido.pulsar(ENTER)
    recorrido.escribir("Ana")
    recorrido.pulsar(ENTER)
    real = recorrido.pantalla()
    assert real.pantalla == "juego"
    daga = ObjetoDTO("itm_daga_oxidada", "Daga oxidada", "arma", 3, 12, ataque_bonus=4)
    antorcha = ObjetoDTO("itm_antorcha", "Antorcha", "antorcha", 1, 5, duracion=40)
    coraza = ObjetoDTO("itm_coraza_cuero", "Coraza de cuero", "armadura", 5, 20, defensa_bonus=3)
    pocion = ObjetoDTO("itm_pocion_menor", "Poción menor", "pocion", 1, 8, cura=6, modificador_velocidad=-10, duracion=20)
    llave = ObjetoDTO("itm_llave_bronce", "Llave de bronce", "llave", 1, 2, abre="puerta-de-bronce")

    def con(objetos=(), cursor=0, maximo=10, arma=None, armadura=None, criterio=None, efectos=(), mensajes=None, **mas):
        estado = replace(real.estado, efectos=list(efectos), inventario=InventarioDTO(
            list(objetos), cursor, len(objetos), maximo, arma, armadura, criterio),
            mensajes=real.estado.mensajes if mensajes is None else mensajes, **mas)
        return replace(real, estado=estado)

    def nueva(pantalla):
        vista._escena.olvidar_la_sala()
        vista.dibujar(pantalla)

    nueva(real)
    guardar("hud_estadisticas_estado_real", None)
    varios = [daga, antorcha, pocion, daga, coraza, llave]
    nueva(replace(con(varios, cursor=2, arma="itm_daga_oxidada", armadura="itm_coraza_cuero", criterio="peso"),
                  aviso="Inventario lleno"))
    guardar("hud_inventario_con_equipados", None)
    efectos = [("veneno", EfectoDTO("veneno", 12, 3)), ("velocidad_positiva", EfectoDTO("velocidad", 30, 50)),
               ("velocidad_negativa", EfectoDTO("velocidad", 25, -40)), ("antorcha", EfectoDTO("antorcha", 40, None))]
    for nombre, efecto in efectos:
        nueva(con([antorcha], efectos=[efecto]))
        guardar(f"hud_efecto_{nombre}", None)
    nueva(con([antorcha], efectos=[efecto for _, efecto in efectos] + [EfectoDTO("niebla", 7, None)]))
    guardar("hud_efectos_todos_juntos", None)
    mensajes = [f"[t={150 + 7 * i}] " + ("Guardián óseo #12 ataca a Jugador: 4 de daño" if i % 3 == 0 else
                                         "Jugador ataca a Rata gigante #10: 6 de daño" if i % 3 == 1 else
                                         "Rata gigante #2 entra a la sala") for i in range(20)]
    nueva(con(varios, mensajes=mensajes))
    guardar("hud_20_mensajes", None)
    nueva(con([], cursor=0))
    guardar("hud_inventario_vacio", None)
    largo = ObjetoDTO("itm_x", "Espada legendaria forjada en las profundidades de la cripta olvidada", "arma", 99, 9999,
                      ataque_bonus=12)
    nueva(con([daga, antorcha, pocion, llave, coraza, daga, antorcha, pocion, llave, largo], cursor=9,
              arma="itm_daga_oxidada", criterio="nombre"))
    guardar("hud_inventario_lleno", None)
    pesada = con_objetos(con_enemigos(replace(real.estado, enemigos=[], objetos_suelo=[], efectos=[EfectoDTO("veneno", 12, 3)]),
                                      12), 12)
    nueva(replace(con(varios, cursor=1, arma="itm_daga_oxidada", mensajes=mensajes, efectos=[EfectoDTO("veneno", 12, 3)]),
                  estado=replace(pesada, inventario=InventarioDTO(varios, 1, len(varios), 10, "itm_daga_oxidada", None,
                                                                 None), mensajes=mensajes),
                  elemento_bajo_el_raton=ElementoDTO("objeto_suelo", 5), objetivo="enemigo-1"))
    guardar("hud_escena_pesada", None)


def hojas_de_medicion(guardar_superficie):
    """Cómo se midieron los marcos de puerta: cada puerta de cada fondo ampliada 3 veces, con regla (cada 10 px, con
    número cada 50) y el rectángulo de EscenaJuego encima. Si el rectángulo no abraza el marco, la medida está mal."""
    from View.Componentes import FONDOS_CONOCIDOS
    from View.EscenaJuego import marcos_de
    fuente = pygame.font.Font(None, 18)
    ampliacion = 3
    for nombre in FONDOS_CONOCIDOS:
        imagen = pygame.transform.smoothscale(pygame.image.load(str(RAIZ / "assets" / "fondos" / f"{nombre}.jpg")).convert(),
                                              (1376, 768))
        hojas = []
        for direccion, marco in enumerate(marcos_de(nombre)):
            if nombre == "fondo_final" and direccion != 0:
                continue                                                  # fondo_final solo trae pintada la puerta del norte
            recorte = marco.inflate(60, 60).clip(imagen.get_rect())
            hoja = pygame.transform.scale(imagen.subsurface(recorte), (recorte.w * ampliacion, recorte.h * ampliacion))
            for x in range((recorte.left // 10 + 1) * 10, recorte.right, 10):
                px = (x - recorte.left) * ampliacion
                pygame.draw.line(hoja, (0, 255, 255), (px, 0), (px, 22 if x % 50 == 0 else 10))
                if x % 50 == 0:
                    hoja.blit(fuente.render(str(x), True, (0, 255, 255)), (px + 2, 22))
            for y in range((recorte.top // 10 + 1) * 10, recorte.bottom, 10):
                py = (y - recorte.top) * ampliacion
                pygame.draw.line(hoja, (0, 255, 255), (0, py), (22 if y % 50 == 0 else 10, py))
                if y % 50 == 0:
                    hoja.blit(fuente.render(str(y), True, (0, 255, 255)), (24, py - 6))
            caja = pygame.Rect((marco.x - recorte.x) * ampliacion, (marco.y - recorte.y) * ampliacion,
                               marco.w * ampliacion, marco.h * ampliacion)
            pygame.draw.rect(hoja, (0, 255, 0), caja, 2)
            hoja.blit(fuente.render("NSEO"[direccion] + f" {tuple(marco)}", True, (255, 255, 0)), (caja.x, max(0, caja.y - 16)))
            hojas.append(hoja)
        ancho = max(h.get_width() for h in hojas) * 2 + 10
        alto = sum(h.get_height() + 6 for h in hojas[0::2]) or 1
        alto = max(alto, sum(h.get_height() + 6 for h in hojas[1::2]))
        lamina = pygame.Surface((ancho, alto))
        lamina.fill((40, 40, 40))
        for columna in (0, 1):
            y = 0
            for hoja in hojas[columna::2]:
                lamina.blit(hoja, (columna * (ancho // 2 + 5), y))
                y += hoja.get_height() + 6
        guardar_superficie(f"medicion_{nombre}", lamina)


def capturar_escenas(vista, recorrido, guardar):
    """La escena de la partida: el estado real de cripta-01 y variaciones armadas a mano con dataclasses.replace."""
    recorrido.pulsar(pygame.K_ESCAPE)                                     # del listado de puntajes al menú
    recorrido.pulsar(ENTER)                                               # Comenzar juego
    recorrido.pulsar(ENTER)                                               # primera cripta
    recorrido.escribir("Ana")
    recorrido.pulsar(ENTER)
    inicial = recorrido.pantalla()
    assert inicial.pantalla == "juego"
    guardar("escena_inicial", recorrido.dibujar())                        # sin sala anterior: el protagonista al centro
    recorrido.pulsar(ARRIBA)                                              # a la sala de las ratas: entra por el sur
    ratas = recorrido.pantalla()
    assert len(ratas.estado.enemigos) == 2 and ratas.objetivo is not None
    guardar("escena_ratas", recorrido.dibujar())
    estado = replace(ratas.estado, enemigos=[], objetos_suelo=[])         # sala 2 (regular), vacía, para armar salas
    otra = lambda **kw: replace(ratas, estado=con_sala(estado, **kw))

    def nueva(pantalla, **kw):
        """Dibuja 'pantalla' como si el jugador acabara de empezar la partida (sin sala anterior)."""
        vista._escena.olvidar_la_sala()
        vista.dibujar(pantalla)

    nueva(otra(N=cerrada(), S=cerrada(), E=cerrada(), O=cerrada()))
    guardar("escena_puertas_cerradas", None)
    # una sola puerta dorada (la que lleva a la sala de salida); las demás, cerradas con cadena
    nueva(otra(N=cerrada(estado.sala_salida), S=cerrada(), E=cerrada(), O=cerrada()))
    guardar("escena_puerta_final", None)
    nueva(otra(S=SalidaDTO(1)))
    guardar("escena_sin_salidas_regular", None)
    en_la_salida = con_sala(replace(inicial.estado, enemigos=[], objetos_suelo=[]), id_sala=inicial.estado.sala_salida,
                            O=SalidaDTO(4), N=cerrada(7))
    nueva(replace(inicial, estado=en_la_salida))
    guardar("escena_sala_final", None)
    # entrar a una sala nueva por cada una de las cuatro puertas: antes se vio la sala 10, luego la 11
    for direccion in "NSEO":
        vista._escena.olvidar_la_sala()
        vista.dibujar(replace(ratas, estado=estado_base(10)))
        llegada = con_objetos(con_enemigos(estado_base(11, **{direccion: SalidaDTO(10)}), 2), 2)
        vista.dibujar(replace(ratas, estado=llegada, objetivo="enemigo-1"))
        guardar(f"escena_entrada_por_{direccion}", None)
    nueva(replace(ratas, estado=con_enemigos(estado, 12)))
    guardar("escena_12_enemigos", None)
    nueva(replace(ratas, estado=con_objetos(estado, 12)))
    guardar("escena_12_objetos", None)
    nueva(replace(ratas, estado=con_objetos(con_enemigos(estado, 6), 6)))
    guardar("escena_6_y_6", None)
    nueva(replace(ratas, estado=con_objetos(con_enemigos(estado, 12), 12)))
    guardar("escena_12_y_12", None)
    pesada = replace(ratas, estado=con_objetos(estado, 6), elemento_bajo_el_raton=ElementoDTO("objeto_suelo", 2))
    nueva(pesada)
    guardar("escena_nombre_de_objeto", None)
    nueva(replace(ratas, estado=con_objetos(estado, 6), elemento_bajo_el_raton=ElementoDTO("enemigo", 0)))
    guardar("escena_sin_nombre_con_un_enemigo_bajo_el_raton", None)
    # la ambientación lúgubre a tres intensidades, para compararlas (la perilla es Componentes.AMBIENTE_INTENSIDAD)
    por_omision = c.AMBIENTE_INTENSIDAD
    try:
        for intensidad in (0.4, 0.5, 0.6):
            c.AMBIENTE_INTENSIDAD = intensidad
            nueva(inicial)
            guardar(f"escena_inicial_ambiente_{intensidad}", None)
            nueva(ratas)
            guardar(f"escena_ratas_ambiente_{intensidad}", None)
            nueva(otra(S=SalidaDTO(1)))
            guardar(f"escena_sin_salidas_regular_ambiente_{intensidad}", None)
    finally:
        c.AMBIENTE_INTENSIDAD = por_omision
    recorrido.pulsar(pygame.K_ESCAPE)
    guardar("escena_pausa", recorrido.dibujar())


if __name__ == "__main__":
    principal()
