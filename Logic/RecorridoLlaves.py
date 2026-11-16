"""
RecorridoLlaves (Integrante 2, feature 003): el recorrido incremental por oleadas, la frontera bloqueada y la fase
hacia afuera (research R4 y R6; data-model §3).

Oleada: mientras la Cola (Estructuras/Cola.py) no esté vacía, se saca una sala; sus llaves sin ver pasan a «vista en
esta oleada»; cada cara abierta o con llave ya obtenida alcanza su destino; una cara con llave no obtenida se anota en
esperando[k]; una cerrada sin llave, en sin_llave. Al vaciarse la cola, las llaves vistas se ordenan por índice (= por
id) con el Ordenador, pasan a obtenidas y se agregan al orden; luego SOLO se reabren las caras de sus esperando[k].
Nunca se repite el recorrido completo (NFR-302): cada sala y cada cara se procesan una vez.
Complejidad: O(S + E + U + K log K) en tiempo; O(S + E + U + K) en espacio.

Si la cripta no es resoluble, el MISMO recorrido sigue (NFR-303): calcular_frontera() junta las caras que quedaron
esperando una llave no obtenida o sin llave y cuyo destino sigue afuera (FR-308), y fase_hacia_afuera() asigna a
cada sala de afuera la puerta que bloquea su zona según FR-310 y su nivel. Todo con while/for y la Cola: SIN
RECURSIÓN (research R6, riesgo R-9).
"""
from Estructuras.Cola import Cola
from Estructuras.Ordenador import Ordenador
from Logic.GrafoLlaves import ABIERTA, CERRADA_CON_LLAVE, SIN_SALIDA, GrafoLlaves

# estado_llave[k]
SIN_VER = 0
VISTA = 1        # vista en la oleada actual
OBTENIDA = 2


