"""
Pruebas de las pantallas victoria y derrota con la Vista REAL. La derrota es real (ControladorPygame real, servicios
reales con el paquete offline y clics sobre lo que la Vista dibujó); la victoria real depende de la llave y del azar,
así que se arma a mano. Se ejecuta desde cualquier carpeta.
"""
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402  (fija SDL_VIDEODRIVER=dummy antes de importar pygame)
from ayudas_vista import ABAJO, ENTER, Recorrido  # noqa: E402

from DTO.ElementoDTO import ELEMENTO_BOTON, ElementoDTO  # noqa: E402
from DTO.PantallaDTO import PantallaDTO  # noqa: E402
from DTO.PuntajeDTO import PuntajeDTO  # noqa: E402
from DTO.ReporteDatosDTO import ReporteDatosDTO  # noqa: E402
import View.PantallaFin as modulo_fin  # noqa: E402
from View.Componentes import ALTO, ANCHO  # noqa: E402
from View.PantallaFin import RECUADRO, lineas_de_puntaje, lineas_de_reporte  # noqa: E402
from View.VistaPygame import VistaPygame  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
OPCIONES = ["Jugar de nuevo", "Ver puntajes", "Menú principal"]
AYUDA = ["Arriba / Abajo o ratón: elegir", "Enter o clic: aceptar", "Esc: menú principal"]
PUNTAJE = PuntajeDTO("Ana", "cripta-01", "fd58f7743b9e", 12, 3, 450)
REPORTE = ReporteDatosDTO(solicitudes_realizadas=7, presupuesto=9, aciertos_cache=21, fallos_cache=4, offline=False)


class VistaAbierta:
    def __enter__(self):
        self.vista = VistaPygame()
        self.vista.abrir()
        return self.vista

    def __exit__(self, *_):
        self.vista.cerrar()


def _fin(nombre="victoria", puntaje=PUNTAJE, reporte=REPORTE, aviso=None, seleccion=0):
    return PantallaDTO(nombre, "", list(OPCIONES), seleccion, aviso=aviso, ayuda=list(AYUDA), puntaje=puntaje,
                       reporte=reporte)


def _zonas(vista):
    return list(zip(vista._zonas._rectangulos, vista._zonas._elementos))


def _copia():
    return pygame.display.get_surface().copy()


def _fondo_original(nombre):
    """El fondo leído directamente del archivo y escalado igual que la Vista (independiente del código de la Vista)."""
    imagen = pygame.image.load(str(RAIZ / "assets" / "fondos" / f"{nombre}.jpg")).convert()
    return pygame.transform.smoothscale(imagen, (ANCHO, ALTO))


def _bytes(superficie, rectangulo):
    return pygame.image.tobytes(superficie.subsurface(rectangulo), "RGB")


