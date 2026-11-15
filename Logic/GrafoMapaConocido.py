"""
GrafoMapaConocido (Lógica, integrante 2, feature 002): el grafo de búsqueda de «ir a» sobre lo que el jugador conoce
(data-model §3; contracts/contrato-mapa-conocido.md (a), confirmado por el integrante 3 en T005).

Tiene la interfaz exacta de specs/001-terreno-cazador/contracts/busqueda-rutas.md:
    cantidad_salas(), salidas(u) y entradas(x), con pares (sala, costo).
Se le pasa tal cual a BusquedaCostoMinimo o a paso_desde_cero.

«Utilizable»: una salida u -> v en la dirección d lo es si y solo si u y v están EXPLORADAS y la cara de u
(caras[u*4 + d]) se recuerda ABIERTA. Costo = SalidaViva.costo (igualado por Lógica, 001 FR-101).

Garantías:
    - Lee mapa.estado y mapa.caras en vivo en cada llamada (no guarda referencias: restaurar los reemplaza).
    - No consulta el estado real de ninguna puerta ni el contenido de ninguna sala (FR-217).
    - (v, c) está en salidas(u) si y solo si (u, c) está en entradas(v).
    - Una sala no explorada no tiene salidas ni entradas. El estado se mira ANTES de leer mazmorra.salas[u], así que
      la posición 0 o un hueco devuelven [] sin error.
    - No avisa a una búsqueda guardada: «ir a» empieza una búsqueda nueva por paso (contrato (a), research R5).

La adyacencia inversa del esqueleto (_inversa: por sala, los pares (origen, dirección) que llegan a ella) solo depende
del esqueleto, que no cambia en la partida: se arma en la primera llamada a entradas, en O(S + E), con arrays, como
en GrafoEsqueleto, y queda en este objeto.

Costos: constructor O(1); cantidad_salas O(1); salidas(u) O(4); entradas(x) O(grado de entrada de x), más O(S + E)
la primera vez.
"""
from DTO.MapaConocidoDTO import ABIERTA, EXPLORADA


class GrafoMapaConocido:
    """Grafo de las salidas utilizables del mapa conocido."""

    def __init__(self, mapa) -> None:
        self.mapa = mapa
        self._inversa: list[list[tuple[int, int]]] | None = None    # por sala: (origen, dirección)

    def cantidad_salas(self) -> int:
        """len(Mazmorra.salas): ids reales de 0 a cantidad_salas() - 1 (la posición 0 puede no ser una sala)."""
        return len(self.mapa.mazmorra.salas)

    def salidas(self, u: int) -> list[tuple[int, int]]:
        """(destino, costo) de las salidas utilizables de u, en orden de dirección; [] si u no está explorada."""
        estado = self.mapa.estado
        if estado[u] != EXPLORADA:
            return []
        caras = self.mapa.caras
        resultado = []
        salidas = self.mapa.mazmorra.salas[u].salidas
        for d in range(4):
            s = salidas[d]
            if s is None or caras[u * 4 + d] != ABIERTA:
                continue
            if self._existe(s.destino) and estado[s.destino] == EXPLORADA:
                resultado.append((s.destino, s.costo))
        return resultado

    def entradas(self, x: int) -> list[tuple[int, int]]:
        """(origen, costo) de las salidas utilizables que llegan a x; [] si x no está explorada."""
        estado = self.mapa.estado
        if estado[x] != EXPLORADA:
            return []
        if self._inversa is None:
            self._armar_inversa()
        caras = self.mapa.caras
        salas = self.mapa.mazmorra.salas
        resultado = []
        for origen, direccion in self._inversa[x]:
            if estado[origen] == EXPLORADA and caras[origen * 4 + direccion] == ABIERTA:
                resultado.append((origen, salas[origen].salidas[direccion].costo))
        return resultado

    # ---- interno

    def _existe(self, sala: int) -> bool:
        salas = self.mapa.mazmorra.salas
        return 0 <= sala < len(salas) and salas[sala] is not None

    def _armar_inversa(self) -> None:
        """Por sala, los pares (origen, dirección) de las salidas del esqueleto que llegan a ella. O(S + E)."""
        salas = self.mapa.mazmorra.salas
        inversa: list[list[tuple[int, int]]] = []
        for _ in range(len(salas)):
            inversa.append([])
        for origen in range(len(salas)):
            sala = salas[origen]
            if sala is None:
                continue
            for direccion in range(4):
                s = sala.salidas[direccion]
                if s is not None and self._existe(s.destino):
                    inversa[s.destino].append((origen, direccion))
        self._inversa = inversa
