"""
BenchResolubilidad (Integrante 2, feature 003): mediciones de --bench de la verificación de resolubilidad (research
R7; NFR-301 a NFR-304, SC-306, SC-307). Vive en Lógica porque mide Lógica, como Logic/BenchRutas.py, y reutiliza de
Logic/BenchLogica.py SOLO el cronómetro (_cronometrar, _mejor_y_mediana) y SEMILLA, sin modificarlo (dependencia de
la 001: el integrante 1 avisa antes de cambiarles el nombre o la firma). Llama directamente a VerificadorResolubilidad:
no inicia partidas, no crea partida.log ni pide datos (FR-301). La fila de la cripta del paquete la agrega
Service/ServicioBench.py, porque leer el paquete es de Datos y Lógica no importa Data ni Service.

    B1  verificación completa, resoluble                       cuadrículas 10×10, 10×100 y 10×1 000
    B2  repetir el recorrido completo en cada oleada (descartada) las mismas (en la mayor, 1 repetición)
    B3  verificación completa, no resoluble (ciclo y cadena)    las mismas
    B4  desglose a 1 000 salas: preparación, recorrido, frontera y ciclos, armado del reporte
    B5  índice de llaves: ordenar y compactar frente a la búsqueda lineal de ids (descartada; en la mayor, 1 repetición)
    B6  frontera agrupada por llave frente a una sola lista (descartada; peines de 100, 1 000 y 3 000 dientes; en el
        mayor, 1 repetición)
La nota de cada fila dice el factor de crecimiento de la mediana respecto del tamaño anterior (SC-307 sin cuentas).

Las variantes descartadas (verificar_ingenua, indice_lineal, RecorridoListaUnica) viven SOLO aquí, como
_AgendaOrdenada en BenchLogica, y reutilizan la preparación de GrafoLlaves: se compara solo la parte que cambia.
Nada de lo prohibido por el Principio II (tasks.md, «Reglas»), también en el bench: los índices son arreglos y se
ordena con Estructuras/Ordenador.py.

cripta_en_cuadricula(filas, columnas, semilla, resoluble), determinista por semilla (random.Random):
  - filas × columnas salas; la sala (fila, columna) tiene id fila*columnas + columna + 1; sala_inicial es (0, 0);
  - salidas abiertas entre vecinas de la misma columna;
  - entre la columna c y la c + 1, puertas cerradas que piden la llave c (llaves encadenadas; una llave abre varias);
  - la llave c está en una fila de la columna c elegida por la semilla; el orden de la lista de ubicaciones también
    se mezcla con la semilla (el resultado no debe depender de él, FR-306);
  - sala_salida es (0, última columna); su única entrada es la puerta desde (1, última columna), que pide
    llave_salida, ubicada en la última columna (en una fila ≥ 1). Por eso se exigen filas ≥ 2;
  - llaves: columnas − 1 de las fronteras más llave_salida;
  - variante no resoluble: se mueve SOLO la llave de la columna m = (columnas − 1) // 2 a la columna m + 1, detrás de
    las puertas que la piden: un ciclo de un paso (m → m) y una cadena de unas K/2 dependientes de m.

cripta_en_peine(dientes, semilla), determinista por semilla (B6; ahí la frontera es grande desde el principio):
  - un pasillo de 'dientes' salas unidas por salidas abiertas (ids 1..dientes; sala_inicial es la 1);
  - de la sala i del pasillo sale al sur una puerta a su diente (id dientes + i + 1) que pide la llave i;
  - la llave 0 está en la sala inicial y la i + 1 en el diente i; llave_salida, en el último diente;
  - sala_salida (id 2·dientes + 1) está al sur del último diente, detrás de una puerta que pide llave_salida;
  - el orden de la lista de ubicaciones se mezcla con la semilla. Salas: 2·dientes + 1; llaves: dientes + 1.
Sin datos de criptas publicadas (Principio VI). Lógica: no importa Data ni Service.
"""
import random