def _rectangulo_del_cambio(a, b):
    """El rectángulo mínimo que contiene todos los píxeles distintos entre las superficies a y b (None si son iguales)."""
    ab, ba = a.copy(), b.copy()
    ab.blit(b, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
    ba.blit(a, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
    ab.blit(ba, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    ab.set_colorkey((0, 0, 0))
    rectangulo = ab.get_bounding_rect()
    return rectangulo if rectangulo.width and rectangulo.height else None


# ---------------------------------------------------------------- qué texto se muestra (puro)
def probar_el_texto_del_puntaje_trae_los_cinco_datos_y_el_caso_sin_puntaje():
    assert lineas_de_puntaje(PUNTAJE) == [("Nombre", "Ana"), ("Cripta", "cripta-01"), ("Acciones", "12"),
                                          ("Enemigos derrotados", "3"), ("Tiempo final", "450")]
    sin_puntaje = lineas_de_puntaje(None)
    assert sin_puntaje == [("", "Puntaje no guardado")]


def probar_el_texto_del_reporte_trae_lo_que_exige_el_enunciado_y_el_presupuesto_desconocido_es_una_raya():
    assert lineas_de_reporte(REPORTE) == [("Solicitudes realizadas", "7"), ("Presupuesto", "9"),
                                          ("Aciertos de caché", "21"), ("Fallos de caché", "4")]
    assert lineas_de_reporte(replace(REPORTE, presupuesto=None))[1] == ("Presupuesto", "—")
    assert lineas_de_reporte(replace(REPORTE, presupuesto=0))[1] == ("Presupuesto", "0")     # 0 no es "desconocido"
    assert lineas_de_reporte(None) == []


# ---------------------------------------------------------------- el fondo y el recuadro
def probar_cada_pantalla_usa_su_fondo_y_nada_se_dibuja_dentro_del_recuadro():
    largo = "No se pudo guardar el puntaje. " * 30
    extremo = PuntajeDTO("W" * 16, "x" * 60, "abc", 10 ** 15, 10 ** 15, 10 ** 15)
    casos = [_fin("victoria"), _fin("derrota"), _fin("victoria", puntaje=None, aviso="No se pudo guardar"),
             _fin("derrota", aviso=largo), _fin("victoria", puntaje=extremo, reporte=replace(
                 REPORTE, solicitudes_realizadas=10 ** 15, presupuesto=None, offline=True))]
    with VistaAbierta() as vista:
        victoria, derrota = _fondo_original("fondo_victoria"), _fondo_original("fondo_derrota")
        assert _bytes(victoria, RECUADRO) != _bytes(derrota, RECUADRO)              # (si no, la prueba no distingue)
        for pantalla in casos:
            vista.dibujar(pantalla)
            propio, ajeno = (victoria, derrota) if pantalla.pantalla == "victoria" else (derrota, victoria)
            dibujado = pygame.display.get_surface()
            assert _bytes(dibujado, RECUADRO) == _bytes(propio, RECUADRO), pantalla.pantalla     # fondo propio, intacto
            assert _bytes(dibujado, RECUADRO) != _bytes(ajeno, RECUADRO), pantalla.pantalla


def probar_los_botones_no_tocan_el_recuadro_y_caben_en_la_pantalla():
    with VistaAbierta() as vista:
        for nombre in ("victoria", "derrota"):
            vista.dibujar(_fin(nombre))
            zonas = _zonas(vista)
            assert [e for _, e in zonas] == [ElementoDTO(ELEMENTO_BOTON, i) for i in range(3)]
            rectangulos = [r for r, _ in zonas]
            for i, r in enumerate(rectangulos):
                assert pygame.Rect(0, 0, ANCHO, ALTO).contains(r)
                assert not r.colliderect(RECUADRO), (r, RECUADRO)
                assert r.top > RECUADRO.bottom                                         # en la franja inferior
                assert all(not r.colliderect(otro) for otro in rectangulos[i + 1:])
                assert vista.elemento_en(r.center) == ElementoDTO(ELEMENTO_BOTON, i)
            assert vista.elemento_en(RECUADRO.center) is None


def probar_el_boton_seleccionado_se_dibuja_resaltado():
    with VistaAbierta() as vista:
        def rojo_del_boton(indice, seleccion):
            vista.dibujar(_fin(seleccion=seleccion))
            r = _zonas(vista)[indice][0]
            return pygame.display.get_surface().get_at((r.left + 10, r.centery))[0]
        assert rojo_del_boton(1, 1) > 120 and rojo_del_boton(1, 0) < 60
        vista.dibujar(_fin(seleccion=-1))
        assert all(pygame.display.get_surface().get_at((r.left + 10, r.centery))[0] < 60 for r, _ in _zonas(vista))


# ---------------------------------------------------------------- casos extremos
def probar_el_puntaje_y_el_reporte_se_dibujan_dentro_de_su_panel():
    izquierdo, derecho = modulo_fin._PANEL_IZQUIERDO, modulo_fin._PANEL_DERECHO
    for panel in (izquierdo, derecho):
        assert not panel.colliderect(RECUADRO) and pygame.Rect(0, 0, ANCHO, ALTO).contains(panel)
    extremo = PuntajeDTO("W" * 16, "cripta-con-un-nombre-muy-largo-de-prueba-" * 3, "abc", 10 ** 15, 10 ** 15, 10 ** 15)
    reporte_extremo = replace(REPORTE, solicitudes_realizadas=10 ** 15, aciertos_cache=10 ** 15, fallos_cache=10 ** 15,
                              presupuesto=10 ** 15, offline=True)
    with VistaAbierta() as vista:
        vista.dibujar(_fin(puntaje=None, reporte=None))
        base = _copia()
        for puntaje in (PUNTAJE, extremo, PuntajeDTO("W" * 16, "", "", 0, 0, 0), None):
            for reporte in (REPORTE, reporte_extremo, replace(REPORTE, presupuesto=None, offline=True), None):
                vista.dibujar(_fin(puntaje=puntaje, reporte=reporte))
                # lo único distinto respecto de la pantalla vacía está dentro de alguno de los dos paneles
                for r in _rectangulos_distintos(base, _copia()):
                    assert izquierdo.contains(r) or derecho.contains(r), (puntaje, reporte, r)


def _rectangulos_distintos(a, b):
    """Los rectángulos (izquierdo y derecho, por separado) donde a y b difieren: sirve para saber que un texto no se sale."""
    resultado = []
    for banda in (pygame.Rect(0, 0, RECUADRO.left, ALTO), pygame.Rect(RECUADRO.right, 0, ANCHO - RECUADRO.right, ALTO)):
        cambio = _rectangulo_del_cambio(a.subsurface(banda), b.subsurface(banda))
        if cambio is not None:
            resultado.append(cambio.move(banda.topleft))
    return resultado


def probar_sin_puntaje_se_dibuja_el_texto_claro_y_el_aviso():
    aviso = "No se pudo guardar el puntaje: la carpeta no se puede escribir."
    with VistaAbierta() as vista:
        vista.dibujar(_fin(puntaje=None, aviso=aviso))
        con_texto = _copia()
        original = modulo_fin.lineas_de_puntaje
        modulo_fin.lineas_de_puntaje = lambda _puntaje: []                     # el mismo cuadro, sin el texto del puntaje
        try:
            vista.dibujar(_fin(puntaje=None, aviso=aviso))
            sin_texto = _copia()
        finally:
            modulo_fin.lineas_de_puntaje = original
        cambio = _rectangulo_del_cambio(con_texto, sin_texto)
        assert cambio is not None and modulo_fin._PANEL_IZQUIERDO.contains(cambio)    # el texto está en el panel
        vista.dibujar(_fin(puntaje=None, aviso=None))
        assert _rectangulo_del_cambio(con_texto, _copia()) is not None                # y el aviso también se dibuja
        caja, lineas = vista._menus.caja_del_aviso(_fin(puntaje=None, aviso=aviso), arriba=True)
        assert caja.bottom < RECUADRO.top and lineas == [aviso]                       # arriba, sin tocar el recuadro
        largo = _fin(puntaje=None, aviso="Aviso larguísimo. " * 80)
        caja, lineas = vista._menus.caja_del_aviso(largo, arriba=True)
        assert caja.bottom < RECUADRO.top and len(lineas) <= 2 and lineas[-1].endswith("...")


def probar_el_reporte_offline_se_indica_y_el_online_no():
    with VistaAbierta() as vista:
        vista.dibujar(_fin(reporte=replace(REPORTE, offline=False)))
        online = _copia()
        vista.dibujar(_fin(reporte=replace(REPORTE, offline=True)))
        cambio = _rectangulo_del_cambio(online, _copia())
        assert cambio is not None and modulo_fin._PANEL_DERECHO.contains(cambio)


# ---------------------------------------------------------------- victoria armada a mano
def probar_la_victoria_a_mano_sin_puntaje_y_con_presupuesto_desconocido():
    with VistaAbierta() as vista:
        pantalla = _fin("victoria", puntaje=None, reporte=replace(REPORTE, presupuesto=None),
                        aviso="No se pudo guardar el puntaje")
        assert pantalla.estado is None                                          # la Vista no necesita la partida
        vista.dibujar(pantalla)
        assert len(_zonas(vista)) == 3


# ---------------------------------------------------------------- de punta a punta (derrota real)
def _hasta_la_derrota(r):
    r.pulsar(ENTER)                                                             # Comenzar juego
    r.pulsar(ENTER)                                                             # la primera cripta
    r.escribir("Ana")
    r.pulsar(ENTER)                                                             # Aceptar
    r.perder()
    pantalla = r.dibujar()
    assert pantalla.pantalla == "derrota"
    return pantalla


def probar_derrota_real_se_dibuja_con_su_puntaje_y_su_reporte():
    vista = VistaPygame()
    vista.abrir()
    try:
        with Recorrido(vista) as r:
            pantalla = _hasta_la_derrota(r)
            assert pantalla.puntaje is not None and pantalla.reporte is not None
            assert pantalla.opciones == OPCIONES
            assert _bytes(pygame.display.get_surface(), RECUADRO) == _bytes(_fondo_original("fondo_derrota"), RECUADRO)
            ruido = _copia()
            vista.dibujar(replace(pantalla, puntaje=replace(pantalla.puntaje, nombre="Otro")))
            assert _rectangulo_del_cambio(ruido, _copia()) is not None          # el dato real se nota en el dibujo
    finally:
        vista.cerrar()


def probar_derrota_real_cada_boton_responde_a_un_clic_real():
    destinos = [("Jugar de nuevo", "criptas"), ("Ver puntajes", "puntajes"), ("Menú principal", "menu")]
    for indice, (texto, destino) in enumerate(destinos):
        vista = VistaPygame()
        vista.abrir()
        try:
            with Recorrido(vista) as r:
                pantalla = _hasta_la_derrota(r)
                assert pantalla.opciones[indice] == texto
                r.clic_en_texto(texto)                                          # por lo que dice el botón, no por su índice
                assert r.pantalla().pantalla == destino, (texto, r.pantalla().pantalla)
        finally:
            vista.cerrar()


def probar_derrota_real_el_raton_resalta_el_boton_y_el_teclado_sigue_funcionando():
    vista = VistaPygame()
    vista.abrir()
    try:
        with Recorrido(vista) as r:
            _hasta_la_derrota(r)
            r.pasar_el_raton_por_texto("Menú principal")
            assert r.pantalla().seleccion == 2
            r.dibujar()
            rectangulo = _zonas(vista)[2][0]
            assert pygame.display.get_surface().get_at((rectangulo.left + 10, rectangulo.centery))[0] > 120
            r.pulsar(ABAJO)
            r.pulsar(ENTER)
            assert r.pantalla().pantalla in ("criptas", "puntajes", "menu")
    finally:
        vista.cerrar()


if __name__ == "__main__":
    probar_el_texto_del_puntaje_trae_los_cinco_datos_y_el_caso_sin_puntaje()
    probar_el_texto_del_reporte_trae_lo_que_exige_el_enunciado_y_el_presupuesto_desconocido_es_una_raya()
    probar_cada_pantalla_usa_su_fondo_y_nada_se_dibuja_dentro_del_recuadro()
    probar_los_botones_no_tocan_el_recuadro_y_caben_en_la_pantalla()
    probar_el_boton_seleccionado_se_dibuja_resaltado()
    probar_el_puntaje_y_el_reporte_se_dibujan_dentro_de_su_panel()
    probar_sin_puntaje_se_dibuja_el_texto_claro_y_el_aviso()
    probar_el_reporte_offline_se_indica_y_el_online_no()
    probar_la_victoria_a_mano_sin_puntaje_y_con_presupuesto_desconocido()
    probar_derrota_real_se_dibuja_con_su_puntaje_y_su_reporte()
    probar_derrota_real_cada_boton_responde_a_un_clic_real()
    probar_derrota_real_el_raton_resalta_el_boton_y_el_teclado_sigue_funcionando()
    print("OK: todas las pruebas de las pantallas de victoria y derrota pasaron")
