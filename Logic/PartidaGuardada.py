from DTO.PartidaGuardadaDTO import (ContadorTipoDTO, EfectoGuardadoDTO, EnemigoGuardadoDTO,
                                    EventoGuardadoDTO, InventarioGuardadoDTO, JugadorGuardadoDTO,
                                    PartidaGuardadaDTO, SalaGuardadaDTO, TrampaGuardadaDTO)
from Estructuras.Ordenador import Ordenador
from Logic.Efectos import Antorcha, Regeneracion, Veneno, Velocidad
from Logic.Enemigo import Enemigo
from Logic.EventoPorg import EventoProgramado
from Logic.Inventario import Inventario
from Logic.Mazmorra import CierrePuerta, Mazmorra, TrampaViva
from Logic.jugador import Jugador
from Logic.motorJuego import Motor

EFECTOS = ["veneno", "velocidad", "antorcha", "regeneracion"]


# Pasa el estado vivo de Lógica a los DTOs de DTO/PartidaGuardadaDTO.py y lo vuelve a armar.
# Se guarda y se carga cuando el control lo tiene el jugador (después de avanzar_hasta_jugador).
# COORDINAR (Integrante 2): GuardadoBinario.guardar(ruta, partida, salas) recibe lo que devuelve guardar
# COORDINAR (Integrante 3): ServicioGuardado arma el ContextoPartida con motor.jugador, motor.mazmorra y motor.inventario
class PartidaGuardada:

    # ---------- Metodos publicos

    # Devuelve (PartidaGuardadaDTO, [SalaGuardadaDTO]); version_catalogo, semilla y el log los da Servicios
    @staticmethod
    def guardar(motor, cripta, version_catalogo, semilla, ruta_log=None, acciones_en_log=0):
        azar_version, azar_estado, azar_gauss = motor.azar.getstate()
        efectos = motor.efectos.activos
        partida = PartidaGuardadaDTO(
            id_cripta=cripta.id, version_cripta=cripta.version, version_catalogo=version_catalogo,
            semilla=semilla, reloj=motor.reloj, siguiente_secuencia=motor.cola.siguiente_secuencia,
            enemigos_derrotados=motor.enemigos_derrotados, terminado=motor.terminado,
            victoria=motor.victoria, salida_abierta=motor.mazmorra.salida_abierta,
            azar_version=azar_version, azar_estado=list(azar_estado), azar_gauss=azar_gauss,
            jugador=_guardar_jugador(motor.jugador),
            inventario=_guardar_inventario(motor.inventario),
            rastro=list(motor.rastro.tiempos),
            contadores_tipo=[ContadorTipoDTO(par[0], par[1]) for par in motor.mazmorra.contadores_tipo],
            efectos=[_guardar_efecto(efecto) for efecto in efectos],
            eventos=[_guardar_evento(evento, motor.mazmorra, efectos) for evento in _eventos_validos(motor.cola)],
            ruta_log=ruta_log, acciones_en_log=acciones_en_log,
        )
        salas = []
        for sala in motor.mazmorra.salas:
            if sala is not None:
                salas.append(_guardar_sala(sala))
        return partida, salas

    # salas_esqueleto: los SalaDTO del esqueleto de la misma versión de la cripta
    # COORDINAR (Integrante 2): fn_ficha(id) la provee la caché del catálogo (objetos, enemigos y trampas)
    @staticmethod
    def cargar(partida, salas, cripta, salas_esqueleto, fn_ficha, fn_mensaje=None):
        mazmorra = Mazmorra(cripta.sala_salida, cripta.llave_salida)
        mazmorra.cargar_esqueleto(salas_esqueleto)
        for sala_guardada in salas:
            _cargar_sala(mazmorra.sala(sala_guardada.id), sala_guardada, fn_ficha)
        mazmorra.salida_abierta = partida.salida_abierta
        mazmorra.contadores_tipo = [[c.tipo, c.cantidad] for c in partida.contadores_tipo]

        inventario = Inventario(cripta.inventario_max)
        guardado = partida.inventario
        inventario.restaurar([fn_ficha(id_objeto) for id_objeto in guardado.objetos],
                             guardado.cursor, guardado.arma, guardado.armadura)

        jugador = Jugador(cripta)
        _cargar_jugador(jugador, partida.jugador, inventario)

        motor = Motor(partida.semilla, jugador, mazmorra, fn_mensaje, inventario)
        motor.reloj = partida.reloj
        motor.enemigos_derrotados = partida.enemigos_derrotados
        motor.terminado = partida.terminado
        motor.victoria = partida.victoria
        motor.azar.setstate((partida.azar_version, tuple(partida.azar_estado), partida.azar_gauss))
        motor.rastro.tiempos = list(partida.rastro)
        for sala in mazmorra.salas:
            if sala is not None:
                for enemigo in sala.enemigos:
                    enemigo.historial = motor.historial

        efectos = [_crear_efecto(e, _buscar_actor(motor, e.actor)) for e in partida.efectos]
        motor.efectos.activos = efectos
        for evento_guardado in partida.eventos:
            _cargar_evento(motor, evento_guardado, efectos)
        motor.cola.siguiente_secuencia = partida.siguiente_secuencia

        # El historial no se guarda: se empieza vacío, como justo después de cerrar un intervalo
        motor.historial.descartar_intervalo_abierto()
        motor._registrar_azar()
        return motor


