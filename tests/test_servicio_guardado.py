"""
Pruebas de ServicioGuardado con el motor real, el paquete offline y el archivo binario de verdad.

Se juega, se guarda, se carga en un servicio NUEVO (con su propia fuente, caché y carpeta de logs, como al
abrir el programa otra vez) y se comprueba que la partida cargada es la misma. Se ejecuta desde cualquier carpeta.
"""
import os
import sys
from dataclasses import replace
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from Data import GuardadoBinario
from Data.BitacoraReplayIO import BitacoraReplayIO, ErrorBitacora
from Data.FuenteOffline import FuenteOffline
from DTO.AccionDTO import AccionDTO
from DTO.ConfiguracionDTO import ConfiguracionDTO
from Service.ServicioAccionJugador import ServicioAccionJugador
from Service.ServicioGuardado import ErrorCarga, ServicioGuardado
from Service.ServicioPartida import ServicioPartida
from Service.ServicioReplay import ServicioReplay
from Service.SincronizadorUsos import SincronizadorUsos
from test_servicios import ID_PERGAMINO, _correr, _crear, _elegir_accion, _verificar_marcas

ACCIONES = ServicioAccionJugador()


def _servicio_partida(carpeta):
    """Un servicio recién abierto: fuente, caché y logs propios."""
    return ServicioPartida(ConfiguracionDTO(offline=True), fuente=FuenteOffline(str(RAIZ / "paquete")),
                           carpeta_cache=os.path.join(carpeta, "cache"), carpeta_logs=os.path.join(carpeta, "logs"))


def _sin_mensajes(estado):
    """Los mensajes en pantalla no se guardan: se compara todo lo demás."""
    return replace(estado, mensajes=[])


def _siguiente_accion(estado, x):
    x = (x * 1103515245 + 12345) % 2147483648
    return _elegir_accion(estado, x), x


def _jugar(partida, ctx, estado, x, pasos):
    """Avanza hasta 'pasos' acciones elegidas mirando solo el estado. Devuelve (estado, x)."""
    for _ in range(pasos):
        if estado.terminado:
            break
        accion, x = _siguiente_accion(estado, x)
        estado = ACCIONES.ejecutar(ctx, accion)
    return estado, x


def _partida_guardada(carpeta, semilla, pasos=8, **opciones):
    """Juega una partida, la guarda y devuelve (servicio, contexto, estado, x, ruta del archivo)."""
    partida, _, ctx = _crear(os.path.join(carpeta, "a"), semilla=semilla, **opciones)
    estado, x = _jugar(partida, ctx, partida.estado(ctx), semilla * 7919, pasos)
    ruta = os.path.join(carpeta, "saves", "partida.sav")        # la carpeta no existe: Datos la crea
    ServicioGuardado(partida).guardar(ctx, ruta)
    return partida, ctx, estado, x, ruta


def _leer(ruta):
    with open(ruta, encoding="utf-8", newline="") as archivo:
        return archivo.read()


def _escribir(ruta, texto):
    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
        archivo.write(texto)


def probar_guardar_y_cargar_deja_el_mismo_estado(carpeta):
    partida, ctx, estado, _, ruta = _partida_guardada(carpeta, 3, reforzar=True)
    assert os.path.isfile(ruta)
    nueva = _servicio_partida(os.path.join(carpeta, "b"))
    ctx2 = ServicioGuardado(nueva).cargar(ruta, "Beto")
    assert _sin_mensajes(nueva.estado(ctx2)) == _sin_mensajes(estado)
    assert ctx2.semilla == 3 and ctx2.nombre_jugador == "Beto" and ctx2.cripta.id == ctx.cripta.id
    assert nueva.puntaje(ctx2).nombre == "Beto"
    _verificar_marcas(ctx2)                                      # las fichas en uso quedaron marcadas en la caché
    assert ctx2.fuente.solicitudes_realizadas() == 0             # --offline no gasta solicitudes


