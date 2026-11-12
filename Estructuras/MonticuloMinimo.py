"""
MonticuloMinimo — cola de prioridad propia (feature 001, research R1).

Montículo binario mínimo sobre un array (list usado como almacenamiento contiguo). Guarda pares
(clave, valor) y los compara por clave y, si empatan, por valor. No usa heapq (Principio II).

    posición i: hijos en 2i + 1 y 2i + 2; padre en (i - 1) // 2.

Costos:
    insertar        O(log n)  se agrega al final y sube
    extraer_minimo  O(log n)  el último pasa a la raíz y baja
    ver_minimo      O(1)
    esta_vacio      O(1)
    tamano          O(1)
    vaciar          O(1)      se cambia el array por uno nuevo
Memoria: O(n). Admite entradas repetidas del mismo valor: quien lo usa descarta las viejas al
extraerlas (borrado perezoso).

Uso actual: la frontera de Logic/BusquedaCostoMinimo.py (búsqueda de ruta del cazador).
No depende de ninguna otra capa.
"""


class MonticuloMinimo:
    """Cola de prioridad mínima de pares (clave, valor)."""

    def __init__(self) -> None:
        self._datos: list[tuple[int, int]] = []

    def insertar(self, clave: int, valor: int) -> None:
        """Agrega el par (clave, valor)."""
        self._datos.append((clave, valor))
        self._subir(len(self._datos) - 1)

    def extraer_minimo(self) -> tuple[int, int]:
        """Saca y devuelve el par de menor clave (y menor valor si empatan). IndexError si está vacío."""
        if not self._datos:
            raise IndexError("El montículo está vacío")
        minimo = self._datos[0]
        ultimo = self._datos.pop()
        if self._datos:
            self._datos[0] = ultimo
            self._bajar(0)
        return minimo

    def ver_minimo(self) -> tuple[int, int] | None:
        """El par mínimo sin sacarlo, o None si está vacío."""
        if not self._datos:
            return None
        return self._datos[0]

    def esta_vacio(self) -> bool:
        """True si no tiene pares."""
        return not self._datos

    def tamano(self) -> int:
        """Cuántos pares tiene (incluidas las entradas repetidas)."""
        return len(self._datos)

    def vaciar(self) -> None:
        """Quita todos los pares."""
        self._datos = []

    # ---- interno

    def _subir(self, i: int) -> None:
        datos = self._datos
        while i > 0:
            padre = (i - 1) // 2
            if not datos[i] < datos[padre]:
                return
            datos[i], datos[padre] = datos[padre], datos[i]
            i = padre

    def _bajar(self, i: int) -> None:
        datos = self._datos
        n = len(datos)
        while True:
            menor = i
            izquierdo = 2 * i + 1
            derecho = izquierdo + 1
            if izquierdo < n and datos[izquierdo] < datos[menor]:
                menor = izquierdo
            if derecho < n and datos[derecho] < datos[menor]:
                menor = derecho
            if menor == i:
                return
            datos[i], datos[menor] = datos[menor], datos[i]
            i = menor
