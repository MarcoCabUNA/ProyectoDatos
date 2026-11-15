"""
GrafoLlaves (Integrante 2, feature 003): la preparación de la verificación de resolubilidad (data-model §3; research
R3, R4 y R5). Se arma una vez por verificación y no guarda nada entre verificaciones.

Las caras se combinan como en la primera parte con una Mazmorra APARTE (cargar_esqueleto aplica _igualar_caras): una
cara sin llave toma la llave y el estado cerrado de su inversa si esta declara llave; si no, cada cara se rige por lo
suyo (FR-302). Así la verificación y el juego combinan igual sin duplicar la regla. Esa Mazmorra se descarta: no toca
el motor, el generador aleatorio ni el contenido de las salas (FR-301). El costo y el cierre automático no se leen.

Todo son arreglos planos indexados por entero (Principio II; ningún dict ni set):
    sala s      existe[s], llaves_en_sala[s]
    cara c      c = sala*4 + dirección (0 N, 1 S, 2 E, 3 O): tipo_cara[c], destino[c], llave_cara[c], es_cara_de_salida[c]
    llave k     ids[k], inicio_ubic[k], fin_ubic[k]; los índices quedan en orden de id (índice menor = id menor)
    ubicación p ubicaciones[p], llave_ubicacion[p]

Índice de llaves (R3): una mención (id, tipo, posición) por cara cerrada con llave, por ubicación y por llave_salida;
se ordenan con el Ordenador y una pasada asigna índices consecutivos. Ubicaciones (R5, FR-309): ordenadas por (llave,
sala, sin enemigo antes que con enemigo, id de enemigo) y una pasada descarta cada una igual a la anterior.
Complejidad: O(S + E + U + M log M), con M ≤ E + U + 1 menciones.
"""
from DTO.CriptaDTO import CriptaDTO
from DTO.SalaDTO import SalaDTO
from DTO.UbicacionLlaveDTO import UbicacionLlaveDTO
from Estructuras.Ordenador import Ordenador
from Logic.Mazmorra import Mazmorra

# tipo_cara[c]
SIN_SALIDA = 0
ABIERTA = 1
CERRADA_CON_LLAVE = 2
CERRADA_SIN_LLAVE = 3

# Tipo de una mención de llave: desempata el ordenamiento para que no dependa del orden de entrada.
_MENCION_CARA = 0
_MENCION_UBICACION = 1
_MENCION_SALIDA = 2


