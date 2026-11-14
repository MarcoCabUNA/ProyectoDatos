"""
MapaConocido (Lógica, integrante 2, feature 002): lo que el jugador sabe de la cripta (data-model §2, research R1-R3).

Dos arreglos indexados por posición, sin dict ni set:
    estado[sala]          DESCONOCIDA / AVISTADA / EXPLORADA, largo S = len(mazmorra.salas)
    caras[sala*4 + d]     SIN_OBSERVAR / ABIERTA / CERRADA (estado recordado de la cara), largo 4·S

Toda escritura pasa por _poner_estado / _poner_cara: si el valor no cambia no hacen nada; si cambia, registran en el
historial una función que devuelve ESA casilla a su valor anterior y después escriben. Así el pergamino deja el mapa
exactamente como antes de la acción (FR-222) sin copiar el mapa (NFR-203). Con historial None solo escriben.

Lógica no importa Datos ni Servicios: las constantes vienen de DTO/MapaConocidoDTO.py.

Costos: estado_sala y estado_cara O(1); _poner_estado y _poner_cara O(1).
"""
from DTO.MapaConocidoDTO import DESCONOCIDA, SIN_OBSERVAR


class MapaConocido:
    """El mapa conocido de una partida. Lo crea el motor (motor.mapa)."""

    def __init__(self, mazmorra, jugador, historial) -> None:
        self.mazmorra = mazmorra            # solo lectura
        self.jugador = jugador              # solo lectura: Sala_Actual
        self.historial = historial          # HistorialRetroceso o None (bench sin motor)
        cantidad = len(mazmorra.salas)
        self.estado: list[int] = [DESCONOCIDA] * cantidad
        self.caras: list[int] = [SIN_OBSERVAR] * (4 * cantidad)

    # ---------- consultas

    def estado_sala(self, sala: int) -> int:
        """Estado de la sala: DESCONOCIDA, AVISTADA o EXPLORADA. O(1)."""
        return self.estado[sala]

    def estado_cara(self, sala: int, direccion: int) -> int:
        """Estado recordado de la cara de 'sala' en 'direccion' (0 N, 1 S, 2 E, 3 O). O(1)."""
        return self.caras[sala * 4 + direccion]

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
