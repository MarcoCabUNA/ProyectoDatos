"""
Pruebas de las animaciones de la Vista (Etapa 9; View/Animaciones.py, View/EfectosEscena.py y lo que EscenaJuego y VistaPygame hacen con
ellos). Tres niveles: funciones puras (tiempo -> valor); la Vista real con un reloj falso (lo único que mueve las animaciones); y una
partida completa dentro del bucle real con animaciones y un reloj que avanza. Se ejecuta desde cualquier carpeta.
"""
import contextlib
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402  (fija SDL_VIDEODRIVER=dummy antes de importar pygame)
from ayudas_vista import Recorrido, cerrada, con_enemigos, con_objetos, estado_base  # noqa: E402

import View.Animaciones as anim  # noqa: E402
import View.Componentes as c  # noqa: E402
from DTO.ElementoDTO import ELEMENTO_OBJETO_SUELO, ElementoDTO  # noqa: E402
from DTO.PantallaDTO import PantallaDTO  # noqa: E402
from View.VistaPygame import VistaPygame  # noqa: E402


# ================================================================ ayudas
class Reloj:
    """Un reloj falso: la Vista lo llama una vez por cuadro; las pruebas lo ponen donde quieren."""

    def __init__(self, ahora=0):
        self.ahora = ahora

    def __call__(self):
        return self.ahora


class RelojQueAvanza:
    """Cada vez que se le pregunta avanza 33 ms (un cuadro a ~30 fps)."""

    def __init__(self, paso=33):
        self.ahora, self.paso = -paso, paso

    def __call__(self):
        self.ahora += self.paso
        return self.ahora


class Lienzo(pygame.Surface):
    """Una superficie que apunta cada blit (la imagen y dónde cayó)."""

    def __init__(self, tamano):
        super().__init__(tamano)
        self.blits = []

    def blit(self, fuente, destino, area=None, special_flags=0):
        self.blits.append((fuente, fuente.get_rect(topleft=tuple(destino)[:2])))
        return super().blit(fuente, destino, area, special_flags)


@contextlib.contextmanager
def vista_abierta(animaciones, reloj=None):
    vista = VistaPygame(animaciones=animaciones, reloj=reloj)
    vista.abrir()
    try:
        yield vista
    finally:
        vista.cerrar()


@contextlib.contextmanager
def tablas_quietas():
    """Las tablas de vaivén, aura y parpadeo en cero: así lo único que cambia con el tiempo es el fotograma de reposo."""
    guardadas = [(t, list(t)) for t in (c.BAMBOLEO, c.PARPADEO)]
    for tabla, _ in guardadas:
        tabla[:] = [0]
    try:
        yield
    finally:
        for tabla, valores in guardadas:
            tabla[:] = valores


def _juego(estado, objetivo=None, bajo=None):
    return PantallaDTO("juego", "", ["Esperar"], -1, estado=estado, objetivo=objetivo, ayuda=["Esc: menú"],
                       elemento_bajo_el_raton=bajo)


def _escena_cargada():
    """Sala 3 con dos ratas, tres objetos distintos y las cuatro salidas cerradas."""
    estado = estado_base(3, N=cerrada(), S=cerrada(), E=cerrada(), O=cerrada())
    return con_objetos(con_enemigos(estado, 2), 3)


def _imagen():
    return pygame.image.tobytes(pygame.display.get_surface(), "RGB")


def _zonas(vista):
    return [(tuple(r), e) for r, e in zip(vista._zonas._rectangulos, vista._zonas._elementos)]


def _luminosidad(superficie):
    return sum(pygame.transform.average_color(superficie)[:3]) / 3


# ================================================================ funciones puras
def probar_fotograma_da_un_bucle_a_los_fps_pedidos_y_aguanta_los_casos_de_borde():
    assert [anim.fotograma(3, ms, 6) for ms in (0, 100, 166, 167, 300, 333, 334, 499, 500, 1000)] == [0, 0, 0, 1, 1, 1, 2, 2, 0, 0]
    assert all(anim.fotograma(1, ms, 6) == 0 for ms in (0, 100, 12345, -50))               # un solo fotograma: siempre el 0
    assert anim.fotograma(0, 100, 6) == 0 and anim.fotograma(-2, 100, 6) == 0 and anim.fotograma(3, 100, 0) == 0
    for ms in range(-3000, 3000, 37):                                                       # nunca fuera de rango, ni con ms < 0
        assert 0 <= anim.fotograma(4, ms, 6) < 4
    assert anim.fotograma(3, 10 ** 12, 6) in (0, 1, 2)