def probar_la_partida_cargada_continua_igual_que_la_original(carpeta):
    total = 0
    for semilla in (1, 2, 3, 4):
        base = os.path.join(carpeta, f"s{semilla}")
        partida, ctx, estado, x, ruta = _partida_guardada(base, semilla, reforzar=True)
        nueva = _servicio_partida(os.path.join(base, "b"))
        ctx2 = ServicioGuardado(nueva).cargar(ruta, "Ana")
        pasos = []                                               # la original sigue; se anota cada paso
        for _ in range(25):
            if estado.terminado:
                break
            accion, x = _siguiente_accion(estado, x)
            estado = ACCIONES.ejecutar(ctx, accion)
            pasos.append((accion, _sin_mensajes(estado)))
        for numero, (accion, esperado) in enumerate(pasos, 1):   # la cargada hace lo mismo: mismo azar, eventos y efectos
            assert _sin_mensajes(ACCIONES.ejecutar(ctx2, accion)) == esperado, f"semilla {semilla}, paso {numero}: {accion}"
        total += len(pasos)
    assert total >= 40, "las partidas de prueba fueron demasiado cortas"


def probar_el_historial_no_se_guarda(carpeta):
    partida, _, ctx = _crear(os.path.join(carpeta, "a"), semilla=2, reforzar=True)
    _jugar(partida, ctx, partida.estado(ctx), 2 * 7919, 3)                 # 3 acciones: se podrían deshacer...
    ctx.inventario.recoger(ctx.resolvedor.ficha(ID_PERGAMINO))             # ...y un pergamino llega justo antes de guardar
    SincronizadorUsos().sincronizar(ctx)
    ruta = os.path.join(carpeta, "partida.sav")
    ServicioGuardado(partida).guardar(ctx, ruta)
    nueva = _servicio_partida(os.path.join(carpeta, "b"))
    ctx2 = ServicioGuardado(nueva).cargar(ruta, "Ana")
    base = nueva.estado(ctx2)
    rechazado = ACCIONES.ejecutar(ctx2, AccionDTO("retroceder"))            # lo anterior a cargar no se puede deshacer
    assert "No hay nada que deshacer" in rechazado.resultado
    assert rechazado.inventario.capacidad == base.inventario.capacidad      # y el pergamino no se gastó
    ACCIONES.ejecutar(ctx2, AccionDTO("esperar"))
    despues = ACCIONES.ejecutar(ctx2, AccionDTO("retroceder"))              # desde la primera acción nueva, sí
    assert despues.resultado is None
    assert (despues.reloj, despues.jugador, despues.enemigos, despues.sala, despues.efectos) == \
           (base.reloj, base.jugador, base.enemigos, base.sala, base.efectos)
    assert despues.inventario.capacidad == base.inventario.capacidad - 1    # el pergamino se consumió


def probar_el_log_continua_en_un_archivo_nuevo(carpeta):
    partida, ctx, estado, x, ruta = _partida_guardada(carpeta, 4, pasos=6, reforzar=True)
    n, log_anterior = ctx.bitacora.acciones_escritas(), ctx.bitacora.ruta()
    assert n >= 3
    _jugar(partida, ctx, estado, x, 3)                           # la original sigue y SU log crece
    texto_anterior = _leer(log_anterior)

    nueva = _servicio_partida(os.path.join(carpeta, "b"))
    ctx2 = ServicioGuardado(nueva).cargar(ruta, "Ana")
    assert ctx2.bitacora.ruta() != log_anterior and ctx2.bitacora.acciones_escritas() == n
    assert BitacoraReplayIO.leer(ctx2.bitacora.ruta()).acciones == BitacoraReplayIO.leer(log_anterior).acciones[:n]
    _jugar(nueva, ctx2, nueva.estado(ctx2), 99, 3)               # la cargada sigue en su log nuevo
    assert ctx2.bitacora.acciones_escritas() > n
    assert _leer(log_anterior) == texto_anterior                 # el anterior no se tocó


