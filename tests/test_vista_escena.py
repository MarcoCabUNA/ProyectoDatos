"""
Pruebas de la escena de juego (View/EscenaJuego.py) con la Vista REAL: fondo por rol, marcos sin salida, puertas, tamaños,
posición del protagonista, reparto de enemigos y objetos, aura, nombre al pasar el ratón y la pausa con la escena detrás.

Las de punta a punta hacen clic donde la FUNCIÓN PURA de reparto (repartir_escena) dice que está cada enemigo u objeto, o
según la posición visual (el que se ve arriba, a la derecha...), nunca según el índice que la Vista registró: así una
Vista que le ponga a un elemento el índice de otro no se compensa a sí misma. Se ejecuta desde cualquier carpeta.
"""
import sys
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import clic, movimiento, pygame  # noqa: E402  (fija SDL_VIDEODRIVER=dummy antes de importar pygame)
from ayudas_vista import (ARRIBA, ENTER, ESC, Recorrido, cerrada, con_enemigos, con_objetos,  # noqa: E402
                          estado_base)

import View.Componentes as c  # noqa: E402
import View.EscenaJuego as escena  # noqa: E402
from DTO.Direcciones import E, N, O, S  # noqa: E402
from DTO.ElementoDTO import (ELEMENTO_BOTON, ELEMENTO_ENEMIGO, ELEMENTO_OBJETO_SUELO, ELEMENTO_PUERTA,  # noqa: E402
                             ElementoDTO)
from DTO.PantallaDTO import PantallaDTO  # noqa: E402
from DTO.SalaDTO import SalidaDTO  # noqa: E402
from UIController.ControlesJuego import ControlesJuego  # noqa: E402
from View.Componentes import ALTO, ANCHO, Fuentes, barra_de_vida  # noqa: E402
from View.EscenaJuego import (FONDO_FINAL, FONDO_INICIAL, FONDO_REGULAR, colocar, direcciones_sin_salida,  # noqa: E402
                              fondo_para, marcos_de, orden_de_dibujo, posicion_del_protagonista, puertas_a_dibujar,
                              repartir_escena, trapecio)
from View.VistaPygame import VistaPygame  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
PANTALLA = pygame.Rect(0, 0, ANCHO, ALTO)
AYUDA_PAUSA = ["Esc: volver a la partida"]
CON_LAS_4_SALIDAS = dict(N=SalidaDTO(1), S=SalidaDTO(1), E=SalidaDTO(1), O=SalidaDTO(1))
PIES_A_PROBAR = [c.PIES_CENTRO] + list(c.PIES_PUERTA)


class SuperficieQueAnota(pygame.Surface):
    """Una superficie normal que además apunta cada blit (la imagen y dónde se puso): así se mide lo que de verdad se dibuja."""

    def __init__(self, tamano):
        super().__init__(tamano)
        self.blits = []

    def blit(self, fuente, destino, area=None, special_flags=0):
        self.blits.append((fuente, fuente.get_rect(topleft=tuple(destino)[:2])))
        return super().blit(fuente, destino, area, special_flags)


class VistaAbierta:
    def __enter__(self):
        self.vista = VistaPygame()
        self.vista.abrir()
        return self.vista

    def __exit__(self, *_):
        self.vista.cerrar()


class Observador:
    """Dibuja la escena sobre una SuperficieQueAnota y recuerda qué sprites de actor pidió al almacén, para medir los que
    realmente se dibujaron (los que se pidieron al probar tamaños y no cupieron no se dibujan)."""

    def __init__(self, vista):
        self.vista = vista
        self.lienzo = SuperficieQueAnota((ANCHO, ALTO))
        self._pedidos = []
        almacen = vista._escena._almacen
        original = almacen.actor_a_altura

        def con_registro(tipo, alto, estado="idle", nombre=""):
            conjunto = original(tipo, alto, estado, nombre)
            self._pedidos.append((tipo, conjunto))
            return conjunto
        almacen.actor_a_altura = con_registro

    def dibujar(self, estado, objetivo=None, bajo_el_raton=None):
        self.lienzo.blits.clear()
        self.vista._zonas.limpiar()
        self.vista._escena.dibujar(self.lienzo, estado, objetivo, True, bajo_el_raton)

    def dibujados(self, tipo):
        """(superficie, rectángulo) de cada sprite dibujado de ese 'tipo' de actor (en el orden en que se dibujó)."""
        resultado = []
        for fuente, rectangulo in self.lienzo.blits:
            if any(t == tipo and conjunto.fotogramas[0] is fuente for t, conjunto in self._pedidos):
                resultado.append((fuente, rectangulo))
        return resultado


def _juego(estado, objetivo=None, bajo_el_raton=None):
    return PantallaDTO("juego", "", [], 0, estado=estado, objetivo=objetivo,       # sin botón: aquí solo se prueba la escena
                       elemento_bajo_el_raton=bajo_el_raton)


def _zonas(vista, tipo=None):
    todas = list(zip(vista._zonas._rectangulos, vista._zonas._elementos))
    return todas if tipo is None else [(r, e) for r, e in todas if e.tipo == tipo]


def _de_izquierda_a_derecha(zonas, clave_fila=lambda r: 0):
    return sorted(zonas, key=lambda zona: (clave_fila(zona[0]), zona[0].left))


def _imagen(superficie=None):
    return pygame.image.tobytes(superficie or pygame.display.get_surface(), "RGB")


def _imagen_de(vista, pantalla):
    vista.dibujar(pantalla)
    return _imagen()


def _fondo_original(nombre):
    imagen = pygame.image.load(str(RAIZ / "assets" / "fondos" / f"{nombre}.jpg")).convert()
    return pygame.transform.smoothscale(imagen, (ANCHO, ALTO))


@contextmanager
def sin_ambiente():
    """Con la ambientación en 0 el fondo de sala es idéntico al JPG original: así se comparan los fondos píxel a píxel."""
    antes = c.AMBIENTE_INTENSIDAD
    c.AMBIENTE_INTENSIDAD = 0
    try:
        yield
    finally:
        c.AMBIENTE_INTENSIDAD = antes


def _luminosidad(superficie):
    return sum(pygame.transform.average_color(superficie)[:3]) / 3


