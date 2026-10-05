"""
GestorContenido (Integrante 2): precarga del contenido de las salas (enunciado §4.2).

Objetivo: que el contenido de una sala esté disponible ANTES de que el jugador entre,
sin esperar ~400 ms en cada puerta y sin gastar el presupuesto pidiendo sala por sala.

Estrategia ("pedir solo cuando hace falta pronto, pero llenar cada pedido"):
  1. Si alguna sala a 'radio' pasos o menos de la sala actual no tiene contenido,
     se hace UNA solicitud.
  2. Esa solicitud se llena con las salas sin contenido MÁS CERCANAS (recorrido BFS
     sobre el esqueleto), hasta 10: pedir 1 o 10 cuesta lo mismo (§3.4).
  3. Si todas las salas cercanas ya están cargadas, no se pide nada.
  4. Una sala ya pedida nunca se vuelve a pedir (array de estados).

Estructuras (solo arrays y la Cola compartida, según la restricción del curso):
  _estado     array indexado por id de sala: NO_PEDIDA / PENDIENTE / CARGADA   O(1) por consulta
  _pendientes Cola de ids marcados para pedir, en orden de llegada
  BFS         Cola + array de distancias (-1 = no visitada)                    O(V + E)

Determinismo (§4.2): el BFS recorre las salidas siempre en orden N, S, E, O, los lotes
se arman en el orden en que se marcaron y FuenteDatos devuelve el contenido en el orden
pedido; así, la misma partida siempre pide los mismos lotes en el mismo orden.

Esta versión es SÍNCRONA: cada solicitud termina antes de seguir. No usa el reloj
virtual (vive en Lógica), así que el tiempo real de red nunca lo altera.
"""
from Data.ClienteHttp import ErrorRed
from Data.FuenteDatos import FuenteDatos
from Data.GestorEsqueleto import GestorEsqueleto
from DTO.SalaDTO import SalaDTO
from Estructuras.Cola import Cola

NO_PEDIDA = 0
PENDIENTE = 1
CARGADA = 2


