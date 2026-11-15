"""
MapaConocido (Lógica, integrante 2, feature 002): lo que el jugador sabe de la cripta (data-model §2, research R1-R3).

Dos arreglos indexados por posición, sin dict ni set:
    estado[sala]          DESCONOCIDA / AVISTADA / EXPLORADA, largo S = len(mazmorra.salas)
    caras[sala*4 + d]     SIN_OBSERVAR / ABIERTA / CERRADA (estado recordado de la cara), largo 4·S

Toda escritura pasa por _poner_estado / _poner_cara: si el valor no cambia no hacen nada; si cambia, registran en el
historial una función que devuelve ESA casilla a su valor anterior y después escriben. Así el pergamino deja el mapa
exactamente como antes de la acción (FR-222) sin copiar el mapa (NFR-203). Con historial None solo escriben.

Lógica no importa Datos ni Servicios: las constantes vienen de DTO/MapaConocidoDTO.py.

Solo escriben el mapa iniciar, entrar y puerta_cambio (research R2). Ninguna operación baja un estado (FR-203).
Las direcciones se recorren siempre en el orden N, S, E, O (0 a 3).

Costos: estado_sala, estado_cara y es_explorada O(1); _poner_estado y _poner_cara O(1); iniciar y puerta_cambio O(g);
entrar O(1 + Σ g de las salas que pasan a exploradas); buscar_exploradas O(S).
"""
from DTO.MapaConocidoDTO import ABIERTA, AVISTADA, CERRADA, DESCONOCIDA, EXPLORADA, SIN_OBSERVAR


