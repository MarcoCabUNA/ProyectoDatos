"""
Pruebas de ServicioReplay con el motor real y el paquete offline.

Se juega una partida sin ayudas (jugador normal, como la verá el replay), se lee su log y se reproduce en una
partida nueva con su propia fuente y caché. Se ejecuta desde cualquier carpeta.
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))          # para reutilizar los ayudantes de test_servicios

from Data.BitacoraReplayIO import BitacoraReplayIO, ErrorBitacora
from Data.FuenteOffline import FuenteOffline
from DTO.ConfiguracionDTO import ConfiguracionDTO
from Service.ServicioPartida import ServicioPartida
from Service.ServicioReplay import ErrorReplay, ServicioReplay
from test_servicios import _correr, _crear, _elegir_accion


def _servicio_para_reproducir(carpeta):
    fuente = FuenteOffline(str(RAIZ / "paquete"))
    partida = ServicioPartida(ConfiguracionDTO(offline=True), fuente=fuente,
                              carpeta_cache=os.path.join(carpeta, "cache"), carpeta_logs=os.path.join(carpeta, "logs"))
    return ServicioReplay(partida)


def _jugar(carpeta, semilla, pasos=40):
    """Una partida normal. Devuelve (ruta del log, estados[0..n]: el estado tras cada acción hecha)."""
    partida, acciones, ctx = _crear(carpeta, semilla=semilla)
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


def _leer(ruta):
    with open(ruta, encoding="utf-8", newline="") as archivo:
        return archivo.read()


def _escribir(ruta, texto):
    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
        archivo.write(texto)


def probar_reproducir_da_exactamente_la_misma_partida(carpeta):
    total = 0
    for semilla in (1, 2, 3, 4, 5, 6, 7, 8):
        ruta, estados = _jugar(os.path.join(carpeta, f"a{semilla}"), semilla)
        n = len(estados) - 1
        if n < 1:
            continue
        texto_antes = _leer(ruta)
        carpeta_b = os.path.join(carpeta, f"b{semilla}")
        avances = []
        resultado = _servicio_para_reproducir(carpeta_b).reproducir(ruta, al_avanzar=lambda i, a, e: avances.append(i))
        assert resultado.estado_final == estados[-1], f"semilla {semilla}: terminó en otro estado"
        assert resultado.acciones_reproducidas == n and avances == list(range(1, n + 1))
        assert resultado.encabezado.semilla == semilla and not resultado.ultima_linea_descartada
        assert _leer(ruta) == texto_antes                          # no toca el log que reproduce
        assert not os.path.exists(os.path.join(carpeta_b, "logs"))  # y no escribe uno nuevo
        total += n
    assert total >= 20, "las partidas fueron demasiado cortas para que la prueba valga"


def probar_una_version_de_cripta_distinta_se_rechaza_sin_ejecutar_nada(carpeta):
    ruta, estados = _jugar(os.path.join(carpeta, "a"), 3)
    version = BitacoraReplayIO.leer(ruta).encabezado.version_cripta
    alterado = os.path.join(carpeta, "version_vieja.log")
    _escribir(alterado, _leer(ruta).replace(f"version_cripta={version}", "version_cripta=000000000000"))
    avances = []
    try:
        _servicio_para_reproducir(os.path.join(carpeta, "b")).reproducir(alterado, al_avanzar=lambda *_: avances.append(1))
    except ErrorReplay as error:
        assert "No se puede garantizar una reproducción fiel" in str(error) and "000000000000" in str(error)
        assert avances == []
        return
    raise AssertionError("Debió lanzar ErrorReplay")


def probar_una_version_de_catalogo_distinta_se_rechaza(carpeta):
    ruta, _ = _jugar(os.path.join(carpeta, "a"), 3)
    version = BitacoraReplayIO.leer(ruta).encabezado.version_catalogo
    alterado = os.path.join(carpeta, "catalogo_viejo.log")
    _escribir(alterado, _leer(ruta).replace(f"version_catalogo={version}", "version_catalogo=000000000000"))
    try:
        _servicio_para_reproducir(os.path.join(carpeta, "b")).reproducir(alterado)
    except ErrorReplay as error:
        assert "catálogo" in str(error)
        return
    raise AssertionError("Debió lanzar ErrorReplay")


def probar_una_accion_imposible_detiene_el_replay(carpeta):
    ruta, _ = _jugar(os.path.join(carpeta, "a"), 3, pasos=0)         # un log con solo el encabezado
    with open(ruta, "a", encoding="utf-8", newline="") as archivo:
        archivo.write("esperar|||\natacar||e-999|\n")
    avances = []
    try:
        _servicio_para_reproducir(os.path.join(carpeta, "b")).reproducir(ruta, al_avanzar=lambda i, a, e: avances.append(i))
    except ErrorReplay as error:
        assert "acción 2" in str(error) and "no se pudo hacer" in str(error)
        assert avances == [1]                                        # la primera sí se reprodujo
        return
    raise AssertionError("Debió lanzar ErrorReplay")


def probar_acciones_despues_de_terminar_la_partida(carpeta):
    for semilla in range(1, 60):
        ruta, estados = _jugar(os.path.join(carpeta, f"a{semilla}"), semilla)
        if estados[-1].terminado:
            break
    else:
        raise AssertionError("ninguna partida de prueba terminó: no se pudo armar el caso")
    with open(ruta, "a", encoding="utf-8", newline="") as archivo:
        archivo.write("esperar|||\n")                                # una acción que nunca pudo ocurrir
    try:
        _servicio_para_reproducir(os.path.join(carpeta, "b")).reproducir(ruta)
    except ErrorReplay as error:
        assert "ya había terminado" in str(error)
        return
    raise AssertionError("Debió lanzar ErrorReplay")


def probar_un_log_ilegible_propaga_el_error_de_datos(carpeta):
    ruta = os.path.join(carpeta, "basura.log")
    _escribir(ruta, "esto no es un log\n")
    try:
        _servicio_para_reproducir(os.path.join(carpeta, "b")).reproducir(ruta)
    except ErrorBitacora:
        return
    raise AssertionError("Debió lanzar ErrorBitacora")


def probar_la_ultima_linea_a_medio_escribir_se_ignora_y_se_avisa(carpeta):
    ruta, estados = _jugar(os.path.join(carpeta, "a"), 4)
    n = len(estados) - 1
    assert n >= 3
    cortado = os.path.join(carpeta, "cortado.log")
    _escribir(cortado, _leer(ruta).rstrip("\n")[:-1])                # sin el salto final y con el último carácter menos
    resultado = _servicio_para_reproducir(os.path.join(carpeta, "b")).reproducir(cortado)
    assert resultado.ultima_linea_descartada and resultado.acciones_reproducidas == n - 1
    assert resultado.estado_final == estados[n - 1]


if __name__ == "__main__":
    for prueba in (probar_reproducir_da_exactamente_la_misma_partida,
                   probar_una_version_de_cripta_distinta_se_rechaza_sin_ejecutar_nada,
                   probar_una_version_de_catalogo_distinta_se_rechaza,
                   probar_una_accion_imposible_detiene_el_replay,
                   probar_acciones_despues_de_terminar_la_partida,
                   probar_un_log_ilegible_propaga_el_error_de_datos,
                   probar_la_ultima_linea_a_medio_escribir_se_ignora_y_se_avisa):
        _correr(prueba)
    print("OK: todas las pruebas de ServicioReplay pasaron")