class RecorridoLlaves:
    """Estado del recorrido sobre un GrafoLlaves: región alcanzable, llaves obtenidas y orden de obtención."""

    def __init__(self, grafo: GrafoLlaves):
        self._grafo = grafo
        self.alcanzable: list[bool] = [False] * grafo.cantidad_salas
        self.estado_llave: list[int] = [SIN_VER] * grafo.cantidad_llaves
        self.oleada_llave: list[int] = [-1] * grafo.cantidad_llaves    # oleada en que se obtuvo, o −1
        self.orden: list[int] = []                                      # índices de llave por (oleada, id)
        # Caras cerradas con la llave k que salen de una sala alcanzable; se vacía al obtener k.
        self.esperando: list[list[int]] = [[] for _ in range(grafo.cantidad_llaves)]
        self.sin_llave: list[int] = []        # caras cerradas sin llave que salen de una sala alcanzable
        self.caras_de_salida: list[int] = []  # caras con es_cara_de_salida que salen de una sala alcanzable
        self.frontera: list[int] = []         # caras de la frontera, ordenadas por c (calcular_frontera)
        # «La puerta que bloquea» de FR-310, con otro nombre: la cara por la que se entra a la zona de s (menor nivel;
        # desempate por sala de origen y dirección), la primera que llegó a esa zona en la fase hacia afuera, o −1.
        self.puerta_que_encierra: list[int] = [-1] * grafo.cantidad_salas
        # Puertas cerradas cruzadas desde la región: 0 dentro de la región, −1 si no se llega (fase_hacia_afuera).
        self.nivel: list[int] = [-1] * grafo.cantidad_salas

    def recorrer(self) -> None:
        """Oleadas desde sala_inicial hasta que no aparece ninguna llave nueva. Se llama una vez."""
        grafo = self._grafo
        cola = Cola()
        inicio = grafo.sala_inicial
        if 0 <= inicio < grafo.cantidad_salas and grafo.existe[inicio]:
            self.alcanzable[inicio] = True
            cola.encolar(inicio)
        oleada = 0
        while True:
            nuevas: list[int] = []
            while not cola.esta_vacia():
                self._visitar(cola.desencolar(), cola, nuevas)
            if len(nuevas) == 0:
                return
            nuevas = Ordenador.ordenar(nuevas, Ordenador.comparar)   # dentro de la oleada, por id (R5)
            for k in nuevas:
                self.estado_llave[k] = OBTENIDA
                self.oleada_llave[k] = oleada
                self.orden.append(k)
            for k in nuevas:                                         # solo se reabren las caras que las esperaban
                for c in self.esperando[k]:
                    self._alcanzar(grafo.destino[c], cola)
                self.esperando[k] = []
            oleada += 1

    def obtenida(self, k: int) -> bool:
        """¿Se obtuvo la llave k?"""
        return self.estado_llave[k] == OBTENIDA

    # ------------------------------------------------------------ reporte (historia 2)
    def calcular_frontera(self) -> None:
        """
        R4, paso 5 (FR-308): las caras de esperando[k] de llaves no obtenidas y de sin_llave cuyo destino sigue fuera
        de la región, ordenadas por c (= por sala alcanzable y dirección). Cada cara sale de una sala alcanzable y se
        anotó una sola vez, así que cada puerta aparece una vez, con la llave de la cara de la sala alcanzable, y una
        salida sin vuelta de afuera hacia la región nunca entra. Después de recorrer().
        """
        grafo = self._grafo
        caras: list[int] = []
        for k in range(grafo.cantidad_llaves):
            if self.estado_llave[k] != OBTENIDA:
                for c in self.esperando[k]:
                    if not self.alcanzable[grafo.destino[c]]:
                        caras.append(c)
        for c in self.sin_llave:
            if not self.alcanzable[grafo.destino[c]]:
                caras.append(c)
        self.frontera = Ordenador.ordenar(caras, Ordenador.comparar)

    def fase_hacia_afuera(self) -> None:
        """
        R6 (FR-310), continuación del mismo recorrido y sin recursión. Nivel 1 = las puertas de la frontera en orden;
        para cada una, si su destino todavía no tiene puerta, se le asigna y se inunda su zona con la Cola (caras
        abiertas o con llave obtenida); las caras cerradas con llave no obtenida o sin llave que salen de la zona son
        las puertas del nivel siguiente, que se ordena por (sala de origen, dirección) antes de procesarlo. Así la
        puerta asignada es la de menor nivel y, si empatan, la de menor sala de origen y dirección. Cada sala y cada
        cara se procesan una vez: O(S + E) más ordenar cada nivel. Después de calcular_frontera().
        """
        grafo = self._grafo
        for s in range(grafo.cantidad_salas):
            if self.alcanzable[s]:
                self.nivel[s] = 0
        actual = self.frontera
        numero = 1
        while len(actual) > 0:
            siguiente: list[int] = []
            for puerta in actual:
                destino = grafo.destino[puerta]
                if self.nivel[destino] != -1:
                    continue                    # dentro de la región o ya en la zona de otra puerta
                self._inundar_zona(destino, puerta, numero, siguiente)
            actual = Ordenador.ordenar(siguiente, Ordenador.comparar)
            numero += 1

    def _inundar_zona(self, inicio: int, puerta: int, numero: int, siguiente: list[int]) -> None:
        """Asigna 'puerta' y 'numero' a la zona de 'inicio' (anchura con la Cola) y anota sus puertas de salida."""
        grafo = self._grafo
        cola = Cola()
        self.puerta_que_encierra[inicio] = puerta
        self.nivel[inicio] = numero
        cola.encolar(inicio)
        while not cola.esta_vacia():
            u = cola.desencolar()
            for d in range(4):
                c = u * 4 + d
                tipo = grafo.tipo_cara[c]
                if tipo == SIN_SALIDA:
                    continue
                destino = grafo.destino[c]
                if self.nivel[destino] != -1:
                    continue
                if tipo == ABIERTA or (tipo == CERRADA_CON_LLAVE and self.estado_llave[grafo.llave_cara[c]] == OBTENIDA):
                    self.puerta_que_encierra[destino] = puerta
                    self.nivel[destino] = numero
                    cola.encolar(destino)
                else:
                    siguiente.append(c)         # cerrada con llave no obtenida o sin llave: nivel siguiente

    # ------------------------------------------------------------ auxiliares
    def _visitar(self, u: int, cola: Cola, nuevas: list[int]) -> None:
        """Procesa la sala alcanzable u: sus llaves y sus cuatro caras."""
        grafo = self._grafo
        for k in grafo.llaves_en_sala[u]:
            if self.estado_llave[k] == SIN_VER:
                self.estado_llave[k] = VISTA
                nuevas.append(k)
        for d in range(4):
            c = u * 4 + d
            tipo = grafo.tipo_cara[c]
            if tipo == SIN_SALIDA:
                continue
            if grafo.es_cara_de_salida[c]:
                self.caras_de_salida.append(c)        # se haya obtenido o no llave_salida
            if tipo == ABIERTA:
                self._alcanzar(grafo.destino[c], cola)
            elif tipo == CERRADA_CON_LLAVE:
                k = grafo.llave_cara[c]
                if self.estado_llave[k] == OBTENIDA:
                    self._alcanzar(grafo.destino[c], cola)
                else:
                    self.esperando[k].append(c)
            else:
                self.sin_llave.append(c)

    def _alcanzar(self, sala: int, cola: Cola) -> None:
        if not self.alcanzable[sala]:
            self.alcanzable[sala] = True
            cola.encolar(sala)