class MapaConocido:
    """El mapa conocido de una partida. Lo crea el motor (motor.mapa)."""

    def __init__(self, mazmorra, jugador, historial) -> None:
        self.mazmorra = mazmorra            # solo lectura
        self.jugador = jugador              # solo lectura: Sala_Actual
        self.historial = historial          # HistorialRetroceso o None (bench sin motor)
        cantidad = len(mazmorra.salas)
        self.estado: list[int] = [DESCONOCIDA] * cantidad
        self.caras: list[int] = [SIN_OBSERVAR] * (4 * cantidad)

    # ---------- puntos de entrada que escriben el mapa (research R2)

    def iniciar(self, sala: int) -> None:
        """Conocimiento inicial (FR-202): la sala inicial explorada, sus vecinas avistadas y sus puertas observadas. O(g)."""
        self._explorar(sala)
        self._observar_puertas(sala)

    def entrar(self, sala: int, antorcha: bool) -> None:
        """
        El jugador entró a 'sala' (FR-203): queda explorada, los destinos de sus salidas avistados y sus puertas
        observadas (FR-207). Con 'antorcha' (el motor pasa si el efecto está activo; el mapa no conoce los efectos),
        también se explora el destino de cada salida de 'sala', abierta o cerrada, en orden de dirección, sin ir más
        allá (FR-210, FR-213); sus puertas no se observan, salvo la cara hacia 'sala' (FR-212). No lee ni carga
        contenido, no toca enemigos ni trampas y no consume tiempo (FR-211). Una vecina ya explorada se salta.
        O(1 + Σ g de las salas que pasan a exploradas).
        """
        self._explorar(sala)
        if antorcha:
            salidas = self.mazmorra.salas[sala].salidas
            for d in range(4):
                s = salidas[d]
                if s is not None and self._existe(s.destino):
                    self._explorar(s.destino)
        self._observar_puertas(sala)

    def puerta_cambio(self, a: int, b: int) -> None:
        """
        Aviso de la Mazmorra (por RepartidorAvisosPuertas) de que cambió una puerta: vuelve a observar las puertas de
        la sala del jugador (FR-207, FR-209). 'a' y 'b' no se usan: el aviso no identifica la puerta sin vuelta
        (research R2). Invariante: mientras el jugador está en x, el recordado de cada cara de cada puerta con cara
        en x es el real. Un aviso de una puerta lejana no cambia ni registra nada. O(1).
        """
        self._observar_puertas(self.jugador.Sala_Actual)

    # ---------- consultas

    def estado_sala(self, sala: int) -> int:
        """Estado de la sala: DESCONOCIDA, AVISTADA o EXPLORADA. O(1)."""
        return self.estado[sala]

    def estado_cara(self, sala: int, direccion: int) -> int:
        """Estado recordado de la cara de 'sala' en 'direccion' (0 N, 1 S, 2 E, 3 O). O(1)."""
        return self.caras[sala * 4 + direccion]

    def es_explorada(self, sala: int) -> bool:
        """
        True solo si 'sala' está EXPLORADA; False si está avistada o desconocida, y para la posición 0 o un hueco.
        No cambia nada ni registra en el historial (contrato (c); la usa ArmadorEstado para el H-2). O(1).
        """
        return self.estado[sala] == EXPLORADA

    def buscar_exploradas(self, nombre: str) -> list[int]:
        """
        Ids de las salas EXPLORADAS cuyo nombre coincide con 'nombre', comparando strip().casefold() en los dos lados
        (H-3, contrato (c)), en orden creciente de id. Un nombre vacío o de solo espacios devuelve [] (no coincide con
        ninguna sala). Si 'nombre' no es str, ValueError: es un error de programación del que llama. No cambia nada.
        O(S).
        """
        if not isinstance(nombre, str):
            raise ValueError(f"buscar_exploradas espera un str, no {type(nombre).__name__}")
        clave = nombre.strip().casefold()
        encontradas = []
        for sala in range(len(self.estado)):
            if self.estado[sala] == EXPLORADA and self.mazmorra.salas[sala].nombre.strip().casefold() == clave:
                encontradas.append(sala)
        return encontradas

    # ---------- exploración y observación (privados)

    def _existe(self, sala: int) -> bool:
        """True si 'sala' es una sala de la cripta (no un hueco ni una posición fuera del mapa)."""
        return 0 <= sala < len(self.estado) and self.mazmorra.salas[sala] is not None

    def _explorar(self, sala: int) -> None:
        """
        Si 'sala' ya está explorada, nada. Si no, la explora y avista los destinos desconocidos de sus salidas
        (FR-203, FR-204), en orden de dirección. O(g).
        """
        if self.estado[sala] == EXPLORADA:
            return
        self._poner_estado(sala, EXPLORADA)
        salidas = self.mazmorra.salas[sala].salidas
        for d in range(4):
            s = salidas[d]
            if s is not None and self._existe(s.destino) and self.estado[s.destino] == DESCONOCIDA:
                self._poner_estado(s.destino, AVISTADA)

    def _observar_puertas(self, sala: int) -> None:
        """
        Observa cada puerta con cara en 'sala' (FR-207): la cara de 'sala' y, si existe, la cara de vuelta del
        destino (Mazmorra._salida_inversa, solo lectura), cada una con su estado real. Una salida sin vuelta de otra
        sala hacia 'sala' no tiene cara aquí y no se observa. O(g).
        """
        salidas = self.mazmorra.salas[sala].salidas
        for d in range(4):
            s = salidas[d]
            if s is None or not self._existe(s.destino):
                continue
            self._poner_cara(sala * 4 + d, CERRADA if s.cerrada else ABIERTA)
            inversa = self.mazmorra._salida_inversa(sala, s.destino)
            if inversa is None:
                continue
            salidas_destino = self.mazmorra.salas[s.destino].salidas
            for d2 in range(4):
                if salidas_destino[d2] is inversa:            # dirección de la cara de vuelta, por identidad
                    self._poner_cara(s.destino * 4 + d2, CERRADA if inversa.cerrada else ABIERTA)
                    break

    # ---------- las dos únicas escrituras

    def _poner_estado(self, sala: int, valor: int) -> None:
        """Escribe el estado de una sala y registra su reversión si cambió."""
        anterior = self.estado[sala]
        if anterior == valor:
            return
        if self.historial is not None:
            self.historial.registrar_cambio(self._reversion("estado", sala, anterior))
        self.estado[sala] = valor

    def _poner_cara(self, cara: int, valor: int) -> None:
        """Escribe el estado recordado de una cara y registra su reversión si cambió."""
        anterior = self.caras[cara]
        if anterior == valor:
            return
        if self.historial is not None:
            self.historial.registrar_cambio(self._reversion("caras", cara, anterior))
        self.caras[cara] = valor

    def _reversion(self, arreglo: str, indice: int, anterior: int):
        """
        Función sin argumentos que devuelve la casilla 'indice' del arreglo ("estado" o "caras") a 'anterior'.
        El índice y el valor quedan ligados al llamar a este método (no se leen después de variables que cambian).
        El arreglo se busca por nombre al deshacer, así que la reversión escribe siempre en el arreglo vigente.
        """
        def deshacer() -> None:
            getattr(self, arreglo)[indice] = anterior
        return deshacer