def probar_bamboleo_es_periodico_acotado_a_2_px_y_con_otra_fase_en_cada_posicion():
    assert all(isinstance(v, int) for v in c.BAMBOLEO) and max(c.BAMBOLEO) == 2 and min(c.BAMBOLEO) == -2
    for indice in range(6):
        for ms in range(0, 4000, 41):
            assert -2 <= anim.bamboleo(ms, indice) <= 2
            assert anim.bamboleo(ms, indice) == anim.bamboleo(ms + c.BAMBOLEO_PERIODO_MS, indice), (ms, indice)   # periódico
    pasos = c.BAMBOLEO_PERIODO_MS // len(c.BAMBOLEO)
    recorrido = [anim.bamboleo(k * pasos, 0) for k in range(len(c.BAMBOLEO))]
    assert recorrido == c.BAMBOLEO and sum(recorrido) == 0                                  # sube y baja lo mismo
    assert [anim.bamboleo(ms, 0) for ms in range(0, 1600, 100)] != [anim.bamboleo(ms, 1) for ms in range(0, 1600, 100)]
    assert anim.bamboleo(300, -4) == anim.bamboleo(300, 0)                                  # un índice raro no rompe nada


def probar_el_alfa_del_aura_respira_y_con_el_raton_encima_es_siempre_mas_claro():
    assert min(c.AURA_BRILLA) > max(c.AURA_RESPIRA)
    for indice in range(5):
        for ms in range(0, 5000, 53):
            normal, resaltado = anim.alfa_aura(ms, indice, False), anim.alfa_aura(ms, indice, True)
            assert normal in c.AURA_RESPIRA and resaltado in c.AURA_BRILLA
            assert 0 <= normal <= 255 and 0 <= resaltado <= 255 and resaltado > normal
    assert len({anim.alfa_aura(ms, 0, False) for ms in range(0, 2400, 100)}) > 4             # de verdad respira
    assert anim.alfa_aura(0, 0, False) == anim.alfa_aura(c.AURA_RESPIRA_PERIODO_MS, 0, False)


def probar_el_parpadeo_es_pequeno_irregular_y_periodico():
    assert max(c.PARPADEO) <= 16 and min(c.PARPADEO) >= 0 and c.PARPADEO_PERIODO_MS == 2500
    valores = [anim.alfa_parpadeo(ms) for ms in range(0, 2500, 20)]
    assert max(valores) == max(c.PARPADEO) and min(valores) == min(c.PARPADEO)
    pasos = [b - a for a, b in zip(c.PARPADEO, c.PARPADEO[1:])]
    assert any(p > 0 for p in pasos) and any(p < 0 for p in pasos) and len(set(pasos)) > 6   # sin patrón regular
    assert all(anim.alfa_parpadeo(ms) == anim.alfa_parpadeo(ms + 2500) for ms in range(0, 2500, 70))


def probar_progreso_antes_durante_despues_y_con_duracion_cero():
    assert anim.progreso(1000, 900, 280) == 0.0 and anim.progreso(1000, 1000, 280) == 0.0
    assert anim.progreso(1000, 1140, 280) == 0.5 and anim.progreso(1000, 1280, 280) == 1.0
    assert anim.progreso(1000, 99999, 280) == 1.0
    assert anim.progreso(1000, 1000, 0) == 1.0 and anim.progreso(1000, 500, 0) == 1.0 and anim.progreso(0, 5, -3) == 1.0
    assert anim.alfa_de_fundido(0.0) == 255 and anim.alfa_de_fundido(1.0) == 0 and anim.alfa_de_fundido(0.5) == 128
    assert anim.alfa_de_fundido(-1) == 255 and anim.alfa_de_fundido(7) == 0                  # se acota
    previo = 256
    for k in range(0, 101):
        alfa = anim.alfa_de_fundido(k / 100)
        assert alfa <= previo
        previo = alfa


def probar_las_tablas_y_las_duraciones_viven_en_componentes_como_listas():
    for tabla in (c.BAMBOLEO, c.AURA_RESPIRA, c.AURA_BRILLA, c.PARPADEO, c.PANTALLAS_CON_FUNDIDO):
        assert isinstance(tabla, list) and len(tabla) >= 2
    assert (c.FUNDIDO_SALA_MS, c.FUNDIDO_PANTALLA_MS, c.ANIM_IDLE_FPS) == (280, 180, 6)
    assert "pausa" not in c.PANTALLAS_CON_FUNDIDO and "juego" not in c.PANTALLAS_CON_FUNDIDO


