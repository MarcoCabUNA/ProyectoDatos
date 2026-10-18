"""
Pruebas de la capa de Servicios con el motor REAL y el paquete offline (<raiz>/paquete).

ServicioPartida, ServicioAccionJugador y ServicioInventario se prueban como los usaría la Vista: solo
con DTOs (EstadoJuegoDTO, InventarioDTO, AccionDTO). Cada prueba usa carpetas temporales para la caché y
los logs. Se ejecuta desde cualquier carpeta.
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from Data.BitacoraReplayIO import BitacoraReplayIO
from Data.ClienteHttp import ErrorRed
from Data.FuenteOffline import FuenteOffline
from Data.FuenteRed import FuenteRed
from DTO.AccionDTO import AccionDTO
from DTO.ConfiguracionDTO import ConfiguracionDTO
from DTO.ObjetoDTO import ObjetoDTO
from Service.ServicioAccionJugador import ServicioAccionJugador
from Service.ServicioGuardado import ServicioGuardado
from Service.ServicioInventario import ServicioInventario
from Service.ServicioPartida import ServicioPartida
from Service.SincronizadorUsos import SincronizadorUsos

ID_CRIPTA = "cripta-01"
ID_PERGAMINO = "itm_pergamino_retroceso"
NORTE, SUR, ESTE, OESTE = 0, 1, 2, 3


def _correr(prueba):
    carpeta = tempfile.mkdtemp()
    try:
        prueba(carpeta)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def _crear(carpeta, semilla=2026, bitacora=True, pergaminos=0, reforzar=False):
    config = ConfiguracionDTO(offline=True, cache_size=25)
    fuente = FuenteOffline(str(RAIZ / "paquete"))
    partida = ServicioPartida(config, fuente=fuente, carpeta_cache=os.path.join(carpeta, "cache"),
                              carpeta_logs=os.path.join(carpeta, "logs"))
    contexto = partida.iniciar_partida(ID_CRIPTA, "Ana", semilla=semilla, registrar_bitacora=bitacora)
    if reforzar:                                   # un jugador fuerte, para que la partida dure
        contexto.jugador.vida = contexto.jugador.vida_Max = 400
        contexto.jugador.ataque = 12
    for _ in range(pergaminos):                    # el pergamino queda fuera del historial (§2.11)
        contexto.inventario.recoger(contexto.resolvedor.ficha(ID_PERGAMINO))
    if pergaminos:                                 # se tocó el inventario por fuera de los servicios: se avisa a la caché
        SincronizadorUsos().sincronizar(contexto)
    return partida, ServicioAccionJugador(), contexto


def _verificar_marcas(ctx):
    """Las marcas de uso REALES de la caché deben coincidir con lo que dice el estado del juego."""
    cache = ctx.resolvedor._cache                    # las pruebas pueden mirar adentro; Servicios no
    en_uso = SincronizadorUsos().ids_en_uso(ctx)
    for id_ficha in en_uso:
        assert cache.contiene(id_ficha) and cache.esta_en_uso(id_ficha), f"{id_ficha} debería estar en uso"
    for id_ficha in cache.ids_en_memoria():
        assert cache.esta_en_uso(id_ficha) == (id_ficha in en_uso), f"marca equivocada en {id_ficha}"


def _en_carpeta(carpeta, funcion):
    """Ejecuta 'funcion' con 'carpeta' como directorio de trabajo (así se prueban las rutas por omisión)."""
    anterior = os.getcwd()
    os.chdir(carpeta)
    try:
        funcion()
    finally:
        os.chdir(anterior)


def probar_la_fuente_por_omision_sale_de_la_configuracion(carpeta):
    # --offline sin fuente inyectada: FuenteOffline lee el paquete de la carpeta de trabajo
    def sin_red():
        partida = ServicioPartida(ConfiguracionDTO(offline=True), carpeta_cache=os.path.join(carpeta, "cache"),
                                  carpeta_logs=os.path.join(carpeta, "logs"))
        assert isinstance(partida.fuente(), FuenteOffline)
        ctx = partida.iniciar_partida(ID_CRIPTA, "Ana", semilla=1)
        assert ctx.cripta.id == ID_CRIPTA
    _en_carpeta(RAIZ, sin_red)
    # sin --offline: se crea la fuente de red (crearla no hace ninguna solicitud)
    assert isinstance(ServicioPartida(ConfiguracionDTO(offline=False)).fuente(), FuenteRed)


def probar_la_cache_por_omision_vive_en_la_carpeta_de_trabajo(carpeta):
    def con_cache_por_omision():
        config = ConfiguracionDTO(offline=True)
        partida = ServicioPartida(config, fuente=FuenteOffline(str(RAIZ / "paquete")),
                                  carpeta_logs=os.path.join(carpeta, "logs"))
        partida.iniciar_partida(ID_CRIPTA, "Ana", semilla=1)
        assert os.path.isdir(os.path.join(carpeta, "cache", "catalogo"))
    _en_carpeta(carpeta, con_cache_por_omision)


def probar_listar_criptas(carpeta):
    partida, _, _ = _crear(carpeta)
    assert ID_CRIPTA in [c.id for c in partida.listar_criptas()]


def probar_estado_inicial(carpeta):
    partida, _, ctx = _crear(carpeta)
    estado = partida.estado(ctx)
    assert estado.sala.id == ctx.cripta.sala_inicial and estado.sala.contenido_cargado
    assert estado.reloj == 0 and not estado.terminado and estado.resultado is None
    assert estado.jugador.id == "jugador" and estado.jugador.vida == ctx.cripta.jugador_vida_max
    assert estado.inventario.capacidad == 0 and estado.inventario.capacidad_maxima == ctx.cripta.inventario_max
    assert any("Comienzas en" in m for m in estado.mensajes)
    assert len(estado.objetos_suelo) == len(ctx.mazmorra.sala(ctx.cripta.sala_inicial).objetos)
    assert ctx.fuente.solicitudes_realizadas() == 0          # --offline no gasta solicitudes
    _verificar_marcas(ctx)


def probar_el_estado_trae_la_sala_inicial_y_la_de_salida(carpeta):
    with open(RAIZ / "paquete" / ID_CRIPTA / "general.json", encoding="utf-8") as archivo:
        general = json.load(archivo)                     # lo esperado sale del paquete, no se escribe fijo
    partida, acciones, ctx = _crear(carpeta)
    estado = partida.estado(ctx)
    assert estado.sala_inicial == estado.sala.id == general["sala_inicial"]
    assert estado.sala_salida == general["sala_salida"] != estado.sala_inicial
    estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=NORTE))
    assert estado.sala.id != general["sala_inicial"]                 # se movió de verdad...
    assert (estado.sala_inicial, estado.sala_salida) == (general["sala_inicial"], general["sala_salida"])
    ruta = os.path.join(carpeta, "saves", "partida.sav")
    ServicioGuardado(partida).guardar(ctx, ruta)
    nueva, _, _ = _crear(os.path.join(carpeta, "b"))
    estado2 = nueva.estado(ServicioGuardado(nueva).cargar(ruta, "Ana"))
    assert (estado2.sala_inicial, estado2.sala_salida) == (general["sala_inicial"], general["sala_salida"])


def probar_la_bitacora_nace_con_su_encabezado(carpeta):
    partida, _, ctx = _crear(carpeta, semilla=777)
    leido = BitacoraReplayIO.leer(ctx.bitacora.ruta())
    assert leido.acciones == [] and leido.encabezado.semilla == 777
    assert leido.encabezado.id_cripta == ID_CRIPTA and leido.encabezado.version_cripta == ctx.cripta.version
    assert leido.encabezado.version_catalogo == ctx.resolvedor.version_catalogo()


def probar_dos_partidas_con_la_misma_semilla_no_pisan_su_log(carpeta):
    _, _, a = _crear(carpeta, semilla=5)
    _, _, b = _crear(carpeta, semilla=5)
    assert a.bitacora.ruta() != b.bitacora.ruta()


def probar_semilla_automatica(carpeta):
    config = ConfiguracionDTO(offline=True)
    partida = ServicioPartida(config, fuente=FuenteOffline(str(RAIZ / "paquete")),
                              carpeta_cache=os.path.join(carpeta, "c"), carpeta_logs=os.path.join(carpeta, "l"))
    ctx = partida.iniciar_partida(ID_CRIPTA, "Ana")
    assert isinstance(ctx.semilla, int) and ctx.semilla > 0
    assert BitacoraReplayIO.leer(ctx.bitacora.ruta()).encabezado.semilla == ctx.semilla


def probar_mover_carga_la_sala_y_se_anota_en_el_log(carpeta):
    partida, acciones, ctx = _crear(carpeta)
    assert not ctx.mazmorra.contenido_cargado(2)
    estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=NORTE))
    assert estado.resultado is None and estado.sala.id == 2 and ctx.mazmorra.contenido_cargado(2)
    assert estado.reloj > 0 and len(estado.enemigos) == 2
    assert BitacoraReplayIO.leer(ctx.bitacora.ruta()).acciones == [AccionDTO("mover", direccion=NORTE)]


def probar_las_acciones_rechazadas_no_cambian_nada(carpeta):
    partida, acciones, ctx = _crear(carpeta)
    antes = partida.estado(ctx)
    for accion, texto in ((AccionDTO("mover", direccion=SUR), "No hay salida"),
                          (AccionDTO("abrir", direccion=NORTE), "No hay nada que abrir"),
                          (AccionDTO("atacar", objetivo="e-999"), "no está en esta sala"),
                          (AccionDTO("recoger", objeto="itm_inexistente"), "No hay"),
                          (AccionDTO("mover"), "Dirección inválida"),
                          (AccionDTO("mover", direccion=9), "Dirección inválida"),
                          (AccionDTO("abrir"), "Dirección inválida"),
                          (AccionDTO("abrir", direccion=-1), "Dirección inválida"),
                          (AccionDTO("atacar"), "Falta indicar"),
                          (AccionDTO("usar"), "Falta indicar"),
                          (AccionDTO("retroceder"), "No tienes ningún pergamino"),
                          (AccionDTO("volar"), "Acción desconocida")):
        estado = acciones.ejecutar(ctx, accion)
        assert estado.resultado is not None and texto in estado.resultado, (accion, estado.resultado)
        assert estado.reloj == antes.reloj and ctx.jugador.acciones == 0
    assert BitacoraReplayIO.leer(ctx.bitacora.ruta()).acciones == []      # lo rechazado no es una acción


def probar_abrir_una_puerta_se_ve_en_el_estado(carpeta):
    partida, acciones, ctx = _crear(carpeta, reforzar=True)
    llave = ctx.mazmorra.llave_requerida(2, ESTE)                        # la que pide la puerta E de la sala 2
    ctx.inventario.recoger(ctx.resolvedor.ficha(llave))
    estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=NORTE))
    assert estado.sala.salidas[ESTE].cerrada
    estado = acciones.ejecutar(ctx, AccionDTO("abrir", direccion=ESTE))
    assert estado.resultado is None and not estado.sala.salidas[ESTE].cerrada       # el estado muestra la puerta ahora
    assert ctx.esqueleto.obtener_sala(2).salidas[ESTE].cerrada                      # el esqueleto original no cambió
    assert "Abres la puerta" in estado.mensajes[-1] or any("Abres la puerta" in m for m in estado.mensajes)
    assert llave in [o.id for o in estado.inventario.objetos]                        # la llave no se consume
    estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=ESTE))
    assert estado.resultado is None and estado.sala.id == 5


def probar_recoger_usar_y_soltar(carpeta):
    partida, acciones, ctx = _crear(carpeta, reforzar=True)
    antorcha = partida.estado(ctx).objetos_suelo[0]
    estado = acciones.ejecutar(ctx, AccionDTO("recoger", objeto=antorcha.id))
    assert estado.resultado is None and estado.objetos_suelo == [] and estado.inventario.capacidad == 1
    assert estado.sala.objetos == []                                      # la sala del estado también muestra el suelo actual
    estado = acciones.ejecutar(ctx, AccionDTO("soltar", objeto=antorcha.id))
    assert estado.inventario.capacidad == 0 and [o.id for o in estado.objetos_suelo] == [antorcha.id]
    assert estado.sala.objetos == [antorcha.id]
    acciones.ejecutar(ctx, AccionDTO("recoger", objeto=antorcha.id))
    estado = acciones.ejecutar(ctx, AccionDTO("usar", objeto=antorcha.id))
    assert estado.inventario.capacidad == 1 and [e.tipo for e in estado.efectos] == ["antorcha"]   # no se gasta al usarla
    assert estado.efectos[0].restante > 0
    estado = acciones.ejecutar(ctx, AccionDTO("soltar", objeto=antorcha.id))
    assert estado.inventario.capacidad == 0 and estado.efectos == []                              # soltarla apaga el velo


def probar_equipar_sube_el_ataque_y_lo_muestra(carpeta):
    partida, acciones, ctx = _crear(carpeta, reforzar=True)
    acciones.ejecutar(ctx, AccionDTO("mover", direccion=NORTE))
    daga = [o for o in partida.estado(ctx).objetos_suelo if o.clase == "arma"][0]
    ataque_antes = partida.estado(ctx).jugador.ataque
    acciones.ejecutar(ctx, AccionDTO("recoger", objeto=daga.id))
    estado = acciones.ejecutar(ctx, AccionDTO("equipar", objeto=daga.id))
    assert estado.inventario.arma_equipada == daga.id
    assert estado.jugador.ataque == ataque_antes + daga.ataque_bonus
    assert estado.inventario.objetos[0].id == daga.id                    # equipar la mueve al frente


def probar_la_sala_del_estado_no_trae_datos_viejos_de_enemigos_ni_trampas(carpeta):
    partida, acciones, ctx = _crear(carpeta, reforzar=True)
    estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=NORTE))
    assert len(estado.enemigos) == 2                                     # lo vivo, aparte
    assert estado.sala.enemigos == [] and estado.sala.trampas == []      # el contenido inicial ya no es cierto
    estado = acciones.ejecutar(ctx, AccionDTO("atacar", objetivo=estado.enemigos[0].id))
    assert estado.sala.enemigos == []                                    # ni siquiera con una rata herida


def probar_derrotar_enemigos_suelta_objetos(carpeta):
    partida, acciones, ctx = _crear(carpeta, reforzar=True)
    estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=NORTE))
    while estado.enemigos and not estado.terminado:
        estado = acciones.ejecutar(ctx, AccionDTO("atacar", objetivo=estado.enemigos[0].id))
    assert estado.enemigos == [] and partida.puntaje(ctx).enemigos_derrotados == 2
    assert [o for o in estado.objetos_suelo if o.clase == "pocion"]       # lo que suelta la rata
    assert any("muere" in m for m in estado.mensajes)


def probar_retroceder_deshace_la_ultima_accion(carpeta):
    partida, acciones, ctx = _crear(carpeta, pergaminos=1)
    antes = partida.estado(ctx)
    acciones.ejecutar(ctx, AccionDTO("esperar"))
    assert partida.estado(ctx).reloj > antes.reloj and ctx.jugador.acciones == 1
    estado = acciones.ejecutar(ctx, AccionDTO("retroceder"))
    assert estado.resultado is None and estado.reloj == antes.reloj and ctx.jugador.acciones == 0
    assert estado.inventario.capacidad == 0                              # el pergamino se consumió
    acciones_en_log = BitacoraReplayIO.leer(ctx.bitacora.ruta()).acciones
    assert acciones_en_log == [AccionDTO("esperar"), AccionDTO("retroceder")]


def probar_retroceder_sin_historial_no_gasta_el_pergamino(carpeta):
    partida, acciones, ctx = _crear(carpeta, pergaminos=1)
    estado = acciones.ejecutar(ctx, AccionDTO("retroceder"))
    assert "No hay nada que deshacer" in estado.resultado and estado.inventario.capacidad == 1


def probar_usar_un_pergamino_es_lo_mismo_que_retroceder(carpeta):
    partida, acciones, ctx = _crear(carpeta, pergaminos=1)
    acciones.ejecutar(ctx, AccionDTO("esperar"))
    estado = acciones.ejecutar(ctx, AccionDTO("usar", objeto=ID_PERGAMINO))
    assert estado.resultado is None and ctx.jugador.acciones == 0 and estado.reloj == 0


def probar_retroceder_revive_al_enemigo_y_resincroniza_las_fichas(carpeta):
    partida, acciones, ctx = _crear(carpeta, reforzar=True, pergaminos=1)
    estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=NORTE))
    sync = SincronizadorUsos()
    while len(estado.enemigos) == 2:
        estado = acciones.ejecutar(ctx, AccionDTO("atacar", objetivo=estado.enemigos[0].id))
    assert len(estado.enemigos) == 1 and sync.ids_en_uso(ctx).count("ent_rata_gigante") == 1
    estado = acciones.ejecutar(ctx, AccionDTO("retroceder"))
    assert len(estado.enemigos) == 2 and sync.ids_en_uso(ctx).count("ent_rata_gigante") == 2
    _verificar_marcas(ctx)                                               # y la caché también se enteró


def probar_con_la_partida_terminada_no_se_acepta_nada(carpeta):
    partida, acciones, ctx = _crear(carpeta, pergaminos=1)
    ctx.jugador.vida = 1                                                 # la trampa de la sala 2 lo mata
    estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=NORTE))
    assert estado.terminado and estado.resultado == "derrota"
    reloj, escritas = estado.reloj, ctx.bitacora.acciones_escritas()
    for accion in (AccionDTO("esperar"), AccionDTO("retroceder"), AccionDTO("mover", direccion=SUR)):
        nuevo = acciones.ejecutar(ctx, accion)
        assert nuevo.terminado and nuevo.resultado == "derrota" and nuevo.reloj == reloj
    assert ctx.bitacora.acciones_escritas() == escritas


def probar_si_falla_la_red_el_juego_queda_intacto(carpeta):
    partida, acciones, ctx = _crear(carpeta)
    antes = partida.estado(ctx)

    def sin_red(*_):
        raise ErrorRed("contenido de salas", "sin conexión de prueba")
    ctx.contenido.asegurar_sala = sin_red
    estado = acciones.ejecutar(ctx, AccionDTO("mover", direccion=NORTE))
    assert estado.resultado.startswith("Sin conexión") and estado.sala.id == antes.sala.id
    assert estado.reloj == antes.reloj and ctx.bitacora.acciones_escritas() == 0


def probar_marcas_de_uso(carpeta):
    partida, acciones, ctx = _crear(carpeta)
    sync = SincronizadorUsos()
    inicial = sync.ids_en_uso(ctx)
    antorcha = partida.estado(ctx).objetos_suelo[0].id
    assert inicial.count(antorcha) == 1                                  # en el suelo de la sala actual
    acciones.ejecutar(ctx, AccionDTO("recoger", objeto=antorcha))
    assert sync.ids_en_uso(ctx).count(antorcha) == 1                     # ahora en el inventario
    acciones.ejecutar(ctx, AccionDTO("mover", direccion=NORTE))
    en_uso = sync.ids_en_uso(ctx)
    assert en_uso.count("ent_rata_gigante") == 2 and en_uso.count("trp_dardos") == 1
    _verificar_marcas(ctx)


def probar_armar_el_estado_no_infla_los_aciertos_de_cache(carpeta):
    partida, acciones, ctx = _crear(carpeta)
    antes = ctx.resolvedor.aciertos()
    for _ in range(5):                                       # la Vista pide el estado en cada turno
        partida.estado(ctx)
    assert ctx.resolvedor.aciertos() == antes


def probar_puntaje_y_reporte(carpeta):
    partida, acciones, ctx = _crear(carpeta)
    acciones.ejecutar(ctx, AccionDTO("esperar"))
    acciones.ejecutar(ctx, AccionDTO("esperar"))
    puntaje = partida.puntaje(ctx)
    assert (puntaje.nombre, puntaje.mazmorra, puntaje.version) == ("Ana", ID_CRIPTA, ctx.cripta.version)
    assert puntaje.acciones == 2 and puntaje.enemigos_derrotados == 0 and puntaje.tiempo_final == ctx.motor.reloj
    reporte = partida.reporte(ctx)
    assert reporte.offline and reporte.solicitudes_realizadas == 0
    assert reporte.presupuesto == ctx.cripta.presupuesto_solicitudes


# ---------- ServicioInventario ----------

def _objeto(id_objeto, peso, nombre, clase="pocion"):
    return ObjetoDTO(id=id_objeto, nombre=nombre, clase=clase, peso=peso, valor=1)


def probar_recorrer_el_inventario_en_su_orden_real(carpeta):
    partida, _, ctx = _crear(carpeta)
    inventario = ServicioInventario()
    for objeto in (_objeto("a", 5, "zeta"), _objeto("b", 1, "beta"), _objeto("c", 3, "Alfa")):
        ctx.inventario.recoger(objeto)
    assert inventario.inventario(ctx).cursor == 0
    assert inventario.siguiente(ctx).cursor == 1
    assert inventario.siguiente(ctx).cursor == 2
    assert inventario.siguiente(ctx).cursor == 2                         # en el extremo no da la vuelta
    assert inventario.anterior(ctx).cursor == 1


def probar_vista_ordenada_y_recorrido_dentro_de_ella(carpeta):
    partida, _, ctx = _crear(carpeta)
    inventario = ServicioInventario()
    for objeto in (_objeto("a", 5, "zeta"), _objeto("b", 1, "beta"), _objeto("b", 1, "beta"),
                   _objeto("c", 3, "Alfa")):
        ctx.inventario.recoger(objeto)
    vista = inventario.ordenar(ctx, "peso")
    assert [o.id for o in vista.objetos] == ["b", "b", "c", "a"] and vista.criterio == "peso"
    assert [o.id for o in ctx.inventario.objetos()] == ["a", "b", "b", "c"]      # el orden real no cambió
    assert vista.objetos[vista.cursor].id == "a"                          # el cursor sigue sobre el mismo objeto
    vista = inventario.anterior(ctx)
    assert vista.objetos[vista.cursor].id == "c"
    vista = inventario.anterior(ctx)                                      # salta el repetido: de c a b
    assert vista.objetos[vista.cursor].id == "b"
    vista = inventario.siguiente(ctx)                                     # hacia adelante también salta el repetido
    assert vista.objetos[vista.cursor].id == "c"
    assert [o.nombre for o in inventario.ordenar(ctx, "nombre").objetos] == ["Alfa", "beta", "beta", "zeta"]
    assert [o.id for o in inventario.ordenar(ctx, None).objetos] == ["a", "b", "b", "c"]


def probar_un_codigo_desconocido_del_motor_nunca_parece_un_exito(carpeta):
    # Si Lógica agregara un código nuevo, la acción no debe verse como realizada (resultado None).
    mensaje = ServicioAccionJugador._mensaje_de_rechazo("codigo_nuevo_de_logica")
    assert "codigo_nuevo_de_logica" in mensaje and mensaje.startswith("No se pudo")


def probar_criterio_invalido_no_cambia_la_vista(carpeta):
    partida, _, ctx = _crear(carpeta)
    inventario = ServicioInventario()
    inventario.ordenar(ctx, "peso")
    try:
        inventario.ordenar(ctx, "color")
    except ValueError:
        assert ctx.criterio_vista == "peso"
        return
    raise AssertionError("Debió lanzar ValueError")


def probar_recorrer_una_vista_ordenada_con_el_inventario_vacio(carpeta):
    partida, _, ctx = _crear(carpeta)
    inventario = ServicioInventario()
    inventario.ordenar(ctx, "peso")
    for dto in (inventario.siguiente(ctx), inventario.anterior(ctx)):
        assert dto.objetos == [] and dto.cursor == 0


def probar_cambiar_la_vista_no_es_una_accion(carpeta):
    partida, _, ctx = _crear(carpeta)
    inventario = ServicioInventario()
    ctx.inventario.recoger(_objeto("a", 5, "zeta"))
    reloj, acciones = ctx.motor.reloj, ctx.jugador.acciones
    inventario.ordenar(ctx, "peso")
    inventario.siguiente(ctx)
    assert ctx.motor.reloj == reloj and ctx.jugador.acciones == acciones
    assert ctx.bitacora.acciones_escritas() == 0


# ---------- La prueba más exigente: reproducir el log da exactamente la misma partida ----------

def _elegir_accion(estado, x):
    """Elige una acción mirando SOLO el EstadoJuegoDTO, como lo haría un jugador desde la Vista."""
    c = []
    ids_inventario = [o.id for o in estado.inventario.objetos]
    for d in range(4):
        salida = estado.sala.salidas[d]
        if salida is None:
            continue
        if not salida.cerrada:
            c.append(AccionDTO("mover", direccion=d))
        elif salida.llave in ids_inventario:
            c.append(AccionDTO("abrir", direccion=d))
    for enemigo in estado.enemigos:
        c.extend([AccionDTO("atacar", objetivo=enemigo.id)] * 3)
    for objeto in estado.objetos_suelo:
        c.extend([AccionDTO("recoger", objeto=objeto.id)] * 2)
    for objeto in estado.inventario.objetos:
        if objeto.clase == "pergamino_retroceso":
            c.append(AccionDTO("retroceder"))
            continue
        c.append(AccionDTO("soltar", objeto=objeto.id))
        if objeto.clase in ("arma", "armadura"):
            c.extend([AccionDTO("equipar", objeto=objeto.id)] * 2)
        if objeto.clase in ("pocion", "antidoto", "antorcha"):
            c.extend([AccionDTO("usar", objeto=objeto.id)] * 2)
    c.append(AccionDTO("esperar"))
    return c[(x >> 8) % len(c)]


def probar_el_replay_reproduce_exactamente_la_misma_partida(carpeta):
    for semilla in (1, 2, 3, 4, 5, 6):
        partida, acciones, ctx = _crear(os.path.join(carpeta, f"a{semilla}"), semilla=semilla,
                                        pergaminos=2, reforzar=True)
        estado, x = partida.estado(ctx), semilla * 7919
        for _ in range(60):
            if estado.terminado:
                break
            x = (x * 1103515245 + 12345) % 2147483648
            estado = acciones.ejecutar(ctx, _elegir_accion(estado, x))
            _verificar_marcas(ctx)                                       # en cada paso de la partida
        leido = BitacoraReplayIO.leer(ctx.bitacora.ruta())
        assert len(leido.acciones) == ctx.bitacora.acciones_escritas() and len(leido.acciones) >= 5

        partida2, acciones2, ctx2 = _crear(os.path.join(carpeta, f"b{semilla}"), semilla=leido.encabezado.semilla,
                                           bitacora=False, pergaminos=2, reforzar=True)
        estado2 = partida2.estado(ctx2)
        for accion in leido.acciones:
            estado2 = acciones2.ejecutar(ctx2, accion)
            assert estado2.resultado in (None, "victoria", "derrota"), (semilla, accion, estado2.resultado)
        assert estado2 == estado, f"el replay de la semilla {semilla} terminó en otro estado"


if __name__ == "__main__":
    for prueba in (probar_la_fuente_por_omision_sale_de_la_configuracion,
                   probar_la_cache_por_omision_vive_en_la_carpeta_de_trabajo, probar_listar_criptas,
                   probar_estado_inicial, probar_el_estado_trae_la_sala_inicial_y_la_de_salida,
                   probar_la_bitacora_nace_con_su_encabezado,
                   probar_dos_partidas_con_la_misma_semilla_no_pisan_su_log, probar_semilla_automatica,
                   probar_mover_carga_la_sala_y_se_anota_en_el_log, probar_las_acciones_rechazadas_no_cambian_nada,
                   probar_abrir_una_puerta_se_ve_en_el_estado, probar_recoger_usar_y_soltar,
                   probar_equipar_sube_el_ataque_y_lo_muestra,
                   probar_la_sala_del_estado_no_trae_datos_viejos_de_enemigos_ni_trampas,
                   probar_derrotar_enemigos_suelta_objetos, probar_retroceder_deshace_la_ultima_accion,
                   probar_retroceder_sin_historial_no_gasta_el_pergamino,
                   probar_usar_un_pergamino_es_lo_mismo_que_retroceder,
                   probar_retroceder_revive_al_enemigo_y_resincroniza_las_fichas,
                   probar_con_la_partida_terminada_no_se_acepta_nada, probar_si_falla_la_red_el_juego_queda_intacto,
                   probar_marcas_de_uso, probar_armar_el_estado_no_infla_los_aciertos_de_cache,
                   probar_puntaje_y_reporte,
                   probar_recorrer_el_inventario_en_su_orden_real, probar_vista_ordenada_y_recorrido_dentro_de_ella,
                   probar_criterio_invalido_no_cambia_la_vista, probar_un_codigo_desconocido_del_motor_nunca_parece_un_exito,
                   probar_recorrer_una_vista_ordenada_con_el_inventario_vacio, probar_cambiar_la_vista_no_es_una_accion,
                   probar_el_replay_reproduce_exactamente_la_misma_partida):
        _correr(prueba)
    print("OK: todas las pruebas de los Servicios pasaron")