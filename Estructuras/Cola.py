"""
Cola (FIFO) — estructura compartida del equipo.

Implementación propia con nodos simplemente enlazados (la restricción del curso permite
solo arrays, listas, pilas y colas implementadas por el equipo; collections.deque está
prohibido).

    frente -> [a] -> [b] -> [c] <- final
    desencolar() saca 'a'; encolar(x) agrega x después de 'c'.

Costos:
    encolar      O(1)  se enlaza después de 'final'
    desencolar   O(1)  se quita el nodo de 'frente'
    ver_frente   O(1)
    esta_vacia   O(1)
    tamano       O(1)  se lleva un contador
Memoria: O(n), un nodo por elemento.

Uso actual: recorrido BFS de GestorContenido (Integrante 2).
Regla del equipo: no cambiar los nombres de los métodos sin avisar a los demás.
"""


class _Nodo:
    __slots__ = ("valor", "siguiente")

    def __init__(self, valor):
        self.valor = valor
        self.siguiente: "_Nodo | None" = None


class Cola:

    def __init__(self):
        self._frente: _Nodo | None = None
        self._final: _Nodo | None = None
        self._tamano = 0

    def encolar(self, valor) -> None:
        """Agrega 'valor' al final de la cola."""
        nodo = _Nodo(valor)
        if self._final is None:          # cola vacía: el nodo es frente y final a la vez
            self._frente = nodo
        else:
            self._final.siguiente = nodo
        self._final = nodo
        self._tamano += 1

    def desencolar(self):
        """Quita y devuelve el elemento del frente. Lanza IndexError si la cola está vacía."""
        if self._frente is None:
            raise IndexError("desencolar de una cola vacía")
        nodo = self._frente
        self._frente = nodo.siguiente
        if self._frente is None:         # se sacó el último: la cola queda vacía
            self._final = None
        self._tamano -= 1
        return nodo.valor

    def ver_frente(self):
        """Devuelve el elemento del frente sin quitarlo. Lanza IndexError si está vacía."""
        if self._frente is None:
            raise IndexError("ver_frente de una cola vacía")
        return self._frente.valor

    def esta_vacia(self) -> bool:
        return self._frente is None

    def tamano(self) -> int:
        return self._tamano

    def __len__(self) -> int:
        return self._tamano