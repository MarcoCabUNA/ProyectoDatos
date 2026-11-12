"""
GrafoEsqueleto (feature 001, T022): el grafo de búsqueda del cazador sobre la Mazmorra.

Implementa el protocolo de specs/001-terreno-cazador/contracts/busqueda-rutas.md:
    cantidad_salas(), salidas(u) y entradas(x), con pares (sala, costo).
«Utilizable» = salida abierta AHORA hacia una sala que existe, con el costo ya igualado (SalidaViva.costo).
Usa el esqueleto completo: no depende de la niebla ni del contenido descargado (FR-112), y una salida
cerrada no cuenta mientras siga cerrada (FR-113).

La adyacencia inversa (por sala, los pares (origen, dirección) que llegan a ella) no cambia durante la
partida: se arma una sola vez, la primera vez que se pide, en O(S + E), con arrays. Si después llegan
más salas al esqueleto, se vuelve a armar. El estado de cada puerta se lee en vivo en cada consulta.
"""


class GrafoEsqueleto:
    """Grafo de salidas abiertas sobre una Mazmorra."""

    def __init__(self, mazmorra) -> None:
        self.mazmorra = mazmorra
        self._inversa: list[list[tuple[int, int]]] | None = None   # por sala: (origen, dirección)

    def cantidad_salas(self) -> int:
        """Los ids válidos van de 0 a cantidad_salas() - 1 (la posición 0 puede no ser una sala)."""
        return len(self.mazmorra.salas)

    def salidas(self, u: int) -> list[tuple[int, int]]:
        """(destino, costo) de las salidas abiertas de u."""
        return self.mazmorra.salidas_abiertas_con_costo(u)

    def entradas(self, x: int) -> list[tuple[int, int]]:
        """(origen, costo) de las salidas abiertas ahora que llegan a x."""
        if self._inversa is None or len(self._inversa) != len(self.mazmorra.salas):
            self._armar_inversa()
        resultado = []
        for origen, direccion in self._inversa[x]:
            salida = self.mazmorra.salida(origen, direccion)
            if not salida.cerrada:
                resultado.append((origen, salida.costo))
        return resultado

    def _armar_inversa(self) -> None:
        salas = self.mazmorra.salas
        inversa: list[list[tuple[int, int]]] = []
        for _ in range(len(salas)):
            inversa.append([])
        for sala in salas:
            if sala is None:
                continue
            for direccion in range(len(sala.salidas)):
                salida = sala.salidas[direccion]
                if salida is not None and self.mazmorra._existe(salida.destino):
                    inversa[salida.destino].append((sala.id, direccion))
        self._inversa = inversa
