"""
verificar_zonas_menu.py — comprobación INDEPENDIENTE de las zonas de clic del menú (herramienta temporal).

Usa solo el contrato de la Vista (abrir, dibujar, elemento_en, cerrar), no las pruebas del proyecto. Dibuja el menú con
la Vista real y recorre toda la ventana preguntando "¿qué hay en este punto?". Comprueba:

  1. Que hay exactamente 5 botones, con los índices 0 a 4 (ElementoDTO("boton", i)).
  2. Que el CENTRO de cada zona devuelve su propio botón.
  3. Que las zonas no se solapan y que no hay ningún elemento que no sea un botón.
  4. Que fuera de los botones (por ejemplo la esquina) no hay nada.
  5. Que al dibujar OTRO menú con un solo botón, las zonas del cuadro anterior desaparecen (se limpian al dibujar).

Cómo usarlo (desde la raíz del proyecto, con el entorno activo):
    python -B verificar_zonas_menu.py
Termina con "RESULTADO: TODO CORRECTO" (código de salida 0) o con "RESULTADO: HAY FALLOS" (código 1).
Es una herramienta temporal: NO la subas a Git; bórrala cuando termines de revisar.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")            # sin ventana real
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from DTO.ElementoDTO import ELEMENTO_BOTON, ElementoDTO  # noqa: E402
from DTO.PantallaDTO import PantallaDTO  # noqa: E402
from View.VistaPygame import VistaPygame  # noqa: E402

ANCHO, ALTO, PASO = 1376, 768, 4                              # resolución lógica y separación de la rejilla de puntos
TEXTOS = ["Comenzar juego", "Modo: Offline", "Cargar partida", "Puntajes", "Salir"]
fallos = []


def comprobar(condicion: bool, texto: str) -> None:
    print(("  [ok]    " if condicion else "  [FALLA] ") + texto)
    if not condicion:
        fallos.append(texto)


def explorar(vista, cantidad: int):
    """Recorre la ventana. Devuelve (cajas por botón, elementos que no son botón). Cada caja: [x0, y0, x1, y1]."""
    cajas = [[ANCHO, ALTO, -1, -1] for _ in range(cantidad)]
    extranos = []
    for y in range(0, ALTO, PASO):
        for x in range(0, ANCHO, PASO):
            elemento = vista.elemento_en((x, y))
            if elemento is None:
                continue
            if elemento.tipo == ELEMENTO_BOTON and 0 <= elemento.indice < cantidad:
                caja = cajas[elemento.indice]
                caja[0], caja[1], caja[2], caja[3] = min(caja[0], x), min(caja[1], y), max(caja[2], x), max(caja[3], y)
            else:
                extranos.append(elemento)
    return cajas, extranos


def se_solapan(a, b) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


vista = VistaPygame()
vista.abrir()
try:
    print("Menú con 5 botones:")
    vista.dibujar(PantallaDTO("menu", "CRIPTA", list(TEXTOS), 0))
    cajas, extranos = explorar(vista, 5)
    encontrados = [c[2] >= 0 for c in cajas]
    comprobar(all(encontrados), f"se encontraron zonas para los 5 botones (índices con zona: {[i for i, e in enumerate(encontrados) if e]})")
    for i, caja in enumerate(cajas):
        if caja[2] >= 0:
            centro = ((caja[0] + caja[2]) // 2, (caja[1] + caja[3]) // 2)
            print(f"            botón {i}: x {caja[0]}–{caja[2]}, y {caja[1]}–{caja[3]}  (≈ {caja[2] - caja[0] + PASO} × {caja[3] - caja[1] + PASO} px)")
            comprobar(vista.elemento_en(centro) == ElementoDTO(ELEMENTO_BOTON, i), f"el centro {centro} del botón {i} devuelve ElementoDTO('boton', {i})")
    hay_solape = any(se_solapan(cajas[i], cajas[j]) for i in range(5) for j in range(i + 1, 5) if cajas[i][2] >= 0 and cajas[j][2] >= 0)
    comprobar(not hay_solape, "las zonas de los botones no se solapan entre sí")
    comprobar(not extranos, f"no hay zonas que no sean botones del menú (encontradas: {len(extranos)})")
    comprobar(vista.elemento_en((0, 0)) is None and vista.elemento_en((ANCHO - 1, ALTO - 1)) is None, "las esquinas de la ventana no tienen nada")

    print("\nOtro cuadro con UN solo botón (las zonas anteriores deben haberse limpiado):")
    vista.dibujar(PantallaDTO("menu", "CRIPTA", ["Solo uno"], 0))
    cajas2, extranos2 = explorar(vista, 5)
    activos = [i for i, c in enumerate(cajas2) if c[2] >= 0]
    comprobar(activos == [0], f"solo existe la zona del botón 0 (con zona: {activos})")
    comprobar(not extranos2, "no queda ninguna zona vieja de otro tipo")
finally:
    vista.cerrar()

print("\nRESULTADO: " + ("TODO CORRECTO" if not fallos else f"HAY FALLOS ({len(fallos)})"))
sys.exit(0 if not fallos else 1)