# ================================================================ la Vista real con reloj falso
def probar_sin_animaciones_la_salida_es_la_de_siempre_y_no_cambia_con_el_tiempo():
    pantalla = _juego(_escena_cargada(), bajo=ElementoDTO(ELEMENTO_OBJETO_SUELO, 1))
    reloj = Reloj()
    with vista_abierta(False, reloj) as vista:
        imagenes = []
        for ms in (0, 100, 333, 1000, 7777):
            reloj.ahora = ms
            vista.dibujar(pantalla)
            imagenes.append(_imagen())
        assert all(i == imagenes[0] for i in imagenes), "sin animaciones, el tiempo no debe cambiar nada"
        assert vista._efectos is None
    with vista_abierta(False) as predeterminada:                                          # VistaPygame() a secas
        predeterminada.dibujar(pantalla)
        assert _imagen() == imagenes[0] and predeterminada._reloj is pygame.time.get_ticks


def probar_con_animaciones_la_escena_cambia_con_el_tiempo_y_es_la_misma_con_el_mismo_reloj():
    pantalla = _juego(_escena_cargada())
    cuadros = []
    for ms in (3000, 3200, 3400):
        reloj = Reloj(ms)
        with vista_abierta(True, reloj) as vista:
            vista.dibujar(pantalla)
            reloj.ahora = ms + 2
            vista.dibujar(pantalla)
            cuadros.append(_imagen())
    assert cuadros[0] != cuadros[1] and cuadros[1] != cuadros[2]
    reloj = Reloj(3000)
    with vista_abierta(True, reloj) as otra:                                              # el mismo reloj, el mismo cuadro
        otra.dibujar(pantalla)
        reloj.ahora = 3002
        otra.dibujar(pantalla)
        assert _imagen() == cuadros[0]


def probar_las_zonas_son_exactamente_las_mismas_con_y_sin_animaciones_en_cualquier_instante():
    escenas = [_juego(_escena_cargada()), _juego(_escena_cargada(), bajo=ElementoDTO(ELEMENTO_OBJETO_SUELO, 2)),
               _juego(replace(_escena_cargada(), enemigos=[]), objetivo=None)]
    with vista_abierta(False, Reloj()) as quieta:
        referencia = []
        for pantalla in escenas:
            quieta.dibujar(pantalla)
            referencia.append(_zonas(quieta))
    assert all(len(r) > 5 for r in referencia[:2])
    reloj = Reloj()
    with vista_abierta(True, reloj) as animada:
        for ms in range(0, 4500, 83):                                                     # durante el fundido y mucho después
            reloj.ahora = ms
            for pantalla, esperadas in zip(escenas, referencia):
                animada.dibujar(pantalla)
                assert _zonas(animada) == esperadas, (ms, pantalla.elemento_bajo_el_raton)