def _rectangulo_del_cambio(a, b):
    """El rectángulo mínimo que contiene todo lo que cambia entre las superficies a y b (None si son iguales)."""
    ab, ba = a.copy(), b.copy()
    ab.blit(b, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
    ba.blit(a, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
    ab.blit(ba, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    ab.set_colorkey((0, 0, 0))
    rectangulo = ab.get_bounding_rect()
    return rectangulo if rectangulo.width and rectangulo.height else None


def _reparto_de(vista, estado, pies):
    """El reparto según la función pura, calculado aparte de la Vista (con su almacén y sus fuentes, solo para medir)."""
    return repartir_escena(vista._escena._almacen, vista._escena._fuentes, estado.enemigos, estado.objetos_suelo,
                           estado.sala.salidas, pies)


def _poner_pies(vista, pies, id_sala=3):
    """Hace que la Vista crea que el protagonista pisa en 'pies' en la sala 'id_sala' (como si ya hubiera entrado)."""
    vista._escena._pies, vista._escena._id_visto = pies, id_sala


class BackendQueAnota:
    """Lo mínimo del ControladorBackend para ControlesJuego: anota cada acción y devuelve el mismo estado."""

    def __init__(self, estado):
        self.estado = estado
        self.llamadas = []

    def abrir(self, direccion):
        self.llamadas.append(("abrir", direccion))
        return self.estado

    def atacar(self, id_enemigo):
        self.llamadas.append(("atacar", id_enemigo))
        return self.estado

    def recoger(self, id_objeto):
        self.llamadas.append(("recoger", id_objeto))
        return self.estado


class JuegoArmado:
    """La Vista real + los ControlesJuego reales con un estado armado a mano. clic_en(punto) hace un clic real."""

    def __init__(self, vista, estado):
        self.vista = vista
        self.backend = BackendQueAnota(estado)
        self.controles = ControlesJuego(self.backend, estado, lambda: 0, lambda: 0)
        self.estado = estado

    def dibujar(self):
        self.vista.dibujar(_juego(self.estado, self.controles.objetivo()))

    def clic_en(self, punto):
        self.controles.procesar_evento(clic(punto), self.vista.elemento_en(punto))


# ================================================================ decisiones puras
def probar_fondo_para_elige_por_el_rol_de_la_sala():
    base = estado_base()
    assert fondo_para(replace(base, sala=replace(base.sala, id=1))) == FONDO_INICIAL
    assert fondo_para(replace(base, sala=replace(base.sala, id=6))) == FONDO_FINAL
    assert fondo_para(replace(base, sala=replace(base.sala, id=3))) == FONDO_REGULAR
    assert fondo_para(replace(base, sala=replace(base.sala, id=3), sala_inicial=None, sala_salida=None)) == FONDO_REGULAR
    assert fondo_para(replace(base, sala_salida=None)) == FONDO_REGULAR
    assert fondo_para(replace(base, sala_inicial=None, sala_salida=3)) == FONDO_FINAL
    coinciden = replace(base, sala_inicial=3, sala_salida=3)                    # inicial y salida son la misma sala
    assert fondo_para(coinciden) == FONDO_INICIAL
    assert fondo_para(replace(coinciden, sala=replace(coinciden.sala, id=4))) == FONDO_REGULAR


def probar_puertas_a_dibujar_solo_las_cerradas_y_la_final_aparte():
    assert puertas_a_dibujar(estado_base()) == []                                 # sin salidas
    abiertas = estado_base(N=SalidaDTO(2), S=SalidaDTO(6), E=SalidaDTO(4), O=SalidaDTO(5))
    assert puertas_a_dibujar(abiertas) == []                                      # abiertas (aunque lleven a la salida)
    mezcla = estado_base(N=cerrada(2), S=SalidaDTO(4), E=cerrada(6), O=cerrada(5))
    assert puertas_a_dibujar(mezcla) == [(N, "puerta_cerrada"), (E, "puerta_final"), (O, "puerta_cerrada")]
    todas = estado_base(N=cerrada(6), S=cerrada(6), E=cerrada(6), O=cerrada(6))
    assert puertas_a_dibujar(todas) == [(d, "puerta_final") for d in (N, S, E, O)]   # la regla no cambia
    sin_salida_conocida = replace(mezcla, sala_salida=None)
    assert all(nombre == "puerta_cerrada" for _, nombre in puertas_a_dibujar(sin_salida_conocida))
    coinciden = replace(estado_base(E=cerrada(3)), sala_inicial=3, sala_salida=3)
    assert puertas_a_dibujar(coinciden) == [(E, "puerta_final")]                  # con inicial == salida, sigue igual


def probar_una_sola_puerta_dorada_y_las_demas_con_cadena():
    estado = estado_base(3, N=cerrada(6), S=cerrada(99), E=cerrada(98), O=cerrada(97))
    assert puertas_a_dibujar(estado) == [(N, "puerta_final"), (S, "puerta_cerrada"), (E, "puerta_cerrada"),
                                         (O, "puerta_cerrada")]


def probar_direcciones_sin_salida():
    assert direcciones_sin_salida(estado_base()) == [N, S, E, O]
    assert direcciones_sin_salida(estado_base(N=SalidaDTO(2), E=cerrada())) == [S, O]
    assert direcciones_sin_salida(estado_base(**CON_LAS_4_SALIDAS)) == []


def probar_el_trapecio_del_hueco_esta_dentro_de_su_marco_y_mira_hacia_la_pared():
    for fondo in c.FONDOS_CONOCIDOS:
        for direccion, marco in enumerate(marcos_de(fondo)):
            puntos = trapecio(marco, direccion)
            assert all(marco.collidepoint(p) for p in puntos), (fondo, direccion)
            xs, ys = [p[0] for p in puntos], [p[1] for p in puntos]
            ancho_en = lambda y: max(x for x, yy in puntos if yy == y) - min(x for x, yy in puntos if yy == y)
            alto_en = lambda x: max(y for xx, y in puntos if xx == x) - min(y for xx, y in puntos if xx == x)
            if direccion in (N, S):
                pared, sala = (min(ys), max(ys)) if direccion == N else (max(ys), min(ys))
                assert ancho_en(pared) > ancho_en(sala)                           # ancho junto a la pared
            else:
                pared, sala = (max(xs), min(xs)) if direccion == E else (min(xs), max(xs))
                assert alto_en(pared) > alto_en(sala)
    assert marcos_de(FONDO_INICIAL)[E].centerx > ANCHO // 2 > marcos_de(FONDO_INICIAL)[O].centerx
    assert marcos_de(FONDO_INICIAL)[N].centery < ALTO // 2 < marcos_de(FONDO_INICIAL)[S].centery


def probar_posicion_del_protagonista_sin_sala_anterior_es_el_centro():
    assert posicion_del_protagonista(estado_base().sala.salidas, None) == c.PIES_CENTRO
    assert posicion_del_protagonista(estado_base(**CON_LAS_4_SALIDAS).sala.salidas, None) == c.PIES_CENTRO
    assert c.SUELO.collidepoint(c.PIES_CENTRO) and abs(c.PIES_CENTRO[0] - c.SUELO.centerx) <= 2


def probar_posicion_del_protagonista_delante_de_la_puerta_por_la_que_entro():
    for nombre, direccion in (("N", N), ("S", S), ("E", E), ("O", O)):
        otra = "S" if nombre != "S" else "N"
        salidas = estado_base(**{nombre: SalidaDTO(7), otra: SalidaDTO(8)}).sala.salidas
        pies = posicion_del_protagonista(salidas, 7)
        assert pies == c.PIES_PUERTA[direccion], (nombre, pies)
        assert c.SUELO.collidepoint(pies)
    lugares = [posicion_del_protagonista(estado_base(**{n: SalidaDTO(7)}).sala.salidas, 7) for n in "NSEO"]
    assert lugares[0][1] < c.PIES_CENTRO[1] < lugares[1][1] and lugares[3][0] < c.PIES_CENTRO[0] < lugares[2][0]
    cerrada_hacia_la_anterior = estado_base(E=cerrada(7)).sala.salidas
    assert posicion_del_protagonista(cerrada_hacia_la_anterior, 7) == c.PIES_PUERTA[E]


def probar_posicion_del_protagonista_al_centro_si_no_se_sabe_por_donde_entro():
    salidas = estado_base(N=SalidaDTO(7), S=SalidaDTO(8)).sala.salidas
    assert posicion_del_protagonista(salidas, 99) == c.PIES_CENTRO                 # la anterior no es contigua
    dos_hacia_la_anterior = estado_base(N=SalidaDTO(7), E=SalidaDTO(7)).sala.salidas
    assert posicion_del_protagonista(dos_hacia_la_anterior, 7) == c.PIES_CENTRO    # hay varias: no se puede decidir
    assert posicion_del_protagonista(estado_base().sala.salidas, 7) == c.PIES_CENTRO    # sin salidas


def probar_colocar_es_determinista_no_solapa_cabe_en_el_suelo_y_respeta_lo_ocupado():
    ocupadas = [pygame.Rect(600, 300, 120, 130), c.PASILLOS[N]]
    for cantidad in (0, 1, 2, 6, 12):
        tamanos = [(60 + 3 * i, 60 + 3 * i) for i in range(cantidad)]
        primero, caben = colocar(tamanos, ocupadas, c.SUELO, c.PIES_CENTRO, 230, 12, 8)
        segundo, _ = colocar(tamanos, ocupadas, c.SUELO, c.PIES_CENTRO, 230, 12, 8)
        assert primero == segundo and caben, cantidad                             # nada de azar
        assert [r.size for r in primero] == tamanos
        for i, r in enumerate(primero):
            assert c.SUELO.contains(r), (cantidad, i)
            assert r.collidelist(ocupadas) == -1, (cantidad, i)
            assert all(not r.colliderect(otro) for otro in primero[i + 1:]), (cantidad, i)
    rectangulos, caben = colocar([(50, 50), (50, 50)], [c.SUELO], c.SUELO, c.PIES_CENTRO, 230, 12, 8)
    assert not caben and len(rectangulos) == 2 and all(c.SUELO.contains(r) for r in rectangulos)   # no falla: avisa
    rectangulos, caben = colocar([(5000, 50)], [], c.SUELO, c.PIES_CENTRO, 230, 12, 8)
    assert not caben and len(rectangulos) == 1                                    # algo que no cabe nunca


def probar_colocar_reparte_alrededor_de_los_pies_dados():
    cerca, _ = colocar([(60, 60)], [], c.SUELO, c.PIES_CENTRO, 100, 12, 8)
    lejos, _ = colocar([(60, 60)], [], c.SUELO, c.PIES_CENTRO, 300, 12, 8)
    distancia = lambda r: ((r.centerx - c.PIES_CENTRO[0]) ** 2 + (r.bottom - c.PIES_CENTRO[1]) ** 2) ** 0.5
    assert abs(distancia(cerca[0]) - 100) < 20 and abs(distancia(lejos[0]) - 300) < 20
    a_la_izquierda, _ = colocar([(60, 60)], [], c.SUELO, c.PIES_PUERTA[O], 150, 12, 8)
    a_la_derecha, _ = colocar([(60, 60)], [], c.SUELO, c.PIES_PUERTA[E], 150, 12, 8)
    assert a_la_izquierda[0].centerx < c.SUELO.centerx < a_la_derecha[0].centerx


def probar_orden_de_dibujo_el_de_mas_abajo_va_encima_y_los_empates_por_indice():
    assert orden_de_dibujo([]) == []
    assert orden_de_dibujo([300, 100, 200]) == [1, 2, 0]
    assert orden_de_dibujo([100, 100, 50]) == [2, 0, 1]
    pies = [431, 12, 600, 431, 77, 300, 300, 1]
    orden = orden_de_dibujo(pies)
    assert sorted(orden) == list(range(len(pies)))
    assert [pies[i] for i in orden] == sorted(pies)


# ================================================================ el reparto (función pura repartir_escena)
def probar_el_reparto_cumple_todo_de_1_a_12_con_el_protagonista_en_el_centro_o_junto_a_cada_puerta():
    combinaciones = [(1, 1), (2, 3), (6, 6), (12, 1), (1, 12), (12, 12)]
    with VistaAbierta() as vista:
        for pies in PIES_A_PROBAR:
            jugador = pygame.Rect((0, 0), c.JUGADOR_OCUPA)
            jugador.midbottom = pies
            for enemigos, objetos in combinaciones:
                estado = con_objetos(con_enemigos(estado_base(3, **CON_LAS_4_SALIDAS), enemigos), objetos)
                reparto = _reparto_de(vista, estado, pies)
                assert len(reparto.enemigos) == enemigos and len(reparto.objetos) == objetos
                zonas = reparto.enemigos + reparto.objetos
                for i, zona in enumerate(zonas):
                    assert c.SUELO.contains(zona), (pies, enemigos, objetos, i)           # todo dentro del suelo
                    assert not zona.colliderect(jugador), (pies, enemigos, objetos, i)   # el protagonista, libre
                    assert zona.collidelist(c.PASILLOS) == -1, (pies, enemigos, objetos, i)    # las puertas, libres
                    assert all(not zona.colliderect(otra) for otra in zonas[i + 1:]), (pies, enemigos, objetos, i)
                assert reparto == _reparto_de(vista, estado, pies)                       # determinista


def probar_el_reparto_no_tapa_el_protagonista_en_todo_el_rango_de_1_a_12_enemigos_y_objetos():
    with VistaAbierta() as vista:
        for pies in (c.PIES_CENTRO, c.PIES_PUERTA[N], c.PIES_PUERTA[O]):
            jugador = pygame.Rect((0, 0), c.JUGADOR_OCUPA)
            jugador.midbottom = pies
            for enemigos in range(1, 13):
                for objetos in (1, 12):
                    estado = con_objetos(con_enemigos(estado_base(3, **CON_LAS_4_SALIDAS), enemigos), objetos)
                    reparto = _reparto_de(vista, estado, pies)
                    zonas = reparto.enemigos + reparto.objetos
                    assert all(not z.colliderect(jugador) and c.SUELO.contains(z) for z in zonas), (pies, enemigos, objetos)
                    assert all(not zonas[i].colliderect(zonas[j]) for i in range(len(zonas))
                               for j in range(i + 1, len(zonas))), (pies, enemigos, objetos)


def probar_los_enemigos_se_achican_todos_con_el_mismo_factor_y_el_protagonista_no():
    with VistaAbierta() as vista:
        observador = Observador(vista)
        alturas = {}
        for cantidad in (1, 2, 6, 12):
            observador.dibujar(con_enemigos(estado_base(3), cantidad))
            ratas = [s.get_height() for s, _ in observador.dibujados("ent_rata_gigante")]
            guardianes = [s.get_height() for s, _ in observador.dibujados("ent_guardian_oseo")]
            jugador = [s.get_height() for s, _ in observador.dibujados("jugador")]
            assert jugador == [c.ALTURA_JUGADOR], (cantidad, jugador)                     # el protagonista no cambia
            assert len(set(ratas)) == 1, (cantidad, ratas)                                # todas las ratas, igual
            if guardianes:
                assert len(set(guardianes)) == 1
                assert abs(guardianes[0] / ratas[0] - c.FACTOR_RESPALDO) < 0.04, (cantidad, ratas, guardianes)
            alturas[cantidad] = ratas[0]
        assert alturas[1] > alturas[6] > alturas[12], alturas                             # más enemigos, más chicos


# ================================================================ tamaños (medidos sobre lo que se dibuja)
def probar_tamanos_propios_mayor_o_igual_que_generico_y_este_mayor_que_el_jugador():
    assert c.ALTURA_JUGADOR == 90                                                         # lo fija la especificación
    with VistaAbierta() as vista:
        observador = Observador(vista)
        observador.dibujar(con_enemigos(estado_base(3), 3))                              # rata, rata, guardián (respaldo)
        rata = [s for s, _ in observador.dibujados("ent_rata_gigante")]
        guardian = [s for s, _ in observador.dibujados("ent_guardian_oseo")]
        jugador = [s for s, _ in observador.dibujados("jugador")]
        assert len(rata) == 2 and len(guardian) == 1 and len(jugador) == 1
        propio, generico, protagonista = rata[0].get_height(), guardian[0].get_height(), jugador[0].get_height()
        assert protagonista == c.ALTURA_JUGADOR == 90
        assert abs(propio - c.ALTURA_ENEMIGO) <= 1                                       # su altura actual, sin cambiarla
        assert abs(generico - round(c.ALTURA_ENEMIGO * c.FACTOR_RESPALDO)) <= 1          # el 85 %
        assert propio >= generico > protagonista, (propio, generico, protagonista)
        sin_sprites = replace(con_enemigos(estado_base(3), 3).enemigos[2], tipo="no-existe-ningun-sprite")
        observador.dibujar(replace(estado_base(3), enemigos=[sin_sprites]))              # sin sprites: también es respaldo
        assert abs(observador.dibujados("no-existe-ningun-sprite")[0][0].get_height() - generico) <= 1


def probar_el_jugador_mide_lo_mismo_en_todas_las_escenas():
    with VistaAbierta() as vista:
        observador = Observador(vista)
        medidas = set()
        for estado in (estado_base(1), estado_base(3, **CON_LAS_4_SALIDAS), estado_base(6),
                       con_objetos(con_enemigos(estado_base(3), 12), 12)):
            observador.dibujar(estado)
            medidas.add(observador.dibujados("jugador")[0][0].get_height())
        assert medidas == {c.ALTURA_JUGADOR}


def probar_los_pies_de_cada_enemigo_apoyan_en_la_base_de_su_zona():
    with VistaAbierta() as vista:
        observador = Observador(vista)
        for cantidad in (1, 3, 6, 12):
            observador.dibujar(con_enemigos(estado_base(3), cantidad))
            zonas = [r for r, _ in _zonas(vista, ELEMENTO_ENEMIGO)]
            dibujados = observador.dibujados("ent_rata_gigante") + observador.dibujados("ent_guardian_oseo")
            assert len(dibujados) == len(zonas) == cantidad
            pies_dibujados = [rectangulo.midbottom for _, rectangulo in dibujados]
            for zona in zonas:
                assert pies_dibujados.count(zona.midbottom) == 1, (cantidad, zona)       # cada zona, un sprite sobre su base


# ================================================================ posición del protagonista en la Vista
def _pies_del_jugador(observador):
    (sprite, rectangulo), = observador.dibujados("jugador")
    return rectangulo.midbottom


def probar_el_protagonista_empieza_en_el_centro_y_entra_delante_de_la_puerta_correcta():
    with VistaAbierta() as vista:
        observador = Observador(vista)
        for nombre, direccion in (("N", N), ("S", S), ("E", E), ("O", O)):
            vista._escena.olvidar_la_sala()
            observador.dibujar(estado_base(10))                                       # sala anterior
            assert _pies_del_jugador(observador) == c.PIES_CENTRO
            nueva = estado_base(11, **{nombre: SalidaDTO(10)})
            for cuadro in range(4):                                                    # y se mantiene cuadro tras cuadro
                observador.dibujar(nueva)
                pies = _pies_del_jugador(observador)
                assert pies == c.PIES_PUERTA[direccion], (nombre, cuadro)
                lado = {N: pies[1] < c.SUELO.centery - 40, S: pies[1] > c.SUELO.centery + 90,        # y se VE de ese lado
                        E: pies[0] > c.SUELO.centerx + 200, O: pies[0] < c.SUELO.centerx - 200}[direccion]
                assert lado, (nombre, pies)


def probar_el_protagonista_va_al_centro_si_la_sala_anterior_no_es_contigua():
    with VistaAbierta() as vista:
        observador = Observador(vista)
        observador.dibujar(estado_base(10))
        observador.dibujar(estado_base(11, N=SalidaDTO(99), S=SalidaDTO(98)))
        assert _pies_del_jugador(observador) == c.PIES_CENTRO


def probar_el_protagonista_olvida_la_sala_anterior_al_pasar_por_el_menu_y_otras_pantallas():
    with VistaAbierta() as vista:
        observador = Observador(vista)
        entrada = estado_base(11, E=SalidaDTO(10))
        for pantalla in ("menu", "criptas", "nombre", "victoria", "derrota", "puntajes"):
            observador.dibujar(estado_base(10))
            vista.dibujar(PantallaDTO(pantalla, "x", ["a", "b", "c"], 0, texto="", puntaje=None, reporte=None,
                                      puntajes=[], criterio="enemigos"))
            observador.dibujar(entrada)
            assert _pies_del_jugador(observador) == c.PIES_CENTRO, pantalla          # olvidó: no hay "sala anterior"
        observador.dibujar(estado_base(10))
        observador.dibujar(entrada)
        assert _pies_del_jugador(observador) == c.PIES_PUERTA[E]                       # sin pasar por el menú, sí


def probar_la_pausa_no_hace_olvidar_la_sala_y_volver_a_la_inicial_deja_delante_de_la_puerta():
    with VistaAbierta() as vista:
        observador = Observador(vista)
        observador.dibujar(estado_base(1, N=SalidaDTO(2)))                              # sala inicial
        dos = estado_base(2, S=SalidaDTO(1), N=SalidaDTO(3))
        observador.dibujar(dos)
        assert _pies_del_jugador(observador) == c.PIES_PUERTA[S]
        vista.dibujar(PantallaDTO("pausa", "Pausa", ["Continuar"], 0, estado=dos))
        observador.dibujar(dos)
        assert _pies_del_jugador(observador) == c.PIES_PUERTA[S]                       # la pausa no lo movió
        observador.dibujar(estado_base(1, N=SalidaDTO(2)))                              # vuelve a la inicial desde otra
        assert _pies_del_jugador(observador) == c.PIES_PUERTA[N]                       # delante de la puerta, no al centro


# ================================================================ el fondo y las puertas que se ven
def probar_cada_rol_de_sala_dibuja_su_fondo():
    with sin_ambiente():
        zona = pygame.Rect(300, 0, 100, 36)                                                # arriba, entre el HUD y la puerta
        with VistaAbierta() as vista:
            fondos = [_fondo_original(n) for n in ("fondo_inicial", "fondo_regular", "fondo_final")]
            for id_sala, esperado in ((1, 0), (3, 1), (6, 2)):
                vista.dibujar(_juego(estado_base(id_sala)))
                dibujado = pygame.image.tobytes(pygame.display.get_surface().subsurface(zona), "RGB")
                for i, fondo in enumerate(fondos):
                    coincide = pygame.image.tobytes(fondo.subsurface(zona), "RGB") == dibujado
                    assert coincide == (i == esperado), (id_sala, i)


def probar_el_texto_de_depuracion_ya_no_tapa_la_escena():
    with sin_ambiente():
        with VistaAbierta() as vista:
            vista.dibujar(_juego(estado_base(3)))
            franja = pygame.Rect(290, 0, 300, 40)                                          # (el HUD y el marco norte quedan fuera)
            assert (pygame.image.tobytes(pygame.display.get_surface().subsurface(franja), "RGB")
                    == pygame.image.tobytes(_fondo_original("fondo_regular").subsurface(franja), "RGB"))
            assert vista._zonas.cantidad() == 0                                            # sin elementos: ninguna zona


def probar_un_clic_sobre_el_marco_de_una_direccion_sin_salida_no_devuelve_zona():
    with VistaAbierta() as vista:
        for id_sala in (1, 3):                                                         # fondo inicial y fondo regular
            vista.dibujar(_juego(estado_base(id_sala, N=SalidaDTO(2))))
            marcos = marcos_de(FONDO_INICIAL if id_sala == 1 else FONDO_REGULAR)
            for direccion in (S, E, O):
                assert vista.elemento_en(marcos[direccion].center) is None, (id_sala, direccion)
            assert vista._zonas.cantidad() == 0


def probar_las_direcciones_sin_salida_se_oscurecen_y_las_abiertas_no():
    with sin_ambiente():
        with VistaAbierta() as vista:
            vista.dibujar(_juego(estado_base(3, **CON_LAS_4_SALIDAS)))
            fondo = _fondo_original("fondo_regular")
            for direccion in (N, S, E, O):
                marco = marcos_de(FONDO_REGULAR)[direccion]
                assert pygame.image.tobytes(pygame.display.get_surface().subsurface(marco), "RGB") == \
                    pygame.image.tobytes(fondo.subsurface(marco), "RGB"), direccion       # una salida abierta no se toca
            for direccion in (N, S, E, O):
                abiertas = {n: SalidaDTO(2) for n in "NSEO"}
                del abiertas["NSEO"[direccion]]
                vista.dibujar(_juego(estado_base(3, **abiertas)))
                dibujado = pygame.display.get_surface()
                for otra in (N, S, E, O):
                    marco = marcos_de(FONDO_REGULAR)[otra]
                    igual = (pygame.image.tobytes(dibujado.subsurface(marco), "RGB")
                             == pygame.image.tobytes(fondo.subsurface(marco), "RGB"))
                    assert igual == (otra != direccion), (direccion, otra)               # solo la que no tiene salida cambia


def probar_fondo_final_no_oscurece_nada_porque_no_tiene_marcos():
    with sin_ambiente():
        with VistaAbierta() as vista:
            vista.dibujar(_juego(estado_base(6)))
            sin_jugador = pygame.Rect(380, 640, 230, 120)                                 # bajo el jugador, sin HUD ni puerta
            assert (pygame.image.tobytes(pygame.display.get_surface().subsurface(sin_jugador), "RGB")
                    == pygame.image.tobytes(_fondo_original("fondo_final").subsurface(sin_jugador), "RGB"))

# ================================================================ la ambientación lúgubre de los fondos de sala
@contextmanager
def _almacen_aparte():
    """Un almacén nuevo (caché vacía) con la ventana abierta, que hace falta para cargar imágenes."""
    from View.AlmacenSprites import AlmacenSprites
    with VistaAbierta():
        yield AlmacenSprites(str(RAIZ / "assets"))


def probar_con_la_ambientacion_en_cero_el_fondo_de_sala_es_el_mismo_conjunto_que_el_original():
    with _almacen_aparte() as almacen:
        for nombre in ("fondo_inicial", "fondo_regular", "fondo_final"):
            assert almacen.fondo_ambientado(nombre, (ANCHO, ALTO), 0) is almacen.fondo(nombre, (ANCHO, ALTO))
            assert almacen.fondo_ambientado(nombre, (ANCHO, ALTO), -3) is almacen.fondo(nombre, (ANCHO, ALTO))   # se acota a 0


def probar_con_la_intensidad_por_omision_el_fondo_de_sala_es_mas_oscuro_pero_no_negro():
    assert c.AMBIENTE_INTENSIDAD == 0.5                                                  # el valor por omisión
    with _almacen_aparte() as almacen:
        for nombre in ("fondo_inicial", "fondo_regular", "fondo_final"):
            original = _luminosidad(almacen.fondo(nombre, (ANCHO, ALTO)).fotogramas[0])
            ambientado = almacen.fondo_ambientado(nombre, (ANCHO, ALTO), c.AMBIENTE_INTENSIDAD).fotogramas[0]
            relacion = _luminosidad(ambientado) / original
            assert 0.55 <= relacion <= 0.85, (nombre, relacion)                              # más oscuro, pero no negro
            assert ambientado.get_size() == (ANCHO, ALTO)
            assert _luminosidad(ambientado) > 20, nombre


def probar_a_mayor_intensidad_mas_oscuro_y_los_bordes_mas_que_el_centro():
    with _almacen_aparte() as almacen:
        previa = 1e9
        for intensidad in (0, 0.25, 0.5, 0.75, 1.0):
            fondo = almacen.fondo_ambientado("fondo_regular", (ANCHO, ALTO), intensidad).fotogramas[0]
            assert _luminosidad(fondo) < previa or intensidad == 0
            previa = _luminosidad(fondo)
        original = almacen.fondo("fondo_regular", (ANCHO, ALTO)).fotogramas[0]
        ambientado = almacen.fondo_ambientado("fondo_regular", (ANCHO, ALTO), 1.0).fotogramas[0]
        esquina, centro = pygame.Rect(0, 0, 200, 120), pygame.Rect(ANCHO // 2 - 100, ALTO // 2 - 60, 200, 120)
        assert (_luminosidad(ambientado.subsurface(esquina)) / _luminosidad(original.subsurface(esquina))
                < _luminosidad(ambientado.subsurface(centro)) / _luminosidad(original.subsurface(centro)))   # la viñeta


def probar_el_fondo_ambientado_se_calcula_una_sola_vez_y_se_guarda_en_la_cache():
    with _almacen_aparte() as almacen:
        primero = almacen.fondo_ambientado("fondo_inicial", (ANCHO, ALTO), 0.5)
        entradas, accesos = almacen.entradas_cache, almacen.accesos_disco
        for _ in range(5):
            assert almacen.fondo_ambientado("fondo_inicial", (ANCHO, ALTO), 0.5) is primero
        assert almacen.entradas_cache == entradas and almacen.accesos_disco == accesos
        assert almacen.fondo_ambientado("fondo_inicial", (ANCHO, ALTO), 0.4) is not primero   # otra intensidad: otro resultado
        with VistaAbierta() as vista:
            for _ in range(3):
                vista.dibujar(_juego(estado_base(1)))
            guardadas = vista._escena._almacen.entradas_cache
            for _ in range(10):
                vista.dibujar(_juego(estado_base(1)))
            assert vista._escena._almacen.entradas_cache == guardadas                          # dibujar no crea nada nuevo


def probar_dibujar_con_ambiente_no_cuesta_apreciablemente_mas_que_sin_el():
    import time

    def medir(intensidad):
        antes = c.AMBIENTE_INTENSIDAD
        c.AMBIENTE_INTENSIDAD = intensidad
        try:
            with VistaAbierta() as vista:
                pantalla = _juego(estado_base(3))
                vista.dibujar(pantalla)                                                    # el primero calcula y guarda
                inicio = time.perf_counter()
                for _ in range(30):
                    vista.dibujar(pantalla)
                return (time.perf_counter() - inicio) / 30
        finally:
            c.AMBIENTE_INTENSIDAD = antes
    sin, con = medir(0), medir(c.AMBIENTE_INTENSIDAD)
    assert con < sin + 0.003, (sin, con)                                                   # a lo sumo 3 ms de diferencia

def probar_la_escena_dibuja_el_fondo_ambientado_con_la_intensidad_de_componentes():
    zona = pygame.Rect(300, 0, 100, 36)                                                # arriba, entre el HUD y la puerta
    with VistaAbierta() as vista:
        almacen = vista._escena._almacen
        for id_sala, nombre in ((1, "fondo_inicial"), (3, "fondo_regular"), (6, "fondo_final")):
            for intensidad in (c.AMBIENTE_INTENSIDAD, 0.9):
                antes, c.AMBIENTE_INTENSIDAD = c.AMBIENTE_INTENSIDAD, intensidad
                try:
                    vista.dibujar(_juego(estado_base(id_sala)))
                finally:
                    c.AMBIENTE_INTENSIDAD = antes
                esperado = almacen.fondo_ambientado(nombre, (ANCHO, ALTO), intensidad).fotogramas[0]
                original = almacen.fondo(nombre, (ANCHO, ALTO)).fotogramas[0]
                dibujado = pygame.image.tobytes(pygame.display.get_surface().subsurface(zona), "RGB")
                assert dibujado == pygame.image.tobytes(esperado.subsurface(zona), "RGB"), (nombre, intensidad)
                assert dibujado != pygame.image.tobytes(original.subsurface(zona), "RGB"), (nombre, intensidad)



def probar_menu_victoria_y_derrota_nunca_piden_el_fondo_ambientado():
    from DTO.PantallaDTO import PantallaDTO as P
    with VistaAbierta() as vista:
        almacen = vista._escena._almacen
        llamadas = []
        original = almacen.fondo_ambientado
        almacen.fondo_ambientado = lambda *a, **k: llamadas.append(a) or original(*a, **k)
        vista.dibujar(P("menu", "", ["Comenzar juego"], 0))
        assert llamadas == []
        vista.dibujar(_juego(estado_base(1)))
        assert len(llamadas) == 1                                                          # la escena de sala sí lo pide
        for nombre in ("fondo_menu", "fondo_victoria", "fondo_derrota"):                  # y fondo() sigue devolviendo el JPG
            assert pygame.image.tobytes(almacen.fondo(nombre, (ANCHO, ALTO)).fotogramas[0], "RGB") ==                 pygame.image.tobytes(_fondo_original(nombre), "RGB"), nombre


def probar_con_ambiente_los_marcos_abiertos_y_los_oscurecidos_se_distinguen_y_los_textos_se_leen():
    marco_n = marcos_de(FONDO_REGULAR)[N]
    with VistaAbierta() as vista:
        vista.dibujar(_juego(estado_base(3, N=SalidaDTO(2))))                              # el norte abierto; S, E y O no
        pantalla = pygame.display.get_surface()
        abierto = _luminosidad(pantalla.subsurface(marco_n))
        for direccion in (S, E, O):
            sin_salida = _luminosidad(pantalla.subsurface(marcos_de(FONDO_REGULAR)[direccion]))
            assert sin_salida < 0.5 * abierto, (direccion, sin_salida, abierto)            # se distinguen con claridad
        vista.dibujar(_juego(estado_base(3, N=SalidaDTO(2), S=SalidaDTO(2), E=SalidaDTO(2), O=SalidaDTO(2))))
        otro = pygame.display.get_surface()
        assert abs(_luminosidad(otro.subsurface(marco_n)) - abierto) < 1                   # y lo abierto es siempre igual
    # el texto y las barras se dibujan encima, con sus colores plenos (la ambientación solo toca el fondo)
    with VistaAbierta() as vista:
        observador = Observador(vista)
        observador.dibujar(estado_base(3))
        assert len(observador.dibujados("jugador")) == 1
        assert any(observador.lienzo.get_at((x, y))[:3] == c.VIDA_BUENA for x in range(ANCHO) for y in range(ALTO))



def probar_las_puertas_cerradas_se_registran_donde_se_ven_en_las_cuatro_direcciones():
    todas = estado_base(3, N=cerrada(), S=cerrada(), E=cerrada(), O=cerrada())
    with VistaAbierta() as vista:
        vista.dibujar(_juego(todas))
        puertas = _zonas(vista, ELEMENTO_PUERTA)
        assert len(puertas) == 4 and vista._zonas.cantidad() == 4
        por_altura = sorted(puertas, key=lambda z: z[0].centery)
        arriba, abajo = por_altura[0], por_altura[-1]
        izquierda, derecha = _de_izquierda_a_derecha(puertas)[0], _de_izquierda_a_derecha(puertas)[-1]
        assert arriba[1].indice == N and abajo[1].indice == S
        assert izquierda[1].indice == O and derecha[1].indice == E
        for rectangulo, elemento in puertas:
            assert PANTALLA.contains(rectangulo)
            assert vista.elemento_en(rectangulo.center) == elemento


def probar_la_puerta_que_lleva_a_la_salida_se_ve_distinta_de_una_cerrada_comun():
    with VistaAbierta() as vista:
        for nombre in ("N", "S", "E", "O"):
            vista.dibujar(_juego(estado_base(3, **{nombre: cerrada(5)})))
            comun = _imagen()
            vista.dibujar(_juego(estado_base(3, **{nombre: cerrada(6)})))
            cambio = _rectangulo_del_cambio(pygame.image.frombytes(comun, (ANCHO, ALTO), "RGB"),
                                            pygame.display.get_surface())
            (rectangulo, _), = _zonas(vista, ELEMENTO_PUERTA)
            assert cambio is not None and rectangulo.inflate(40, 40).contains(cambio), nombre
            final = vista._escena._almacen.puerta("puerta_final", "NSEO".index(nombre),
                                                  escena.escala_de_puerta("puerta_final"))
            assert final.origen == "ui/puerta_final" and rectangulo.size == final.fotogramas[0].get_size()


def _opacos(sprite, lado):
    """Cuántos píxeles opacos hay en la mitad del sprite que cae del lado 'lado' (N, S, E u O)."""
    ancho, alto = sprite.get_size()
    mitad = {N: pygame.Rect(0, 0, ancho, alto // 2), S: pygame.Rect(0, alto - alto // 2, ancho, alto // 2),
             O: pygame.Rect(0, 0, ancho // 2, alto), E: pygame.Rect(ancho - ancho // 2, 0, ancho // 2, alto)}[lado]
    return sum(1 for x in range(mitad.left, mitad.right) for y in range(mitad.top, mitad.bottom)
               if sprite.get_at((x, y)).a > 0)


def probar_cada_puerta_mira_hacia_su_pared():
    """Los sprites son para el norte: su lado ancho debe quedar contra la pared de su dirección."""
    with VistaAbierta() as vista:
        almacen = vista._escena._almacen
        for nombre in ("puerta_cerrada", "puerta_final"):
            for direccion in (N, S, E, O):
                sprite = almacen.puerta(nombre, direccion, escena.escala_de_puerta(nombre)).fotogramas[0]
                opuesta = {N: S, S: N, E: O, O: E}[direccion]
                assert _opacos(sprite, direccion) > _opacos(sprite, opuesta), (nombre, direccion)


# ================================================================ muchos elementos, solapes y orden
def probar_muchos_enemigos_y_objetos_se_registran_dentro_de_la_pantalla_y_son_clicables():
    with VistaAbierta() as vista:
        for enemigos in (0, 1, 2, 6, 12):
            for objetos in (0, 1, 6, 12):
                vista.dibujar(_juego(con_objetos(con_enemigos(estado_base(3), enemigos), objetos)))
                zonas = _zonas(vista)
                assert sorted(e.indice for _, e in _zonas(vista, ELEMENTO_ENEMIGO)) == list(range(enemigos))
                assert sorted(e.indice for _, e in _zonas(vista, ELEMENTO_OBJETO_SUELO)) == list(range(objetos))
                for i, (rectangulo, elemento) in enumerate(zonas):
                    assert PANTALLA.contains(rectangulo) and c.SUELO.contains(rectangulo), (enemigos, objetos, i)
                    assert all(not rectangulo.colliderect(otra) for otra, _ in zonas[i + 1:]), (enemigos, objetos, i)
                    for punto in (rectangulo.center, rectangulo.topleft, (rectangulo.right - 1, rectangulo.bottom - 1)):
                        assert vista.elemento_en(punto) == elemento, (enemigos, objetos, i)


def probar_las_zonas_estan_donde_dice_la_funcion_pura_de_reparto():
    with VistaAbierta() as vista:
        estado = con_objetos(con_enemigos(estado_base(3, **CON_LAS_4_SALIDAS), 5), 4)
        vista.dibujar(_juego(estado))
        reparto = _reparto_de(vista, estado, c.PIES_CENTRO)
        assert sorted((r.topleft, r.size, e.tipo, e.indice) for r, e in _zonas(vista, ELEMENTO_ENEMIGO)) == \
            sorted((r.topleft, r.size, ELEMENTO_ENEMIGO, i) for i, r in enumerate(reparto.enemigos))
        assert sorted((r.topleft, r.size, e.tipo, e.indice) for r, e in _zonas(vista, ELEMENTO_OBJETO_SUELO)) == \
            sorted((r.topleft, r.size, ELEMENTO_OBJETO_SUELO, i) for i, r in enumerate(reparto.objetos))


def probar_las_zonas_se_registran_en_el_orden_de_dibujo_de_abajo_hacia_arriba():
    with VistaAbierta() as vista:
        for pies in PIES_A_PROBAR:
            _poner_pies(vista, pies)
            vista.dibujar(_juego(con_objetos(con_enemigos(estado_base(3, **CON_LAS_4_SALIDAS), 9), 9)))
            movibles = [r for r, e in _zonas(vista) if e.tipo in (ELEMENTO_ENEMIGO, ELEMENTO_OBJETO_SUELO)]
            assert len(movibles) == 18
            assert [r.bottom for r in movibles] == sorted(r.bottom for r in movibles), pies   # el de abajo, el último


def _con_reparto_falso(enemigos, objetos):
    """Cambia colocar por uno que pone cada enemigo y cada objeto donde diga la prueba (para forzar solapes). Los
    lugares son los pies (x de la esquina izquierda, y del borde de abajo). Devuelve el colocar de verdad."""
    anterior = escena.colocar

    def falso(tamanos, ocupadas, suelo, pies, radio, paso, separacion):
        lugares = enemigos if radio == c.REPARTO_RADIO_ENEMIGOS else objetos
        return [pygame.Rect(x, y - alto, ancho, alto) for (ancho, alto), (x, y) in zip(tamanos, lugares)], True

    escena.colocar = falso
    return anterior


def probar_con_zonas_solapadas_gana_la_que_tiene_los_pies_mas_abajo_sea_enemigo_u_objeto():
    for pies_enemigo, pies_objeto, gana in ((520, 470, ELEMENTO_ENEMIGO), (470, 520, ELEMENTO_OBJETO_SUELO)):
        anterior = _con_reparto_falso([(500, pies_enemigo)], [(600, pies_objeto)])
        try:
            with VistaAbierta() as vista:
                vista.dibujar(_juego(con_objetos(con_enemigos(estado_base(3), 1), 1)))
                (r_enemigo, enemigo) = _zonas(vista, ELEMENTO_ENEMIGO)[0]
                (r_objeto, objeto) = _zonas(vista, ELEMENTO_OBJETO_SUELO)[0]
                comun = r_enemigo.clip(r_objeto)
                assert comun.width > 0 and comun.height > 0, "la prueba necesita zonas que se solapen"
                assert vista.elemento_en(comun.center) == (enemigo if gana == ELEMENTO_ENEMIGO else objeto), \
                    (pies_enemigo, pies_objeto)
                assert [e.tipo for _, e in _zonas(vista)][-1] == gana                 # lo último que se registró es lo de abajo
                solo_del_otro = next(p for p in ((x, y) for x in range(r_objeto.left, r_objeto.right)
                                                 for y in range(r_objeto.top, r_objeto.bottom))
                                     if not r_enemigo.collidepoint(p)) if gana == ELEMENTO_ENEMIGO else next(
                    p for p in ((x, y) for x in range(r_enemigo.left, r_enemigo.right)
                                for y in range(r_enemigo.top, r_enemigo.bottom)) if not r_objeto.collidepoint(p))
                assert vista.elemento_en(solo_del_otro) == (objeto if gana == ELEMENTO_ENEMIGO else enemigo)
        finally:
            escena.colocar = anterior


def probar_una_puerta_cerrada_y_un_enemigo_encima_la_zona_del_enemigo_gana():
    anterior = _con_reparto_falso([(1150, 460)], [])
    try:
        with VistaAbierta() as vista:
            vista.dibujar(_juego(con_enemigos(estado_base(3, E=cerrada()), 1)))
            (r_puerta, _), (r_enemigo, enemigo) = _zonas(vista, ELEMENTO_PUERTA)[0], _zonas(vista, ELEMENTO_ENEMIGO)[0]
            comun = r_puerta.clip(r_enemigo)
            assert comun.width > 0 and comun.height > 0
            assert vista.elemento_en(comun.center) == enemigo
    finally:
        escena.colocar = anterior


# ================================================================ clics de punta a punta (estados armados)
def probar_clic_en_cada_puerta_cerrada_abre_la_direccion_que_se_ve():
    todas = estado_base(3, N=cerrada(), S=cerrada(), E=cerrada(), O=cerrada())
    lugares = [("arriba", N, lambda z: min(z, key=lambda t: t[0].centery)),
               ("abajo", S, lambda z: max(z, key=lambda t: t[0].centery)),
               ("derecha", E, lambda z: max(z, key=lambda t: t[0].centerx)),
               ("izquierda", O, lambda z: min(z, key=lambda t: t[0].centerx))]
    with VistaAbierta() as vista:
        for nombre, esperada, elegir in lugares:
            for estado in (todas, replace(todas, sala_salida=3 + 1000)):
                juego = JuegoArmado(vista, estado)
                juego.dibujar()
                rectangulo, _ = elegir(_zonas(vista, ELEMENTO_PUERTA))                  # la puerta que SE VE en ese lugar
                juego.clic_en(rectangulo.center)
                assert juego.backend.llamadas == [("abrir", esperada)], (nombre, juego.backend.llamadas)


def probar_clic_en_la_puerta_final_abre_la_direccion_que_se_ve():
    with VistaAbierta() as vista:
        for nombre, direccion in (("N", N), ("S", S), ("E", E), ("O", O)):
            juego = JuegoArmado(vista, estado_base(3, **{nombre: cerrada(6)}))
            juego.dibujar()
            (rectangulo, _), = _zonas(vista, ELEMENTO_PUERTA)
            lugar = {N: rectangulo.centery < ALTO / 4, S: rectangulo.centery > 3 * ALTO / 4,
                     E: rectangulo.centerx > 3 * ANCHO / 4, O: rectangulo.centerx < ANCHO / 4}[direccion]
            assert lugar, (nombre, rectangulo)
            juego.clic_en(rectangulo.center)
            assert juego.backend.llamadas == [("abrir", direccion)]


def probar_clic_en_el_punto_del_enemigo_k_segun_la_funcion_de_reparto_ataca_al_k():
    with VistaAbierta() as vista:
        for pies in PIES_A_PROBAR:
            for cantidad in (1, 2, 6, 12):
                estado = con_enemigos(estado_base(3), cantidad)
                reparto = _reparto_de(vista, estado, pies)
                for k in range(cantidad):
                    juego = JuegoArmado(vista, estado)
                    _poner_pies(vista, pies)                                         # los pies que supone la prueba
                    juego.dibujar()
                    juego.clic_en(reparto.enemigos[k].center)                        # el punto de la función pura
                    assert juego.backend.llamadas == [("atacar", f"enemigo-{k + 1}")], (pies, cantidad, k)


def probar_clic_en_el_punto_del_objeto_k_segun_la_funcion_de_reparto_recoge_el_k():
    with VistaAbierta() as vista:
        for pies in PIES_A_PROBAR:
            for cantidad in (1, 6, 12):
                estado = con_objetos(estado_base(3), cantidad)
                reparto = _reparto_de(vista, estado, pies)
                for k in range(cantidad):
                    juego = JuegoArmado(vista, estado)
                    _poner_pies(vista, pies)
                    juego.dibujar()
                    juego.clic_en(reparto.objetos[k].center)
                    assert juego.backend.llamadas == [("recoger", estado.objetos_suelo[k].id)], (pies, cantidad, k)


def probar_el_enemigo_objetivo_se_resalta_y_el_resalte_no_cambia_las_zonas():
    with VistaAbierta() as vista:
        estado = con_enemigos(estado_base(3), 3)
        vista.dibujar(_juego(estado, None))
        sin = pygame.display.get_surface().copy()
        zonas_sin = _zonas(vista)
        vista.dibujar(_juego(estado, "enemigo-2"))
        con = pygame.display.get_surface().copy()
        assert _zonas(vista) == zonas_sin
        cambio = _rectangulo_del_cambio(sin, con)
        segundo = next(r for r, e in _zonas(vista, ELEMENTO_ENEMIGO) if e.indice == 1)   # (se registran de abajo hacia arriba)
        assert cambio is not None and segundo.inflate(40, 40).contains(cambio)          # solo el segundo cambia
        vista.dibujar(_juego(estado, "no-existe"))
        assert _imagen() == _imagen(sin)                                                 # un objetivo desconocido no resalta


# ================================================================ aura y nombre de los objetos
def probar_los_objetos_dibujan_aura_y_los_enemigos_no():
    with VistaAbierta() as vista:
        almacen = vista._escena._almacen
        llamadas = []
        original = almacen.aura_de_objeto
        almacen.aura_de_objeto = lambda *a, **k: (llamadas.append(a), original(*a, **k))[1]
        vista.dibujar(_juego(con_enemigos(estado_base(3), 6)))
        assert llamadas == []                                                            # los enemigos no llevan aura
        vista.dibujar(_juego(con_objetos(estado_base(3), 5)))
        assert len(llamadas) == 5                                                        # un aura por objeto
        con_aura = pygame.display.get_surface().copy()
        zonas = [r for r, _ in _zonas(vista, ELEMENTO_OBJETO_SUELO)]
        almacen.aura_de_objeto = lambda *a, **k: pygame.Surface((1, 1), pygame.SRCALPHA)  # el mismo cuadro, sin aura
        vista.dibujar(_juego(con_objetos(estado_base(3), 5)))
        sin_aura = pygame.display.get_surface().copy()
        huellas = [z.inflate(2 * c.AURA_MARGEN, 2 * c.AURA_MARGEN) for z in zonas]
        for huella in huellas:
            assert _rectangulo_del_cambio(con_aura.subsurface(huella), sin_aura.subsurface(huella)) is not None, huella
        for superficie in (con_aura, sin_aura):                                           # fuera de las huellas, nada cambia
            for huella in huellas:
                superficie.fill((0, 0, 0), huella)
        assert _imagen(con_aura) == _imagen(sin_aura)


def probar_no_hay_etiquetas_permanentes_con_el_nombre_de_los_objetos():
    with VistaAbierta() as vista:
        estado = con_objetos(estado_base(3), 5)
        vista.dibujar(_juego(estado))
        a = _imagen()
        otros_nombres = [replace(o, nombre=o.nombre + " con otro nombre larguísimo") for o in estado.objetos_suelo]
        vista.dibujar(_juego(replace(estado, objetos_suelo=otros_nombres)))
        assert _imagen() == a                                                            # el nombre no se dibuja


def probar_el_aura_no_cambia_las_zonas_ni_tapa_a_otros_elementos():
    with VistaAbierta() as vista:
        estado = con_objetos(con_enemigos(estado_base(3), 6), 12)
        reparto = _reparto_de(vista, estado, c.PIES_CENTRO)
        huellas = [z.inflate(2 * c.AURA_MARGEN, 2 * c.AURA_MARGEN) for z in reparto.objetos]
        todos = reparto.enemigos + huellas
        for i, huella in enumerate(huellas):                                             # el aura cabe sin pisar a nadie
            assert all(not huella.colliderect(otro) for j, otro in enumerate(todos) if j != len(reparto.enemigos) + i)
        vista.dibujar(_juego(estado))
        lado = c.LADO_OBJETO
        for rectangulo, elemento in _zonas(vista, ELEMENTO_OBJETO_SUELO):
            sprite = vista._escena._almacen.objeto(estado.objetos_suelo[elemento.indice].id,
                                                   estado.objetos_suelo[elemento.indice].clase, lado).fotogramas[0]
            assert rectangulo.size == sprite.get_size()                                  # la zona es la del sprite, sin aura


def probar_el_aura_se_prepara_una_vez_por_objeto_y_se_guarda_en_la_cache():
    with VistaAbierta() as vista:
        almacen = vista._escena._almacen
        a = almacen.aura_de_objeto("itm_antorcha", "antorcha", c.LADO_OBJETO, c.AURA_MARGEN, c.AURA_COLOR,
                                   c.AURA_INTENSIDAD)
        entradas = almacen.entradas_cache
        b = almacen.aura_de_objeto("itm_antorcha", "antorcha", c.LADO_OBJETO, c.AURA_MARGEN, c.AURA_COLOR,
                                   c.AURA_INTENSIDAD)
        assert a is b and almacen.entradas_cache == entradas
        vista.dibujar(_juego(con_objetos(estado_base(3), 6)))                            # calentar
        entradas, accesos = almacen.entradas_cache, almacen.accesos_disco
        for _ in range(5):
            vista.dibujar(_juego(con_objetos(estado_base(3), 6)))
        assert almacen.entradas_cache == entradas and almacen.accesos_disco == accesos   # nada nuevo en cada cuadro


def probar_el_nombre_del_objeto_aparece_solo_con_el_objeto_bajo_el_raton_y_es_el_suyo():
    with VistaAbierta() as vista:
        estado = con_objetos(estado_base(3), 6)
        vista.dibujar(_juego(estado))
        sin = pygame.display.get_surface().copy()
        reparto = _reparto_de(vista, estado, c.PIES_CENTRO)
        for k in range(6):
            bajo = ElementoDTO(ELEMENTO_OBJETO_SUELO, k)
            vista.dibujar(_juego(estado, bajo_el_raton=bajo))
            con = pygame.display.get_surface().copy()
            cambio = _rectangulo_del_cambio(sin, con)
            assert cambio is not None and PANTALLA.contains(cambio), k
            assert reparto.objetos[k].inflate(300, 120).contains(cambio), (k, cambio)    # junto a ese objeto
            # es el nombre de ESE objeto: cambiar el de otro no cambia la etiqueta; cambiar el suyo, sí
            otro = (k + 1) % 6
            renombrado = [replace(o, nombre="Nombre distinto") if i == otro else o for i, o in enumerate(estado.objetos_suelo)]
            vista.dibujar(_juego(replace(estado, objetos_suelo=renombrado), bajo_el_raton=bajo))
            assert _imagen() == _imagen(con), k
            renombrado = [replace(o, nombre="Nombre distinto") if i == k else o for i, o in enumerate(estado.objetos_suelo)]
            vista.dibujar(_juego(replace(estado, objetos_suelo=renombrado), bajo_el_raton=bajo))
            assert _imagen() != _imagen(con), k


def probar_el_nombre_no_se_dibuja_con_indice_fuera_de_rango_ni_con_otros_tipos_de_elemento():
    with VistaAbierta() as vista:
        estado = con_objetos(con_enemigos(estado_base(3, E=cerrada()), 2), 3)
        vista.dibujar(_juego(estado))
        sin = _imagen()
        zonas_sin = _zonas(vista)
        for elemento in (ElementoDTO(ELEMENTO_OBJETO_SUELO, 3), ElementoDTO(ELEMENTO_OBJETO_SUELO, 99),
                         ElementoDTO(ELEMENTO_OBJETO_SUELO, -1), ElementoDTO(ELEMENTO_ENEMIGO, 0),
                         ElementoDTO(ELEMENTO_PUERTA, E), ElementoDTO(ELEMENTO_BOTON, 0), ElementoDTO("inventario", 0),
                         ElementoDTO("otra-cosa", 1), None):
            vista.dibujar(_juego(estado, bajo_el_raton=elemento))
            assert _imagen() == sin, elemento
            assert _zonas(vista) == zonas_sin, elemento
        vista.dibujar(_juego(estado, bajo_el_raton=ElementoDTO(ELEMENTO_OBJETO_SUELO, 2)))
        assert _imagen() != sin                                                            # (y con uno válido, sí)
        assert _zonas(vista) == zonas_sin                                                  # pero sin zonas nuevas


def probar_la_etiqueta_queda_dentro_de_la_pantalla_incluso_con_objetos_junto_al_borde():
    esquinas = [(0, 40), (ANCHO - 60, 40), (0, ALTO - 2), (ANCHO - 60, ALTO - 2), (600, 20), (700, ALTO - 2)]
    anterior = _con_reparto_falso([], esquinas)
    try:
        with VistaAbierta() as vista:
            base = con_objetos(estado_base(3), 6)
            estado = replace(base, objetos_suelo=[replace(o, nombre="Un nombre bastante largo de objeto")
                                                  for o in base.objetos_suelo])
            vista.dibujar(_juego(estado))
            sin = pygame.display.get_surface().copy()
            for k in range(6):
                vista.dibujar(_juego(estado, bajo_el_raton=ElementoDTO(ELEMENTO_OBJETO_SUELO, k)))
                cambio = _rectangulo_del_cambio(sin, pygame.display.get_surface())
                assert cambio is not None and PANTALLA.contains(cambio), (k, cambio)
    finally:
        escena.colocar = anterior


def probar_la_barra_de_vida_es_proporcional_y_aguanta_los_extremos():
    with VistaAbierta():
        fuentes = Fuentes()

        def verde(vida, vida_max):
            """Hasta dónde llega el relleno: el último píxel verde de CUALQUIER fila. El número va encima, en medio de la
            barra, y es más alto que ella: a media vida tapa en la fila de arriba justo el final del relleno."""
            lienzo = pygame.Surface((120, 14))
            barra_de_vida(lienzo, fuentes, pygame.Rect(0, 0, 120, 14), vida, vida_max)
            return max((x for x in range(120) for y in range(14) if lienzo.get_at((x, y))[:3] == (84, 168, 72)),
                       default=0)
        completa, mitad = verde(12, 12), verde(6, 12)
        assert completa > 110 and abs(mitad - completa / 2) <= 3
        assert verde(0, 12) == 0 and verde(-3, 12) == 0 and verde(5, 0) == 0
        assert verde(50, 12) == completa                                                  # vida de más: no se sale de la barra


def probar_los_nombres_largos_y_la_vida_extrema_no_rompen_la_escena():
    with VistaAbierta() as vista:
        base = con_enemigos(estado_base(3), 4)
        raros = [replace(e, nombre="Nombre larguísimo de enemigo " * 4, vida=-5, vida_max=0) if i == 0 else
                 replace(e, vida=99, vida_max=12) for i, e in enumerate(base.enemigos)]
        vista.dibujar(_juego(replace(base, enemigos=raros)))
        for rectangulo, _ in _zonas(vista, ELEMENTO_ENEMIGO):
            assert PANTALLA.contains(rectangulo)


# ================================================================ la pausa con la escena detrás
def probar_la_pausa_dibuja_la_escena_detras_sin_cambiar_sus_zonas():
    opciones = ["Continuar", "Guardar partida", "Cargar partida", "Salir al menú"]
    estado = con_objetos(con_enemigos(estado_base(3, E=cerrada()), 2), 1)
    with VistaAbierta() as vista:
        sin_estado = PantallaDTO("pausa", "Pausa", opciones, 0, ayuda=AYUDA_PAUSA)
        con_estado = replace(sin_estado, estado=estado)
        vista.dibujar(sin_estado)
        zonas_sin, imagen_sin = _zonas(vista), _imagen()
        vista.dibujar(con_estado)
        assert _zonas(vista) == zonas_sin                                                  # las mismas zonas: solo los botones
        assert [e.tipo for _, e in _zonas(vista)] == [ELEMENTO_BOTON] * 4
        assert _imagen() != imagen_sin                                                     # y detrás se ve la partida
        assert _imagen_de(vista, replace(con_estado, estado=con_enemigos(estado, 6))) != _imagen_de(vista, con_estado)
        assert _imagen_de(vista, replace(con_estado, elemento_bajo_el_raton=ElementoDTO(ELEMENTO_OBJETO_SUELO, 0))) \
            == _imagen_de(vista, con_estado)                                               # en la pausa no hay nombres


# ================================================================ de punta a punta con servicios reales
def _entrar_a_la_partida(r):
    r.pulsar(ENTER)                                                                        # Comenzar juego
    r.pulsar(ENTER)                                                                        # la primera cripta
    r.escribir("Ana")
    r.pulsar(ENTER)                                                                        # Aceptar
    assert r.pantalla().pantalla == "juego"


def _a_la_sala_de_las_ratas(r):
    """Dibuja la sala 1 (para que la Vista sepa de dónde se viene) y sube a la sala de las ratas. Devuelve la pantalla y
    los pies que la función pura da para esa entrada."""
    r.dibujar()
    r.pulsar(ARRIBA)
    pantalla = r.dibujar()
    return pantalla, posicion_del_protagonista(pantalla.estado.sala.salidas, 1)


def probar_real_clic_en_el_punto_del_enemigo_2_ataca_a_la_rata_2():
    vista = VistaPygame()
    vista.abrir()
    try:
        with Recorrido(vista) as r:
            _entrar_a_la_partida(r)
            pantalla, pies = _a_la_sala_de_las_ratas(r)
            assert pies == c.PIES_PUERTA[S]                                                # entró por la puerta del sur
            assert [e.nombre for e in pantalla.estado.enemigos] == ["Rata gigante #1", "Rata gigante #2"]
            reparto = _reparto_de(vista, pantalla.estado, pies)
            r.controlador.procesar_evento(clic(reparto.enemigos[1].center))                # donde la función pura lo pone
            mensajes = r.pantalla().estado.mensajes
            assert any("Jugador ataca a Rata gigante #2" in m for m in mensajes), mensajes
            assert not any("Jugador ataca a Rata gigante #1" in m for m in mensajes), mensajes
    finally:
        vista.cerrar()


def probar_real_clic_en_el_punto_del_enemigo_1_ataca_a_la_rata_1():
    vista = VistaPygame()
    vista.abrir()
    try:
        with Recorrido(vista) as r:
            _entrar_a_la_partida(r)
            pantalla, pies = _a_la_sala_de_las_ratas(r)
            reparto = _reparto_de(vista, pantalla.estado, pies)
            r.controlador.procesar_evento(clic(reparto.enemigos[0].center))
            mensajes = r.pantalla().estado.mensajes
            assert any("Jugador ataca a Rata gigante #1" in m for m in mensajes), mensajes
            assert not any("Jugador ataca a Rata gigante #2" in m for m in mensajes), mensajes
    finally:
        vista.cerrar()


def probar_real_clic_en_el_punto_de_la_antorcha_la_deja_en_el_inventario():
    vista = VistaPygame()
    vista.abrir()
    try:
        with Recorrido(vista) as r:
            _entrar_a_la_partida(r)
            pantalla = r.dibujar()
            assert [o.nombre for o in pantalla.estado.objetos_suelo] == ["Antorcha"]
            assert pantalla.estado.inventario.objetos == []
            reparto = _reparto_de(vista, pantalla.estado, c.PIES_CENTRO)                   # sin sala anterior: al centro
            r.controlador.procesar_evento(clic(reparto.objetos[0].center))
            estado = r.pantalla().estado
            assert [o.nombre for o in estado.inventario.objetos] == ["Antorcha"]
            assert estado.objetos_suelo == []
            r.dibujar()
            assert _zonas(vista, ELEMENTO_OBJETO_SUELO) == []                              # y ya no se dibuja en el suelo
    finally:
        vista.cerrar()


def probar_real_mover_el_raton_sobre_el_objeto_muestra_su_nombre_y_otro_sitio_o_una_tecla_lo_quitan():
    vista = VistaPygame()
    vista.abrir()
    try:
        with Recorrido(vista) as r:
            _entrar_a_la_partida(r)
            pantalla = r.dibujar()
            sin = _imagen()
            punto = _reparto_de(vista, pantalla.estado, c.PIES_CENTRO).objetos[0].center
            assert r.pantalla().elemento_bajo_el_raton is None
            r.controlador.procesar_evento(movimiento(punto))                                # el ratón sobre la antorcha
            assert r.pantalla().elemento_bajo_el_raton == ElementoDTO(ELEMENTO_OBJETO_SUELO, 0)
            r.dibujar()
            con_nombre = _imagen()
            assert con_nombre != sin                                                        # aparece su nombre
            r.controlador.procesar_evento(movimiento((8, 8)))                               # a otro sitio
            assert r.pantalla().elemento_bajo_el_raton is None
            r.dibujar()
            assert _imagen() == sin                                                         # desaparece
            r.controlador.procesar_evento(movimiento(punto))
            r.dibujar()
            assert _imagen() == con_nombre                                                  # vuelve igual
            r.pulsar(pygame.K_TAB)                                                          # una tecla lo quita
            assert r.pantalla().elemento_bajo_el_raton is None
            r.dibujar()
            assert _imagen() == sin
    finally:
        vista.cerrar()


def probar_real_clic_en_la_puerta_cerrada_sin_llave_da_un_aviso_y_la_sala_sigue_igual():
    vista = VistaPygame()
    vista.abrir()
    try:
        with Recorrido(vista) as r:
            _entrar_a_la_partida(r)
            _a_la_sala_de_las_ratas(r)                                                      # sala 2: salida E cerrada con llave
            (rectangulo, elemento), = _zonas(vista, ELEMENTO_PUERTA)
            assert rectangulo.centerx > ANCHO / 2 and elemento.indice == E                  # se ve a la derecha: el este
            sala = r.pantalla().estado.sala.id
            r.controlador.procesar_evento(clic(rectangulo.center))
            despues = r.pantalla()
            assert despues.estado.sala.id == sala
            assert despues.aviso or despues.estado.resultado or any("llave" in m.lower() for m in despues.estado.mensajes)
    finally:
        vista.cerrar()


def probar_real_pausa_con_la_partida_detras_y_vuelta_a_la_partida():
    vista = VistaPygame()
    vista.abrir()
    try:
        with Recorrido(vista) as r:
            _entrar_a_la_partida(r)
            _a_la_sala_de_las_ratas(r)
            r.pulsar(ESC)
            pantalla = r.dibujar()
            assert pantalla.pantalla == "pausa" and pantalla.estado is not None
            assert [e.tipo for _, e in _zonas(vista)] == [ELEMENTO_BOTON] * 4
            r.clic_en_texto("Continuar")
            assert r.pantalla().pantalla == "juego"
    finally:
        vista.cerrar()


if __name__ == "__main__":
    probar_fondo_para_elige_por_el_rol_de_la_sala()
    probar_puertas_a_dibujar_solo_las_cerradas_y_la_final_aparte()
    probar_una_sola_puerta_dorada_y_las_demas_con_cadena()
    probar_direcciones_sin_salida()
    probar_el_trapecio_del_hueco_esta_dentro_de_su_marco_y_mira_hacia_la_pared()
    probar_posicion_del_protagonista_sin_sala_anterior_es_el_centro()
    probar_posicion_del_protagonista_delante_de_la_puerta_por_la_que_entro()
    probar_posicion_del_protagonista_al_centro_si_no_se_sabe_por_donde_entro()
    probar_colocar_es_determinista_no_solapa_cabe_en_el_suelo_y_respeta_lo_ocupado()
    probar_colocar_reparte_alrededor_de_los_pies_dados()
    probar_orden_de_dibujo_el_de_mas_abajo_va_encima_y_los_empates_por_indice()
    probar_el_reparto_cumple_todo_de_1_a_12_con_el_protagonista_en_el_centro_o_junto_a_cada_puerta()
    probar_el_reparto_no_tapa_el_protagonista_en_todo_el_rango_de_1_a_12_enemigos_y_objetos()
    probar_los_enemigos_se_achican_todos_con_el_mismo_factor_y_el_protagonista_no()
    probar_tamanos_propios_mayor_o_igual_que_generico_y_este_mayor_que_el_jugador()
    probar_el_jugador_mide_lo_mismo_en_todas_las_escenas()
    probar_los_pies_de_cada_enemigo_apoyan_en_la_base_de_su_zona()
    probar_el_protagonista_empieza_en_el_centro_y_entra_delante_de_la_puerta_correcta()
    probar_el_protagonista_va_al_centro_si_la_sala_anterior_no_es_contigua()
    probar_el_protagonista_olvida_la_sala_anterior_al_pasar_por_el_menu_y_otras_pantallas()
    probar_la_pausa_no_hace_olvidar_la_sala_y_volver_a_la_inicial_deja_delante_de_la_puerta()
    probar_cada_rol_de_sala_dibuja_su_fondo()
    probar_el_texto_de_depuracion_ya_no_tapa_la_escena()
    probar_un_clic_sobre_el_marco_de_una_direccion_sin_salida_no_devuelve_zona()
    probar_las_direcciones_sin_salida_se_oscurecen_y_las_abiertas_no()
    probar_fondo_final_no_oscurece_nada_porque_no_tiene_marcos()
    probar_con_la_ambientacion_en_cero_el_fondo_de_sala_es_el_mismo_conjunto_que_el_original()
    probar_con_la_intensidad_por_omision_el_fondo_de_sala_es_mas_oscuro_pero_no_negro()
    probar_a_mayor_intensidad_mas_oscuro_y_los_bordes_mas_que_el_centro()
    probar_el_fondo_ambientado_se_calcula_una_sola_vez_y_se_guarda_en_la_cache()
    probar_dibujar_con_ambiente_no_cuesta_apreciablemente_mas_que_sin_el()
    probar_la_escena_dibuja_el_fondo_ambientado_con_la_intensidad_de_componentes()
    probar_menu_victoria_y_derrota_nunca_piden_el_fondo_ambientado()
    probar_con_ambiente_los_marcos_abiertos_y_los_oscurecidos_se_distinguen_y_los_textos_se_leen()
    probar_las_puertas_cerradas_se_registran_donde_se_ven_en_las_cuatro_direcciones()
    probar_la_puerta_que_lleva_a_la_salida_se_ve_distinta_de_una_cerrada_comun()
    probar_cada_puerta_mira_hacia_su_pared()
    probar_muchos_enemigos_y_objetos_se_registran_dentro_de_la_pantalla_y_son_clicables()
    probar_las_zonas_estan_donde_dice_la_funcion_pura_de_reparto()
    probar_las_zonas_se_registran_en_el_orden_de_dibujo_de_abajo_hacia_arriba()
    probar_con_zonas_solapadas_gana_la_que_tiene_los_pies_mas_abajo_sea_enemigo_u_objeto()
    probar_una_puerta_cerrada_y_un_enemigo_encima_la_zona_del_enemigo_gana()
    probar_clic_en_cada_puerta_cerrada_abre_la_direccion_que_se_ve()
    probar_clic_en_la_puerta_final_abre_la_direccion_que_se_ve()
    probar_clic_en_el_punto_del_enemigo_k_segun_la_funcion_de_reparto_ataca_al_k()
    probar_clic_en_el_punto_del_objeto_k_segun_la_funcion_de_reparto_recoge_el_k()
    probar_el_enemigo_objetivo_se_resalta_y_el_resalte_no_cambia_las_zonas()
    probar_los_objetos_dibujan_aura_y_los_enemigos_no()
    probar_no_hay_etiquetas_permanentes_con_el_nombre_de_los_objetos()
    probar_el_aura_no_cambia_las_zonas_ni_tapa_a_otros_elementos()
    probar_el_aura_se_prepara_una_vez_por_objeto_y_se_guarda_en_la_cache()
    probar_el_nombre_del_objeto_aparece_solo_con_el_objeto_bajo_el_raton_y_es_el_suyo()
    probar_el_nombre_no_se_dibuja_con_indice_fuera_de_rango_ni_con_otros_tipos_de_elemento()
    probar_la_etiqueta_queda_dentro_de_la_pantalla_incluso_con_objetos_junto_al_borde()
    probar_la_barra_de_vida_es_proporcional_y_aguanta_los_extremos()
    probar_los_nombres_largos_y_la_vida_extrema_no_rompen_la_escena()
    probar_la_pausa_dibuja_la_escena_detras_sin_cambiar_sus_zonas()
    probar_real_clic_en_el_punto_del_enemigo_2_ataca_a_la_rata_2()
    probar_real_clic_en_el_punto_del_enemigo_1_ataca_a_la_rata_1()
    probar_real_clic_en_el_punto_de_la_antorcha_la_deja_en_el_inventario()
    probar_real_mover_el_raton_sobre_el_objeto_muestra_su_nombre_y_otro_sitio_o_una_tecla_lo_quitan()
    probar_real_clic_en_la_puerta_cerrada_sin_llave_da_un_aviso_y_la_sala_sigue_igual()
    probar_real_pausa_con_la_partida_detras_y_vuelta_a_la_partida()
    print("OK: todas las pruebas de la escena de juego pasaron")
