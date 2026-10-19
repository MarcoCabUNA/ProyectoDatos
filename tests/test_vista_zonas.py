"""
Pruebas de ZonasClic y de los componentes puros de la Vista (distribución de botones, texto). Se ejecuta desde
cualquier carpeta.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402  (fija SDL_VIDEODRIVER=dummy antes de importar pygame)

from DTO.ElementoDTO import ELEMENTO_BOTON, ELEMENTO_ENEMIGO, ElementoDTO  # noqa: E402
from View.Componentes import (BOTON_ALTO, BOTON_ALTO_MINIMO, ajustar_lineas, distribuir_botones,  # noqa: E402
                              recortar_a_ancho)
from View.ZonasClic import ZonasClic  # noqa: E402

BOTON_0 = ElementoDTO(ELEMENTO_BOTON, 0)
BOTON_1 = ElementoDTO(ELEMENTO_BOTON, 1)
ENEMIGO = ElementoDTO(ELEMENTO_ENEMIGO, 0)


def probar_un_punto_dentro_devuelve_su_elemento_y_fuera_none():
    zonas = ZonasClic()
    zonas.agregar(pygame.Rect(10, 10, 100, 50), BOTON_0)
    assert zonas.buscar((10, 10)) == BOTON_0 and zonas.buscar((109, 59)) == BOTON_0
    assert zonas.buscar((110, 30)) is None and zonas.buscar((50, 60)) is None and zonas.buscar((0, 0)) is None


def probar_zonas_superpuestas_devuelven_la_ultima_registrada():
    zonas = ZonasClic()
    zonas.agregar(pygame.Rect(0, 0, 200, 200), BOTON_0)
    zonas.agregar(pygame.Rect(50, 50, 100, 100), ENEMIGO)        # dibujado encima
    zonas.agregar(pygame.Rect(120, 120, 100, 100), BOTON_1)      # encima de las dos
    assert zonas.buscar((10, 10)) == BOTON_0
    assert zonas.buscar((60, 60)) == ENEMIGO                      # la última que contiene el punto
    assert zonas.buscar((130, 130)) == BOTON_1
    assert zonas.buscar((140, 140)) == BOTON_1
    assert zonas.buscar((100, 100)) == ENEMIGO


def probar_limpiar_vacia_las_zonas():
    zonas = ZonasClic()
    zonas.agregar(pygame.Rect(0, 0, 50, 50), BOTON_0)
    assert zonas.cantidad() == 1
    zonas.limpiar()
    assert zonas.cantidad() == 0 and zonas.buscar((10, 10)) is None


def probar_agregar_guarda_una_copia_del_rectangulo():
    zonas = ZonasClic()
    rectangulo = pygame.Rect(0, 0, 50, 50)
    zonas.agregar(rectangulo, BOTON_0)
    rectangulo.move_ip(500, 500)                                  # si no se copió, la zona se movería
    assert zonas.buscar((10, 10)) == BOTON_0 and zonas.buscar((510, 510)) is None


def _no_se_solapan(rectangulos):
    for i in range(len(rectangulos)):
        for j in range(i + 1, len(rectangulos)):
            assert not rectangulos[i].colliderect(rectangulos[j]), (i, j)


def probar_pocos_botones_van_en_una_columna_con_su_alto_normal():
    area = pygame.Rect(100, 100, 400, 300)
    rectangulos = distribuir_botones(4, area)
    assert len(rectangulos) == 4 and all(r.height == BOTON_ALTO and r.width == 400 for r in rectangulos)
    assert [r.top for r in rectangulos] == sorted(r.top for r in rectangulos)
    _no_se_solapan(rectangulos)


def probar_muchos_botones_se_achican_y_luego_pasan_a_mas_columnas():
    area = pygame.Rect(100, 100, 800, 400)
    for cantidad in (1, 5, 9, 12, 13, 40, 150):
        rectangulos = distribuir_botones(cantidad, area)
        assert len(rectangulos) == cantidad
        _no_se_solapan(rectangulos)
        for r in rectangulos:
            assert area.contains(r), (cantidad, r)
            assert r.height >= BOTON_ALTO_MINIMO or cantidad == 1, (cantidad, r.height)
    una_columna = distribuir_botones(9, area)
    assert len({r.left for r in una_columna}) == 1 and una_columna[0].height < BOTON_ALTO   # achicados, una columna
    assert len({r.left for r in distribuir_botones(40, area)}) > 1                         # varias columnas
    assert distribuir_botones(0, area) == []


def probar_texto_recortado_y_ajustado():
    pygame.font.init()
    try:
        fuente = pygame.font.Font(None, 28)
        ancho = fuente.size("Una frase bastante larga para cortar")[0] // 2
        corto = recortar_a_ancho(fuente, "Una frase bastante larga para cortar", ancho)
        assert corto.endswith("...") and fuente.size(corto)[0] <= ancho
        assert recortar_a_ancho(fuente, "Hola", 500) == "Hola"
        lineas = ajustar_lineas(fuente, "uno dos tres cuatro cinco seis siete ocho nueve diez", ancho)
        assert len(lineas) > 1 and all(fuente.size(linea)[0] <= ancho for linea in lineas)
        assert " ".join(lineas) == "uno dos tres cuatro cinco seis siete ocho nueve diez"
        assert ajustar_lineas(fuente, "", 100) == [""]
    finally:
        pygame.quit()


if __name__ == "__main__":
    probar_un_punto_dentro_devuelve_su_elemento_y_fuera_none()
    probar_zonas_superpuestas_devuelven_la_ultima_registrada()
    probar_limpiar_vacia_las_zonas()
    probar_agregar_guarda_una_copia_del_rectangulo()
    probar_pocos_botones_van_en_una_columna_con_su_alto_normal()
    probar_muchos_botones_se_achican_y_luego_pasan_a_mas_columnas()
    probar_texto_recortado_y_ajustado()
    print("OK: todas las pruebas de ZonasClic y de los componentes pasaron")