def probar_el_protagonista_usa_sus_tres_fotogramas_de_reposo_a_3_fps_y_el_vaiven_mueve_solo_el_dibujo():
    pantalla = _juego(_escena_cargada())
    reloj = Reloj(2000)
    with vista_abierta(True, reloj) as vista:
        vista.dibujar(pantalla)                                                           # (el fundido ya pasó pronto)
        almacen = vista._escena._almacen
        jugador = pantalla.estado.jugador
        fotogramas = almacen.actor_a_altura(jugador.tipo, c.ALTURA_JUGADOR, nombre=jugador.nombre).fotogramas
        assert len(fotogramas) == 3
        enemigo = almacen.actor_a_altura(pantalla.estado.enemigos[0].tipo, 100).fotogramas
        assert len(enemigo) == 1
        vistos, posiciones = [], []
        vista._superficie = Lienzo((c.ANCHO, c.ALTO))
        for ms in range(4000, 4000 + 1600, 50):
            reloj.ahora = ms
            vista._superficie.blits.clear()
            vista.dibujar(pantalla)
            for imagen, rectangulo in vista._superficie.blits:
                for k, f in enumerate(fotogramas):
                    if imagen is f:
                        vistos.append((ms, k))
                reparto = vista._escena._repartir(pantalla.estado)
                for i, e in enumerate(reparto.sprites):
                    if imagen is e and rectangulo.centerx == reparto.enemigos[i].centerx:   # (dos ratas comparten el sprite)
                        posiciones.append((ms, i, rectangulo.y, rectangulo.x))
        assert c.ANIM_IDLE_JUGADOR_FPS == 3                                               # ciclo de 1 s con sus 3 fotogramas
        assert all(k == anim.fotograma(3, ms, 3) for ms, k in vistos) and {k for _, k in vistos} == {0, 1, 2}
        assert all(k == (ms % 1000) * 3 // 1000 for ms, k in vistos)                      # 0-333 ms: 0, 334-666: 1, 667-999: 2
        for i in (0, 1):
            ys = [y for ms, j, y, x in posiciones if j == i]
            assert max(ys) - min(ys) == 4, (i, max(ys) - min(ys))                         # ±2 px
            assert len({x for ms, j, y, x in posiciones if j == i}) == 1                  # solo en vertical
        fase0 = [y for ms, j, y, x in posiciones if j == 0]
        fase1 = [y for ms, j, y, x in posiciones if j == 1]
        assert fase0 != fase1                                                             # fase distinta por posición


def probar_el_aura_respira_con_el_alfa_de_la_tabla_y_brilla_mas_en_el_objeto_bajo_el_raton():
    estado = _escena_cargada()
    reloj = Reloj(5000)
    with vista_abierta(True, reloj) as vista:
        almacen = vista._escena._almacen
        auras = [almacen.aura_de_objeto(o.id, o.clase, c.LADO_OBJETO, c.AURA_MARGEN, c.AURA_COLOR, c.AURA_INTENSIDAD_ANIMADA)
                 for o in estado.objetos_suelo]
        assert len({id(a) for a in auras}) == 3
        for ms in range(5000, 8000, 130):
            reloj.ahora = ms
            for resaltado in (-1, 0, 1, 2):
                vista.dibujar(_juego(estado, bajo=None if resaltado < 0 else ElementoDTO(ELEMENTO_OBJETO_SUELO, resaltado)))
                for i, aura in enumerate(auras):
                    assert aura.get_alpha() == anim.alfa_aura(ms, i, i == resaltado), (ms, i, resaltado)
                    if i == resaltado:
                        assert aura.get_alpha() > max(c.AURA_RESPIRA)


def probar_el_fundido_de_sala_empieza_opaco_termina_transparente_y_nunca_tapa_el_hud():
    pantalla = _juego(estado_base(3))
    reloj = Reloj(1000)
    libre = pygame.Rect(300, 200, 300, 150)                                               # escena sin HUD ni puertas
    with tablas_quietas(), vista_abierta(True, reloj) as vista:
        vista.dibujar(pantalla)                                                           # primer cuadro de la sala: empieza
        pantalla_negra = pygame.display.get_surface().subsurface(libre).copy()
        assert _luminosidad(pantalla_negra) == 0.0                                        # opaco
        hud = pygame.display.get_surface().subsurface(c.HUD_AYUDA).copy()
        claros = sum(1 for x in range(hud.get_width()) for y in range(hud.get_height()) if hud.get_at((x, y))[:3] == c.TEXTO_SUAVE)
        assert claros > 100, "el HUD tiene que verse, con su color, aunque la escena esté a oscuras"
        luminosidades = []
        for ms in (1000, 1070, 1140, 1210, 1279, 1280, 1500):
            reloj.ahora = ms
            vista.dibujar(pantalla)
            luminosidades.append(_luminosidad(pygame.display.get_surface().subsurface(libre)))
        assert luminosidades[0] == 0.0 and all(a <= b for a, b in zip(luminosidades, luminosidades[1:]))
        assert luminosidades[2] > 0 and luminosidades[-1] == luminosidades[-2] > luminosidades[3]
    reloj2 = Reloj(1720)                                                    # (1720 + 280 = 2000: el reposo en su fotograma 0)
    with tablas_quietas(), vista_abierta(True, reloj2) as animada:
        animada.dibujar(pantalla)
        reloj2.ahora = 1720 + c.FUNDIDO_SALA_MS
        animada.dibujar(pantalla)
        animado = _imagen()
    with vista_abierta(False) as estatica:                                                # idéntico al cuadro de siempre
        estatica.dibujar(pantalla)
        assert _imagen() == animado, "al terminar el fundido y sin vaivén ni parpadeo, el cuadro es el de siempre"


def probar_el_fundido_de_sala_vuelve_a_empezar_al_cambiar_de_sala_y_no_al_seguir_en_ella():
    reloj = Reloj(0)
    libre = pygame.Rect(300, 200, 300, 150)
    with tablas_quietas(), vista_abierta(True, reloj) as vista:
        vista.dibujar(_juego(estado_base(3)))
        reloj.ahora = 1000
        vista.dibujar(_juego(estado_base(3)))
        assert _luminosidad(pygame.display.get_surface().subsurface(libre)) > 20           # sigue en la misma sala: sin fundido
        reloj.ahora = 1100
        vista.dibujar(_juego(estado_base(4)))                                             # otra sala
        assert _luminosidad(pygame.display.get_surface().subsurface(libre)) == 0.0
        reloj.ahora = 1100 + 280
        vista.dibujar(_juego(estado_base(4)))
        assert _luminosidad(pygame.display.get_surface().subsurface(libre)) > 20


def probar_el_fundido_de_pantalla_de_menu_dura_180_ms_cubre_todo_y_no_se_repite_en_la_misma_pantalla():
    menu = PantallaDTO("menu", "", ["Comenzar juego", "Salir"], 0)
    criptas = PantallaDTO("criptas", "Elige", ["Volver"], 0)
    reloj = Reloj(500)
    with vista_abierta(True, reloj) as vista:
        vista.dibujar(menu)
        assert _luminosidad(pygame.display.get_surface()) == 0.0                           # empieza opaco, en toda la pantalla
        reloj.ahora = 590
        vista.dibujar(menu)
        medio = _luminosidad(pygame.display.get_surface())
        reloj.ahora = 680
        vista.dibujar(menu)
        final = _imagen()
        assert 0 < medio < _luminosidad(pygame.display.get_surface())
        reloj.ahora = 5000
        vista.dibujar(menu)
        assert _imagen() == final                                                         # terminó: idéntico al cuadro estático
        reloj.ahora = 6000
        vista.dibujar(criptas)                                                            # otra pantalla: otro fundido
        assert _luminosidad(pygame.display.get_surface()) == 0.0
    with vista_abierta(False) as estatica:
        estatica.dibujar(menu)
        assert _imagen() == final


def probar_la_pausa_dibuja_la_escena_congelada_y_sin_fundido():
    pantalla = _juego(_escena_cargada())
    pausa = PantallaDTO("pausa", "Pausa", ["Continuar", "Salir al menú"], 0, estado=pantalla.estado)
    reloj = Reloj(4000)
    with vista_abierta(True, reloj) as vista:
        vista.dibujar(pantalla)
        reloj.ahora = 4300
        vista.dibujar(pantalla)
        en_marcha = _imagen()
        reloj.ahora = 4400
        vista.dibujar(pausa)
        congelada = _imagen()
        for ms in (4800, 5100, 9000):
            reloj.ahora = ms
            vista.dibujar(pausa)
            assert _imagen() == congelada, ms                                             # el tiempo no mueve nada en la pausa
        assert congelada != en_marcha
        assert _luminosidad(pygame.display.get_surface()) > 2                             # (la pausa ya es oscura de por sí) y no hay fundido


def probar_el_parpadeo_es_una_sola_capa_oscura_de_a_lo_sumo_16_de_alfa_y_no_recalcula_el_fondo():
    pantalla = _juego(estado_base(3))
    reloj = Reloj(9000)
    calculos = []
    original = pygame.transform.grayscale
    pygame.transform.grayscale = lambda *a, **k: calculos.append(1) or original(*a, **k)
    try:
        with vista_abierta(True, reloj) as vista:
            vista.dibujar(pantalla)
            primeras, entradas = len(calculos), vista._escena._almacen.entradas_cache
            claro = oscuro = None
            for ms in range(9000 + 400, 9000 + 400 + 2500, 20):
                reloj.ahora = ms
                vista.dibujar(pantalla)
                brillo = _luminosidad(pygame.display.get_surface().subsurface(pygame.Rect(300, 200, 300, 150)))
                claro = brillo if claro is None else max(claro, brillo)
                oscuro = brillo if oscuro is None else min(oscuro, brillo)
            assert len(calculos) == primeras == 1                                          # el fondo se calculó UNA vez
            assert vista._escena._almacen.entradas_cache == entradas                       # y la caché no creció
            assert 0 < claro - oscuro <= 16 * 0.2 * 2 + 1.0                                # capa leve: unos pocos niveles
            assert claro > oscuro
    finally:
        pygame.transform.grayscale = original


def probar_la_cache_de_sprites_no_crece_ni_por_cuadro_ni_por_instancia():
    reloj = Reloj(0)
    with vista_abierta(True, reloj) as vista:
        pantalla = _juego(_escena_cargada(), bajo=ElementoDTO(ELEMENTO_OBJETO_SUELO, 0))
        for _ in range(3):
            vista.dibujar(pantalla)
        entradas = vista._escena._almacen.entradas_cache
        for ms in range(0, 6000, 33):                                                     # 180 cuadros, con aura, bamboleo y reposo
            reloj.ahora = ms
            vista.dibujar(pantalla)
        assert vista._escena._almacen.entradas_cache == entradas
        # ocho ratas con nombres distintos comparten sprites: no hay entradas por instancia
        muchas = _juego(con_objetos(con_enemigos(_escena_cargada(), 8), 3))
        vista.dibujar(muchas)
        con_ocho = vista._escena._almacen.entradas_cache
        nombres = [e.nombre for e in muchas.estado.enemigos]                              # los mismos nombres, repartidos de otro modo
        nombres = nombres[1:] + nombres[:1]
        otras = _juego(replace(muchas.estado, enemigos=[replace(e, nombre=n) for e, n in zip(muchas.estado.enemigos, nombres)]))
        vista.dibujar(otras)
        assert vista._escena._almacen.entradas_cache == con_ocho


# ================================================================ de punta a punta
def probar_fotograma_unico_se_reproduce_una_vez_y_se_queda_en_el_ultimo():
    assert [anim.fotograma_unico(3, ms, 600) for ms in (-50, 0, 199, 200, 399, 400, 599, 600, 601, 10 ** 9)] == [0, 0, 0, 1, 1, 2, 2, 2, 2, 2]
    assert anim.fotograma_unico(1, 123, 600) == 0 and anim.fotograma_unico(0, 123, 600) == 0
    assert anim.fotograma_unico(3, 5, 0) == 2 and anim.fotograma_unico(3, 5, -1) == 2
    assert c.MUERTE_JUGADOR_MS == 600 and isinstance(c.MUERTE_JUGADOR_MS, int)


def _terminado(estado, resultado):
    return replace(estado, terminado=True, resultado=resultado, jugador=replace(estado.jugador, vida=0 if resultado == "derrota" else 9))


def _que_fotograma_del_protagonista(vista, pantalla, almacen):
    """('idle' o 'muerte', k) del protagonista en el último cuadro dibujado en el Lienzo de la vista."""
    jugador = pantalla.estado.jugador
    idle = almacen.actor_a_altura(jugador.tipo, c.ALTURA_JUGADOR, nombre=jugador.nombre).fotogramas
    muerte = almacen.actor_a_altura(jugador.tipo, c.ALTURA_JUGADOR, "muerte", jugador.nombre).fotogramas
    vistos = []
    for imagen, _ in vista._superficie.blits:
        for k, f in enumerate(idle):
            if imagen is f:
                vistos.append(("idle", k))
        for k, f in enumerate(muerte):
            if imagen is f:
                vistos.append(("muerte", k))
    assert len(vistos) == 1, vistos                                                   # el protagonista se dibuja una sola vez
    return vistos[0]


def _dibujar_en_lienzo(vista, pantalla, reloj, ms, almacen):
    reloj.ahora = ms
    vista._superficie.blits.clear()
    vista.dibujar(pantalla)
    return _que_fotograma_del_protagonista(vista, pantalla, almacen)


def probar_en_la_derrota_el_protagonista_cae_con_sus_tres_fotogramas_de_muerte_y_se_queda_en_el_ultimo():
    en_curso = _juego(_escena_cargada())
    derrota = _juego(_terminado(_escena_cargada(), "derrota"))
    reloj = Reloj(5000)
    with vista_abierta(True, reloj) as vista:
        vista.dibujar(en_curso)
        almacen = vista._escena._almacen
        assert len(almacen.actor_a_altura("jugador", c.ALTURA_JUGADOR, "muerte", "Jugador").fotogramas) == 3
        vista._superficie = Lienzo((c.ANCHO, c.ALTO))
        for ms in range(5100, 5700, 40):                                              # la partida en curso: nunca la muerte
            assert _dibujar_en_lienzo(vista, en_curso, reloj, ms, almacen)[0] == "idle"
        tiempos = (9000, 9050, 9199, 9200, 9399, 9400, 9599, 9600, 9601, 10500, 60000)   # el primer cuadro terminado: 9000
        vistos = [_dibujar_en_lienzo(vista, derrota, reloj, ms, almacen) for ms in tiempos]
        assert vistos == [("muerte", k) for k in (0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 2)], vistos
        assert _dibujar_en_lienzo(vista, en_curso, reloj, 70000, almacen)[0] == "idle"   # otra partida: la cuenta se olvida
        assert _dibujar_en_lienzo(vista, derrota, reloj, 80000, almacen) == ("muerte", 0)
        assert _dibujar_en_lienzo(vista, derrota, reloj, 80300, almacen) == ("muerte", 1)
        assert _dibujar_en_lienzo(vista, derrota, reloj, 80100, almacen) == ("muerte", 0)   # el reloj retrocedió: empieza de nuevo


def probar_con_victoria_el_protagonista_no_muere_y_sin_animaciones_tampoco_cae():
    victoria = _juego(_terminado(_escena_cargada(), "victoria"))
    derrota = _juego(_terminado(_escena_cargada(), "derrota"))
    reloj = Reloj(5000)
    with vista_abierta(True, reloj) as vista:
        vista.dibujar(victoria)
        almacen = vista._escena._almacen
        vista._superficie = Lienzo((c.ANCHO, c.ALTO))
        for ms in (5000, 5100, 5300, 5700, 7000):
            assert _dibujar_en_lienzo(vista, victoria, reloj, ms, almacen)[0] == "idle", ms
    with vista_abierta(False) as vista:                                               # sin animaciones: ni la muerte ni el reposo
        vista.dibujar(derrota)
        almacen = vista._escena._almacen
        vista._superficie = Lienzo((c.ANCHO, c.ALTO))
        jugador = derrota.estado.jugador
        idle0 = almacen.actor_a_altura(jugador.tipo, c.ALTURA_JUGADOR, nombre=jugador.nombre).fotogramas[0]
        for _ in range(3):
            vista._superficie.blits.clear()
            vista.dibujar(derrota)
            assert sum(1 for imagen, _ in vista._superficie.blits if imagen is idle0) == 1


def probar_la_muerte_no_cambia_las_zonas_de_clic_y_la_barra_queda_en_cero():
    derrota = _juego(_terminado(_escena_cargada(), "derrota"), "enemigo-1")
    mismas = []
    for animaciones in (False, True):
        reloj = Reloj(3000)
        with vista_abierta(animaciones, reloj) as vista:
            tomas = []
            for ms in (3000, 3150, 3450, 4000):
                reloj.ahora = ms
                vista.dibujar(derrota)
                tomas.append(_zonas(vista))
            assert all(t == tomas[0] for t in tomas)
            mismas.append(tomas[0])
    assert mismas[0] == mismas[1]
    assert derrota.estado.jugador.vida == 0 and derrota.estado.jugador.vida_max > 0


def probar_una_partida_perdida_con_demora_muestra_la_escena_final_y_luego_la_derrota():
    import os
    from ayudas_controladores import CONFIG_OFFLINE
    from ayudas_pygame import crear_fabrica, tecla
    from UIController.ControladorPygame import ControladorPygame
    reloj = RelojQueAvanza()
    vista = VistaPygame(animaciones=True, reloj=reloj)
    with Recorrido(vista) as recorrido:
        recorrido.controlador = ControladorPygame(vista, CONFIG_OFFLINE,
                                                  crear_fabrica(recorrido.carpeta, os.path.join(recorrido.carpeta, "puntajes.jsonl")),
                                                  demora_fin_ms=1500, reloj_ms=lambda: reloj.ahora)
        pantallas = []                                                                # lo que se dibujó en cada cuadro
        dibujar = vista.dibujar

        def dibujando(pantalla):
            pantallas.append((pantalla.pantalla, pantalla.estado is not None and pantalla.estado.terminado))
            return dibujar(pantalla)
        vista.dibujar = dibujando
        pasos = [[tecla(pygame.K_RETURN)], [tecla(pygame.K_RETURN)]] + [[tecla(pygame.K_BACKSPACE)]] * 16 + \
                [[tecla(ord("a"), caracter="a")], [tecla(pygame.K_RETURN)], [tecla(pygame.K_UP)]]
        cuadros = {"n": 0}

        def eventos():
            cuadros["n"] += 1
            if pantallas and pantallas[-1][0] == "derrota":
                return [pygame.event.Event(pygame.QUIT)]
            if cuadros["n"] <= len(pasos):
                return pasos[cuadros["n"] - 1]
            terminado = bool(pantallas) and pantallas[-1] == ("juego", True)
            assert cuadros["n"] < 600, "la partida no terminó"                              # (nunca un bucle sin fin)
            return [] if terminado else [tecla(pygame.K_z)]
        recorrido.controlador.ejecutar(eventos)
        nombres = [n for n, _ in pantallas]
        finales = [i for i, par in enumerate(pantallas) if par == ("juego", True)]
        assert nombres[-1] == "derrota" and finales and nombres[finales[-1] + 1] == "derrota", nombres[-5:]   # (QUIT: un cuadro más)
        assert nombres.count("derrota") == len(nombres) - finales[-1] - 1                                 # y ninguna derrota antes
        assert 40 <= len(finales) <= 50, len(finales)                                 # ~1500 ms a 33 ms por cuadro
        assert vista._superficie is None                                              # y la ventana se cerró


def probar_una_partida_completa_dentro_del_bucle_real_con_animaciones_y_clics_que_aciertan():
    import test_main
    reloj = RelojQueAvanza()
    vista = VistaPygame(animaciones=True, reloj=reloj)
    with Recorrido(vista) as recorrido:
        guion = test_main.Guion(recorrido)
        recorrido.controlador.ejecutar(guion)
        assert recorrido.controlador._activo is False and guion.termino is False
        assert reloj.ahora > 300                                                          # el reloj avanzó de verdad (en cada cuadro)


if __name__ == "__main__":
    probar_fotograma_da_un_bucle_a_los_fps_pedidos_y_aguanta_los_casos_de_borde()
    probar_bamboleo_es_periodico_acotado_a_2_px_y_con_otra_fase_en_cada_posicion()
    probar_el_alfa_del_aura_respira_y_con_el_raton_encima_es_siempre_mas_claro()
    probar_el_parpadeo_es_pequeno_irregular_y_periodico()
    probar_progreso_antes_durante_despues_y_con_duracion_cero()
    probar_las_tablas_y_las_duraciones_viven_en_componentes_como_listas()
    probar_sin_animaciones_la_salida_es_la_de_siempre_y_no_cambia_con_el_tiempo()
    probar_con_animaciones_la_escena_cambia_con_el_tiempo_y_es_la_misma_con_el_mismo_reloj()
    probar_las_zonas_son_exactamente_las_mismas_con_y_sin_animaciones_en_cualquier_instante()
    probar_el_protagonista_usa_sus_tres_fotogramas_de_reposo_a_3_fps_y_el_vaiven_mueve_solo_el_dibujo()
    probar_el_aura_respira_con_el_alfa_de_la_tabla_y_brilla_mas_en_el_objeto_bajo_el_raton()
    probar_el_fundido_de_sala_empieza_opaco_termina_transparente_y_nunca_tapa_el_hud()
    probar_el_fundido_de_sala_vuelve_a_empezar_al_cambiar_de_sala_y_no_al_seguir_en_ella()
    probar_el_fundido_de_pantalla_de_menu_dura_180_ms_cubre_todo_y_no_se_repite_en_la_misma_pantalla()
    probar_la_pausa_dibuja_la_escena_congelada_y_sin_fundido()
    probar_el_parpadeo_es_una_sola_capa_oscura_de_a_lo_sumo_16_de_alfa_y_no_recalcula_el_fondo()
    probar_la_cache_de_sprites_no_crece_ni_por_cuadro_ni_por_instancia()
    probar_fotograma_unico_se_reproduce_una_vez_y_se_queda_en_el_ultimo()
    probar_en_la_derrota_el_protagonista_cae_con_sus_tres_fotogramas_de_muerte_y_se_queda_en_el_ultimo()
    probar_con_victoria_el_protagonista_no_muere_y_sin_animaciones_tampoco_cae()
    probar_la_muerte_no_cambia_las_zonas_de_clic_y_la_barra_queda_en_cero()
    probar_una_partida_perdida_con_demora_muestra_la_escena_final_y_luego_la_derrota()
    probar_una_partida_completa_dentro_del_bucle_real_con_animaciones_y_clics_que_aciertan()
    print("OK: todas las pruebas de las animaciones pasaron")
