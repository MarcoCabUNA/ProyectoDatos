import random

from DTO.Direcciones import DIRECCIONES
from Logic.ColaEventos import ColaEventos
from Logic.EventoPorg import EventoProgramado
from Logic.GestorEfectos import GestorEfectos
from Logic.RastroSalas import RastroSalas


class Motor:
    # COORDINAR (Integrante 3): faltan COSTO_RECOGER = 25, COSTO_SOLTAR = 25, COSTO_USAR = 50 y COSTO_EQUIPAR = 50; tras cada acción llamar terminar_accion_jugador(costo)
    COSTO_MOVER = 100
    COSTO_ATACAR = 100
    COSTO_ESPERAR = 100
    COSTO_ABRIR = 50

    # COORDINAR (Integrante 3): fn_mensaje recibe la bitácora circular de 20 mensajes
    # COORDINAR (Integrante 3): la semilla va en el encabezado del log de replay
    # COORDINAR (Integrante 3): el estado de self.azar (getstate/setstate) debe restaurarse al retroceder
    # COORDINAR (Integrante 2 y 3): definir qué estado de Lógica se guarda en el guardado binario
    def __init__(self, semilla, jugador, mazmorra, fn_mensaje=None):
        self.reloj = 0
        self.cola = ColaEventos()
        self.azar = random.Random(semilla)
        self.jugador = jugador
        self.mazmorra = mazmorra
        self.rastro = RastroSalas()
        self.efectos = GestorEfectos(self)
        self.fn_mensaje = fn_mensaje
        self.enemigos_derrotados = 0
        self.terminado = False
        self.victoria = False

    # ---------- Metodos publicos

    def iniciar(self):
        self.jugador.Evento_pendiente = self.cola.programar(EventoProgramado(0, "accion_actor", self.jugador))
        self.rastro.marcar(self.jugador.Sala_Actual, 0)
        self.activar_enemigos(self.mazmorra.enemigos_dormidos(self.jugador.Sala_Actual))

    # COORDINAR (Integrante 3): registrar el cambio en HistorialRetroceso (activo)
    def activar_enemigos(self, enemigos):
        for enemigo in _ordenar_por_id(enemigos):
            enemigo.activo = True
            self.programar_accion(enemigo, 100)

    def programar_accion(self, actor, costo):
        tiempo = self.reloj + actor.Calcu_de_Intervalo(costo)
        actor.Evento_pendiente = self.cola.programar(EventoProgramado(tiempo, "accion_actor", actor))

    def programar_efecto(self, retraso, tipo, efecto):
        return self.cola.programar(EventoProgramado(self.reloj + retraso, tipo, efecto))

    # COORDINAR (Integrante 3): registrar el cambio en HistorialRetroceso (velocidad y Evento_pendiente)
    def cambiar_velocidad(self, actor, velocidad_nueva):
        evento_viejo = actor.Evento_pendiente
        if evento_viejo is None or not evento_viejo.esta_valido():
            actor.velocidad = velocidad_nueva
            return
        restante = evento_viejo.tiempo - self.reloj
        restante_nuevo = max(1, restante * actor.velocidad // velocidad_nueva)
        actor.velocidad = velocidad_nueva
        evento_viejo.cancelar()
        tiempo = self.reloj + restante_nuevo
        actor.Evento_pendiente = self.cola.programar(EventoProgramado(tiempo, "accion_actor", actor))

    # COORDINAR (Integrante 3): registrar el cambio en HistorialRetroceso (reloj); al devolver True termina el intervalo a revertir
    def avanzar_hasta_jugador(self):
        while not self.terminado and not self.cola.esta_vacia():
            evento = self.cola.obtener_siguiente()
            self.reloj = evento.tiempo
            if evento.dueno is self.jugador:
                self.jugador.Evento_pendiente = None
                return True
            evento.dueno.activar(self, evento)
        return False

    # COORDINAR (Integrante 3): registrar el cambio en HistorialRetroceso (acciones); PuntajeDTO usa jugador.acciones, enemigos_derrotados, reloj y victoria
    def terminar_accion_jugador(self, costo):
        self.jugador.acciones += 1
        self.rastro.marcar(self.jugador.Sala_Actual, self.reloj)
        self.programar_accion(self.jugador, costo)

    # COORDINAR (Integrante 2): si devuelve "pendiente", Servicios pide el contenido, lo carga con cargar_contenido y reintenta
    # COORDINAR (Integrante 3): registrar el cambio en HistorialRetroceso (Sala_Actual del jugador)
    def mover_jugador(self, direccion):
        salida = self.mazmorra.salida(self.jugador.Sala_Actual, direccion)
        if salida is None:
            return "sin_salida"
        if salida.cerrada:
            return "cerrada"
        destino = salida.destino
        if not self.mazmorra.contenido_cargado(destino):
            return "pendiente"
        self.jugador.Sala_Actual = destino
        self.mensaje(f"Entras a {self.mazmorra.sala(destino).nombre}")
        self.activar_enemigos(self.mazmorra.enemigos_dormidos(destino))
        self._activar_trampas(destino)
        if not self.terminado and destino == self.mazmorra.sala_salida and self.mazmorra.salida_abierta:
            self.terminado = True
            self.victoria = True
            self.mensaje("Has escapado de la cripta")
        self.terminar_accion_jugador(self.COSTO_MOVER)
        return "ok"

    # COORDINAR (Integrante 3): fn_tiene_objeto(id) la provee el Inventario
    def abrir_puerta(self, direccion, fn_tiene_objeto):
        llave = self.mazmorra.llave_requerida(self.jugador.Sala_Actual, direccion)
        if llave is None:
            return "nada_que_abrir"
        if not fn_tiene_objeto(llave):
            return "sin_llave"
        self.mazmorra.abrir_puerta(self.jugador.Sala_Actual, direccion, self)
        self.mensaje(f"Abres la puerta {DIRECCIONES[direccion]}")
        self.terminar_accion_jugador(self.COSTO_ABRIR)
        return "ok"

    def atacar_enemigo(self, instancia):
        enemigo = self.mazmorra.buscar_enemigo(self.jugador.Sala_Actual, instancia)
        if enemigo is None:
            return "sin_objetivo"
        self.atacar(self.jugador, enemigo)
        self.terminar_accion_jugador(self.COSTO_ATACAR)
        return "ok"

    def esperar(self):
        self.terminar_accion_jugador(self.COSTO_ESPERAR)
        return "ok"

    def turno_enemigo(self, enemigo):
        if not enemigo.Vivo():
            return
        if enemigo.Sala_Actual == self.jugador.Sala_Actual:
            self.atacar(enemigo, self.jugador)
        else:
            destino = enemigo.estrategia.decidir(enemigo, self)
            if destino is not None:
                self.mazmorra.mover_enemigo(enemigo, destino)
                if destino == self.jugador.Sala_Actual:
                    self.mensaje(f"{enemigo.nombre_visible()} entra a la sala")
        if not self.terminado:
            self.programar_accion(enemigo, 100)

    def atacar(self, atacante, defensor):
        dano = max(1, atacante.ataque_efectivo() + self.azar.randint(0, 4) - defensor.defensa_efectiva())
        defensor.Recibir_Dannio(dano)
        self.mensaje(f"{atacante.nombre_visible()} ataca a {defensor.nombre_visible()}: {dano} de daño")
        if not defensor.Vivo():
            self.morir(defensor)

    # COORDINAR (Integrante 2): la ficha del enemigo muerto deja de estar en uso en la caché
    # COORDINAR (Integrante 3): registrar el cambio en HistorialRetroceso (enemigos_derrotados y terminado)
    def morir(self, actor):
        if actor.Evento_pendiente is not None:
            actor.Evento_pendiente.cancelar()
        if actor is self.jugador:
            self.terminado = True
            self.mensaje("Has muerto")
            return
        self.enemigos_derrotados += 1
        self.mensaje(f"{actor.nombre_visible()} muere")
        for id_objeto in actor.objetos_que_suelta():
            self.mazmorra.soltar_objeto(actor.Sala_Actual, id_objeto)

    def mensaje(self, texto):
        if self.fn_mensaje is not None:
            self.fn_mensaje(f"[t={self.reloj}] {texto}")

    # ---------- Metodos privados

    # COORDINAR (Integrante 3): registrar el cambio en HistorialRetroceso (armada)
    def _activar_trampas(self, id_sala):
        for trampa in self.mazmorra.trampas_armadas(id_sala):
            self.jugador.Recibir_Dannio(trampa.ficha.danio)
            trampa.armada = False
            self.mensaje(f"{trampa.ficha.nombre}: {trampa.ficha.danio} de daño")
            self.programar_efecto(trampa.ficha.rearme, "rearme_trampa", trampa)
            if not self.jugador.Vivo():
                self.morir(self.jugador)
                return


# COORDINAR (Integrante 3): reemplazar por el Ordenador (§4.9)
def _ordenar_por_id(lista):
    resultado = list(lista)
    for i in range(1, len(resultado)):
        actual = resultado[i]
        j = i - 1
        while j >= 0 and resultado[j].id > actual.id:
            resultado[j + 1] = resultado[j]
            j -= 1
        resultado[j + 1] = actual
    return resultado