def probar_el_replay_de_una_partida_guardada_y_continuada(carpeta):
    """Sin ayudas (jugador normal): guardar, cargar, seguir jugando y reproducir el log completo da lo mismo."""
    for semilla in range(1, 40):
        base = os.path.join(carpeta, f"s{semilla}")
        partida, _, ctx = _crear(os.path.join(base, "a"), semilla=semilla)
        estado, x = _jugar(partida, ctx, partida.estado(ctx), semilla * 7919, 3)
        if estado.terminado or ctx.bitacora.acciones_escritas() < 2:
            continue
        ruta = os.path.join(base, "p.sav")
        ServicioGuardado(partida).guardar(ctx, ruta)
        nueva = _servicio_partida(os.path.join(base, "b"))
        ctx2 = ServicioGuardado(nueva).cargar(ruta, "Ana")
        antes = ctx2.bitacora.acciones_escritas()
        estado2, _ = _jugar(nueva, ctx2, nueva.estado(ctx2), x, 6)
        if ctx2.bitacora.acciones_escritas() == antes:
            continue
        resultado = ServicioReplay(_servicio_partida(os.path.join(base, "c"))).reproducir(ctx2.bitacora.ruta())
        assert resultado.acciones_reproducidas == ctx2.bitacora.acciones_escritas()
        assert _sin_mensajes(resultado.estado_final) == _sin_mensajes(estado2)
        return
    raise AssertionError("ninguna partida de prueba sirvió para armar el caso")


def probar_guardar_no_cambia_la_partida(carpeta):
    partida, _, ctx = _crear(os.path.join(carpeta, "a"), semilla=5, reforzar=True)
    _jugar(partida, ctx, partida.estado(ctx), 5 * 7919, 6)
    antes, escritas = partida.estado(ctx), ctx.bitacora.acciones_escritas()
    texto, deshacibles = _leer(ctx.bitacora.ruta()), ctx.motor.historial.cantidad()
    ServicioGuardado(partida).guardar(ctx, os.path.join(carpeta, "p.sav"))
    assert partida.estado(ctx) == antes and ctx.bitacora.acciones_escritas() == escritas
    assert _leer(ctx.bitacora.ruta()) == texto and ctx.motor.historial.cantidad() == deshacibles


def probar_guardar_una_partida_ya_cargada(carpeta):
    partida, ctx, _, x, ruta = _partida_guardada(carpeta, 6, reforzar=True)
    nueva = _servicio_partida(os.path.join(carpeta, "b"))
    ctx2 = ServicioGuardado(nueva).cargar(ruta, "Ana")
    estado2, _ = _jugar(nueva, ctx2, nueva.estado(ctx2), x, 5)
    ruta2 = os.path.join(carpeta, "saves", "segunda.sav")
    ServicioGuardado(nueva).guardar(ctx2, ruta2)
    tercera = _servicio_partida(os.path.join(carpeta, "c"))
    ctx3 = ServicioGuardado(tercera).cargar(ruta2, "Ana")
    assert _sin_mensajes(tercera.estado(ctx3)) == _sin_mensajes(estado2)
    assert ctx3.bitacora.acciones_escritas() == ctx2.bitacora.acciones_escritas()
    assert ctx3.bitacora.ruta() not in (ctx2.bitacora.ruta(), ctx.bitacora.ruta())     # la cadena de logs sigue


def probar_una_partida_sin_log_se_guarda_y_se_carga(carpeta):
    partida, _, ctx = _crear(os.path.join(carpeta, "a"), semilla=2, bitacora=False, reforzar=True)
    estado, _ = _jugar(partida, ctx, partida.estado(ctx), 2 * 7919, 5)
    ruta = os.path.join(carpeta, "sin_log.sav")
    ServicioGuardado(partida).guardar(ctx, ruta)
    nueva = _servicio_partida(os.path.join(carpeta, "b"))
    ctx2 = ServicioGuardado(nueva).cargar(ruta, "Ana")
    assert ctx2.bitacora is None and _sin_mensajes(nueva.estado(ctx2)) == _sin_mensajes(estado)
    assert not os.path.exists(os.path.join(carpeta, "b", "logs"))


