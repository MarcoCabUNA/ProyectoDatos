"""
Pruebas de FR-118 (feature 001, T048): las reglas del terreno y del cazador en los modos sin vista.

Se juega una partida con ServicioPartida sobre FuenteCuadriculaConCazador (tests/ayudas_terreno.py): una cuadrícula
de 4 × 4 con costos entre 1 y 300, un cazador y un errante. Después se lee su log y, cada uno en una partida nueva
con su propia fuente y caché, sin instanciar la vista:
  - `--replay` (ServicioReplay) la reproduce entera y pasa por los mismos estados;
  - `--replay … --hasta t` (ServicioReplayHasta, feature 004) da en cada t el estado que tenía la partida viva en t;
  - `--verificar` (ServicioResolubilidad, feature 003) da el mismo reporte con costos y cazadores que sin ellos.
Los datos inválidos de FR-122 con `--verificar` (código 1) los prueba H3-7 en test_terreno_cazador.py.
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
from Service.ServicioReplayHasta import ServicioReplayHasta  # noqa: E402
from Service.ServicioResolubilidad import ServicioResolubilidad  # noqa: E402
from ayudas_linea_tiempo import resumen_vivo  # noqa: E402
from DTO.ReporteResolubilidadDTO import RESOLUBLE  # noqa: E402
from DTO.SalaDTO import SalidaDTO  # noqa: E402
from DTO.UbicacionLlaveDTO import UbicacionLlaveDTO  # noqa: E402
from test_servicios import _elegir_accion  # noqa: E402
from tests.Utilidades import FuenteCuadricula  # noqa: E402
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


def _jugar(carpeta, semilla, pasos=60, resumenes=None):
    """
    Una partida normal con log. Devuelve (ruta del log, estados[0..n]: el estado tras cada acción hecha). Si se pasa
    la lista 'resumenes', se le agrega el resumen vivo (como `historia t`) al inicio y tras cada acción hecha.
    """
    partida = _partida(carpeta, semilla)
    acciones = ServicioAccionJugador()
    ctx = partida.iniciar_partida("cuadricula", "Ana", semilla=semilla)
    estado, x = partida.estado(ctx), semilla * 7919
    estados = [estado]
    if resumenes is not None:
        resumenes.append(resumen_vivo(ctx))
    for _ in range(pasos):
        if estado.terminado:
            break
        x = (x * 1103515245 + 12345) % 2147483648
        nuevo = acciones.ejecutar(ctx, _elegir_accion(estado, x))
        if nuevo.resultado is None or nuevo.terminado:             # la acción se hizo (no fue rechazada)
            estados.append(nuevo)
            if resumenes is not None:
                resumenes.append(resumen_vivo(ctx))
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


def probar_fr118_replay_hasta_da_el_estado_de_cada_instante(carpeta):
    instantes = 0
    con_cazador = 0
    for semilla in SEMILLAS:
        resumenes = []
        ruta, estados = _jugar(os.path.join(carpeta, f"a{semilla}"), semilla, resumenes=resumenes)
        n = len(resumenes) - 1
        if n < 1:
            continue
        servicio = ServicioReplayHasta(_partida(os.path.join(carpeta, f"h{semilla}"), semilla))
        for i in sorted({0, 1, n // 3, n // 2, (2 * n) // 3, n}):
            vivo = resumenes[i]
            resumen = servicio.reproducir_hasta(ruta, vivo.reloj)
            assert resumen == vivo, f"semilla {semilla}, t={vivo.reloj}: el resumen difiere del estado vivo"
            instantes += 1
            con_cazador += sum(1 for enemigo in vivo.enemigos if enemigo.comportamiento == "cazador")
        if estados[-1].terminado:                                  # FR-412: t posterior al final, el estado final
            resumen = servicio.reproducir_hasta(ruta, resumenes[-1].reloj + 100)
            assert resumen.terminada_antes and resumen.reloj == resumenes[-1].reloj, f"semilla {semilla}"
    assert instantes >= 20, f"solo se comprobaron {instantes} instantes"
    assert con_cazador > 0, "el cazador nunca estuvo a la vista en un instante comprobado"


class _ConPuertaFinal:
    """
    Mezcla para --verificar: las caras que entran a la sala 16 (la salida, desde la 12 y la 15) y las de vuelta
    quedan cerradas con itm_llave, y la llave está en la sala 6. Así la cuadrícula es resoluble con [itm_llave].
    """

    def obtener_pagina_salas(self, id_cripta, pagina, version):
        salas = super().obtener_pagina_salas(id_cripta, pagina, version)
        for sala in salas:
            for direccion, cara in enumerate(sala.salidas):
                if cara is not None and (sala.id == 16 or cara.sala_destino == 16):
                    sala.salidas[direccion] = SalidaDTO(cara.sala_destino, True, "itm_llave", None, cara.costo)
        return salas

    def obtener_llaves(self, id_cripta):
        return [UbicacionLlaveDTO("itm_llave", 6)]


class _CuadriculaConLlave(_ConPuertaFinal, FuenteCuadriculaConCazador):
    """La cuadrícula de las partidas (costos de la semilla, cazador y errante) con la puerta final."""


class _CuadriculaSinCostosNiCazador(_ConPuertaFinal, FuenteCuadricula):
    """La misma cuadrícula sin costos declarados y sin enemigos."""

    def __init__(self):
        super().__init__(4)


def probar_fr118_verificar_no_depende_de_costos_ni_cazadores(carpeta):
    def verificar(fuente, nombre):
        partida = ServicioPartida(ConfiguracionDTO(offline=True), fuente=fuente,
                                  carpeta_cache=os.path.join(carpeta, nombre, "cache"),
                                  carpeta_logs=os.path.join(carpeta, nombre, "logs"))
        return ServicioResolubilidad(partida).verificar("cuadricula")

    referencia = verificar(_CuadriculaSinCostosNiCazador(), "sin")
    assert referencia.veredicto == RESOLUBLE, referencia
    assert referencia.orden_llaves == ["itm_llave"], referencia
    for semilla in SEMILLAS:
        fuente = _CuadriculaConLlave(semilla)
        assert verificar(fuente, f"v{semilla}") == referencia, f"semilla {semilla}"
        assert fuente.lotes == [], "--verificar no debe pedir el contenido de las salas (003 R9)"
        costos = []
        for sala in fuente.obtener_pagina_salas("cuadricula", 1, "v"):
            for cara in sala.salidas:
                if cara is not None and cara.costo not in costos:
                    costos.append(cara.costo)
        assert len(costos) >= 4, f"costos: {costos}"              # la cuadrícula verificada sí tiene costos


def probar_fr118_modos_sin_vista_no_cargan_la_vista(carpeta):
    for nombre in sys.modules:
        assert nombre != "pygame" and not nombre.startswith(("pygame.", "View")), nombre


if __name__ == "__main__":
    for prueba in (probar_fr118_replay_reproduce_los_mismos_estados_con_costos_y_cazador,
                   probar_fr118_replay_hasta_da_el_estado_de_cada_instante,
                   probar_fr118_verificar_no_depende_de_costos_ni_cazadores,
                   probar_fr118_modos_sin_vista_no_cargan_la_vista):
        _correr(prueba)
    print("OK: todas las pruebas de los modos sin vista con terreno y cazador pasaron")
