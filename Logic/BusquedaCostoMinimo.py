"""
BusquedaCostoMinimo (feature 001, T023): búsqueda de costo mínimo reanudable desde un origen.

Contrato: specs/001-terreno-cazador/contracts/busqueda-rutas.md. Decisiones: research.md R1 a R3.

- Mide la distancia de cada sala HACIA el origen: al resolver una sala x relaja grafo.entradas(x),
  así que una salida u -> x solo se lee al resolver x (por eso la búsqueda va «al revés»).
- Es reanudable: distancia_hasta(sala, limite) extiende la búsqueda solo hasta resolver esa sala o hasta
  que el mínimo de la frontera pase el límite, y otra llamada sigue desde donde quedó.
- Arrays con generación: distancia, marca_distancia y marca_resuelta se crean una sola vez, en el
  constructor, con grafo.cantidad_salas() casillas (el esqueleto ya está cargado y no crece). Una casilla
  vale solo si su marca es igual a la generación actual, así que reiniciar no recorre los arrays.
- La frontera es un MonticuloMinimo con borrado perezoso: las entradas viejas se descartan al extraerlas.
- No usa el generador aleatorio (FR-115): el desempate es por menor id (FR-111).

No conoce cazadores ni jugadores: el grafo es un parámetro (lo reutiliza «ir a», feature 002).
"""
from Estructuras.MonticuloMinimo import MonticuloMinimo


class BusquedaCostoMinimo:
    """Búsqueda de costo mínimo hacia un origen, reanudable y con corte en un límite."""

    def __init__(self, grafo) -> None:
        self.grafo = grafo
        salas = grafo.cantidad_salas()
        self.distancia: list[int] = [0] * salas
        self.marca_distancia: list[int] = [-1] * salas       # -1: no vale en ninguna generación
        self.marca_resuelta: list[int] = [-1] * salas
        self.frontera = MonticuloMinimo()
        self.generacion = 0
        self.origen: int | None = None
        self.resueltas = 0

    def reiniciar(self, origen: int) -> None:
        """Empieza una búsqueda nueva desde 'origen'. No recorre los arrays: cambia la generación."""
        self.generacion += 1
        self.frontera.vaciar()
        self.origen = origen
        self._fijar_distancia(origen, 0)
        self.frontera.insertar(0, origen)

    def distancia_hasta(self, sala: int, limite: int | None) -> int | None:
        """
        La distancia d de 'sala' al origen, extendiendo la búsqueda solo lo necesario. None si no hay ruta
        o si d > limite (limite None = sin tope). Si d = limite, devuelve d (FR-109, FR-110).
        """
        while not self.esta_resuelta(sala) and not self.frontera.esta_vacio():
            clave, x = self.frontera.ver_minimo()
            if limite is not None and clave > limite:
                break
            self.frontera.extraer_minimo()
            if self.esta_resuelta(x) or clave != self.distancia[x]:
                continue                                    # entrada vieja (borrado perezoso)
            self.marca_resuelta[x] = self.generacion
            self.resueltas += 1
            for origen, costo in self.grafo.entradas(x):
                nueva = clave + costo
                if not self.esta_resuelta(origen) and (not self._tiene_distancia(origen)
                                                       or nueva < self.distancia[origen]):
                    self._fijar_distancia(origen, nueva)
                    self.frontera.insertar(nueva, origen)
        if not self.esta_resuelta(sala):
            return None
        d = self.distancia[sala]
        if limite is not None and d > limite:
            return None
        return d

    def esta_resuelta(self, sala: int) -> bool:
        """True si la distancia de 'sala' ya es definitiva en esta búsqueda."""
        return self.marca_resuelta[sala] == self.generacion

    def distancia_resuelta(self, sala: int) -> int:
        """La distancia definitiva de 'sala' (debe estar resuelta)."""
        return self.distancia[sala]

    def paso_hacia_origen(self, u: int, d: int) -> tuple[int, int]:
        """
        (v, costo): la vecina v de MENOR id con costo(u, v) + dist(v) = d, y el costo de la salida más barata
        hacia ella (FR-111, FR-119). Toda vecina que cumple la igualdad tiene dist < d y ya está resuelta (R3).
        """
        mejor_v = None
        mejor_costo = None
        for v, costo in self.grafo.salidas(u):
            if not self.esta_resuelta(v) or costo + self.distancia[v] != d:
                continue
            if mejor_v is None or v < mejor_v or (v == mejor_v and costo < mejor_costo):
                mejor_v = v
                mejor_costo = costo
        if mejor_v is None:
            raise ValueError(f"La sala {u} no tiene una vecina en una ruta de costo {d}")
        return mejor_v, mejor_costo

    # ---- interno

    def _tiene_distancia(self, sala: int) -> bool:
        return self.marca_distancia[sala] == self.generacion

    def _fijar_distancia(self, sala: int, valor: int) -> None:
        self.distancia[sala] = valor
        self.marca_distancia[sala] = self.generacion


def paso_desde_cero(grafo, origen: int, u: int, limite: int | None) -> tuple[int, int] | None:
    """
    Referencia sin reutilización (alternativa A de R2): crea una búsqueda nueva desde 'origen' y devuelve
    el paso (destino, costo) de 'u' por una ruta de costo mínimo d ≤ limite, o None si no hay ruta,
    si d > limite o si u ya es el origen.
    """
    if u == origen:
        return None
    busqueda = BusquedaCostoMinimo(grafo)
    busqueda.reiniciar(origen)
    d = busqueda.distancia_hasta(u, limite)
    if d is None:
        return None
    return busqueda.paso_hacia_origen(u, d)
