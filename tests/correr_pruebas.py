"""
Corre TODAS las pruebas del proyecto con un solo comando:

    python tests/correr_pruebas.py            (con uv: uv run python tests/correr_pruebas.py)

Hay dos tipos de pruebas y "unittest discover" solo encuentra el primero:
  1. Las de unittest (Test*.py y algunos test_*.py): se corren con "python -m unittest discover".
  2. Los scripts test_*.py que no usan unittest: cada uno ejecuta sus funciones probar_* en su bloque
     if __name__ == "__main__" e imprime una línea "OK: ..." al final. Hay que correrlos uno por uno.

Cada prueba corre en su propio proceso, con "python -B" (sin bytecode viejo de __pycache__) y con
SDL_VIDEODRIVER=dummy (las de la Vista no abren ventanas). Escribe un resumen y termina con código 0 si todo pasó
y 1 si algo falló. Las pruebas de la Vista necesitan pygame-ce instalado.
"""
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = RAIZ / "tests"
sys.path.insert(0, str(RAIZ))

from Estructuras.Ordenador import Ordenador  # noqa: E402  (sin sorted(): §4.9)


def scripts_sin_unittest() -> list[Path]:
    """Los test_*.py con bloque __main__ que no usan unittest, en orden alfabético."""
    scripts = []
    rutas = Ordenador.ordenar(list(CARPETA.glob("test_*.py")), lambda a, b: Ordenador.comparar(a.name, b.name))
    for ruta in rutas:
        texto = ruta.read_text(encoding="utf-8")
        if "__main__" in texto and "unittest" not in texto:
            scripts.append(ruta)
    return scripts


def correr(argumentos: list[str]) -> tuple[bool, str, str]:
    """(pasó, toda la salida, la línea que la resume: la última "OK: ..." de stdout o, si no hay, la última línea)."""
    entorno = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    proceso = subprocess.run([sys.executable, "-B", *argumentos], cwd=RAIZ, env=entorno,
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
    salida = (proceso.stdout + proceso.stderr).strip()
    resumen = salida.splitlines()[-1] if salida else "(sin salida)"
    for linea in proceso.stdout.splitlines():                # los avisos de pygame van a stderr
        if linea.startswith("OK"):
            resumen = linea
    return proceso.returncode == 0, salida, resumen


def main() -> int:
    fallos = []

    ok, salida, _ = correr(["-m", "unittest", "discover", "-s", "tests", "-p", "[Tt]est*.py"])
    resumen = [linea for linea in salida.splitlines() if linea.startswith(("Ran ", "OK", "FAILED"))]
    print("unittest discover:", " ".join(resumen) or "(sin resumen)")
    if not ok:
        fallos.append(("unittest discover", salida))

    scripts = scripts_sin_unittest()
    for ruta in scripts:
        ok, salida, resumen = correr([str(ruta.relative_to(RAIZ))])
        print(f"  {'ok   ' if ok else 'FALLA'} {ruta.name}: {resumen[:150]}")
        if not ok:
            fallos.append((ruta.name, salida))

    print()
    print(f"Scripts: {len(scripts) - sum(1 for nombre, _ in fallos if nombre != 'unittest discover')} de {len(scripts)} pasaron.")
    for nombre, salida in fallos:
        print(f"\n===== {nombre} =====\n{salida[-3000:]}")
    print("TODO PASÓ" if not fallos else f"FALLARON {len(fallos)}")
    return 0 if not fallos else 1


if __name__ == "__main__":
    sys.exit(main())
