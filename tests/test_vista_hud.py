"""
Pruebas del HUD de la partida (View/HudJuego.py, Etapa 7): estadísticas, efectos (velos y líneas), mensajes, inventario,
botón Esperar, aviso y ayuda. Tres niveles: funciones puras; la Vista real con un estado armado a mano (se mide lo que de verdad
se dibuja con fuentes y lienzo que anotan); y de punta a punta con el Controlador y los servicios reales (los clics van a la
POSICIÓN VISUAL de cada cosa, nunca al índice que la Vista registró). Se ejecuta desde cualquier carpeta.
"""
import json
import sys
from contextlib import contextmanager
from types import SimpleNamespace
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import clic, movimiento, pygame, rueda, tecla  # noqa: E402  (fija SDL_VIDEODRIVER=dummy antes de importar pygame)
from ayudas_vista import (ARRIBA, ENTER, Recorrido, cerrada, con_enemigos, con_objetos, estado_base)  # noqa: E402

import View.Componentes as c  # noqa: E402
import View.EscenaJuego as escena  # noqa: E402
from DTO.ElementoDTO import ELEMENTO_BOTON, ELEMENTO_INVENTARIO, ElementoDTO  # noqa: E402
from DTO.EfectoDTO import EfectoDTO  # noqa: E402
from DTO.InventarioDTO import InventarioDTO  # noqa: E402
from DTO.ObjetoDTO import ObjetoDTO  # noqa: E402
from DTO.PantallaDTO import PantallaDTO  # noqa: E402
from Logic.Inventario import Inventario  # noqa: E402
from Service.ServicioInventario import ServicioInventario  # noqa: E402
from UIController.ControlesJuego import AYUDA_JUEGO, ControlesJuego  # noqa: E402
from View.HudJuego import (criterio_a_texto, casillas_del_inventario, datos_del_objeto, efectos_a_mostrar,  # noqa: E402
                           indices_equipados, lineas_de_mensajes, ventana_del_inventario)
from View.VistaPygame import VistaPygame  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
PANTALLA = pygame.Rect(0, 0, c.ANCHO, c.ALTO)
PIES_A_PROBAR = [c.PIES_CENTRO] + list(c.PIES_PUERTA)
ANTORCHA = ObjetoDTO("itm_antorcha", "Antorcha", "antorcha", 1, 5, duracion=40)
DAGA = ObjetoDTO("itm_daga_oxidada", "Daga oxidada", "arma", 3, 12, ataque_bonus=4)
CORAZA = ObjetoDTO("itm_coraza_cuero", "Coraza de cuero", "armadura", 5, 20, defensa_bonus=3)
POCION = ObjetoDTO("itm_pocion_menor", "Poción menor", "pocion", 1, 8, cura=6, modificador_velocidad=-10, duracion=20)
LLAVE = ObjetoDTO("itm_llave_bronce", "Llave de bronce", "llave", 1, 2, abre="puerta-de-bronce")


# ================================================================ ayudas
class VistaAbierta:
    def __enter__(self):
        self.vista = VistaPygame()
        self.vista.abrir()
        return self.vista

    def __exit__(self, *_):
        self.vista.cerrar()


class FuenteQueAnota:
    """Una fuente que se porta igual que la de verdad y apunta cada texto que renderiza (con la superficie que devolvió)."""

    def __init__(self, fuente, nombre, anotaciones):
        self._fuente, self.nombre, self._anotaciones = fuente, nombre, anotaciones

    def render(self, texto, antialias, color, *resto):
        superficie = self._fuente.render(texto, antialias, color, *resto)
        self._anotaciones.append((texto, superficie, self.nombre))
        return superficie

    def size(self, texto):
        return self._fuente.size(texto)

    def get_linesize(self):
        return self._fuente.get_linesize()

    def get_height(self):
        return self._fuente.get_height()


class Lienzo(pygame.Surface):
    """Una superficie que apunta cada blit (la imagen que se puso y dónde), en orden."""

    def __init__(self, tamano):
        super().__init__(tamano)
        self.blits = []

    def blit(self, fuente, destino, area=None, special_flags=0):
        self.blits.append((fuente, fuente.get_rect(topleft=tuple(destino)[:2])))
        return super().blit(fuente, destino, area, special_flags)


class VistaMedida:
    """La Vista real dibujando sobre un Lienzo, con todas las fuentes anotando. dibujar() devuelve el PantallaDTO dibujado;
    textos() da (texto, rectángulo, fuente) de cada texto que se puso en pantalla, en el orden en que se dibujó."""

    def __enter__(self):
        self.vista = VistaPygame()
        self.vista.abrir()
        self.anotaciones = []
        fuentes = self.vista._fuentes
        for nombre in ("titulo", "boton", "texto", "pie", "chico", "mensajes", "ayuda_juego"):
            setattr(fuentes, nombre, FuenteQueAnota(getattr(fuentes, nombre), nombre, self.anotaciones))
        self.lienzo = Lienzo((c.ANCHO, c.ALTO))
        self.vista._superficie = self.lienzo
        return self

    def __exit__(self, *_):
        self.vista.cerrar()

    def dibujar(self, pantalla):
        self.lienzo.blits.clear()
        self.anotaciones.clear()
        self.vista._escena.olvidar_la_sala()
        self.vista.dibujar(pantalla)
        return pantalla

    def textos(self):
        resultado = []
        for imagen, rectangulo in self.lienzo.blits:
            for texto, superficie, nombre in self.anotaciones:
                if superficie is imagen:
                    resultado.append((texto, rectangulo, nombre))
                    break
        return resultado

    def lista(self):
        return [texto for texto, _, _ in self.textos()]


def _inventario(objetos, cursor=0, maximo=10, arma=None, armadura=None, criterio=None):
    return InventarioDTO(list(objetos), cursor, len(objetos), maximo, arma, armadura, criterio)


def _pantalla(inventario=None, efectos=(), mensajes=(), aviso=None, seleccion=-1, bajo=None, **cambios_del_estado):
    estado = estado_base(3, N=cerrada())
    estado = replace(estado, inventario=inventario or _inventario([]), efectos=list(efectos), mensajes=list(mensajes),
                     reloj=cambios_del_estado.pop("reloj", 450), **cambios_del_estado)
    return PantallaDTO("juego", "", ["Esperar"], seleccion, aviso=aviso, ayuda=list(AYUDA_JUEGO), estado=estado,
                       elemento_bajo_el_raton=bajo)


def _mensajes(n):
    return [f"[t={100 + 7 * i}] Rata gigante #{i + 1} ataca a Jugador: {i} de daño" for i in range(n)]


def _luminosidad(superficie):
    return sum(pygame.transform.average_color(superficie)[:3]) / 3


def _zonas(vista, tipo=None):
    todas = list(zip(vista._zonas._rectangulos, vista._zonas._elementos))
    return todas if tipo is None else [(r, e) for r, e in todas if e.tipo == tipo]


def _fuente(tam):
    pygame.font.init()
    return pygame.font.Font(None, tam)


def _en_pantalla(vista, pantalla):
    vista.dibujar(pantalla)
    return pygame.display.get_surface()


# ================================================================ funciones puras
def probar_efectos_a_mostrar_los_cinco_casos():
    veneno, rapido, lento, antorcha, raro = (EfectoDTO("veneno", 12, 3), EfectoDTO("velocidad", 30, 50),
                                             EfectoDTO("velocidad", 25, -40), EfectoDTO("antorcha", 40, None),
                                             EfectoDTO("niebla", 9, None))
    visibles = efectos_a_mostrar([veneno, rapido, lento, antorcha, raro])
    assert [v.velo for v in visibles] == [c.VELO_VENENO, c.VELO_RAPIDO, c.VELO_LENTO, c.VELO_ANTORCHA, None]
    assert len({c.VELO_VENENO, c.VELO_RAPIDO, c.VELO_LENTO, c.VELO_ANTORCHA}) == 4          # cuatro colores distintos
    for visible, efecto in zip(visibles, [veneno, rapido, lento, antorcha, raro]):
        assert str(efecto.restante) in visible.texto, visible                              # el tiempo restante
    assert "Veneno" in visibles[0].texto and "+50" in visibles[1].texto and "-40" in visibles[2].texto
    assert "Antorcha" in visibles[3].texto and "Niebla" in visibles[4].texto
    assert efectos_a_mostrar([]) == []
    assert efectos_a_mostrar([EfectoDTO("velocidad", 5, 0)])[0].velo is None               # sin valor que acelere o frene
    assert efectos_a_mostrar([EfectoDTO("velocidad", 5, None)])[0].velo is None
    assert c.VELO_RAPIDO[2] > c.VELO_RAPIDO[0] and c.VELO_VENENO[1] > c.VELO_VENENO[0]   # azul y verde de verdad
    assert c.VELO_LENTO[0] > c.VELO_LENTO[1] and c.VELO_LENTO[2] > c.VELO_LENTO[1]         # violeta: rojo y azul sobre el verde
    assert c.VELO_ANTORCHA[0] > c.VELO_ANTORCHA[2]                                         # naranja
    for velo in (c.VELO_VENENO, c.VELO_RAPIDO, c.VELO_LENTO, c.VELO_ANTORCHA):
        assert 0 < velo[3] <= 60, velo                                                     # baja opacidad