class GestorContenido:

    def __init__(self, fuente: FuenteDatos, esqueleto: GestorEsqueleto, radio: int = 2):
        """
        esqueleto: ya cargado (GestorEsqueleto.cargar). El contenido recibido se guarda
                   en él con actualizar_sala(), para que haya una sola copia de cada sala.
        radio:     distancia máxima (en salas) que debe estar cargada alrededor del
                   jugador. Si algo dentro de ese radio falta, se hace una solicitud.
        """
        if not esqueleto.esta_cargado():
            raise ValueError("El esqueleto debe estar cargado antes de crear GestorContenido")
        if radio < 0:
            raise ValueError("El radio no puede ser negativo")
        cripta = esqueleto.cripta()
        assert cripta is not None   # esta_cargado() lo garantiza
        self._fuente = fuente
        self._esqueleto = esqueleto
        self._id_cripta = cripta.id
        self._radio = radio
        self._tamano = self._mayor_id() + 1
        self._estado: list[int] = [NO_PEDIDA] * self._tamano
        self._pendientes = Cola()
        # Contadores para el reporte y --bench.
        self._lotes = 0
        self._salas_pedidas = 0

    # ------------------------------------------------------------ consultas
    def contenido_disponible(self, id_sala: int) -> bool:
        """O(1). Lo pregunta Servicios antes de confirmar un movimiento."""
        return self._en_rango(id_sala) and self._estado[id_sala] == CARGADA

    def obtener_contenido(self, id_sala: int) -> SalaDTO | None:
        """La sala con su contenido, o None si todavía no está cargada. O(1)."""
        if not self.contenido_disponible(id_sala):
            return None
        return self._esqueleto.obtener_sala(id_sala)

    def lotes_realizados(self) -> int:
        return self._lotes

    def salas_pedidas(self) -> int:
        return self._salas_pedidas

    # ------------------------------------------------------------ operaciones (Guía §3.2)
    def solicitar_si_falta(self, id_sala: int) -> bool:
        """
        Marca la sala para pedirla en el próximo resolver_pendientes(), si nunca se pidió.
        Devuelve True si quedó marcada. O(1).
        """
        self._validar_sala(id_sala)
        if self._estado[id_sala] != NO_PEDIDA:
            return False
        self._estado[id_sala] = PENDIENTE
        self._pendientes.encolar(id_sala)
        return True

    def resolver_pendientes(self) -> None:
        """
        Pide todas las salas marcadas, en lotes de hasta 10, en el orden en que se marcaron.
        Si una solicitud falla, las salas que no llegaron vuelven a NO_PEDIDA (se podrán
        pedir más adelante) y el error se propaga.
        """
        while not self._pendientes.esta_vacia():
            lote: list[int] = []
            while not self._pendientes.esta_vacia() and len(lote) < FuenteDatos.MAX_SALAS_POR_CONTENIDO:
                lote.append(self._pendientes.desencolar())
            try:
                recibidos = self._fuente.obtener_contenido(self._id_cripta, lote)
            except ErrorRed:
                self._descartar_pendientes(lote)
                raise
            self._lotes += 1
            self._salas_pedidas += len(lote)
            # Se integran en el orden pedido (FuenteDatos ya los devuelve así).
            for contenido in recibidos:
                sala = self._esqueleto.obtener_sala(contenido.sala)
                assert sala is not None
                self._esqueleto.actualizar_sala(sala.con_contenido(contenido))
                self._estado[contenido.sala] = CARGADA

    def precargar_alrededor(self, id_sala: int) -> int:
        """
        Precarga ANTICIPADA: se llama cada vez que el jugador llega a una sala.
        Si falta contenido a 'radio' pasos o menos, hace UNA solicitud con las 10 salas sin
        contenido más cercanas. Devuelve cuántas salas pidió (0 si no hizo falta).

        Si la red falla (o se agota el presupuesto) NO interrumpe el juego: devuelve 0 y
        esas salas se intentarán después. La que nunca puede faltar es la sala a la que el
        jugador quiere entrar: para eso está asegurar_sala().
        """
        self._validar_sala(id_sala)
        if not self._falta_dentro_del_radio(id_sala):
            return 0
        marcadas = self._marcar_mas_cercanas(id_sala, FuenteDatos.MAX_SALAS_POR_CONTENIDO)
        try:
            self.resolver_pendientes()
        except ErrorRed:
            return 0
        return marcadas

    def asegurar_sala(self, id_sala: int) -> SalaDTO:
        """
        Garantiza que la sala tenga contenido (§4.2: el jugador nunca queda en una sala
        cuyo contenido no se conoce). Si ya está cargada, no pide nada. Si no, hace UNA
        solicitud con esa sala primero y la completa con las más cercanas que falten.
        Aquí un error de red SÍ se propaga: Servicios decide qué hacer (no mover al jugador).
        """
        self._validar_sala(id_sala)
        if self._estado[id_sala] != CARGADA:
            self._marcar_mas_cercanas(id_sala, FuenteDatos.MAX_SALAS_POR_CONTENIDO)
            self.resolver_pendientes()
        sala = self.obtener_contenido(id_sala)
        assert sala is not None
        return sala

    # ------------------------------------------------------------ BFS
    def _falta_dentro_del_radio(self, origen: int) -> bool:
        """BFS limitado a 'radio' pasos: ¿alguna sala alcanzable sin contenido pedido?"""
        distancia = [-1] * self._tamano
        cola = Cola()
        distancia[origen] = 0
        cola.encolar(origen)
        while not cola.esta_vacia():
            actual = cola.desencolar()
            if self._estado[actual] == NO_PEDIDA:
                return True
            if distancia[actual] == self._radio:
                continue   # no se expande más allá del radio
            for vecino in self._esqueleto.vecinos(actual):
                if distancia[vecino] == -1:
                    distancia[vecino] = distancia[actual] + 1
                    cola.encolar(vecino)
        return False

    def _marcar_mas_cercanas(self, origen: int, maximo: int) -> int:
        """
        BFS desde 'origen' (sin límite de distancia): marca para pedir las primeras 'maximo'
        salas NO_PEDIDA que encuentra. Como el BFS visita por distancia creciente, son las
        más cercanas; con empate, gana el orden N, S, E, O. Devuelve cuántas marcó.
        """
        distancia = [-1] * self._tamano
        cola = Cola()
        distancia[origen] = 0
        cola.encolar(origen)
        marcadas = 0
        while not cola.esta_vacia() and marcadas < maximo:
            actual = cola.desencolar()
            if self.solicitar_si_falta(actual):
                marcadas += 1
            for vecino in self._esqueleto.vecinos(actual):
                if distancia[vecino] == -1:
                    distancia[vecino] = distancia[actual] + 1
                    cola.encolar(vecino)
        return marcadas

    # ------------------------------------------------------------ auxiliares
    def _descartar_pendientes(self, lote: list[int]) -> None:
        """Tras un fallo: el lote y lo que seguía en la cola vuelven a NO_PEDIDA."""
        for id_sala in lote:
            self._estado[id_sala] = NO_PEDIDA
        while not self._pendientes.esta_vacia():
            self._estado[self._pendientes.desencolar()] = NO_PEDIDA

    def _mayor_id(self) -> int:
        mayor = 0
        for id_sala in self._esqueleto.ids_salas():
            if id_sala > mayor:
                mayor = id_sala
        return mayor

    def _en_rango(self, id_sala: int) -> bool:
        return 0 <= id_sala < self._tamano

    def _validar_sala(self, id_sala: int) -> None:
        if not self._esqueleto.existe_sala(id_sala):
            raise ValueError(f"No existe la sala {id_sala} en el esqueleto")