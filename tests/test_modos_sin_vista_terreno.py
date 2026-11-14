"""
Pruebas de FR-118 (feature 001, T048): las reglas del terreno y del cazador en los modos sin vista.

Se juega una partida con ServicioPartida sobre FuenteCuadriculaConCazador (tests/ayudas_terreno.py): una cuadrícula
de 4 × 4 con costos entre 1 y 300, un cazador y un errante. Después se lee su log y ServicioReplay la reproduce en
una partida nueva, con su propia fuente y caché, sin instanciar la vista.

Pendiente: `--replay … --hasta` (spec 004) y `--verificar` (spec 003) todavía no existen en esta rama; sus pruebas
se agregan cuando lleguen (H3-7 sigue con skip en test_terreno_cazador.py por lo mismo).
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))          # para reutilizar los ayudantes de test_servicios

from DTO.ConfiguracionDTO import ConfiguracionDTO  # noqa: E402
from Service.ServicioAccionJugador import ServicioAccionJugador  # noqa: E402
from Service.ServicioPartida import ServicioPartida  # noqa: E402
from Service.ServicioReplay import ServicioReplay  # noqa: E402
from test_servicios import _elegir_accion  # noqa: E402
from tests.ayudas_terreno import FuenteCuadriculaConCazador  # noqa: E402

SEMILLAS = (1, 2, 3, 4, 5, 6)


def _correr(prueba):
    carpeta = tempfile.mkdtemp()
    try:
        prueba(carpeta)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def _partida(carpeta, semilla):
    return ServicioPartida(ConfiguracionDTO(offline=True), fuente=FuenteCuadriculaConCazador(semilla),
                           carpeta_cache=os.path.join(carpeta, "cache"), carpeta_logs=os.path.join(carpeta, "logs"))


def _jugar(carpeta, semilla, pasos=60):
    """Una partida normal con log. Devuelve (ruta del log, estados[0..n]: el estado tras cada acción hecha)."""
    partida = _partida(carpeta, semilla)
    acciones = ServicioAccionJugador()
    ctx = partida.iniciar_partida("cuadricula", "Ana", semilla=semilla)
    estado, x = partida.estado(ctx), semilla * 7919
    estados = [estado]
    for _ in range(pasos):
        if estado.terminado:
            break
        x = (x * 1103515245 + 12345) % 2147483648
        nuevo = acciones.ejecutar(ctx, _elegir_accion(estado, x))
        if nuevo.resultado is None or nuevo.terminado:             # la acción se hizo (no fue rechazada)
            estados.append(nuevo)
        estado = nuevo
    return ctx.bitacora.ruta(), estados


def probar_fr118_replay_reproduce_los_mismos_estados_con_costos_y_cazador(carpeta):
    acciones = 0
    con_cazador = 0
    costos = []
    for semilla in SEMILLAS:
        ruta, estados = _jugar(os.path.join(carpeta, f"a{semilla}"), semilla)
        n = len(estados) - 1
        if n < 1:
            continue
        reproducidos = []
        resultado = ServicioReplay(_partida(os.path.join(carpeta, f"b{semilla}"), semilla)).reproducir(
            ruta, al_avanzar=lambda i, accion, estado: reproducidos.append(estado))
        assert resultado.acciones_reproducidas == n, f"semilla {semilla}"
        assert reproducidos == estados[1:], f"semilla {semilla}: algún estado intermedio difiere"
        assert resultado.estado_final == estados[-1]
        assert resultado.encabezado.semilla == semilla
        acciones += n
        for estado in estados:
            for enemigo in estado.enemigos:
                if enemigo.comportamiento == "cazador":
                    con_cazador += 1
            for salida in estado.sala.salidas:
                if salida is not None and salida.costo not in costos:
                    costos.append(salida.costo)
    assert acciones >= 60, "las partidas fueron demasiado cortas para que la prueba valga"
    assert con_cazador > 0, "el cazador nunca estuvo a la vista: la prueba no cubre FR-118 para el cazador"
    assert len(costos) >= 4, f"costos vistos: {costos}"     # los costos de la cuadrícula llegan al estado (FR-116)


def probar_fr118_replay_no_carga_la_vista(carpeta):
    for nombre in sys.modules:
        assert nombre != "pygame" and not nombre.startswith(("pygame.", "View")), nombre


if __name__ == "__main__":
    for prueba in (probar_fr118_replay_reproduce_los_mismos_estados_con_costos_y_cazador,
                   probar_fr118_replay_no_carga_la_vista):
        _correr(prueba)
    print("PENDIENTE: --replay … --hasta (spec 004) y --verificar (spec 003) todavía no existen en esta rama")
    print("OK: todas las pruebas de los modos sin vista con terreno y cazador pasaron")