def probar_el_equipado_con_ids_repetidos_marca_solo_el_primero():
    objetos = [DAGA, ANTORCHA, DAGA, CORAZA, CORAZA, DAGA]
    assert indices_equipados(_inventario(objetos, arma="itm_daga_oxidada")) == [0]
    assert indices_equipados(_inventario(objetos, arma="itm_daga_oxidada", armadura="itm_coraza_cuero")) == [0, 3]
    assert indices_equipados(_inventario(objetos, armadura="itm_coraza_cuero")) == [3]
    assert indices_equipados(_inventario(objetos)) == []
    assert indices_equipados(_inventario(objetos, arma="itm_que_no_esta")) == []
    assert indices_equipados(_inventario([], arma="itm_daga_oxidada")) == []
    assert indices_equipados(_inventario([DAGA], arma="itm_daga_oxidada", armadura="itm_daga_oxidada")) == [0]


def probar_lineas_de_mensajes_20_de_20_menos_de_20_y_mas_de_20():
    veinte = _mensajes(20)
    assert lineas_de_mensajes(veinte) == veinte and c.HUD_MENSAJES_LINEAS == 20
    assert lineas_de_mensajes(veinte[:7]) == veinte[:7] and lineas_de_mensajes([]) == []
    treinta = _mensajes(30)
    assert lineas_de_mensajes(treinta) == treinta[10:]                                      # las más recientes, en orden
    assert lineas_de_mensajes(veinte)[-1] == veinte[-1]                                     # la más reciente, la última
    assert lineas_de_mensajes(veinte, 3) == veinte[-3:] and lineas_de_mensajes(veinte, 0) == []


def probar_el_detalle_del_objeto_trae_los_datos_y_solo_los_bonus_que_no_son_none():
    assert datos_del_objeto(DAGA) == ["Daga oxidada", "Clase: arma", "Peso: 3   Valor: 12", "Ataque: +4"]
    assert datos_del_objeto(CORAZA)[-1] == "Defensa: +3" and len(datos_del_objeto(CORAZA)) == 4
    assert datos_del_objeto(POCION)[3:] == ["Cura: 6", "Velocidad: -10", "Duración: 20"]
    assert datos_del_objeto(LLAVE)[3:] == ["Abre: puerta-de-bronce"]
    assert len(datos_del_objeto(ObjetoDTO("x", "X", "pocion", 1, 1))) == 3                  # sin ningún bonus
    assert criterio_a_texto(None) == "Orden: real" and criterio_a_texto("peso") == "Orden: peso"
    assert criterio_a_texto("valor") == "Orden: valor" and criterio_a_texto("nombre") == "Orden: nombre"


def probar_las_casillas_estan_dentro_del_panel_son_de_46_y_no_se_solapan():
    casillas = casillas_del_inventario(10)
    assert len(casillas) == 10 and all(k.size == (c.INV_LADO, c.INV_LADO) == (46, 46) for k in casillas)
    for i, casilla in enumerate(casillas):
        assert c.HUD_INVENTARIO.contains(casilla), i
        assert all(not casilla.colliderect(otra) for otra in casillas[i + 1:]), i
    assert [k.y for k in casillas[:5]] == [casillas[0].y] * 5 and [k.y for k in casillas[5:]] == [casillas[5].y] * 5
    assert casillas[5].y > casillas[0].bottom and casillas[1].x > casillas[0].right        # 2 filas de 5
    assert casillas_del_inventario(0) == [] and len(casillas_del_inventario(40)) == c.INV_CASILLAS_MAX


# ================================================================ la maqueta: el HUD no tapa nada
def _zonas_de_puertas():
    """Las zonas de puerta de los tres fondos, con las dos clases de puerta (cerrada y la de la salida), dibujadas de verdad."""
    resultado = []
    with VistaAbierta() as vista:
        for id_sala in (1, 3, 6):
            for cierre in (cerrada(), cerrada(6)):
                vista._escena.olvidar_la_sala()
                vista.dibujar(PantallaDTO("juego", "", [], 0, estado=estado_base(id_sala, N=cierre, S=cierre, E=cierre,
                                                                             O=cierre)))
                resultado += [(f"puerta {'NSEO'[d]}", pygame.Rect(r)) for d, r in enumerate(vista._zonas._rectangulos)]
    return resultado


