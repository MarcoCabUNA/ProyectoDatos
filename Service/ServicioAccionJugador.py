"""
ServicioAccionJugador (Servicios, Integrante 3): ejecuta UNA acción del jugador y devuelve el estado.

Recibe el AccionDTO (del Controlador, o de ServicioReplay al reproducir un log, que produce el mismo
DTO) y llama al método del motor que corresponde. No decide si la acción es válida según las reglas
del juego: eso lo responde el motor con un código ("ok", "sin_salida", "inventario_lleno"...) que aquí
solo se traduce a un mensaje. Lo que sí hace es lo que Lógica no puede, porque no conoce Datos:

  1. DATOS PRIMERO, LÓGICA DESPUÉS. Para mover, el contenido de la sala destino se carga antes de llamar
     al motor (§2.5, §4.2). Si la red falla, el juego queda intacto y se informa el error.
  2. Después de cada acción: se avanza el reloj hasta la siguiente decisión del jugador, se sincronizan
     las fichas en uso de la caché y se arma el estado.
  3. Cada acción que SÍ se hizo se anexa a la bitácora de replay. Las rechazadas no: no consumen tiempo
     y no son acciones del jugador. Leer un pergamino sí se anexa (cambia el curso de la partida).

Reglas que impone este servicio:
  - Con la partida terminada no se acepta ninguna acción (usar un pergamino con la partida terminada
    corrompería el estado: el último intervalo nunca se cerró).
  - Leer un pergamino NO avanza el reloj: el retroceso deja al jugador justo en una decisión.
    "retroceder" y "usar" sobre un pergamino son lo mismo. Si no hay pergamino, se rechaza.
Los objetos se identifican por su id (ver Inventario.ubicar), igual en una partida en vivo que en un replay.
"""
from Data.ClienteHttp import ErrorRed
from DTO.AccionDTO import AccionDTO
from DTO.EstadoJuegoDTO import EstadoJuegoDTO
from Service.ArmadorEstado import ArmadorEstado
from Service.ContextoPartida import ContextoPartida
from Service.SincronizadorUsos import SincronizadorUsos

CLASE_PERGAMINO = "pergamino_retroceso"

# Código que devuelve el motor (o este servicio) -> mensaje para el jugador. Es un array de pares y no
# un dict (§7): son pocos y solo se recorren al rechazar una acción.
_MENSAJES_DE_RECHAZO = [
    ("sin_salida", "No hay salida en esa dirección."),
    ("cerrada", "La puerta está cerrada: hay que abrirla con su llave."),
    ("nada_que_abrir", "No hay nada que abrir en esa dirección."),
    ("sin_llave", "No tienes la llave de esa puerta."),
    ("sin_objetivo", "Ese enemigo no está en esta sala."),
    ("inventario_lleno", "Tu inventario está lleno: suelta algo primero."),
    ("sin_objeto", "No hay (o no tienes) ese objeto."),
    ("no_equipable", "Ese objeto no se puede equipar."),
    ("no_usable", "Ese objeto no se puede usar."),
    ("sin_historial", "No hay nada que deshacer."),
    ("sin_pergamino", "No tienes ningún pergamino de retroceso."),
    ("direccion_invalida", "Dirección inválida: use N, S, E u O."),
    ("falta_objetivo", "Falta indicar a qué enemigo atacar."),
    ("falta_objeto", "Falta indicar el objeto."),
    ("accion_desconocida", "Acción desconocida."),
]


class ServicioAccionJugador:

    def __init__(self):
        self._armador = ArmadorEstado()
        self._sincronizador = SincronizadorUsos()

    def ejecutar(self, contexto: ContextoPartida, accion: AccionDTO) -> EstadoJuegoDTO:
        motor = contexto.motor
        if motor.terminado:
            return self._armador.armar_estado(contexto)             # el resultado es victoria o derrota
        es_lectura_de_pergamino = self._es_lectura_de_pergamino(contexto, accion)
        try:
            codigo = self._ejecutar_en_el_motor(contexto, accion)
        except ErrorRed as error:                                   # falló la red antes de cambiar nada
            return self._armador.armar_estado(contexto, f"Sin conexión con el servicio: {error}")
        if codigo != "ok":
            return self._armador.armar_estado(contexto, self._mensaje_de_rechazo(codigo))
        if contexto.bitacora is not None:
            contexto.bitacora.anexar(accion)
        if not es_lectura_de_pergamino:
            motor.avanzar_hasta_jugador()
        self._sincronizador.sincronizar(contexto)
        return self._armador.armar_estado(contexto)

    # ---- interno ----

    def _ejecutar_en_el_motor(self, contexto, accion: AccionDTO) -> str:
        motor, tipo = contexto.motor, accion.tipo
        if tipo == "mover":
            if not self._direccion_valida(accion.direccion):
                return "direccion_invalida"
            self._cargar_destino_si_falta(contexto, accion.direccion)
            return motor.mover_jugador(accion.direccion)
        if tipo == "abrir":
            if not self._direccion_valida(accion.direccion):
                return "direccion_invalida"
            return motor.abrir_puerta(accion.direccion, contexto.inventario.tiene_objeto)
        if tipo == "atacar":
            if accion.objetivo is None:
                return "falta_objetivo"
            return motor.atacar_enemigo(accion.objetivo)
        if tipo == "esperar":
            return motor.esperar()
        if tipo == "retroceder":
            id_pergamino = self._id_de_un_pergamino(contexto)
            if id_pergamino is None:
                return "sin_pergamino"
            return motor.usar(id_pergamino)
        if tipo in ("recoger", "soltar", "equipar", "usar"):
            if accion.objeto is None:
                return "falta_objeto"
            if tipo == "recoger":
                return motor.recoger(accion.objeto, contexto.resolvedor.ficha)
            if tipo == "soltar":
                return motor.soltar(accion.objeto)
            if tipo == "equipar":
                return motor.equipar(accion.objeto)
            return motor.usar(accion.objeto)
        return "accion_desconocida"

    @staticmethod
    def _direccion_valida(direccion) -> bool:
        return isinstance(direccion, int) and not isinstance(direccion, bool) and 0 <= direccion <= 3

    @staticmethod
    def _cargar_destino_si_falta(contexto, direccion: int) -> None:
        """El motor no deja entrar a una sala sin contenido (devuelve 'pendiente'): se lo da Datos primero."""
        salida = contexto.mazmorra.salida(contexto.jugador.Sala_Actual, direccion)
        if salida is None or salida.cerrada or contexto.mazmorra.contenido_cargado(salida.destino):
            return
        sala = contexto.contenido.asegurar_sala(salida.destino)
        contexto.mazmorra.cargar_contenido(sala, contexto.resolvedor.ficha)

    @staticmethod
    def _id_de_un_pergamino(contexto):
        for objeto in contexto.inventario.objetos():
            if objeto.clase == CLASE_PERGAMINO:
                return objeto.id
        return None

    @staticmethod
    def _es_lectura_de_pergamino(contexto, accion: AccionDTO) -> bool:
        if accion.tipo == "retroceder":
            return True
        if accion.tipo != "usar":
            return False
        for objeto in contexto.inventario.objetos():
            if objeto.id == accion.objeto:
                return objeto.clase == CLASE_PERGAMINO
        return False

    @staticmethod
    def _mensaje_de_rechazo(codigo: str) -> str:
        for clave, mensaje in _MENSAJES_DE_RECHAZO:
            if clave == codigo:
                return mensaje
        return f"No se pudo realizar la acción ({codigo})."