# ---------- Guardar

def _guardar_jugador(jugador):
    return JugadorGuardadoDTO(jugador.vida, jugador.vida_Max, jugador.ataque, jugador.defensa,
                              jugador.velocidad, jugador.Sala_Actual, jugador.acciones)


def _guardar_inventario(inventario):
    objetos = [objeto.id for objeto in inventario.objetos()]
    cursor = None if inventario.esta_vacio() else inventario.posicion_cursor()
    arma, armadura = inventario.posiciones_equipadas()
    return InventarioGuardadoDTO(objetos, cursor, arma, armadura)


def _guardar_efecto(efecto):
    cambio_real = efecto.cambio_real if efecto.tipo == "velocidad" else 0
    return EfectoGuardadoDTO(efecto.tipo, efecto.actor.id, efecto.duracion, efecto.valor, efecto.fin, cambio_real)


# En el orden en que saldrían de la cola; así al cargarlos el montículo queda igual
def _eventos_validos(cola):
    validos = []
    for evento in cola.eventos:
        if evento.esta_valido():
            validos.append(evento)
    return Ordenador.ordenar(validos, _comparar_eventos)


def _guardar_evento(evento, mazmorra, efectos):
    dueno = evento.dueno
    if evento.tipo == "accion_actor":
        return EventoGuardadoDTO(evento.tiempo, evento.secuencia, evento.tipo, actor=dueno.id)
    if evento.tipo in EFECTOS:
        return EventoGuardadoDTO(evento.tiempo, evento.secuencia, evento.tipo, efecto=efectos.index(dueno))
    for sala in mazmorra.salas:
        if sala is None:
            continue
        if evento.tipo == "rearme_trampa" and dueno in sala.trampas:
            return EventoGuardadoDTO(evento.tiempo, evento.secuencia, evento.tipo, sala=sala.id,
                                     trampa=dueno.instancia)
        if evento.tipo == "cierre_puerta":
            for direccion in range(4):
                if sala.salidas[direccion] is dueno.caras[0]:
                    return EventoGuardadoDTO(evento.tiempo, evento.secuencia, evento.tipo, sala=sala.id,
                                             direccion=direccion)
    raise ValueError(f"No se pudo guardar el evento {evento!r}")


def _guardar_sala(sala):
    puertas = [salida is not None and salida.cerrada for salida in sala.salidas]
    trampas = [TrampaGuardadaDTO(t.instancia, t.ficha.id, t.armada) for t in sala.trampas]
    enemigos = [EnemigoGuardadoDTO(e.id, e.tipo(), e.vida, e.velocidad, e.numero, e.activo)
                for e in sala.enemigos]
    return SalaGuardadaDTO(sala.id, sala.contenido_cargado, puertas, list(sala.objetos), trampas, enemigos)


