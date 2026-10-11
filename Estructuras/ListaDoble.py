"""
ListaDoble (doblemente enlazada) — estructura compartida del equipo.

Implementación propia con nodos doblemente enlazados

    cabeza -> [a] <-> [b] <-> [c] <- cola
    (a.anterior es None)          (c.siguiente es None)

Cada elemento vive en un NodoDoble. Quien agrega un elemento recibe su nodo y puede usarlo
después como "mango" para quitarlo o moverlo SIN recorrer la lista. Esa es la razón de ser
de esta estructura: operar sobre un nodo conocido cuesta O(1) sin importar su posición.

Costos:
    agregar_al_frente   O(1)  se enlaza antes de 'cabeza'
    agregar_al_final    O(1)  se enlaza después de 'cola'
    quitar(nodo)        O(1)  solo se reenlazan los dos vecinos del nodo
    mover_al_frente     O(1)  quitar + agregar al frente, sin recorrer
    insertar_despues    O(1)  vuelve a enlazar un nodo suelto después de otro (deshacer)
    contiene(nodo)      O(1)  se consulta el dueño del nodo
    a_array             O(n)  recorre de cabeza a cola
    tamano/esta_vacia   O(1)  se lleva un contador
Memoria: O(n), un nodo por elemento.

Uso: Inventario (Integrante 3). Disponible para la política de desalojo de CacheCatalogo
(Integrante 2), que necesita las mismas operaciones: mover_al_frente al usar una ficha y
quitar(cola) al desalojar la menos usada.
Regla del equipo: no cambiar los nombres de los métodos sin avisar a los demás.
"""

class NodoDoble:
    __slots__ = ("dato", "anterior", "siguiente", "_dueno")

    def __init__(self, dato):
        self.dato = dato
        self.anterior: "NodoDoble | None" = None
        self.siguiente: "NodoDoble | None" = None
        self._dueno: "ListaDoble | None" = None  # lista a la que pertenece; None si no está en ninguna


class ListaDoble:

    def __init__(self):
        self._cabeza: NodoDoble | None = None
        self._cola: NodoDoble | None = None
        self._tamano = 0

 # ---- Lectura de los extremos (solo lectura: nadie de afuera puede romper los enlaces) ----

    @property   # transforma un m[etodo de una clase en un atributo de lectura
    def cabeza(self) -> "NodoDoble | None":
        return self._cabeza

    @property
    def cola(self) -> "NodoDoble | None":
        return self._cola

    # agregar nuevos elementos

    def agregar_al_frente(self, dato):
        nodo = NodoDoble(dato)
        self._enlazar_al_frente(nodo)
        return nodo

    def agregar_al_final(self, dato):
        nodo = NodoDoble(dato)

        if self._cola is None:
            self._cabeza = nodo
        else:
            nodo.anterior = self._cola
            self._cola.siguiente = nodo

        self._cola = nodo
        nodo._dueno = self
        self._tamano += 1
        return nodo

    # eliminar y mover elementos

    def eliminar(self, nodo : NodoDoble):
        self._verificar_dueno(nodo)
        self._desenlazar(nodo)
        return nodo.dato

    def mover_al_frente(self, nodo : NodoDoble) -> None:
        self._verificar_dueno(nodo)

        if nodo is self._cabeza:
            return

        self._desenlazar(nodo)
        self._enlazar_al_frente(nodo)

    def insertar_despues(self, nodo: NodoDoble, anterior: "NodoDoble | None") -> None:
        """Vuelve a enlazar un nodo suelto después de 'anterior' (None = al frente).
        Lo usa HistorialRetroceso para deshacer un soltar o un equipar."""
        if nodo._dueno is not None:
            raise ValueError("El nodo ya pertenece a una lista")
        if anterior is None:
            self._enlazar_al_frente(nodo)
            return
        self._verificar_dueno(anterior)
        nodo.anterior = anterior
        nodo.siguiente = anterior.siguiente
        if anterior.siguiente is None:
            self._cola = nodo
        else:
            anterior.siguiente.anterior = nodo
        anterior.siguiente = nodo
        nodo._dueno = self
        self._tamano += 1

    # consultar lista o un elemento en la lista

    def contiene(self, nodo) -> bool:
        return nodo is not None and nodo._dueno is self

    def a_array(self) -> list:
        datos = []
        actual = self._cabeza

        while actual is not None:
            datos.append(actual.dato)
            actual = actual.siguiente
        return datos

    def esta_vacia(self) -> bool:
        return self._cabeza is None

    def tamano(self) -> int:
        return self._tamano

    def __len__(self) -> int:
        return self._tamano

    # funciones auxiliares para la lista (privadas)

    def _verificar_dueno(self, nodo) -> None:
        if nodo is None or nodo._dueno is not self:
            raise ValueError("El nodo no pertenece a esta lista")

    def _desenlazar(self, nodo: NodoDoble) -> None:
        if nodo.anterior is None:
            self._cabeza = nodo.siguiente
        else:
            nodo.anterior.siguiente = nodo.siguiente

        if nodo.siguiente is None:
            self._cola = nodo.anterior
        else:
            nodo.siguiente.anterior = nodo.anterior

        nodo.anterior = None
        nodo.siguiente = None
        nodo._dueno = None
        self._tamano -= 1

    def _enlazar_al_frente(self, nodo: NodoDoble) -> None:
        nodo.anterior = None
        nodo.siguiente = self._cabeza

        if self._cabeza is None:
            self._cola = nodo
        else:
            self._cabeza.anterior = nodo

        self._cabeza = nodo
        nodo._dueno = self
        self._tamano += 1