from DTO.CriptaDTO import CriptaDTO
from DTO.Direcciones import E, N, O, S
from DTO.ReporteResolubilidadDTO import NO_RESOLUBLE, ReporteResolubilidadDTO
from DTO.ResultadoBenchDTO import ResultadoBenchDTO
from DTO.SalaDTO import SalaDTO, SalidaDTO
from DTO.UbicacionLlaveDTO import UbicacionLlaveDTO
from Estructuras.Cola import Cola
from Estructuras.Ordenador import Ordenador
from Logic.BenchLogica import SEMILLA, _cronometrar, _mejor_y_mediana
from Logic.CiclosLlaves import CiclosLlaves
from Logic.GrafoLlaves import (_MENCION_CARA, _MENCION_UBICACION, ABIERTA, CERRADA_CON_LLAVE, SIN_SALIDA,
                               GrafoLlaves)
from Logic.RecorridoLlaves import OBTENIDA, VISTA, SIN_VER, RecorridoLlaves
from Logic.VerificadorResolubilidad import _ciclos, _no_obtenibles, _puerta, verificar

LLAVE_SALIDA = "llave_salida"
SUBSISTEMA = "resolubilidad"

CUADRICULAS = ((10, 10), (10, 100), (10, 1000))   # 100, 1 000 y 10 000 salas; 10, 100 y 1 000 llaves (R7)
DESGLOSE = (10, 100)                              # B4: 1 000 salas (NFR-301, SC-306)
DIENTES = (100, 1000, 3000)                       # B6: unas 200, 2 000 y 6 000 salas
REPETICIONES = 7


def _id_llave(columna: int) -> str:
    """Id de la llave de la frontera columna → columna + 1. Con ceros a la izquierda: el orden de id es el de columna."""
    return f"llave_{columna:05d}"


def cripta_en_cuadricula(filas: int, columnas: int, semilla: int,
                         resoluble: bool) -> tuple[CriptaDTO, list[SalaDTO], list[UbicacionLlaveDTO]]:
    """Cripta sintética en cuadrícula con llaves encadenadas (research R7). Lanza ValueError si filas < 2."""
    if filas < 2:
        raise ValueError(f"la cuadrícula necesita al menos 2 filas (se pidieron {filas})")
    if columnas < 2:
        raise ValueError(f"la cuadrícula necesita al menos 2 columnas (se pidieron {columnas})")
    ultima = columnas - 1

    def id_sala(fila: int, columna: int) -> int:
        return fila * columnas + columna + 1

    salas: list[SalaDTO] = []
    for fila in range(filas):
        for columna in range(columnas):
            salidas: list[SalidaDTO | None] = [None, None, None, None]
            if fila > 0:
                if columna == ultima and fila == 1:      # la entrada a sala_salida: pide llave_salida
                    salidas[N] = SalidaDTO(id_sala(0, columna), True, LLAVE_SALIDA)
                else:
                    salidas[N] = SalidaDTO(id_sala(fila - 1, columna))
            if fila < filas - 1:
                if columna == ultima and fila == 0:      # la vuelta desde sala_salida pide lo mismo
                    salidas[S] = SalidaDTO(id_sala(1, columna), True, LLAVE_SALIDA)
                else:
                    salidas[S] = SalidaDTO(id_sala(fila + 1, columna))
            entra_a_salida = fila == 0 and columna + 1 == ultima
            sale_de_salida = fila == 0 and columna == ultima
            if columna < ultima and not entra_a_salida:
                salidas[E] = SalidaDTO(id_sala(fila, columna + 1), True, _id_llave(columna))
            if columna > 0 and not sale_de_salida:
                salidas[O] = SalidaDTO(id_sala(fila, columna - 1), True, _id_llave(columna - 1))
            salas.append(SalaDTO(id_sala(fila, columna), f"Sala {id_sala(fila, columna)}", salidas, "bench"))

    generador = random.Random(semilla)
    medio = (columnas - 1) // 2
    ubicaciones: list[UbicacionLlaveDTO] = []
    for columna in range(ultima):
        fila = generador.randrange(filas)
        destino = columna + 1 if (not resoluble and columna == medio) else columna
        if destino == ultima and fila == 0:
            fila = 1                                     # sala_salida no guarda llaves
        ubicaciones.append(UbicacionLlaveDTO(_id_llave(columna), id_sala(fila, destino)))
    ubicaciones.append(UbicacionLlaveDTO(LLAVE_SALIDA, id_sala(generador.randrange(1, filas), ultima)))
    generador.shuffle(ubicaciones)

    cripta = CriptaDTO(id="bench", version="bench", salas_total=filas * columnas, paginas=1,
                       salas_por_pagina=filas * columnas, sala_inicial=id_sala(0, 0), sala_salida=id_sala(0, ultima),
                       llave_salida=LLAVE_SALIDA, presupuesto_solicitudes=1, inventario_max=10, jugador_vida_max=30,
                       jugador_ataque=6, jugador_defensa=2, jugador_velocidad=100)
    return cripta, salas, ubicaciones