# ---------- Cargar

def _cargar_sala(sala, guardada, fn_ficha):
    sala.contenido_cargado = guardada.contenido_cargado
    for direccion in range(4):
        if sala.salidas[direccion] is not None:
            sala.salidas[direccion].cerrada = guardada.puertas_cerradas[direccion]
    sala.objetos = list(guardada.objetos)
    for t in guardada.trampas:
        trampa = TrampaViva(t.instancia, fn_ficha(t.tipo))
        trampa.armada = t.armada
        sala.trampas.append(trampa)
    for e in guardada.enemigos:
        enemigo = Enemigo(fn_ficha(e.tipo), e.instancia, e.vida, e.numero, sala.id)
        enemigo.velocidad = e.velocidad
        enemigo.activo = e.activo
        sala.enemigos.append(enemigo)


# Jugador.arma y Jugador.armadura salen del inventario (acuerdo del equipo)
def _cargar_jugador(jugador, guardado, inventario):
    jugador.vida = guardado.vida
    jugador.vida_Max = guardado.vida_max
    jugador.ataque = guardado.ataque
    jugador.defensa = guardado.defensa
    jugador.velocidad = guardado.velocidad
    jugador.Sala_Actual = guardado.sala_actual
    jugador.acciones = guardado.acciones
    jugador.arma = inventario.arma_equipada()
    jugador.armadura = inventario.armadura_equipada()


def _crear_efecto(guardado, actor):
    if guardado.tipo == "veneno":
        efecto = Veneno(actor, guardado.valor, guardado.duracion)
    elif guardado.tipo == "velocidad":
        efecto = Velocidad(actor, guardado.valor, guardado.duracion)
        efecto.cambio_real = guardado.cambio_real
    elif guardado.tipo == "regeneracion":
        efecto = Regeneracion(actor, guardado.valor)
    else:
        efecto = Antorcha(actor, guardado.duracion)
    efecto.fin = guardado.fin
    return efecto


# programar() numera con siguiente_secuencia: se fija antes para conservar la secuencia guardada
def _cargar_evento(motor, guardado, efectos):
    mazmorra = motor.mazmorra
    if guardado.tipo == "accion_actor":
        dueno = _buscar_actor(motor, guardado.actor)
    elif guardado.tipo in EFECTOS:
        dueno = efectos[guardado.efecto]
    elif guardado.tipo == "rearme_trampa":
        dueno = _buscar_trampa(mazmorra.sala(guardado.sala), guardado.trampa)
    else:
        cara = mazmorra.salida(guardado.sala, guardado.direccion)
        caras = [cara]
        inversa = mazmorra._salida_inversa(guardado.sala, cara.destino)
        if inversa is not None:
            caras.append(inversa)
        dueno = CierrePuerta(caras)       # las mismas caras que junta Mazmorra.abrir_puerta
    motor.cola.siguiente_secuencia = guardado.secuencia
    evento = motor.cola.programar(EventoProgramado(guardado.tiempo, guardado.tipo, dueno))
    if guardado.tipo == "accion_actor":
        dueno.Evento_pendiente = evento
    elif guardado.tipo in EFECTOS:
        dueno.evento = evento


def _buscar_actor(motor, id_actor):
    if id_actor == motor.jugador.id:
        return motor.jugador
    for sala in motor.mazmorra.salas:
        if sala is not None:
            for enemigo in sala.enemigos:
                if enemigo.id == id_actor:
                    return enemigo
    raise ValueError(f"No existe el actor {id_actor!r} en la partida guardada")


def _buscar_trampa(sala, instancia):
    for trampa in sala.trampas:
        if trampa.instancia == instancia:
            return trampa
    raise ValueError(f"No existe la trampa {instancia!r} en la sala {sala.id}")


def _comparar_eventos(a, b):
    if a.tiempo != b.tiempo:
        return Ordenador.comparar(a.tiempo, b.tiempo)
    return Ordenador.comparar(a.secuencia, b.secuencia)
