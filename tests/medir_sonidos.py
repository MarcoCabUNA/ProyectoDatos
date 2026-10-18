"""
Mide los 11 archivos de assets/sonidos (no es una prueba): para cada uno, la duración, cuándo empieza a sonar (primera muestra
por encima del 10 % del pico), hasta cuándo suena (la última), el pico y qué haría el cargador con él (tope, ganancia y duración
final). Al terminar, cuánto tarda el cargador en abrir el mezclador y preparar los 9 sonidos cortos.

    python tests/medir_sonidos.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402  (fija los controladores dummy de video y audio)

from View import Componentes as c  # noqa: E402
from View.Sonidos import Sonidos, preparar, primer_indice_sobre  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = RAIZ / "assets" / c.CARPETA_SONIDOS


def _ultimo_indice_sobre(muestras, umbral: int, paso: int = 2048) -> int:
    inicio = (len(muestras) // paso) * paso
    while inicio >= 0:
        trozo = muestras[inicio:inicio + paso]
        if trozo and (max(trozo) > umbral or min(trozo) < -umbral):
            for i in range(len(trozo) - 1, -1, -1):
                if abs(trozo[i]) > umbral:
                    return inicio + i
        inicio -= paso
    return -1


def _tabla() -> list:
    """Los 11 nombres con su fila de ajustes (tope, fundido) o None si es música larga."""
    filas = [(fila[0], fila) for fila in c.SONIDOS_CORTOS]
    for fila in c.MUSICAS:
        filas.append((fila[0], None))
    return filas


def main() -> int:
    pygame.mixer.init(frequency=c.MEZCLADOR[0], size=c.MEZCLADOR[1], channels=c.MEZCLADOR[2], buffer=c.MEZCLADOR[3])
    frecuencia, _, canales = pygame.mixer.get_init()
    print(f"{'archivo':<24}{'dur s':>8}{'inicio ms':>11}{'suena hasta':>13}{'pico':>7}   cargador")
    for nombre, fila in _tabla():
        ruta = CARPETA / (nombre + c.SONIDO_EXTENSION)
        if not ruta.exists():
            print(f"{nombre:<24}  (falta {ruta})")
            continue
        sonido = pygame.mixer.Sound(str(ruta))
        muestras = memoryview(sonido.get_raw()).cast("h")
        pico = max(max(muestras), -min(muestras)) / 32768
        umbral = int(pico * 32768 * c.SONIDO_UMBRAL_INICIO)
        primera = primer_indice_sobre(muestras, umbral)
        ultima = _ultimo_indice_sobre(muestras, umbral)
        inicio_ms = primera // canales * 1000 // frecuencia
        fin_s = ultima // canales / frecuencia
        if fila is None:
            accion = "música en streaming: no se procesa"
        else:
            preparado, _ = preparar(sonido.get_raw(), canales, frecuencia, fila[1], fila[2])
            ganancia = min(c.SONIDO_GANANCIA_MAX, c.SONIDO_PICO_OBJETIVO / pico)
            tope = f"tope {fila[1]} ms" if fila[1] else "sin tope"
            subida = f", ganancia x{ganancia:.2f}" if ganancia > c.SONIDO_GANANCIA_MIN else ""
            accion = (f"quita {max(0, inicio_ms - c.SONIDO_MARGEN_MS)} ms, {tope}{subida}, fundido {fila[2]} ms"
                      f" -> dura {len(preparado) // (2 * canales) * 1000 / frecuencia:.0f} ms")
        print(f"{nombre:<24}{len(muestras) / canales / frecuencia:>8.2f}{inicio_ms:>11}{fin_s:>12.2f}s{pico:>7.2f}   {accion}")
    pygame.mixer.quit()

    motor = Sonidos(str(RAIZ / "assets"))
    comienzo = time.perf_counter()
    abierto = motor.abrir()
    total = time.perf_counter() - comienzo
    motor.cerrar()
    print()
    print(f"Cargador (mezclador + 9 efectos): {total * 1000:.0f} ms en total (pide menos de 800 ms); abierto={abierto};"
          f" envolvente de Low_Health: {len(motor.envolvente_latido)} ventanas de {c.SONIDO_VENTANA_MS} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