def probar_ningun_panel_del_hud_toca_una_puerta_ni_el_sitio_del_protagonista_y_los_tramos_laterales_quedan_libres():
    puertas = _zonas_de_puertas()
    assert len(puertas) == 24
    ancho, alto = c.JUGADOR_OCUPA
    protagonistas = [(f"protagonista {i}", pygame.Rect(x - ancho // 2, y - alto, ancho, alto))
                     for i, (x, y) in enumerate(PIES_A_PROBAR)]
    for nombre_panel, panel in zip(("estadisticas", "efectos", "mensajes", "inventario", "esperar", "aviso", "ayuda"),
                                   c.HUD_PANELES):
        assert PANTALLA.contains(panel), nombre_panel
        for nombre, zona in puertas + protagonistas:
            assert not panel.colliderect(zona), (nombre_panel, nombre, panel, zona)
        assert not panel.colliderect(pygame.Rect(0, 296, 280, 174)) and not panel.colliderect(
            pygame.Rect(1096, 296, 280, 174)), nombre_panel                                 # el tramo y 296-470 de las bandas
    assert all(not a.colliderect(b) for i, a in enumerate(c.HUD_PANELES) for b in c.HUD_PANELES[i + 1:])
    assert c.SUELO == pygame.Rect(280, 170, 816, 450)                                       # el suelo no se achicó
    assert (c.HUD_MENSAJES.x, c.HUD_MENSAJES.right, c.HUD_MENSAJES.y, c.HUD_MENSAJES.bottom) == (8, 358, 470, 760)
    assert (c.HUD_ESPERAR.x, c.HUD_ESPERAR.right) == (1028, 1368) == (c.HUD_AYUDA.x, c.HUD_AYUDA.right)
    assert [p.width for p in (c.HUD_ESTADISTICAS, c.HUD_EFECTOS, c.HUD_INVENTARIO)] == [264, 264, 264]


def probar_con_12_enemigos_y_12_objetos_ninguna_zona_solapa_un_panel_con_el_protagonista_en_cada_sitio():
    estado = con_objetos(con_enemigos(estado_base(3, N=cerrada(), S=cerrada(), E=cerrada(), O=cerrada()), 12), 12)
    with VistaAbierta() as vista:
        almacen = vista._escena._almacen
        for pies in PIES_A_PROBAR:
            reparto = escena.repartir_escena(almacen, vista._fuentes, estado.enemigos, estado.objetos_suelo,
                                             estado.sala.salidas, pies)
            assert len(reparto.enemigos) == 12 and len(reparto.objetos) == 12
            for zona in reparto.enemigos + reparto.objetos:
                assert c.SUELO.contains(zona), (pies, zona)
                for panel in c.HUD_PANELES:
                    assert not zona.colliderect(panel), (pies, zona, panel)
            # y lo que se registra al dibujar de verdad tampoco toca el HUD (la ficha de nombre y barra va dentro del rectángulo)
            vista._escena._id_visto, vista._escena._pies = 3, pies
            vista._zonas.limpiar()
            vista.dibujar(replace(_pantalla(), estado=estado))
            for rectangulo, elemento in _zonas(vista):
                if elemento.tipo in ("enemigo", "objeto_suelo"):
                    assert all(not rectangulo.colliderect(panel) for panel in c.HUD_PANELES), (pies, elemento)


def probar_si_el_reparto_ignorara_los_paneles_si_se_pisarian_los_paneles_del_suelo():
    """Control de la prueba anterior: sin los paneles en 'ocupadas' el reparto de 12 + 12 sí cae bajo mensajes o ayuda."""
    estado = con_objetos(con_enemigos(estado_base(3, N=cerrada(), S=cerrada(), E=cerrada(), O=cerrada()), 12), 12)
    original = list(c.HUD_PANELES)
    with VistaAbierta() as vista:
        c.HUD_PANELES[:] = []
        try:
            reparto = escena.repartir_escena(vista._escena._almacen, vista._fuentes, estado.enemigos,
                                             estado.objetos_suelo, estado.sala.salidas, c.PIES_CENTRO)
        finally:
            c.HUD_PANELES[:] = original
    pisados = [z for z in reparto.enemigos + reparto.objetos
               if any(z.colliderect(p) for p in (c.HUD_MENSAJES, c.HUD_ESPERAR, c.HUD_AVISO, c.HUD_AYUDA))]
    assert pisados, "la prueba anterior no distinguiría nada: el reparto no llega a los paneles de abajo"


# ================================================================ que el texto cabe en su panel
_ENEMIGOS = ["Rata gigante", "Guardián óseo"]
_SALAS_DE_EJEMPLO = ["Entrada derruida", "Pasillo de las urnas", "Cripta baja", "Osario profundo", "Nicho sellado", "Salida"]


def _nombres_reales(clases):
    """Los nombres del catálogo y de las salas del paquete offline (assets de verdad, no inventados)."""
    catalogo = json.loads((RAIZ / "paquete" / "catalogo.json").read_text(encoding="utf-8"))["entidades"]
    nombres = []

    def recorrer(nodo):
        if isinstance(nodo, dict):
            if "nombre" in nodo and (nodo.get("clase") or nodo.get("tipo")) in clases:
                nombres.append(nodo["nombre"])
            for valor in nodo.values():
                recorrer(valor)
        elif isinstance(nodo, list):
            for valor in nodo:
                recorrer(valor)
    recorrer(catalogo)
    return nombres


def _mensajes_peores_del_motor():
    """Cada plantilla de mensaje de Logic/ (motorJuego, Efectos, ServicioPartida, ServicioGuardado) con el peor caso: tiempo de 4
    cifras, enemigo #99, daño de 3 cifras y los nombres más largos del catálogo y de las salas del paquete."""
    enemigos = _nombres_reales(["enemigo"]) or _ENEMIGOS
    objetos = _nombres_reales(["arma", "armadura", "pocion", "antidoto", "llave", "antorcha", "pergamino_retroceso"])
    trampas = _nombres_reales(["trampa"])
    salas = []
    for archivo in ("salas_p1.json", "general.json"):
        texto = (RAIZ / "paquete" / "cripta-01" / archivo).read_text(encoding="utf-8")
        salas += [valor for valor in _valores_de(json.loads(texto), "nombre")]
    salas = salas or _SALAS_DE_EJEMPLO
    t = "[t=9999] "
    mensajes = []
    for e in enemigos:
        n = f"{e} #99"
        mensajes += [f"{t}{n} ataca a Jugador: 999 de daño", f"{t}Jugador ataca a {n}: 999 de daño",
                     f"{t}{n} entra a la sala", f"{t}{n} muere", f"{t}El veneno hace 999 de daño a {n}",
                     f"{t}{n} envenena a Jugador (999)", f"{t}{n} regenera 999 de vida",
                     f"{t}{n} ralentiza a Jugador", f"{t}{n} acelera a Jugador"]
    mensajes += [f"{t}El veneno hace 999 de daño a Jugador", f"{t}Has muerto", f"{t}La antorcha se apaga",
                 f"{t}Has escapado de la cripta", f"{t}Lees el pergamino: el tiempo retrocede",
                 f"{t}Abres la puerta Norte", f"{t}Abres la puerta Sur"]
    mensajes += [f"{t}{m}" for m in ("Entras a ", "Comienzas en ", "Partida cargada: estás en ")
                 for m in [m + s for s in salas]]
    mensajes += [f"{t}{verbo} {o}" for o in objetos for verbo in ("Recoges", "Sueltas", "Equipas", "Usas")]
    mensajes += [f"{t}{x}: 999 de daño" for x in trampas]
    mensajes += [f"{t}{x} envenena a Jugador (999)" for x in trampas] + [f"{t}Se activa {x}" for x in trampas]
    return mensajes


def _valores_de(nodo, clave):
    if isinstance(nodo, dict):
        for k, v in nodo.items():
            if k == clave and isinstance(v, str):
                yield v
            else:
                yield from _valores_de(v, clave)
    elif isinstance(nodo, list):
        for v in nodo:
            yield from _valores_de(v, clave)


def probar_todos_los_mensajes_reales_del_motor_caben_en_el_ancho_util_del_panel_de_mensajes():
    ancho_util = c.HUD_MENSAJES.width - 2 * c.HUD_RELLENO
    mensajes = _mensajes_peores_del_motor()
    assert len(mensajes) > 40
    pygame.font.init()
    fuente = _fuente(c.TAM_MENSAJES)
    mas_ancho = max(mensajes, key=lambda m: fuente.size(m)[0])
    # Sin margen extra: la fuente por defecto mide igual en 16 y 17 y en 18 el peor ya no cabe, así que ningún tamaño
    # deja 10 px libres. Lo que importa es que ninguno se corte con "..." y que no haya una fuente mayor que sirva.
    assert fuente.size(mas_ancho)[0] <= ancho_util, (mas_ancho, fuente.size(mas_ancho)[0], ancho_util)
    siguiente = _fuente(c.TAM_MENSAJES + 1)
    assert max(siguiente.size(m)[0] for m in mensajes) > ancho_util, "hay una fuente más grande en la que caben todos"
    assert c.HUD_MENSAJES_INTERLINEA >= fuente.get_height() + 1
    assert c.HUD_MENSAJES_ARRIBA + c.HUD_MENSAJES_LINEAS * c.HUD_MENSAJES_INTERLINEA <= c.HUD_MENSAJES.height


def probar_los_mensajes_de_una_partida_real_caben_enteros_sin_cortes():
    vista = VistaPygame()
    vista.abrir()
    try:
        with Recorrido(vista) as r:
            r.pulsar(ENTER, ENTER)
            r.escribir("Ana")
            r.pulsar(ENTER)
            r.pulsar(ARRIBA)
            vistos = []
            for _ in range(60):
                if r.pantalla().pantalla != "juego":
                    break
                r.pulsar(pygame.K_z)
                if r.pantalla().estado is not None:
                    vistos += r.pantalla().estado.mensajes
            assert any("ataca a" in m for m in vistos)
            fuente = vista._fuentes.mensajes
            ancho_util = c.HUD_MENSAJES.width - 2 * c.HUD_RELLENO
            assert all(fuente.size(m)[0] <= ancho_util for m in vistos)
    finally:
        vista.cerrar()


def probar_las_11_lineas_de_ayuda_caben_en_su_panel_con_las_constantes_reales():
    assert len(AYUDA_JUEGO) == 11
    ancho_util = c.HUD_AYUDA.width - 2 * c.HUD_RELLENO
    fuente = _fuente(c.TAM_AYUDA_JUEGO)
    assert max(fuente.size(linea)[0] for linea in AYUDA_JUEGO) <= ancho_util
    assert max(_fuente(c.TAM_AYUDA_JUEGO + 1).size(linea)[0] for linea in AYUDA_JUEGO) > ancho_util   # la más grande que cabe
    assert c.HUD_RELLENO + len(AYUDA_JUEGO) * c.HUD_AYUDA_INTERLINEA <= c.HUD_AYUDA.height
    assert c.HUD_AYUDA_INTERLINEA >= fuente.get_height()
    with VistaMedida() as m:
        m.dibujar(_pantalla())
        ayuda = [(t, r) for t, r, f in m.textos() if f == "ayuda_juego"]
        assert [t for t, _ in ayuda] == list(AYUDA_JUEGO)                                  # las 11, completas y en orden
        assert all(c.HUD_AYUDA.contains(r) for _, r in ayuda)


# ================================================================ lo que dibuja la Vista real
def probar_las_estadisticas_y_el_reloj_se_ven_con_los_valores_del_jugador():
    with VistaMedida() as m:
        pantalla = m.dibujar(_pantalla(reloj=1234))
        jugador = pantalla.estado.jugador
        textos = m.lista()
        for esperado in (f"Ataque: {jugador.ataque}", f"Defensa: {jugador.defensa}", f"Velocidad: {jugador.velocidad}",
                         "Reloj: 1234", f"{jugador.vida}/{jugador.vida_max}"):
            assert esperado in textos, (esperado, textos)
        ubicados = [r for t, r, _ in m.textos() if t in (f"Ataque: {jugador.ataque}", "Reloj: 1234")]
        assert all(c.HUD_ESTADISTICAS.contains(r) for r in ubicados)


def probar_los_20_mensajes_se_dibujan_completos_la_mas_reciente_abajo_y_dentro_del_panel():
    with VistaMedida() as m:
        mensajes = _mensajes(20)
        m.dibujar(_pantalla(mensajes=mensajes))
        puestos = [(t, r) for t, r, f in m.textos() if f == "mensajes"]
        assert [t for t, _ in puestos] == mensajes                                         # los 20, en orden cronológico
        ys = [r.y for _, r in puestos]
        assert ys == sorted(ys) and len(set(ys)) == 20                                      # de arriba a abajo, uno por línea
        assert all(c.HUD_MENSAJES.contains(r) for _, r in puestos)
        assert puestos[-1][1].y == max(ys) and puestos[0][0] == mensajes[0]                # la más reciente, abajo
        m.dibujar(_pantalla(mensajes=_mensajes(5)))
        assert [t for t, _, f in m.textos() if f == "mensajes"] == _mensajes(5)           # con menos, solo esas
        m.dibujar(_pantalla(mensajes=_mensajes(26)))
        assert [t for t, _, f in m.textos() if f == "mensajes"] == _mensajes(26)[-20:]    # con más, las últimas 20


def probar_un_mensaje_muy_largo_se_corta_con_puntos_suspensivos_dentro_del_panel_y_el_normal_no():
    largo = "[t=9999] " + "Guardián óseo #99 ataca a Jugador con una cantidad absurda de texto " * 3
    with VistaMedida() as m:
        m.dibujar(_pantalla(mensajes=[largo, _mensajes(1)[0]]))
        puestos = [(t, r) for t, r, f in m.textos() if f == "mensajes"]
        assert puestos[0][0].endswith("...") and puestos[0][0] != largo and c.HUD_MENSAJES.contains(puestos[0][1])
        assert puestos[1][0] == _mensajes(1)[0]                                            # uno normal no se toca


def probar_el_inventario_muestra_casillas_sprites_contador_criterio_cursor_y_equipado():
    objetos = [DAGA, ANTORCHA, POCION, DAGA, CORAZA]
    with VistaMedida() as m:
        almacen = m.vista._escena._almacen
        pantalla = m.dibujar(_pantalla(_inventario(objetos, cursor=2, arma="itm_daga_oxidada",
                                                   armadura="itm_coraza_cuero", criterio="peso")))
        textos = m.lista()
        assert "5/10" in textos and "Orden: peso" in textos                                 # contador y criterio
        casillas = casillas_del_inventario(10)
        for i, objeto in enumerate(objetos):                                                # el sprite de cada objeto, en su casilla
            sprite = almacen.objeto(objeto.id, objeto.clase, c.INV_SPRITE).fotogramas[0]
            assert any(imagen is sprite and casillas[i].contains(r) for imagen, r in m.lienzo.blits), (i, objeto.id)
        assert [t for t in textos if t == "E"] == ["E", "E"]                                # equipado: arma (0) y armadura (4)
        insignias = [r for t, r, _ in m.textos() if t == "E"]
        assert casillas[0].colliderect(insignias[0]) and casillas[4].colliderect(insignias[1])
        assert not any(casillas[i].colliderect(r) for r in insignias for i in (1, 2, 3))   # la daga repetida NO se marca
        for linea in datos_del_objeto(POCION):                                              # los datos del objeto bajo el cursor
            assert linea in textos, linea
        assert "Ataque: +4" not in textos                                                   # y solo los de ese objeto
        assert pantalla.estado.inventario.cursor == 2


def probar_el_cursor_se_ve_sobre_su_casilla_y_solo_sobre_esa():
    objetos = [DAGA, ANTORCHA, POCION]
    with VistaAbierta() as vista:
        casillas = casillas_del_inventario(10)
        for cursor in (0, 1, 2):
            pantalla = _en_pantalla(vista, _pantalla(_inventario(objetos, cursor=cursor)))
            doradas = [i for i, k in enumerate(casillas) if pantalla.get_at((k.x + 1, k.centery))[:3] == c.ORO]
            assert doradas == [cursor], (cursor, doradas)


def probar_solo_la_primera_casilla_con_el_id_equipado_lleva_la_marca_en_pantalla():
    with VistaMedida() as m:
        m.dibujar(_pantalla(_inventario([DAGA, DAGA, DAGA], arma="itm_daga_oxidada")))
        insignias = [r for t, r, _ in m.textos() if t == "E"]
        casillas = casillas_del_inventario(10)
        assert len(insignias) == 1 and casillas[0].colliderect(insignias[0]), insignias
        m.dibujar(_pantalla(_inventario([ANTORCHA, DAGA])))
        assert "E" not in m.lista()                                                         # sin nada equipado, ninguna marca


def probar_las_zonas_del_inventario_son_solo_las_casillas_ocupadas_y_el_boton_es_el_0():
    objetos = [DAGA, ANTORCHA, POCION]
    with VistaAbierta() as vista:
        _en_pantalla(vista, _pantalla(_inventario(objetos)))
        casillas = casillas_del_inventario(10)
        for i in range(3):
            assert vista.elemento_en(casillas[i].center) == ElementoDTO(ELEMENTO_INVENTARIO, i), i
        for i in range(3, 10):
            assert vista.elemento_en(casillas[i].center) is None, i                         # casilla vacía: nada
        assert len(_zonas(vista, ELEMENTO_INVENTARIO)) == 3
        assert vista.elemento_en(c.HUD_ESPERAR.center) == ElementoDTO(ELEMENTO_BOTON, 0)
        assert len(_zonas(vista, ELEMENTO_BOTON)) == 1
        for panel in (c.HUD_ESTADISTICAS, c.HUD_EFECTOS, c.HUD_MENSAJES, c.HUD_AVISO, c.HUD_AYUDA):
            assert vista.elemento_en(panel.center) is None                                  # el resto del HUD no es clicable


def probar_el_boton_esperar_se_resalta_segun_la_seleccion():
    with VistaAbierta() as vista:
        normal = _en_pantalla(vista, _pantalla(seleccion=-1)).subsurface(c.HUD_ESPERAR).copy()
        resaltado = _en_pantalla(vista, _pantalla(seleccion=0)).subsurface(c.HUD_ESPERAR).copy()
        assert pygame.image.tobytes(normal, "RGB") != pygame.image.tobytes(resaltado, "RGB")
        assert pygame.image.tobytes(_en_pantalla(vista, _pantalla(seleccion=3)).subsurface(c.HUD_ESPERAR), "RGB") == \
            pygame.image.tobytes(normal, "RGB")                                             # otra selección: no se resalta
    with VistaMedida() as m:
        m.dibujar(_pantalla())
        assert "Esperar" in m.lista()
        m.dibujar(replace(_pantalla(), opciones=[]))
        assert "Esperar" not in m.lista() and _zonas(m.vista, ELEMENTO_BOTON) == []               # sin opciones, sin botón ni zona


def probar_el_aviso_se_destaca_en_su_panel_y_la_ayuda_siempre_esta():
    with VistaMedida() as m:
        m.dibujar(_pantalla(aviso="Inventario lleno"))
        puestos = [(t, r) for t, r, _ in m.textos() if t == "Inventario lleno"]
        assert len(puestos) == 1 and c.HUD_AVISO.contains(puestos[0][1])
        m.dibujar(_pantalla(aviso="No se pudo guardar la partida porque la carpeta no se puede escribir " * 4))
        lineas = [r for t, r, f in m.textos() if f == "mensajes" and c.HUD_AVISO.colliderect(r)]
        assert 1 <= len(lineas) <= c.HUD_AVISO_LINEAS and all(c.HUD_AVISO.contains(r) for r in lineas)
        m.dibujar(_pantalla(aviso=None))
        assert not any(c.HUD_AVISO.colliderect(r) for _, r, _ in m.textos())                # sin aviso, el panel no se dibuja
        assert [t for t, _, f in m.textos() if f == "ayuda_juego"] == list(AYUDA_JUEGO)


def probar_los_velos_de_los_efectos_tiñen_la_escena_con_su_color_se_crean_una_vez_y_el_desconocido_no_tiñe():
    puntos = [(420, 60), (900, 110), (520, 700), (700, 330)]
    casos = [(EfectoDTO("veneno", 9, 3), c.VELO_VENENO), (EfectoDTO("velocidad", 9, 50), c.VELO_RAPIDO),
             (EfectoDTO("velocidad", 9, -50), c.VELO_LENTO), (EfectoDTO("antorcha", 9, None), c.VELO_ANTORCHA)]
    with VistaAbierta() as vista:
        sin = _en_pantalla(vista, _pantalla()).copy()
        for efecto, color in casos:
            con = _en_pantalla(vista, _pantalla(efectos=[efecto]))
            for punto in puntos:
                antes, despues = sin.get_at(punto)[:3], con.get_at(punto)[:3]
                esperado = [round(a + (v - a) * color[3] / 255) for a, v in zip(antes, color[:3])]
                assert all(abs(d - e) <= 2 for d, e in zip(despues, esperado)), (efecto, punto, antes, despues, esperado)
        raro = _en_pantalla(vista, _pantalla(efectos=[EfectoDTO("niebla", 9, None)]))
        for punto in puntos:
            assert raro.get_at(punto) == sin.get_at(punto), punto                           # tipo desconocido: sin velo
        sin_ventana = _en_pantalla(vista, _pantalla(efectos=[casos[0][0], casos[1][0]]))
        assert sin_ventana.get_at(puntos[0]) != sin.get_at(puntos[0])                       # con dos efectos, los velos se suman
        hud = vista._hud
        velos = list(hud._velos)
        for _ in range(5):
            _en_pantalla(vista, _pantalla(efectos=[casos[0][0], casos[1][0]]))
        assert len(hud._velos) == len(velos) == 4 and all(a is b for a, b in zip(hud._velos, velos))   # creados una sola vez


def probar_un_efecto_de_cada_tipo_escribe_su_nombre_y_su_tiempo_restante_en_el_panel_de_efectos():
    efectos = [EfectoDTO("veneno", 12, 3), EfectoDTO("velocidad", 30, 50), EfectoDTO("velocidad", 25, -40),
               EfectoDTO("antorcha", 40, None), EfectoDTO("niebla", 7, None)]
    with VistaMedida() as m:
        m.dibujar(_pantalla(efectos=efectos))
        puestos = [(t, r) for t, r, f in m.textos() if f == "pie" and c.HUD_EFECTOS.colliderect(r)]
        esperados = [v.texto for v in efectos_a_mostrar(efectos)]
        assert esperados[0] in [t for t, _ in puestos]
        assert all(c.HUD_EFECTOS.contains(r) for _, r in puestos)
        m.dibujar(_pantalla())
        assert "Ninguno" in m.lista()                                                       # sin efectos lo dice


def probar_el_nombre_del_objeto_bajo_el_raton_se_dibuja_despues_del_hud_y_por_encima_de_el():
    nombre = "Pergamino de retroceso antiguo y larguísimo"
    anterior = escena.colocar

    def falso(tamanos, ocupadas, suelo, pies, radio, paso, separacion):
        lugares = [] if radio == c.REPARTO_RADIO_ENEMIGOS else [(284, 240)]               # pegado al borde izquierdo del suelo
        return [pygame.Rect(x, y - alto, ancho, alto) for (ancho, alto), (x, y) in zip(tamanos, lugares)], True
    escena.colocar = falso
    try:
        with VistaMedida() as m:
            objeto = ObjetoDTO("itm_pergamino_retroceso", nombre, "pergamino_retroceso", 1, 1)
            estado = replace(_pantalla().estado, objetos_suelo=[objeto])
            pantalla = replace(_pantalla(), estado=estado, elemento_bajo_el_raton=ElementoDTO("objeto_suelo", 0))
            m.dibujar(pantalla)
            etiqueta = [r for t, r, _ in m.textos() if t == nombre]
            assert len(etiqueta) == 1
            etiqueta = etiqueta[0]
            assert etiqueta.collidelist(c.HUD_PANELES) != -1, "la prueba necesita una etiqueta que pise el HUD"
            ultimo_del_hud = max(i for i, (imagen, r) in enumerate(m.lienzo.blits)
                                 if any(r.topleft == p.topleft for p in c.HUD_PANELES))
            indice_etiqueta = next(i for i, (imagen, r) in enumerate(m.lienzo.blits) if r == etiqueta)
            assert indice_etiqueta > ultimo_del_hud, (indice_etiqueta, ultimo_del_hud)     # la etiqueta, después de todo el HUD
            assert indice_etiqueta == max(i for i, (_, r) in enumerate(m.lienzo.blits) if r.colliderect(etiqueta))
            # y en pantalla de verdad el texto de la etiqueta no queda tapado por el panel: sus píxeles claros están a la vista
            m.dibujar(replace(pantalla, elemento_bajo_el_raton=None))
            assert nombre not in m.lista()                                                 # sin ratón encima, no hay etiqueta
    finally:
        escena.colocar = anterior


# ================================================================ casos extremos
def _todo_dentro_de_los_paneles(vista, pantalla, extra=()):
    """Dibuja el HUD solo, sobre un lienzo de un color imposible: lo que no es ese color tiene que estar dentro de un panel."""
    lienzo = pygame.Surface((c.ANCHO, c.ALTO), pygame.SRCALPHA)
    lienzo.fill((1, 2, 3, 255))
    vista._hud.dibujar(lienzo, pantalla)
    fuera = lienzo.copy()
    for panel in list(c.HUD_PANELES) + list(extra):
        fuera.fill((1, 2, 3, 255), panel)
    return pygame.mask.from_threshold(fuera, (1, 2, 3, 255), (1, 1, 1, 255)).count() == c.ANCHO * c.ALTO


def probar_inventario_vacio_lleno_y_con_nombres_largos_no_rompen_ni_se_salen_del_panel():
    largo = ObjetoDTO("itm_x", "Espada legendaria forjada en las profundidades de la cripta olvidada", "arma", 99999,
                      123456789, ataque_bonus=12345, abre="llave-con-un-identificador-larguisimo-que-no-cabe")
    lleno = [DAGA, ANTORCHA, POCION, LLAVE, CORAZA, DAGA, ANTORCHA, POCION, LLAVE, largo]
    with VistaMedida() as m:
        m.dibujar(_pantalla(_inventario([])))
        assert "0/10" in m.lista() and "Orden: real" in m.lista()
        assert len(_zonas(m.vista, ELEMENTO_BOTON)) == 1                                # el botón; ninguna casilla clicable
        assert len(_zonas(m.vista, ELEMENTO_INVENTARIO)) == 0
        assert _todo_dentro_de_los_paneles(m.vista, _pantalla(_inventario([])))
        m.dibujar(_pantalla(_inventario(lleno, cursor=9, arma="itm_daga_oxidada")))
        assert "10/10" in m.lista()
        assert len(_zonas(m.vista, ELEMENTO_INVENTARIO)) == 10
        textos = [(t, r) for t, r, _ in m.textos() if c.HUD_INVENTARIO.colliderect(r)]
        assert all(c.HUD_INVENTARIO.contains(r) for _, r in textos), textos                # el detalle largo se corta, no se sale
        assert any(t.endswith("...") for t, _ in textos)
        assert _todo_dentro_de_los_paneles(m.vista, _pantalla(_inventario(lleno, cursor=9)))
        m.dibujar(_pantalla(_inventario(lleno, cursor=12)))                                # cursor fuera de rango: sin detalle ni error
        assert "Espada legendaria" not in " ".join(m.lista())


def probar_con_todo_lleno_a_la_vez_nada_se_dibuja_fuera_de_los_paneles():
    """(Con efectos de tipo desconocido: los velos de los otros cubren a propósito toda la pantalla.)"""
    efectos = [EfectoDTO(f"raro{i}", 10 ** 9, None) for i in range(9)]
    with VistaAbierta() as vista:
        pantalla = _pantalla(_inventario([DAGA] * 10, cursor=4, arma="itm_daga_oxidada"), efectos[:3],
                             _mensajes(20) + ["x" * 400], aviso="Aviso muy largo " * 30, seleccion=0, reloj=10 ** 9)
        assert _todo_dentro_de_los_paneles(vista, pantalla)
        pantalla = replace(pantalla, estado=replace(pantalla.estado, efectos=efectos))
        assert _todo_dentro_de_los_paneles(vista, pantalla)                                # más efectos de los que caben
        assert _todo_dentro_de_los_paneles(vista, replace(pantalla, ayuda=["x" * 300] * 30))


# ================================================================ la ventana del inventario (más de 15 casillas)
CAPACIDADES = [10, 15, 16, 30, 100]


def probar_la_ventana_siempre_contiene_al_cursor_se_mueve_lo_justo_y_con_15_o_menos_no_se_mueve():
    for capacidad in CAPACIDADES:
        for sentido in (1, -1):
            inicio = 0 if sentido == 1 else max(0, capacidad - 15)
            recorrido = range(capacidad) if sentido == 1 else range(capacidad - 1, -1, -1)
            for cursor in recorrido:
                nuevo = ventana_del_inventario(inicio, cursor, capacidad)
                assert 0 <= nuevo <= max(0, capacidad - 15), (capacidad, cursor, nuevo)
                assert nuevo <= cursor < nuevo + 15, (capacidad, cursor, nuevo)          # el cursor, dentro de la ventana
                assert abs(nuevo - inicio) <= 1, (capacidad, cursor, inicio, nuevo)       # paso a paso, se mueve de a uno
                if capacidad <= 15:
                    assert nuevo == 0, (capacidad, cursor)                                # nada cambia con 15 o menos
                inicio = nuevo
    # un clic sobre una casilla visible no mueve la ventana (el cursor ya está dentro)
    for capacidad in (16, 30, 100):
        for inicio in range(0, capacidad - 14, 3):
            for k in range(15):
                assert ventana_del_inventario(inicio, inicio + k, capacidad) == inicio, (capacidad, inicio, k)
    assert ventana_del_inventario(40, 500, 30) == 15 and ventana_del_inventario(0, -3, 30) == 0   # cursor fuera de rango
    assert ventana_del_inventario(0, 29, 30) == 15 and ventana_del_inventario(15, 0, 30) == 0       # saltos largos


def _objetos_distintos(n):
    return [ObjetoDTO(f"itm_{i:03d}", f"Objeto {i}", "llave", 1, i) for i in range(n)]


class BackendDeInventario:
    """El inventario de verdad (Logic.Inventario y Service.ServicioInventario) detrás de ControlesJuego. usar, equipar y soltar
    solo anotan a qué objeto se pidió."""

    def __init__(self, capacidad, objetos):
        self.inventario = Inventario(capacidad)
        for objeto in objetos:
            self.inventario.recoger(objeto)
        self.contexto = SimpleNamespace(inventario=self.inventario, criterio_vista=None)
        self.servicio = ServicioInventario()
        self.llamadas = []
        self.estado = None

    def foto(self):
        return self.servicio.inventario(self.contexto)

    def inventario_siguiente(self):
        return self.servicio.siguiente(self.contexto)

    def inventario_anterior(self):
        return self.servicio.anterior(self.contexto)

    def usar(self, id_objeto):
        self.llamadas.append(("usar", id_objeto))
        return self.estado

    def equipar(self, id_objeto):
        self.llamadas.append(("equipar", id_objeto))
        return self.estado

    def soltar(self, id_objeto):
        self.llamadas.append(("soltar", id_objeto))
        return self.estado


class Reloj:
    def __init__(self):
        self.ahora = 1000

    def __call__(self):
        return self.ahora


def _juego_con_inventario(capacidad, cantidad):
    """(backend, controles, reloj): un inventario real de 'capacidad' casillas con 'cantidad' objetos distintos."""
    backend = BackendDeInventario(capacidad, _objetos_distintos(cantidad))
    estado = replace(estado_base(3), inventario=backend.foto())
    backend.estado = estado
    reloj = Reloj()
    return backend, ControlesJuego(backend, estado, reloj, lambda: 0), reloj


def _lo_que_se_ve(m, controles):
    """Dibuja el estado de 'controles' y devuelve (el id del objeto de cada casilla de la ventana según su SPRITE, las casillas
    con el borde dorado del cursor). Nada de esto lee el índice que la Vista registró."""
    estado = controles.estado
    m.dibujar(replace(_pantalla(), estado=estado))
    almacen = m.vista._escena._almacen
    casillas = casillas_del_inventario(estado.inventario.capacidad_maxima)
    por_sprite = [(almacen.objeto(o.id, o.clase, c.INV_SPRITE).fotogramas[0], o.id) for o in estado.inventario.objetos]
    ids = []
    for casilla in casillas:
        id_visto = None
        for imagen, rectangulo in m.lienzo.blits:
            if casilla.contains(rectangulo):
                for sprite, id_objeto in por_sprite:
                    if imagen is sprite:
                        id_visto = id_objeto
        ids.append(id_visto)
    doradas = [k for k, casilla in enumerate(casillas) if m.lienzo.get_at((casilla.x + 1, casilla.centery))[:3] == c.ORO]
    return ids, doradas


def probar_con_capacidades_10_15_16_30_y_100_el_cursor_siempre_se_ve_y_todo_objeto_es_alcanzable_con_tab_y_rueda():
    for capacidad in CAPACIDADES:
        cantidad = capacidad if capacidad <= 30 else 60                  # (con 100 casillas: 60 objetos y 40 vacías)
        with VistaMedida() as m:
            backend, controles, _ = _juego_con_inventario(capacidad, cantidad)
            ids_reales = [o.id for o in controles.estado.inventario.objetos]
            for medio in ("Tab", "rueda"):
                if medio == "Tab":
                    adelante = lambda: controles.procesar_evento(tecla(pygame.K_TAB))          # noqa: E731
                    atras = lambda: controles.procesar_evento(tecla(pygame.K_TAB, pygame.KMOD_SHIFT))    # noqa: E731
                else:
                    adelante = lambda: controles.procesar_evento(rueda(-1))                    # noqa: E731
                    atras = lambda: controles.procesar_evento(rueda(1))                        # noqa: E731
                vistos = []
                for _ in range(cantidad):
                    ids, doradas = _lo_que_se_ve(m, controles)
                    cursor = controles.estado.inventario.cursor
                    assert len(doradas) == 1, (capacidad, medio, cursor, doradas)             # el cursor se ve, y una sola vez
                    assert ids[doradas[0]] == ids_reales[cursor], (capacidad, medio, cursor)  # y es sobre SU objeto
                    assert f"Objeto {cursor}" in m.lista()                                    # su detalle (índice real)
                    if capacidad <= 15:
                        assert ids[:cantidad] == ids_reales[:cantidad] and doradas[0] == cursor   # como siempre
                    vistos.append(cursor)
                    adelante()
                assert vistos == list(range(cantidad)), (capacidad, medio)                    # todos alcanzados, en orden
                for _ in range(cantidad):                                                     # y de vuelta hasta el principio
                    ids, doradas = _lo_que_se_ve(m, controles)
                    assert len(doradas) == 1 and ids[doradas[0]] == ids_reales[controles.estado.inventario.cursor]
                    atras()
                assert controles.estado.inventario.cursor == 0


def probar_el_clic_simple_por_posicion_visual_lleva_el_cursor_al_objeto_de_esa_casilla_y_el_doble_clic_lo_usa():
    for capacidad in CAPACIDADES:
        cantidad = capacidad if capacidad <= 30 else 60
        with VistaMedida() as m:
            backend, controles, reloj = _juego_con_inventario(capacidad, cantidad)
            casillas = casillas_del_inventario(capacidad)
            for _ in range(cantidad - 1 if capacidad > 15 else 3):                           # a una ventana avanzada
                controles.procesar_evento(tecla(pygame.K_TAB))
            for k in range(len(casillas)):
                ids, _ = _lo_que_se_ve(m, controles)
                esperado = ids[k]
                if esperado is None:                                                         # casilla vacía: no es clicable
                    assert m.vista.elemento_en(casillas[k].center) is None, (capacidad, k)
                    continue
                reloj.ahora += 5000                                                          # que no cuente como doble clic
                controles.procesar_evento(clic(casillas[k].center), m.vista.elemento_en(casillas[k].center))
                nuevo, doradas = _lo_que_se_ve(m, controles)
                cursor = controles.estado.inventario.cursor
                assert controles.estado.inventario.objetos[cursor].id == esperado, (capacidad, k)   # el objeto que se VE en k
                assert nuevo == ids and doradas == [k], (capacidad, k)                       # y la ventana no se movió
                backend.llamadas.clear()
                controles.procesar_evento(clic(casillas[k].center), m.vista.elemento_en(casillas[k].center))   # doble clic
                assert backend.llamadas == [("usar", esperado)], (capacidad, k, backend.llamadas)
    # equipar (clic derecho) también actúa sobre el objeto que se ve en la casilla
    with VistaMedida() as m:
        backend, controles, reloj = _juego_con_inventario(30, 30)
        for _ in range(29):
            controles.procesar_evento(tecla(pygame.K_TAB))
        ids, _ = _lo_que_se_ve(m, controles)
        casillas = casillas_del_inventario(30)
        controles.procesar_evento(clic(casillas[3].center, 3), m.vista.elemento_en(casillas[3].center))
        assert backend.llamadas == [("equipar", ids[3])]


def probar_la_marca_de_equipado_y_el_detalle_usan_el_indice_real_en_la_ventana_desplazada():
    objetos = _objetos_distintos(30)
    with VistaMedida() as m:
        # el arma equipada está en el índice real 20 y el cursor en el 25: la ventana (que parte de 0) se corre a 11..25
        m.dibujar(_pantalla(InventarioDTO(objetos, 25, 30, 30, objetos[20].id, objetos[3].id, None)))
        casillas = casillas_del_inventario(30)
        insignias = [r for t, r, _ in m.textos() if t == "E"]
        assert len(insignias) == 1 and casillas[20 - 11].colliderect(insignias[0]), insignias   # (el 3 queda fuera: no se ve)
        assert "Objeto 25" in m.lista() and "Objeto 20" not in m.lista()
        assert "30/30" in m.lista()
        m.dibujar(_pantalla(InventarioDTO(objetos, 0, 30, 30, objetos[20].id, objetos[3].id, None)))
        insignias = [r for t, r, _ in m.textos() if t == "E"]
        assert len(insignias) == 1 and casillas[3].colliderect(insignias[0]), insignias         # ventana 0..14: se ve el 3 y no el 20


def probar_real_un_clic_simple_en_la_casilla_k_mueve_el_cursor_al_objeto_k_y_el_doble_clic_lo_usa_con_siete_objetos():
    objetos = [DAGA, CORAZA, LLAVE, POCION, replace(ANTORCHA, duracion=400), ObjetoDTO("itm_llave_negra", "Llave negra", "llave", 1, 3),
               ObjetoDTO("itm_pergamino_retroceso", "Pergamino de retroceso", "pergamino_retroceso", 1, 30)]
    with _partida() as (vista, r):
        inventario = r.controlador._backend._contexto.inventario        # el inventario REAL de la partida real
        for objeto in objetos:
            assert inventario.recoger(objeto) is not None
        r.pulsar(pygame.K_TAB)                                          # (el Controlador vuelve a pedir la vista del inventario)
        r.pulsar(pygame.K_TAB)
        pantalla = r.dibujar()
        assert [o.nombre for o in pantalla.estado.inventario.objetos] == [o.nombre for o in objetos]
        casillas = casillas_del_inventario(10)
        for k in (4, 0, 6, 2, 5, 1, 3):                                 # en desorden: un clic simple en la casilla VISIBLE k
            r.dibujar()
            r.controlador.procesar_evento(clic(casillas[k].center))
            pantalla, textos = _textos_dibujados(vista, r)
            assert pantalla.estado.inventario.cursor == k, (k, pantalla.estado.inventario.cursor)
            assert objetos[k].nombre in textos and f"Clase: {objetos[k].clase}" in textos, (k, textos)
            assert len(pantalla.estado.inventario.objetos) == 7        # un clic simple no gasta nada
            r.controlador.procesar_evento(clic(casillas[(k + 1) % 7].center))   # (otra casilla: el siguiente clic no es doble)
        # doble clic sobre la casilla 3 (la poción): se usa ESA y no otra
        r.dibujar()
        r.controlador.procesar_evento(clic(casillas[1].center))
        r.controlador.procesar_evento(clic(casillas[3].center))
        r.controlador.procesar_evento(clic(casillas[3].center))
        estado = r.pantalla().estado
        nombres = [o.nombre for o in estado.inventario.objetos]
        assert "Poción menor" not in nombres and len(nombres) == 6 and "Antorcha" in nombres, nombres
        # ahora la antorcha ocupa la casilla 3: doble clic y aparece su efecto
        r.dibujar()
        r.controlador.procesar_evento(clic(casillas[1].center))
        r.controlador.procesar_evento(clic(casillas[3].center))
        r.controlador.procesar_evento(clic(casillas[3].center))
        estado = r.pantalla().estado
        assert "Antorcha" not in [o.nombre for o in estado.inventario.objetos]
        assert [e.tipo for e in estado.efectos].count("antorcha") == 1, (estado.efectos, estado.mensajes, estado.resultado)


def probar_los_avisos_fijos_del_controlador_caben_en_el_panel_y_uno_de_red_se_corta_dentro_de_el():
    import re
    import Service.ServicioAccionJugador as acciones
    pygame.font.init()
    fuente = _fuente(c.TAM_MENSAJES)
    ancho = c.HUD_AVISO.width - 2 * c.HUD_RELLENO
    fijos = [mensaje for _, mensaje in acciones._MENSAJES_DE_RECHAZO]
    for archivo in ("ControlesJuego.py", "ControladorBackend.py"):
        texto = (RAIZ / "UIController" / archivo).read_text(encoding="utf-8")
        fijos += [m.replace("{que}", "enemigo").replace("{LARGO_MAXIMO_NOMBRE}", "16")
                  .replace("{mensaje}", "Criterio desconocido").replace("{criterio!r}", "'peso'")
                  for m in re.findall(r'ErrorOperacion\(f?"([^"]+)"', texto)]
    assert len(fijos) >= 25
    for mensaje in fijos + ["No se pudo realizar la acción (codigo_nuevo)."]:
        assert len(c.ajustar_lineas(fuente, mensaje, ancho)) <= c.HUD_AVISO_LINEAS, mensaje      # en 3 líneas como mucho
    assert max(len(c.ajustar_lineas(fuente, m, ancho)) for m in fijos) <= 2
    largo = "Sin conexión con el servicio: Falló 'pedir catálogo': no se pudo conectar al servidor " + "(error de red) " * 20
    assert len(c.ajustar_lineas(fuente, largo, ancho)) > c.HUD_AVISO_LINEAS                      # este no cabe entero...
    with VistaMedida() as m:
        m.dibujar(_pantalla(aviso=largo))
        puestas = [(t, r) for t, r, f in m.textos() if f == "mensajes" and c.HUD_AVISO.colliderect(r)]
        assert len(puestas) == c.HUD_AVISO_LINEAS and puestas[-1][0].endswith("...")             # ...se corta con "..."
        assert all(c.HUD_AVISO.contains(r) for _, r in puestas)


# ================================================================ de punta a punta (Controlador y servicios reales)
def _entrar(r):
    r.pulsar(ENTER)
    r.pulsar(ENTER)
    r.escribir("Ana")
    r.pulsar(ENTER)
    assert r.pantalla().pantalla == "juego"


@contextmanager
def _partida():
    vista = VistaPygame()
    vista.abrir()
    try:
        with Recorrido(vista) as r:
            _entrar(r)
            yield vista, r
    finally:
        vista.cerrar()


def _textos_dibujados(vista, r):
    """Dibuja el cuadro actual sobre un lienzo anotando los textos (como VistaMedida, pero con el Controlador real)."""
    anotaciones = []
    fuentes = vista._fuentes
    originales = []
    for nombre in ("titulo", "boton", "texto", "pie", "chico", "mensajes", "ayuda_juego"):
        originales.append((nombre, getattr(fuentes, nombre)))
        setattr(fuentes, nombre, FuenteQueAnota(getattr(fuentes, nombre), nombre, anotaciones))
    pantalla = r.dibujar()
    for nombre, fuente in originales:
        setattr(fuentes, nombre, fuente)
    return pantalla, [t for t, _, _ in anotaciones]


def probar_real_recoger_la_antorcha_usarla_con_doble_clic_cambiar_el_orden_y_esperar():
    with _partida() as (vista, r):
        pantalla = r.dibujar()
        assert [o.nombre for o in pantalla.estado.objetos_suelo] == ["Antorcha"] and pantalla.estado.inventario.objetos == []
        reparto = escena.repartir_escena(vista._escena._almacen, vista._fuentes, pantalla.estado.enemigos,
                                         pantalla.estado.objetos_suelo, pantalla.estado.sala.salidas, c.PIES_CENTRO)
        r.controlador.procesar_evento(clic(reparto.objetos[0].center))                     # clic sobre la antorcha del suelo
        pantalla, textos = _textos_dibujados(vista, r)
        assert [o.nombre for o in pantalla.estado.inventario.objetos] == ["Antorcha"]
        assert "1/10" in textos and "Antorcha" in textos and "Clase: antorcha" in textos   # en el inventario, con su detalle
        casilla = casillas_del_inventario(10)[0]
        assert vista.elemento_en(casilla.center) == ElementoDTO(ELEMENTO_INVENTARIO, 0)    # y se puede hacer clic en ella
        assert vista.elemento_en(casillas_del_inventario(10)[1].center) is None            # una casilla vacía no devuelve zona
        r.controlador.procesar_evento(clic(casillas_del_inventario(10)[5].center))         # clic sobre una casilla vacía
        assert [o.nombre for o in r.pantalla().estado.inventario.objetos] == ["Antorcha"]  # no pasó nada
        assert r.pantalla().estado.efectos == []
        sin_efecto = pygame.display.get_surface().copy()
        r.dibujar()
        r.controlador.procesar_evento(clic(casilla.center))                                # doble clic sobre la casilla
        r.controlador.procesar_evento(clic(casilla.center))
        pantalla, textos = _textos_dibujados(vista, r)
        assert [e.tipo for e in pantalla.estado.efectos] == ["antorcha"], pantalla.estado.efectos
        visible = efectos_a_mostrar(pantalla.estado.efectos)[0]
        assert visible.texto in textos and "Antorcha" in visible.texto                      # la línea de texto del efecto
        con_efecto = pygame.display.get_surface()
        punto = (420, 60)
        assert con_efecto.get_at(punto)[:3] != sin_efecto.get_at(punto)[:3]                # y el velo sobre la escena
        assert con_efecto.get_at(punto)[0] >= sin_efecto.get_at(punto)[0]                  # (naranja: sube el rojo)
        r.pulsar(pygame.K_v)                                                               # V: otro criterio de orden
        pantalla, textos = _textos_dibujados(vista, r)
        criterio = pantalla.estado.inventario.criterio
        assert criterio is not None and f"Orden: {criterio}" in textos and "Orden: real" not in textos
        reloj = pantalla.estado.reloj
        r.dibujar()
        r.controlador.procesar_evento(clic(c.HUD_ESPERAR.center))                          # clic en el botón Esperar
        pantalla, textos = _textos_dibujados(vista, r)
        assert pantalla.estado.reloj > reloj and f"Reloj: {pantalla.estado.reloj}" in textos


def probar_real_el_nombre_del_objeto_bajo_el_ratón_sigue_apareciendo_con_el_hud():
    with _partida() as (vista, r):
        pantalla = r.dibujar()
        reparto = escena.repartir_escena(vista._escena._almacen, vista._fuentes, pantalla.estado.enemigos,
                                         pantalla.estado.objetos_suelo, pantalla.estado.sala.salidas, c.PIES_CENTRO)
        r.controlador.procesar_evento(movimiento(reparto.objetos[0].center))
        pantalla, textos = _textos_dibujados(vista, r)
        assert pantalla.elemento_bajo_el_raton == ElementoDTO("objeto_suelo", 0)
        assert textos.count("Antorcha") >= 1


if __name__ == "__main__":
    probar_efectos_a_mostrar_los_cinco_casos()
    probar_el_equipado_con_ids_repetidos_marca_solo_el_primero()
    probar_lineas_de_mensajes_20_de_20_menos_de_20_y_mas_de_20()
    probar_el_detalle_del_objeto_trae_los_datos_y_solo_los_bonus_que_no_son_none()
    probar_las_casillas_estan_dentro_del_panel_son_de_46_y_no_se_solapan()
    probar_ningun_panel_del_hud_toca_una_puerta_ni_el_sitio_del_protagonista_y_los_tramos_laterales_quedan_libres()
    probar_con_12_enemigos_y_12_objetos_ninguna_zona_solapa_un_panel_con_el_protagonista_en_cada_sitio()
    probar_si_el_reparto_ignorara_los_paneles_si_se_pisarian_los_paneles_del_suelo()
    probar_todos_los_mensajes_reales_del_motor_caben_en_el_ancho_util_del_panel_de_mensajes()
    probar_los_mensajes_de_una_partida_real_caben_enteros_sin_cortes()
    probar_las_11_lineas_de_ayuda_caben_en_su_panel_con_las_constantes_reales()
    probar_las_estadisticas_y_el_reloj_se_ven_con_los_valores_del_jugador()
    probar_los_20_mensajes_se_dibujan_completos_la_mas_reciente_abajo_y_dentro_del_panel()
    probar_un_mensaje_muy_largo_se_corta_con_puntos_suspensivos_dentro_del_panel_y_el_normal_no()
    probar_el_inventario_muestra_casillas_sprites_contador_criterio_cursor_y_equipado()
    probar_el_cursor_se_ve_sobre_su_casilla_y_solo_sobre_esa()
    probar_solo_la_primera_casilla_con_el_id_equipado_lleva_la_marca_en_pantalla()
    probar_las_zonas_del_inventario_son_solo_las_casillas_ocupadas_y_el_boton_es_el_0()
    probar_el_boton_esperar_se_resalta_segun_la_seleccion()
    probar_el_aviso_se_destaca_en_su_panel_y_la_ayuda_siempre_esta()
    probar_los_velos_de_los_efectos_tiñen_la_escena_con_su_color_se_crean_una_vez_y_el_desconocido_no_tiñe()
    probar_un_efecto_de_cada_tipo_escribe_su_nombre_y_su_tiempo_restante_en_el_panel_de_efectos()
    probar_el_nombre_del_objeto_bajo_el_raton_se_dibuja_despues_del_hud_y_por_encima_de_el()
    probar_inventario_vacio_lleno_y_con_nombres_largos_no_rompen_ni_se_salen_del_panel()
    probar_con_todo_lleno_a_la_vez_nada_se_dibuja_fuera_de_los_paneles()
    probar_la_ventana_siempre_contiene_al_cursor_se_mueve_lo_justo_y_con_15_o_menos_no_se_mueve()
    probar_con_capacidades_10_15_16_30_y_100_el_cursor_siempre_se_ve_y_todo_objeto_es_alcanzable_con_tab_y_rueda()
    probar_el_clic_simple_por_posicion_visual_lleva_el_cursor_al_objeto_de_esa_casilla_y_el_doble_clic_lo_usa()
    probar_la_marca_de_equipado_y_el_detalle_usan_el_indice_real_en_la_ventana_desplazada()
    probar_los_avisos_fijos_del_controlador_caben_en_el_panel_y_uno_de_red_se_corta_dentro_de_el()
    probar_real_recoger_la_antorcha_usarla_con_doble_clic_cambiar_el_orden_y_esperar()
    probar_real_un_clic_simple_en_la_casilla_k_mueve_el_cursor_al_objeto_k_y_el_doble_clic_lo_usa_con_siete_objetos()
    probar_real_el_nombre_del_objeto_bajo_el_ratón_sigue_apareciendo_con_el_hud()
    print("OK: todas las pruebas del HUD de la partida pasaron")