class GrafoLlaves:
    """Caras combinadas, índice propio de llaves y ubicaciones ordenadas sin repetir, en arreglos planos."""

    def __init__(self, cripta: CriptaDTO, salas: list[SalaDTO], ubicaciones: list[UbicacionLlaveDTO]):
        mazmorra = Mazmorra(cripta.sala_salida, cripta.llave_salida)   # aparte: se descarta al terminar
        mazmorra.cargar_esqueleto(salas)
        self.sala_inicial: int = cripta.sala_inicial
        self.sala_salida: int = cripta.sala_salida
        self.cantidad_salas: int = self._cantidad_salas(len(mazmorra.salas), cripta, ubicaciones)
        menciones: list[tuple[str, int, int]] = []
        self._leer_caras(mazmorra, menciones)
        for i in range(len(ubicaciones)):
            menciones.append((ubicaciones[i].id, _MENCION_UBICACION, i))
        menciones.append((cripta.llave_salida, _MENCION_SALIDA, 0))
        llave_de_entrada = self._indexar_llaves(menciones, len(ubicaciones))
        self._ordenar_ubicaciones(ubicaciones, llave_de_entrada)
        self._marcar_caras_de_salida()

    # ------------------------------------------------------------ preparación
    def _cantidad_salas(self, largo: int, cripta: CriptaDTO, ubicaciones: list[UbicacionLlaveDTO]) -> int:
        """Id máximo + 1, también si sala_inicial, sala_salida o una ubicación nombran una sala más alta."""
        cantidad = largo
        for sala in (cripta.sala_inicial, cripta.sala_salida):
            if sala + 1 > cantidad:
                cantidad = sala + 1
        for u in ubicaciones:
            if u.sala + 1 > cantidad:
                cantidad = u.sala + 1
        return cantidad

    def _leer_caras(self, mazmorra: Mazmorra, menciones: list[tuple[str, int, int]]) -> None:
        """Lee las caras ya combinadas. Una cara con llave pero no cerrada es abierta, como en la primera parte."""
        n = self.cantidad_salas
        self.existe: list[bool] = [False] * n
        self.tipo_cara: list[int] = [SIN_SALIDA] * (n * 4)
        self.destino: list[int] = [-1] * (n * 4)
        self.llave_cara: list[int] = [-1] * (n * 4)
        largo = len(mazmorra.salas)
        for s in range(largo):
            sala = mazmorra.salas[s]
            if sala is None:
                continue
            self.existe[s] = True
            for d in range(4):
                salida = sala.salidas[d]
                if salida is None or not (0 <= salida.destino < largo) or mazmorra.salas[salida.destino] is None:
                    continue
                c = s * 4 + d
                self.destino[c] = salida.destino
                if not salida.cerrada:
                    self.tipo_cara[c] = ABIERTA
                elif salida.llave is None:
                    self.tipo_cara[c] = CERRADA_SIN_LLAVE
                else:
                    self.tipo_cara[c] = CERRADA_CON_LLAVE
                    menciones.append((salida.llave, _MENCION_CARA, c))

    def _indexar_llaves(self, menciones: list[tuple[str, int, int]], cantidad_ubicaciones: int) -> list[int]:
        """
        R3: ordena las menciones por (id, tipo, posición) y asigna índices consecutivos; escribe el índice en
        llave_cara y en llave_salida. Devuelve el índice de llave de cada ubicación en el orden de entrada.
        """
        ordenadas = Ordenador.ordenar(menciones, Ordenador.comparar)
        self.ids: list[str] = []
        llave_de_entrada = [-1] * cantidad_ubicaciones
        self.llave_salida: int = -1   # siempre existe: llave_salida se menciona siempre
        for id_llave, tipo, posicion in ordenadas:
            if len(self.ids) == 0 or self.ids[len(self.ids) - 1] != id_llave:
                self.ids.append(id_llave)
            k = len(self.ids) - 1
            if tipo == _MENCION_CARA:
                self.llave_cara[posicion] = k
            elif tipo == _MENCION_UBICACION:
                llave_de_entrada[posicion] = k
            else:
                self.llave_salida = k
        self.cantidad_llaves: int = len(self.ids)
        return llave_de_entrada

    def _ordenar_ubicaciones(self, ubicaciones: list[UbicacionLlaveDTO], llave_de_entrada: list[int]) -> None:
        """R5 y FR-309: ordena por (llave, sala, sin enemigo primero, enemigo) y quita las idénticas en una pasada."""

        def comparar(i: int, j: int) -> int:
            if llave_de_entrada[i] != llave_de_entrada[j]:
                return llave_de_entrada[i] - llave_de_entrada[j]
            a, b = ubicaciones[i], ubicaciones[j]
            if a.sala != b.sala:
                return -1 if a.sala < b.sala else 1
            if (a.enemigo is None) != (b.enemigo is None):
                return -1 if a.enemigo is None else 1
            if a.enemigo is not None and b.enemigo is not None and a.enemigo != b.enemigo:
                return -1 if a.enemigo < b.enemigo else 1
            return 0

        orden = Ordenador.ordenar(list(range(len(ubicaciones))), comparar)
        self.ubicaciones: list[UbicacionLlaveDTO] = []
        self.llave_ubicacion: list[int] = []
        anterior = -1
        for i in orden:
            if anterior != -1 and comparar(anterior, i) == 0:
                continue                                   # idéntica a la anterior: se indica una sola vez
            self.ubicaciones.append(ubicaciones[i])
            self.llave_ubicacion.append(llave_de_entrada[i])
            anterior = i
        self.inicio_ubic: list[int] = [0] * self.cantidad_llaves   # tramo vacío ⇒ «sin ubicación»
        self.fin_ubic: list[int] = [0] * self.cantidad_llaves
        self.llaves_en_sala: list[list[int]] = [[] for _ in range(self.cantidad_salas)]
        for p in range(len(self.ubicaciones)):
            k = self.llave_ubicacion[p]
            if p == 0 or self.llave_ubicacion[p - 1] != k:
                self.inicio_ubic[k] = p
            self.fin_ubic[k] = p + 1
            sala = self.ubicaciones[p].sala
            if 0 <= sala < self.cantidad_salas:
                self.llaves_en_sala[sala].append(k)

    def _marcar_caras_de_salida(self) -> None:
        """
        FR-304: la cara c lleva a sala_salida, está cerrada y SU PROPIA llave (ya combinada) es llave_salida: la cara
        de la sala desde la que se entra. hay_puerta_de_salida falso ⇒ motivo de FR-322.
        """
        self.es_cara_de_salida: list[bool] = [False] * len(self.tipo_cara)
        self.hay_puerta_de_salida: bool = False
        for c in range(len(self.tipo_cara)):
            if (self.tipo_cara[c] == CERRADA_CON_LLAVE and self.destino[c] == self.sala_salida
                    and self.llave_cara[c] == self.llave_salida):
                self.es_cara_de_salida[c] = True
                self.hay_puerta_de_salida = True