def probar_al_cargar_los_mensajes_empiezan_con_el_aviso(carpeta):
    _, _, _, _, ruta = _partida_guardada(carpeta, 3, reforzar=True)
    nueva = _servicio_partida(os.path.join(carpeta, "b"))
    mensajes = nueva.estado(ServicioGuardado(nueva).cargar(ruta, "Ana")).mensajes
    assert len(mensajes) == 1 and "Partida cargada" in mensajes[0]


def probar_una_version_distinta_no_se_carga(carpeta):
    _, _, _, _, ruta = _partida_guardada(carpeta, 3, reforzar=True)
    dto, salas = GuardadoBinario.cargar(ruta), GuardadoBinario.cargar_salas(ruta)
    for campo, texto in (("version_cripta", "versión"), ("version_catalogo", "catálogo")):
        alterada = os.path.join(carpeta, f"{campo}.sav")
        GuardadoBinario.guardar(alterada, replace(dto, **{campo: "000000000000"}), salas)
        base = os.path.join(carpeta, f"b_{campo}")
        try:
            ServicioGuardado(_servicio_partida(base)).cargar(alterada, "Ana")
        except ErrorCarga as error:
            assert "No se puede continuar esa partida" in str(error) and texto in str(error)
            assert not os.path.exists(os.path.join(base, "logs"))              # no dejó ningún log suelto
            continue
        raise AssertionError("Debió lanzar ErrorCarga")


def probar_un_archivo_inexistente_o_danado_se_informa(carpeta):
    nueva = _servicio_partida(os.path.join(carpeta, "b"))
    basura = os.path.join(carpeta, "basura.sav")
    with open(basura, "wb") as archivo:
        archivo.write(b"esto no es una partida")
    for ruta in (os.path.join(carpeta, "no_existe.sav"), basura):
        try:
            ServicioGuardado(nueva).cargar(ruta, "Ana")
        except GuardadoBinario.ErrorGuardado:
            continue
        raise AssertionError("Debió lanzar ErrorGuardado")


def probar_si_el_log_anterior_no_cuadra_no_se_carga_ni_se_crea_nada(carpeta):
    partida, ctx, _, _, ruta = _partida_guardada(carpeta, 4, pasos=6, reforzar=True)
    log = ctx.bitacora.ruta()
    texto = _leer(log)
    assert ctx.bitacora.acciones_escritas() >= 2
    # 1) el log tiene MENOS acciones de las que la partida guardada necesita
    lineas = texto.rstrip("\n").split("\n")
    _escribir(log, "\n".join(lineas[:-1]) + "\n")
    # 2) el log se borró
    for caso, preparar in (("incompleto", lambda: None), ("borrado", lambda: os.remove(log))):
        preparar()
        base = os.path.join(carpeta, f"b_{caso}")
        try:
            ServicioGuardado(_servicio_partida(base)).cargar(ruta, "Ana")
        except ErrorBitacora:
            assert not os.path.exists(os.path.join(base, "logs")), caso
            continue
        raise AssertionError(f"Debió lanzar ErrorBitacora ({caso})")


if __name__ == "__main__":
    for prueba in (probar_guardar_y_cargar_deja_el_mismo_estado, probar_la_partida_cargada_continua_igual_que_la_original,
                   probar_el_historial_no_se_guarda, probar_el_log_continua_en_un_archivo_nuevo,
                   probar_el_replay_de_una_partida_guardada_y_continuada, probar_guardar_no_cambia_la_partida,
                   probar_guardar_una_partida_ya_cargada, probar_una_partida_sin_log_se_guarda_y_se_carga,
                   probar_al_cargar_los_mensajes_empiezan_con_el_aviso, probar_una_version_distinta_no_se_carga,
                   probar_un_archivo_inexistente_o_danado_se_informa,
                   probar_si_el_log_anterior_no_cuadra_no_se_carga_ni_se_crea_nada):
        _correr(prueba)
    print("OK: todas las pruebas de ServicioGuardado pasaron")