def cripta_en_peine(dientes: int,
                    semilla: int) -> tuple[CriptaDTO, list[SalaDTO], list[UbicacionLlaveDTO]]:
    """Cripta sintética en peine (research R7, B6): la frontera empieza con 'dientes' puertas. ValueError si dientes < 1."""
    if dientes < 1:
        raise ValueError(f"el peine necesita al menos 1 diente (se pidieron {dientes})")
    ultimo = dientes - 1
    sala_salida = 2 * dientes + 1

    def pasillo(i: int) -> int:
        return i + 1

    def diente(i: int) -> int:
        return dientes + i + 1

    salas: list[SalaDTO] = []
    for i in range(dientes):                                   # el pasillo
        salidas: list[SalidaDTO | None] = [None, None, None, None]
        if i > 0:
            salidas[O] = SalidaDTO(pasillo(i - 1))
        if i < ultimo:
            salidas[E] = SalidaDTO(pasillo(i + 1))
        salidas[S] = SalidaDTO(diente(i), True, _id_llave(i))
        salas.append(SalaDTO(pasillo(i), f"Sala {pasillo(i)}", salidas, "bench"))
    for i in range(dientes):                                   # los dientes
        salidas = [None, None, None, None]
        salidas[N] = SalidaDTO(pasillo(i), True, _id_llave(i))
        if i == ultimo:
            salidas[S] = SalidaDTO(sala_salida, True, LLAVE_SALIDA)
        salas.append(SalaDTO(diente(i), f"Sala {diente(i)}", salidas, "bench"))
    salidas = [None, None, None, None]
    salidas[N] = SalidaDTO(diente(ultimo), True, LLAVE_SALIDA)
    salas.append(SalaDTO(sala_salida, f"Sala {sala_salida}", salidas, "bench"))

    ubicaciones = [UbicacionLlaveDTO(_id_llave(0), pasillo(0))]
    for i in range(ultimo):
        ubicaciones.append(UbicacionLlaveDTO(_id_llave(i + 1), diente(i)))
    ubicaciones.append(UbicacionLlaveDTO(LLAVE_SALIDA, diente(ultimo)))
    random.Random(semilla).shuffle(ubicaciones)

    cantidad = 2 * dientes + 1
    cripta = CriptaDTO(id="bench", version="bench", salas_total=cantidad, paginas=1, salas_por_pagina=cantidad,
                       sala_inicial=pasillo(0), sala_salida=sala_salida, llave_salida=LLAVE_SALIDA,
                       presupuesto_solicitudes=1, inventario_max=10, jugador_vida_max=30, jugador_ataque=6,
                       jugador_defensa=2, jugador_velocidad=100)
    return cripta, salas, ubicaciones


