"""
ReconstructorEstado (Servicios, Integrante 3, feature 004): rearma el estado de un instante pasado, hacia adelante.

No viaja hacia atrás: parte del punto de control más cercano ANTERIOR (búsqueda binaria, O(log P)), arma con él un
Motor APARTE (PartidaGuardada.cargar sobre la copia en memoria del punto) y re-simula las acciones vigentes con
DespachoAcciones y avanzar_hasta_jugador. Lo que re-simula nunca pasa de K acciones (FR-416).

    hasta_accion(k)     el Motor justo antes de la acción k (el jugador tiene el control, `historia #k`)
    hasta_instante(t)   el Motor en el instante t (`historia <t>`)
    acciones_reaplicadas   cuántas acciones re-simuló la última reconstrucción (nunca más de K)

Regla de consulta para un instante t (FR-402, data-model.md «Qué punto usa una consulta»):
    j = la última acción con tiempo estrictamente MENOR que t. Si en t hay una decisión del jugador, esa decisión no
        se hace: el estado pedido es el de justo antes de ella. (Es lo mismo que «j = última con tiempo <= t» y,
        si esa acción cae justo en t, quitarla.)
    - Si el último punto con acciones_completadas == j ya tiene reloj >= t, ese punto ES el estado pedido: el jugador
      tiene el control, sus eventos anteriores a la decisión ya corrieron y el suyo ya salió de la cola. Se parte de él.
      No se llama a avanzar_hasta(t): con el reloj del punto igual a t correría los eventos de ese mismo instante que la
      cola ordena DESPUÉS de la decisión, y FR-402 pide el estado justo antes de ella.
    - Si no, se parte del último punto con acciones_completadas <= j - 1, se re-simulan hasta la acción j - 1, se
      ejecuta la acción j y se llama a avanzar_hasta(t). (Con j = 0 se parte del punto 0.)
    - Excepción: si la partida terminó y t es el reloj del final, la acción que cae en t SÍ se hizo (fue la que terminó la
      partida, por ejemplo la que llegó a la salida): el estado de ese instante es el final, igual al vivo.
El reloj del resultado lo pone ArmadorResumen: el instante pedido (FR-405).

Nunca toca `contexto.motor`, la bitácora, el historial de retroceso ni la caché viva, y no le pide nada a Data (FR-407,
Principio VII): las fichas y el contenido de las salas salen de la propia línea; el esqueleto, de memoria
(`GestorEsqueleto.obtener_sala` no hace solicitudes). La búsqueda compartida del cazador (`motor.rutas`) arranca vacía
en el Motor aparte, porque PartidaGuardada no la guarda; la decisión del cazador es la misma (FR-114, T070).

La regla del prefijo por ordinal de los registros de carga y la del punto tomado tras un pergamino llegan en T032 y T034;
aquí cada sala que la re-simulación necesita y el punto no trae se toma de la línea al entrar (registros de carga básicos).
"""
from DTO.PartidaGuardadaDTO import PartidaGuardadaDTO
from Logic.LineaTiempo import LineaTiempo, PuntoControl
from Logic.PartidaGuardada import PartidaGuardada
from Logic.motorJuego import Motor
from Service.ContextoPartida import ContextoPartida
from Service.DespachoAcciones import DespachoAcciones


class _DatosDeLaLinea:
    """El proveedor de datos del despacho (ficha y sala), respaldado por los registros de la línea y no por Data."""

    def __init__(self, linea: LineaTiempo) -> None:
        self._linea = linea

    def ficha(self, id_ficha: str, contar_acierto: bool = True):
        """La ficha que la partida ya había pedido. Si no está, la línea está incompleta: es un error."""
        ficha = self._linea.ficha(id_ficha)
        if ficha is None:
            raise LookupError(f"La línea de tiempo no tiene la ficha {id_ficha!r}")
        return ficha

    def sala(self, id_sala: int):
        """El contenido inicial de la sala, tal como Data lo entregó la primera vez."""
        for registro in self._linea.cargas:
            if registro.sala.id == id_sala:
                return registro.sala
        raise LookupError(f"La línea de tiempo no tiene el contenido de la sala {id_sala}")


class ReconstructorEstado:
    """Rearma, en un Motor aparte, el estado de la partida en un instante o antes de una acción."""

    def __init__(self, contexto: ContextoPartida) -> None:
        self._linea: LineaTiempo = contexto.linea
        self._cripta = contexto.cripta
        self._esqueleto = contexto.esqueleto
        self._datos = _DatosDeLaLinea(contexto.linea)
        self._despacho = DespachoAcciones()
        self._reloj_del_final: int | None = contexto.motor.reloj if contexto.motor.terminado else None   # solo se lee
        self.acciones_reaplicadas: int = 0

    # ---------- Consultas

    def hasta_accion(self, k: int) -> Motor:
        """El Motor justo antes de la acción k (k ya validada, de 1 a las acciones vigentes)."""
        self.acciones_reaplicadas = 0
        punto = self._linea.ubicar_punto(k - 1)
        motor = self._cargar(punto)
        self._reaplicar(motor, punto.acciones_completadas, k - 1)
        return motor

    def hasta_instante(self, t: int) -> Motor:
        """El Motor en el instante t (t ya validado, de 0 al reloj actual)."""
        self.acciones_reaplicadas = 0
        if t == self._reloj_del_final:
            j = self._linea.ubicar_accion_por_tiempo(t)          # el final de la partida: la acción de t se hizo
        else:
            j = self._linea.ubicar_accion_por_tiempo(t - 1)      # acciones con tiempo < t: la de t, si la hay, no se hace
        punto = self._linea.ubicar_punto(j)
        if punto.acciones_completadas == j and punto.partida.reloj >= t:
            return self._cargar(punto)                           # el punto ya es el estado pedido
        punto = self._linea.ubicar_punto(j - 1 if j > 0 else 0)
        motor = self._cargar(punto)
        if j == 0:
            motor.avanzar_hasta(t)
            return motor
        self._reaplicar(motor, punto.acciones_completadas, j - 1)
        self._despachar(motor, j)                                 # la acción j: aceptada, sin esperar a la siguiente decisión
        self.acciones_reaplicadas += 1
        motor.avanzar_hasta(t)
        return motor

    # ---------- Interno

    def _cargar(self, punto: PuntoControl) -> Motor:
        """Un Motor nuevo con la copia del punto (el punto no se modifica). Sin función de mensajes."""
        salas_esqueleto = [self._esqueleto.obtener_sala(i) for i in self._esqueleto.ids_salas()]
        return PartidaGuardada.cargar(punto.partida, punto.salas, self._cripta, salas_esqueleto,
                                      self._datos.ficha, None)

    def _reaplicar(self, motor: Motor, desde: int, hasta: int) -> None:
        """Re-simula las acciones desde+1 .. hasta (cada una hasta la siguiente decisión del jugador)."""
        for numero in range(desde + 1, hasta + 1):
            self._despachar(motor, numero)
            motor.avanzar_hasta_jugador()
            self.acciones_reaplicadas += 1

    def _despachar(self, motor: Motor, numero: int) -> None:
        """Ejecuta la acción número `numero` de la línea. Una vigente ya fue aceptada una vez: debe serlo otra vez."""
        accion = self._linea.accion(numero).accion
        codigo = self._despacho.ejecutar(motor, self._datos, accion)
        if codigo != "ok":
            raise RuntimeError(f"La acción {numero} de la línea ({accion.tipo}) ya no es aceptada al re-simular: {codigo}")
