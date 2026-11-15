"""
CiclosLlaves (Integrante 2, feature 003): ciclos de llaves y llaves dependientes (FR-310; research R6; data-model §3).

Cada llave no obtenible k tiene a lo sumo una arista: siguiente[k], la llave que pide la puerta que bloquea su
ubicación de menor nivel (si empatan, la primera en el orden de FR-309). No tiene arista (−1) si esa puerta es «sin
llave», si la llave no tiene ubicación o si ninguna de sus salas se alcanza ni cruzando puertas. Es un grafo
funcional: los ciclos son disjuntos y se hallan sin repetir.

SIN RECURSIÓN (riesgo R-9: una cadena de 1 000 llaves llegaría al límite de Python): seguir las aristas es un while
que guarda el camino en un arreglo, y al terminar cada recorrido un for sobre ese camino asigna entrada[k]:
    - la llave actual ya es de este recorrido  -> ciclo nuevo desde pos_camino[k]; las anteriores dependen de k;
    - la llave actual es de un recorrido previo -> todas toman su entrada (la de un ciclo, o −1);
    - no hay arista                              -> todas toman −1 (solo aparecen entre las no obtenibles).
Cada llave entra una vez a 'camino' y se recorre una vez más al asignar: O(K). Los ciclos se rotan para empezar por
su llave de menor id y se ordenan por esa llave (O(C log C)); los dependientes salen por id en una pasada.
"""
from Estructuras.Ordenador import Ordenador
from Logic.GrafoLlaves import CERRADA_CON_LLAVE, GrafoLlaves
from Logic.RecorridoLlaves import RecorridoLlaves


class CiclosLlaves:
    """Aristas entre llaves no obtenibles, ciclos (rotados y ordenados) y dependientes de cada ciclo."""

    def __init__(self, grafo: GrafoLlaves, recorrido: RecorridoLlaves):
        """Necesita el recorrido con la fase hacia afuera ya hecha (puerta_que_encierra y nivel)."""
        self._grafo = grafo
        self._recorrido = recorrido
        k_total = grafo.cantidad_llaves
        self.siguiente: list[int] = [-1] * k_total      # llave de la puerta que la bloquea, o −1 (sin arista)
        self.ubic_usada: list[int] = [-1] * k_total     # posición en grafo.ubicaciones de la ubicación usada, o −1
        self.puerta_usada: list[int] = [-1] * k_total   # cara que bloquea la ubicación usada, o −1
        self.marca: list[int] = [0] * k_total           # número del recorrido que la visitó, o 0
        self.pos_camino: list[int] = [0] * k_total      # posición de k en 'camino' durante su recorrido
        self.camino: list[int] = []                     # llaves del recorrido actual, en el orden de las aristas
        self.ciclo_de: list[int] = [-1] * k_total       # ciclo al que pertenece o del que depende, o −1
        self.entrada: list[int] = [-1] * k_total        # llave del ciclo donde entra su cadena (ella misma si está en él)
        self.ciclos: list[list[int]] = []               # llaves de cada ciclo, desde su menor id, por id de la primera
        self.dependientes: list[list[int]] = []         # dependientes de cada ciclo (mismo índice), por id
        self._calcular_aristas()
        self._detectar()

    def _calcular_aristas(self) -> None:
        """siguiente[k], ubic_usada[k] y puerta_usada[k] de cada llave no obtenible. O(U)."""
        grafo, recorrido = self._grafo, self._recorrido
        for k in range(grafo.cantidad_llaves):
            if recorrido.obtenida(k):
                continue
            mejor = -1
            for p in range(grafo.inicio_ubic[k], grafo.fin_ubic[k]):     # ya en el orden de FR-309
                sala = grafo.ubicaciones[p].sala
                if not (0 <= sala < grafo.cantidad_salas) or recorrido.nivel[sala] < 1:
                    continue                                              # no se alcanza ni cruzando puertas
                if mejor == -1 or recorrido.nivel[sala] < recorrido.nivel[grafo.ubicaciones[mejor].sala]:
                    mejor = p
            if mejor == -1:
                continue
            puerta = recorrido.puerta_que_encierra[grafo.ubicaciones[mejor].sala]
            self.ubic_usada[k] = mejor
            self.puerta_usada[k] = puerta
            if grafo.tipo_cara[puerta] == CERRADA_CON_LLAVE:
                self.siguiente[k] = grafo.llave_cara[puerta]

    def _detectar(self) -> None:
        """Recorridos por id con while y asignación con for: ciclos, entrada y ciclo_de. Sin recursión."""
        grafo, recorrido = self._grafo, self._recorrido
        sin_ordenar: list[list[int]] = []
        recorrido_actual = 0
        for inicio in range(grafo.cantidad_llaves):                       # índices en orden de id
            if recorrido.obtenida(inicio) or self.marca[inicio] != 0:
                continue
            recorrido_actual += 1
            self.camino = []
            k = inicio
            while k != -1 and self.marca[k] == 0:
                self.marca[k] = recorrido_actual
                self.pos_camino[k] = len(self.camino)
                self.camino.append(k)
                k = self.siguiente[k]
            if k != -1 and self.marca[k] == recorrido_actual:             # se cerró un ciclo nuevo
                numero = len(sin_ordenar)
                miembros: list[int] = []
                for i in range(self.pos_camino[k], len(self.camino)):
                    llave = self.camino[i]
                    miembros.append(llave)
                    self.entrada[llave] = llave
                    self.ciclo_de[llave] = numero
                for i in range(self.pos_camino[k]):
                    self.entrada[self.camino[i]] = k
                    self.ciclo_de[self.camino[i]] = numero
                sin_ordenar.append(self._rotar(miembros))
            else:                                                         # recorrido previo, o sin arista
                entrada = self.entrada[k] if k != -1 else -1
                ciclo = self.ciclo_de[k] if k != -1 else -1
                for llave in self.camino:
                    self.entrada[llave] = entrada
                    self.ciclo_de[llave] = ciclo
        self._ordenar_ciclos(sin_ordenar)

    @staticmethod
    def _rotar(miembros: list[int]) -> list[int]:
        """El ciclo empezando por su llave de menor índice (= menor id), sin cambiar el sentido de las aristas."""
        menor = 0
        for i in range(1, len(miembros)):
            if miembros[i] < miembros[menor]:
                menor = i
        rotado: list[int] = []
        for i in range(len(miembros)):
            rotado.append(miembros[(menor + i) % len(miembros)])
        return rotado

    def _ordenar_ciclos(self, sin_ordenar: list[list[int]]) -> None:
        """Ciclos por id de su llave inicial; dependientes de cada uno por id (una pasada sobre las llaves)."""
        orden = Ordenador.ordenar(list(range(len(sin_ordenar))), lambda a, b: sin_ordenar[a][0] - sin_ordenar[b][0])
        nuevo_numero = [0] * len(sin_ordenar)
        for posicion in range(len(orden)):
            nuevo_numero[orden[posicion]] = posicion
            self.ciclos.append(sin_ordenar[orden[posicion]])
            self.dependientes.append([])
        for k in range(self._grafo.cantidad_llaves):
            if self.ciclo_de[k] == -1:
                continue
            self.ciclo_de[k] = nuevo_numero[self.ciclo_de[k]]
            if self.entrada[k] != k:
                self.dependientes[self.ciclo_de[k]].append(k)