# ====================================================================== B2: repetir el recorrido (descartada, R4)
def verificar_ingenua(cripta: CriptaDTO, salas: list[SalaDTO],
                      ubicaciones: list[UbicacionLlaveDTO]) -> tuple[bool, list[str]]:
    """
    La alternativa ingenua de §5.4 (descartada; vive solo en el bench): la misma preparación de GrafoLlaves y, en cada
    oleada, un recorrido COMPLETO desde sala_inicial con las llaves obtenidas hasta entonces; las llaves nuevas se
    agregan ordenadas por índice (= por id, R5) y se repite hasta que no aparece ninguna. Misma definición de oleada
    que RecorridoLlaves, así que da el mismo orden. Devuelve (resoluble según FR-304, orden de ids).
    Con llaves encadenadas hace K + 1 recorridos: O(K · (S + E + U)).
    """
    grafo = GrafoLlaves(cripta, salas, ubicaciones)
    obtenida = [False] * grafo.cantidad_llaves
    orden: list[int] = []
    while True:
        alcanzable = [False] * grafo.cantidad_salas
        vista = [False] * grafo.cantidad_llaves
        nuevas: list[int] = []
        cola = Cola()
        inicio = grafo.sala_inicial
        if 0 <= inicio < grafo.cantidad_salas and grafo.existe[inicio]:
            alcanzable[inicio] = True
            cola.encolar(inicio)
        while not cola.esta_vacia():
            u = cola.desencolar()
            for k in grafo.llaves_en_sala[u]:
                if not obtenida[k] and not vista[k]:
                    vista[k] = True
                    nuevas.append(k)
            for d in range(4):
                c = u * 4 + d
                tipo = grafo.tipo_cara[c]
                if tipo == ABIERTA or (tipo == CERRADA_CON_LLAVE and obtenida[grafo.llave_cara[c]]):
                    destino = grafo.destino[c]
                    if not alcanzable[destino]:
                        alcanzable[destino] = True
                        cola.encolar(destino)
        if len(nuevas) == 0:
            break
        nuevas = Ordenador.ordenar(nuevas, Ordenador.comparar)
        for k in nuevas:
            obtenida[k] = True
            orden.append(k)
    resoluble = False
    if grafo.hay_puerta_de_salida and obtenida[grafo.llave_salida]:
        for c in range(len(grafo.tipo_cara)):
            if grafo.es_cara_de_salida[c] and alcanzable[c // 4]:
                resoluble = True
                break
    return resoluble, [grafo.ids[k] for k in orden]


# ====================================================================== B5: índice de llaves (R3)
class _GrafoQueGuardaMenciones(GrafoLlaves):
    """GrafoLlaves que guarda una copia de las menciones en el orden de entrada, para medir solo el índice (B5)."""

    def _indexar_llaves(self, menciones: list[tuple[str, int, int]], cantidad_ubicaciones: int) -> list[int]:
        self.menciones: list[tuple[str, int, int]] = list(menciones)
        return super()._indexar_llaves(menciones, cantidad_ubicaciones)


def menciones_de(cripta: CriptaDTO, salas: list[SalaDTO],
                 ubicaciones: list[UbicacionLlaveDTO]) -> tuple[GrafoLlaves, list[tuple[str, int, int]]]:
    """El GrafoLlaves preparado y sus menciones (id, tipo, posición) en el orden en que las arma, sin ordenar."""
    grafo = _GrafoQueGuardaMenciones(cripta, salas, ubicaciones)
    return grafo, grafo.menciones


def indice_ordenando(grafo: GrafoLlaves, menciones: list[tuple[str, int, int]],
                     cantidad_ubicaciones: int) -> tuple[list[str], list[int], list[int], int]:
    """
    La decisión (R3), con el código del juego: GrafoLlaves._indexar_llaves (ordenar las menciones y compactar).
    Devuelve (ids, llave_cara, llave de cada ubicación de entrada, llave_salida), para compararlo con indice_lineal.
    """
    llave_de_entrada = grafo._indexar_llaves(menciones, cantidad_ubicaciones)
    return list(grafo.ids), list(grafo.llave_cara), llave_de_entrada, grafo.llave_salida


def indice_lineal(menciones: list[tuple[str, int, int]], cantidad_caras: int,
                  cantidad_ubicaciones: int) -> tuple[list[str], list[int], list[int], int]:
    """
    La alternativa descartada de R3 (vive solo en el bench): cada mención busca su id entre los ya vistos, de punta a
    punta; al final se ordenan los K ids y se reescriben los índices, para dar el MISMO índice que la decisión
    (índices en orden de id). O(M·K) la búsqueda + O(K log K + M) el final. Mismo resultado que indice_ordenando.
    """
    vistos: list[str] = []
    provisional = [0] * len(menciones)
    for j in range(len(menciones)):
        id_llave = menciones[j][0]
        i = 0
        while i < len(vistos) and vistos[i] != id_llave:
            i += 1
        if i == len(vistos):
            vistos.append(id_llave)
        provisional[j] = i
    orden = Ordenador.ordenar(list(range(len(vistos))), lambda a, b: Ordenador.comparar(vistos[a], vistos[b]))
    rango = [0] * len(vistos)
    ids: list[str] = []
    for r in range(len(orden)):
        rango[orden[r]] = r
        ids.append(vistos[orden[r]])
    llave_cara = [-1] * cantidad_caras
    llave_de_entrada = [-1] * cantidad_ubicaciones
    llave_salida = -1
    for j in range(len(menciones)):
        _, tipo, posicion = menciones[j]
        k = rango[provisional[j]]
        if tipo == _MENCION_CARA:
            llave_cara[posicion] = k
        elif tipo == _MENCION_UBICACION:
            llave_de_entrada[posicion] = k
        else:
            llave_salida = k
    return ids, llave_cara, llave_de_entrada, llave_salida


# ====================================================================== B6: frontera en una sola lista (R4)
class RecorridoListaUnica(RecorridoLlaves):
    """
    La alternativa descartada de R4 (vive solo en el bench): el mismo recorrido por oleadas, pero las caras cerradas
    con una llave no obtenida van a UNA sola lista, que se revisa entera al obtener cada llave (en vez de
    esperando[k]). O(S + E + K·F). Da el mismo orden, las mismas oleadas y la misma región que RecorridoLlaves.
    """

    def __init__(self, grafo: GrafoLlaves):
        super().__init__(grafo)
        self.lista_unica: list[int] = []

    def recorrer(self) -> None:
        """Como RecorridoLlaves.recorrer, salvo que cada llave nueva revisa toda la lista única."""
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
            nuevas = Ordenador.ordenar(nuevas, Ordenador.comparar)
            for k in nuevas:
                self.estado_llave[k] = OBTENIDA
                self.oleada_llave[k] = oleada
                self.orden.append(k)
            for k in nuevas:                         # cada llave revisa la lista entera
                quedan: list[int] = []
                for c in self.lista_unica:
                    if grafo.llave_cara[c] == k:
                        self._alcanzar(grafo.destino[c], cola)
                    else:
                        quedan.append(c)
                self.lista_unica = quedan
            oleada += 1

    def _visitar(self, u: int, cola: Cola, nuevas: list[int]) -> None:
        """Como RecorridoLlaves._visitar, pero la cara con llave no obtenida va a la lista única."""
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
                self.caras_de_salida.append(c)
            if tipo == ABIERTA:
                self._alcanzar(grafo.destino[c], cola)
            elif tipo == CERRADA_CON_LLAVE:
                k = grafo.llave_cara[c]
                if self.estado_llave[k] == OBTENIDA:
                    self._alcanzar(grafo.destino[c], cola)
                else:
                    self.lista_unica.append(c)
            else:
                self.sin_llave.append(c)


# ====================================================================== mediciones
def medir(cuadriculas=CUADRICULAS, desglose=DESGLOSE, dientes=DIENTES,
          repeticiones: int = REPETICIONES) -> list[ResultadoBenchDTO]:
    """B1 a B6 con los tamaños dados (por defecto, los de research R7). Las pruebas lo llaman con tamaños chicos."""
    return (medir_verificacion(cuadriculas, repeticiones) + medir_desglose(desglose, repeticiones)
            + medir_indice(cuadriculas, repeticiones) + medir_frontera(dientes, repeticiones))


def medir_verificacion(cuadriculas=CUADRICULAS, repeticiones: int = REPETICIONES) -> list[ResultadoBenchDTO]:
    """B1 (resoluble), B2 (repetir el recorrido, descartada; en la mayor, 1 repetición) y B3 (no resoluble)."""
    resueltas = [cripta_en_cuadricula(f, c, SEMILLA, True) for f, c in cuadriculas]
    no_resolubles = [cripta_en_cuadricula(f, c, SEMILLA, False) for f, c in cuadriculas]
    b1: list[tuple[int, list[float], str]] = []
    b2: list[tuple[int, list[float], str]] = []
    b3: list[tuple[int, list[float], str]] = []
    for i in range(len(cuadriculas)):
        f, c = cuadriculas[i]
        datos = resueltas[i]
        b1.append((f * c, _cronometrar(_llamada(verificar, datos), repeticiones), f"{f}×{c}, {c} llaves"))
        reps_b2 = 1 if i == len(cuadriculas) - 1 else repeticiones
        b2.append((f * c, _cronometrar(_llamada(verificar_ingenua, datos), reps_b2),
                   f"{f}×{c}, {c} llaves, un recorrido completo por oleada"))
        datos = no_resolubles[i]
        dependientes = c - (c - 1) // 2 - 1
        b3.append((f * c, _cronometrar(_llamada(verificar, datos), repeticiones),
                   f"{f}×{c}, {c} llaves, 1 ciclo de 1 llave y {dependientes} dependientes"))
    return (_filas("B1 verificación incremental, resoluble", b1)
            + _filas("B2 repetir el recorrido por oleada (descartada)", b2)
            + _filas("B3 verificación incremental, no resoluble", b3))


def medir_desglose(desglose=DESGLOSE, repeticiones: int = REPETICIONES) -> list[ResultadoBenchDTO]:
    """
    B4: dónde se va el tiempo de la verificación, en la cripta no resoluble de B3 (es la que pasa por todas las fases):
    preparación (GrafoLlaves, R3), recorrido (R4), frontera, fase hacia afuera y ciclos (R6) y armado del reporte (R5).
    Cada fase parte del estado que dejan las anteriores, que no se cronometran.
    """
    f, c = desglose
    cripta, salas, ubicaciones = cripta_en_cuadricula(f, c, SEMILLA, False)
    grafo = GrafoLlaves(cripta, salas, ubicaciones)

    def preparar() -> GrafoLlaves:
        return GrafoLlaves(cripta, salas, ubicaciones)

    def recorrido_nuevo() -> RecorridoLlaves:
        return RecorridoLlaves(grafo)

    def recorrido_hecho() -> RecorridoLlaves:
        recorrido = RecorridoLlaves(grafo)
        recorrido.recorrer()
        return recorrido

    def frontera_y_ciclos(recorrido: RecorridoLlaves) -> CiclosLlaves:
        recorrido.calcular_frontera()
        recorrido.fase_hacia_afuera()
        return CiclosLlaves(grafo, recorrido)

    def ciclos_hechos() -> tuple[RecorridoLlaves, CiclosLlaves]:
        recorrido = recorrido_hecho()
        return recorrido, frontera_y_ciclos(recorrido)

    def armar(estado: tuple[RecorridoLlaves, CiclosLlaves]) -> ReporteResolubilidadDTO:
        recorrido, ciclos = estado
        return ReporteResolubilidadDTO(cripta.id, NO_RESOLUBLE, cripta.version, cripta.llave_salida,
                                       llaves_no_obtenibles=_no_obtenibles(grafo, recorrido),
                                       frontera=[_puerta(grafo, x) for x in recorrido.frontera],
                                       ciclos=_ciclos(grafo, ciclos))

    fases = [("preparación (R3)", _cronometrar(preparar, repeticiones)),
             ("recorrido (R4)", _cronometrar(lambda r: r.recorrer(), repeticiones, recorrido_nuevo)),
             ("frontera, fase hacia afuera y ciclos (R6)", _cronometrar(frontera_y_ciclos, repeticiones,
                                                                        recorrido_hecho)),
             ("armado del reporte (R5)", _cronometrar(armar, repeticiones, ciclos_hechos))]
    medianas = [_mejor_y_mediana(tiempos) for _, tiempos in fases]
    total = 0.0
    for _, mediana in medianas:
        total += mediana
    resultados: list[ResultadoBenchDTO] = []
    for i in range(len(fases)):
        mejor, mediana = medianas[i]
        parte = 100 * mediana / total if total > 0 else 0.0
        nota = (f"cripta no resoluble de B3, {f}×{c}, {c} llaves; {parte:.0f} % de la suma de las medianas "
                f"({total:.3f} ms); {repeticiones} repeticiones")
        resultados.append(ResultadoBenchDTO(SUBSISTEMA, f"B4 desglose: {fases[i][0]}", f * c, mejor, mediana, nota))
    return resultados


def medir_indice(cuadriculas=CUADRICULAS, repeticiones: int = REPETICIONES) -> list[ResultadoBenchDTO]:
    """B5: ordenar y compactar (GrafoLlaves) frente a la búsqueda lineal de ids (descartada; en la mayor, 1 repetición)."""
    ordenando: list[tuple[int, list[float], str]] = []
    lineal: list[tuple[int, list[float], str]] = []
    for i in range(len(cuadriculas)):
        f, c = cuadriculas[i]
        cripta, salas, ubicaciones = cripta_en_cuadricula(f, c, SEMILLA, True)
        grafo, menciones = menciones_de(cripta, salas, ubicaciones)
        detalle = f"{f}×{c}, {len(menciones)} menciones, {grafo.cantidad_llaves} llaves"
        u = len(ubicaciones)
        caras = len(grafo.tipo_cara)

        def copia(menciones=menciones) -> list[tuple[str, int, int]]:
            return list(menciones)               # cada repetición, las menciones en el orden de entrada

        def con_orden(m, grafo=grafo, u=u) -> None:
            grafo._indexar_llaves(m, u)

        def con_lineal(m, caras=caras, u=u) -> None:
            indice_lineal(m, caras, u)

        ordenando.append((f * c, _cronometrar(con_orden, repeticiones, copia), detalle))
        reps = 1 if i == len(cuadriculas) - 1 else repeticiones
        lineal.append((f * c, _cronometrar(con_lineal, reps, copia), detalle))
    return _intercalar(_filas("B5 índice de llaves: ordenar y compactar", ordenando),
                       _filas("B5 índice de llaves: búsqueda lineal (descartada)", lineal))


def medir_frontera(dientes=DIENTES, repeticiones: int = REPETICIONES) -> list[ResultadoBenchDTO]:
    """B6: frontera agrupada por llave frente a una sola lista (descartada; en el peine mayor, 1 repetición)."""
    agrupada: list[tuple[int, list[float], str]] = []
    unica: list[tuple[int, list[float], str]] = []
    for i in range(len(dientes)):
        d = dientes[i]
        cripta, salas, ubicaciones = cripta_en_peine(d, SEMILLA)
        grafo = GrafoLlaves(cripta, salas, ubicaciones)
        detalle = f"peine de {d} dientes, {d + 1} llaves, frontera inicial de {d} puertas"

        def con_agrupada(grafo=grafo) -> RecorridoLlaves:
            return RecorridoLlaves(grafo)

        def con_unica(grafo=grafo) -> RecorridoLlaves:
            return RecorridoListaUnica(grafo)

        agrupada.append((2 * d + 1, _cronometrar(_recorrer, repeticiones, con_agrupada), detalle))
        reps = 1 if i == len(dientes) - 1 else repeticiones
        unica.append((2 * d + 1, _cronometrar(_recorrer, reps, con_unica), detalle))
    return _intercalar(_filas("B6 frontera agrupada por llave", agrupada),
                       _filas("B6 frontera en una sola lista (descartada)", unica))


# ------------------------------------------------------------ auxiliares
def _llamada(funcion, datos):
    """Una función sin argumentos que llama a funcion(*datos)."""
    cripta, salas, ubicaciones = datos
    return lambda: funcion(cripta, salas, ubicaciones)


def _recorrer(recorrido: RecorridoLlaves) -> None:
    recorrido.recorrer()


def _filas(caso: str, medidas: list[tuple[int, list[float], str]]) -> list[ResultadoBenchDTO]:
    """
    Una fila por tamaño. La nota dice el factor de crecimiento de la mediana respecto del tamaño anterior y cuántas
    repeticiones se hicieron («1 repetición» en las alternativas cuadráticas del tamaño mayor).
    """
    resultados: list[ResultadoBenchDTO] = []
    anterior_tamano = 0
    anterior_mediana = 0.0
    for i in range(len(medidas)):
        tamano, tiempos, detalle = medidas[i]
        mejor, mediana = _mejor_y_mediana(tiempos)
        partes = [detalle]
        if i == 0:
            partes.append("base del crecimiento")
        elif anterior_mediana > 0:
            partes.append(f"×{mediana / anterior_mediana:.1f} respecto de {anterior_tamano} salas")
        else:
            partes.append(f"sin factor respecto de {anterior_tamano} salas (mediana anterior 0)")
        partes.append("1 repetición" if len(tiempos) == 1 else f"{len(tiempos)} repeticiones")
        resultados.append(ResultadoBenchDTO(SUBSISTEMA, caso, tamano, mejor, mediana, "; ".join(partes)))
        anterior_tamano, anterior_mediana = tamano, mediana
    return resultados


def _intercalar(a: list[ResultadoBenchDTO], b: list[ResultadoBenchDTO]) -> list[ResultadoBenchDTO]:
    """Las filas de la decisión y de la alternativa, tamaño por tamaño (a[0], b[0], a[1], b[1], ...)."""
    resultados: list[ResultadoBenchDTO] = []
    for i in range(len(a)):
        resultados.append(a[i])
        resultados.append(b[i])
    return resultados


if __name__ == "__main__":
    for r in medir():
        print(f"{r.subsistema} | {r.caso} | {r.tamano} | {r.mejor_ms:.3f} | {r.mediana_ms:.3f} | {r.nota}")
