"""
Pruebas de las pantallas con botones (menu, criptas, nombre, pausa, puntajes) con la Vista REAL. Las de punta a punta
usan además el ControladorPygame real, servicios reales (paquete offline) y eventos simulados.
Se ejecuta desde cualquier carpeta.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402  (fija SDL_VIDEODRIVER=dummy antes de importar pygame)
from ayudas_vista import ABAJO, ENTER, ESC, Recorrido  # noqa: E402

from DTO.ElementoDTO import ELEMENTO_BOTON, ElementoDTO  # noqa: E402
from DTO.PantallaDTO import PantallaDTO  # noqa: E402
from DTO.PuntajeDTO import PuntajeDTO  # noqa: E402
from View.Componentes import ALTO, ANCHO, BOTON_ALTO_MINIMO  # noqa: E402
from View.VistaPygame import VistaPygame  # noqa: E402

OPCIONES_MENU = ["Comenzar juego", "Modo: Offline", "Cargar partida", "Puntajes", "Salir"]
AYUDA = ["Arriba / Abajo o ratón: elegir", "Enter o clic: aceptar"]


class VistaAbierta:
    """Una VistaPygame real, abierta para la prueba. Úsala con 'with'."""

    def __enter__(self):
        self.vista = VistaPygame()
        self.vista.abrir()
        return self.vista

    def __exit__(self, *_):
        self.vista.cerrar()


def _zonas(vista):
    return list(zip(vista._zonas._rectangulos, vista._zonas._elementos))


def _imagen(vista):
    return pygame.image.tobytes(pygame.display.get_surface(), "RGB")


def _menu(opciones=None, seleccion=0, titulo="CRIPTA", aviso=None):
    return PantallaDTO("menu", titulo, list(OPCIONES_MENU if opciones is None else opciones), seleccion,
                       aviso=aviso, ayuda=list(AYUDA))


# ---------------------------------------------------------------- zonas de los botones
def probar_cada_boton_del_menu_responde_en_su_centro_y_fuera_no_hay_nada():
    with VistaAbierta() as vista:
        vista.dibujar(_menu())
        zonas = _zonas(vista)
        assert len(zonas) == 5
        for i, (rectangulo, _) in enumerate(zonas):
            assert vista.elemento_en(rectangulo.center) == ElementoDTO(ELEMENTO_BOTON, i)
        assert vista.elemento_en((3, 3)) is None
        assert vista.elemento_en((ANCHO - 3, ALTO - 3)) is None
        assert vista.elemento_en((zonas[0][0].centerx, zonas[0][0].top - 6)) is None      # encima del primero


def probar_los_botones_del_menu_no_se_solapan_y_caben_en_la_pantalla():
    with VistaAbierta() as vista:
        vista.dibujar(_menu())
        rectangulos = [r for r, _ in _zonas(vista)]
        for i, r in enumerate(rectangulos):
            assert pygame.Rect(0, 0, ANCHO, ALTO).contains(r)
            assert all(not r.colliderect(otro) for otro in rectangulos[i + 1:])


def probar_las_zonas_se_limpian_al_inicio_de_cada_dibujar():
    with VistaAbierta() as vista:
        vista.dibujar(_menu())
        ultimo_del_menu = _zonas(vista)[4][0].center
        vista.dibujar(PantallaDTO("puntajes", "Puntajes", ["Cambiar el orden", "Volver"], 0, criterio="enemigos"))
        assert len(_zonas(vista)) == 2                                   # solo las del cuadro actual
        assert vista.elemento_en(ultimo_del_menu) is None or vista.elemento_en(ultimo_del_menu).indice < 2
        vista.dibujar(_menu())
        assert len(_zonas(vista)) == 5


# ---------------------------------------------------------------- el menú no repite el título
def probar_el_menu_no_dibuja_el_titulo_del_dto():
    with VistaAbierta() as vista:
        vista.dibujar(_menu(titulo="CRIPTA"))
        con_titulo = _imagen(vista)
        vista.dibujar(_menu(titulo="OTRO TITULO MUY DISTINTO"))
        assert _imagen(vista) == con_titulo                              # el título no cambia ni un píxel
        vista.dibujar(PantallaDTO("criptas", "Elige una cripta", ["A", "Volver"], 0))
        a = _imagen(vista)
        vista.dibujar(PantallaDTO("criptas", "Otro", ["A", "Volver"], 0))
        assert _imagen(vista) != a                                        # en las demás pantallas sí se dibuja


# ---------------------------------------------------------------- resaltado
def probar_el_boton_seleccionado_se_dibuja_resaltado():
    with VistaAbierta() as vista:
        def color_del_boton(indice, seleccion):
            vista.dibujar(_menu(seleccion=seleccion))
            rectangulo = _zonas(vista)[indice][0]
            return pygame.display.get_surface().get_at((rectangulo.left + 10, rectangulo.centery))[:3]
        resaltado, normal = color_del_boton(2, 2), color_del_boton(2, 0)
        assert resaltado[0] > 120 and resaltado[1] < 80, resaltado       # rojo
        assert normal[0] < 60, normal                                    # oscuro
        vista.dibujar(_menu(seleccion=-1))                                # sin selección: ninguno resaltado
        for rectangulo, _ in _zonas(vista):
            assert pygame.display.get_surface().get_at((rectangulo.left + 10, rectangulo.centery))[0] < 60


# ---------------------------------------------------------------- criptas
def probar_la_lista_de_criptas_sigue_legible_con_muchas():
    with VistaAbierta() as vista:
        for cantidad in (1, 3, 8, 14, 40, 120):
            opciones = [f"Cripta número {i} - {i} salas, dificultad 2" for i in range(cantidad)] + ["Volver"]
            vista.dibujar(PantallaDTO("criptas", "Elige una cripta", opciones, 0, ayuda=list(AYUDA)))
            zonas = _zonas(vista)
            assert len(zonas) == cantidad + 1
            rectangulos = [r for r, _ in zonas]
            for i, (rectangulo, elemento) in enumerate(zonas):
                assert elemento == ElementoDTO(ELEMENTO_BOTON, i)
                assert pygame.Rect(0, 0, ANCHO, ALTO).contains(rectangulo), (cantidad, i)
                assert rectangulo.height >= BOTON_ALTO_MINIMO, (cantidad, i)
                assert all(not rectangulo.colliderect(otro) for otro in rectangulos[i + 1:]), (cantidad, i)
        vista.dibujar(PantallaDTO("criptas", "Elige una cripta", ["Una", "Volver"], 1))
        volver_con_una = _zonas(vista)[-1][0]
        vista.dibujar(PantallaDTO("criptas", "Elige una cripta", ["A", "B", "C", "Volver"], 3))
        assert _zonas(vista)[-1][0] == volver_con_una                    # Volver siempre en el mismo sitio


# ---------------------------------------------------------------- nombre, pausa y puntajes
def probar_el_nombre_dibuja_el_texto_y_el_cursor_parpadea():
    with VistaAbierta() as vista:
        pantalla = lambda texto: PantallaDTO("nombre", "¿Cómo te llamas?", ["Aceptar", "Volver"], 0, texto=texto)
        menus = vista._menus
        superficie = pygame.display.get_surface()
        menus.dibujar(superficie, pantalla("Ana"), 0)
        con_cursor = _imagen(vista)
        menus.dibujar(superficie, pantalla("Ana"), 500)
        sin_cursor = _imagen(vista)
        menus.dibujar(superficie, pantalla("Ana"), 1000)
        assert _imagen(vista) == con_cursor and sin_cursor != con_cursor
        vista._zonas.limpiar()                                           # (se llamó a menus directamente, sin vista.dibujar)
        menus.dibujar(superficie, pantalla("Beto"), 0)
        assert _imagen(vista) != con_cursor
        assert [e.indice for _, e in _zonas(vista)] == [0, 1]


def probar_la_pausa_y_los_avisos_se_dibujan():
    with VistaAbierta() as vista:
        pausa = PantallaDTO("pausa", "Pausa", ["Continuar", "Guardar partida", "Cargar partida", "Salir al menú"], 1,
                            ayuda=["Esc: volver a la partida"])
        vista.dibujar(pausa)
        assert [e.indice for _, e in _zonas(vista)] == [0, 1, 2, 3]
        sin_aviso = _imagen(vista)
        largo = "No se pudo guardar la partida porque " + "el disco está lleno " * 12
        vista.dibujar(PantallaDTO("pausa", "Pausa", pausa.opciones, 1, aviso=largo, ayuda=pausa.ayuda))
        assert _imagen(vista) != sin_aviso and len(_zonas(vista)) == 4


def probar_un_aviso_largo_no_tapa_la_ayuda_ni_los_botones_de_la_pausa():
    opciones = ["Continuar", "Guardar partida", "Cargar partida", "Salir al menú"]
    ayudas = [["Esc: volver"], ["Arriba / Abajo", "Enter: aceptar", "Esc: volver"]]
    avisos = ["Corto", "No se pudo guardar la partida. " * 3, "No se pudo guardar la partida porque " + "el disco está lleno " * 30]
    with VistaAbierta() as vista:
        for ayuda in ayudas:
            vista.dibujar(PantallaDTO("pausa", "Pausa", opciones, 1, ayuda=ayuda))
            tope = vista._menus.tope_de_la_ayuda(PantallaDTO("pausa", "Pausa", opciones, 1, ayuda=ayuda))
            sin_aviso = pygame.image.tobytes(pygame.display.get_surface().subsurface((0, tope, ANCHO, ALTO - tope)), "RGB")
            ultimo_boton = max(r.bottom for r, _ in _zonas(vista))
            for aviso in avisos:
                pantalla = PantallaDTO("pausa", "Pausa", opciones, 1, aviso=aviso, ayuda=ayuda)
                vista.dibujar(pantalla)
                caja, lineas = vista._menus.caja_del_aviso(pantalla)
                assert caja.bottom <= tope, (caja, tope)                          # no pisa la ayuda
                assert caja.top >= ultimo_boton and len(lineas) <= 2, (caja, ultimo_boton)   # ni los botones
                assert pygame.Rect(0, 0, ANCHO, ALTO).contains(caja)
                bajo_el_aviso = pygame.image.tobytes(pygame.display.get_surface().subsurface((0, tope, ANCHO, ALTO - tope)), "RGB")
                assert bajo_el_aviso == sin_aviso, "el aviso cambió los píxeles de la ayuda"
            assert vista._menus.caja_del_aviso(pantalla)[1][-1].endswith("...")   # el más largo se corta con "..."
            assert vista._menus.caja_del_aviso(PantallaDTO("pausa", "Pausa", opciones, 1, aviso="Corto"))[1] == ["Corto"]
        assert vista._menus.caja_del_aviso(PantallaDTO("pausa", "Pausa", opciones, 1)) == (None, [])


def probar_los_puntajes_vacios_pocos_y_muchos():
    fila = lambda i: PuntajeDTO(f"Jugador{i}", "cripta-01", "abcdef0123456789", 10 + i, i, 100 + i)
    with VistaAbierta() as vista:
        base = ["Cambiar el orden", "Volver"]
        vista.dibujar(PantallaDTO("puntajes", "Puntajes", base, 0, puntajes=[], criterio="enemigos"))
        vacia = _imagen(vista)
        vista.dibujar(PantallaDTO("puntajes", "Puntajes", base, 0, puntajes=[fila(1)], criterio="enemigos"))
        assert _imagen(vista) != vacia
        for criterio in ("enemigos", "tiempo", "acciones", "nombre", "otro"):
            vista.dibujar(PantallaDTO("puntajes", "Puntajes", base, 0, puntajes=[fila(i) for i in range(60)],
                                      criterio=criterio))
            assert [e.indice for _, e in _zonas(vista)] == [0, 1]       # la tabla no registra zonas


# ---------------------------------------------------------------- de punta a punta
def probar_de_punta_a_punta_con_clics_hasta_la_partida_y_la_pausa():
    vista = VistaPygame()
    vista.abrir()
    try:
        with Recorrido(vista) as r:
            assert r.pantalla().pantalla == "menu"
            r.clic_en_boton(0)                                           # Comenzar juego
            assert r.pantalla().pantalla == "criptas" and r.pantalla().opciones[-1] == "Volver"
            r.clic_en_boton(0)                                           # la primera cripta
            assert r.pantalla().pantalla == "nombre"
            r.escribir("Ana")
            assert r.pantalla().texto == "Ana"
            r.clic_en_boton(0)                                           # Aceptar
            assert r.pantalla().pantalla == "juego" and r.pantalla().estado.jugador.nombre
            r.pulsar(ESC)
            assert r.pantalla().pantalla == "pausa"
            r.clic_en_boton(3)                                           # Salir al menú
            assert r.pantalla().pantalla == "menu"
    finally:
        vista.cerrar()


def probar_de_punta_a_punta_el_raton_sobre_un_boton_cambia_la_seleccion_y_se_ve_resaltado():
    vista = VistaPygame()
    vista.abrir()
    try:
        with Recorrido(vista) as r:
            assert r.pantalla().seleccion == 0
            r.pasar_el_raton_por(3)                                      # Puntajes
            assert r.pantalla().seleccion == 3
            r.dibujar()
            rectangulo = vista._zonas._rectangulos[3]
            assert pygame.display.get_surface().get_at((rectangulo.left + 10, rectangulo.centery))[0] > 120
            primero = vista._zonas._rectangulos[0]
            assert pygame.display.get_surface().get_at((primero.left + 10, primero.centery))[0] < 60
            r.pulsar(ABAJO)                                              # el teclado sigue desde el botón señalado
            assert r.pantalla().seleccion == 4
            r.clic_en_boton(3)                                           # Puntajes
            assert r.pantalla().pantalla == "puntajes"
            r.clic_en_boton(1)                                           # Volver
            assert r.pantalla().pantalla == "menu"
            r.pulsar(ENTER)
            assert r.pantalla().pantalla == "criptas"
    finally:
        vista.cerrar()


if __name__ == "__main__":
    probar_cada_boton_del_menu_responde_en_su_centro_y_fuera_no_hay_nada()
    probar_los_botones_del_menu_no_se_solapan_y_caben_en_la_pantalla()
    probar_las_zonas_se_limpian_al_inicio_de_cada_dibujar()
    probar_el_menu_no_dibuja_el_titulo_del_dto()
    probar_el_boton_seleccionado_se_dibuja_resaltado()
    probar_la_lista_de_criptas_sigue_legible_con_muchas()
    probar_el_nombre_dibuja_el_texto_y_el_cursor_parpadea()
    probar_la_pausa_y_los_avisos_se_dibujan()
    probar_un_aviso_largo_no_tapa_la_ayuda_ni_los_botones_de_la_pausa()
    probar_los_puntajes_vacios_pocos_y_muchos()
    probar_de_punta_a_punta_con_clics_hasta_la_partida_y_la_pausa()
    probar_de_punta_a_punta_el_raton_sobre_un_boton_cambia_la_seleccion_y_se_ve_resaltado()
    print("OK: todas las pruebas de las pantallas con botones pasaron")
