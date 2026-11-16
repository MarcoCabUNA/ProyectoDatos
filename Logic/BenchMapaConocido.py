"""
BenchMapaConocido (Lógica, integrante 2, feature 002, T052 a T054): mediciones de --bench del mapa conocido, B1 a B11
(research R7; NFR-201 a NFR-205, SC-203, SC-204, SC-206, SC-207; Principio VIII).

Cargas SINTÉTICAS y deterministas (Principios VI y VIII): cuadrículas de lado 10, 32 y 100 (100, 1 024 y 10 000 salas)
con _cuadricula_con_costos de Logic/BenchRutas.py (costos de random.Random(SEMILLA) entre 1 y 300) y estados del mapa
preparados por semilla con MapaConocido.restaurar (no se cronometra). Mismo cronómetro y formato que
Logic/BenchLogica.py, del que se reutilizan _cronometrar, _mejor_y_mediana y SEMILLA sin modificarlo; de
Logic/BenchRutas.py, _cuadricula_con_costos, _motor_con_cazadores, _centro y _peor, también sin modificarlo.

  B1   consulta de estado de sala (estado_sala)                      NFR-201, SC-203
  B2   consulta de cara recordada (estado_cara)                      NFR-201, SC-203
  B3   alternativa descartada de R1: listas de ids recorridas        Principio VIII
  B4   entrada con antorcha que revela lo mismo con mapas mayores    NFR-202, SC-204
  B5   alternativa descartada de R2: recalcular «avistadas»          Principio VIII
  B6   entrar con antorcha, cerrar el intervalo y deshacer           NFR-203, SC-207
  B7   alternativa descartada de R3: copiar el mapa y restaurarlo    Principio VIII
  B8   ciclo de eventos con la antorcha y 30 cazadores (1 024 salas) NFR-205, SC-206
  B9   a_guardado + restaurar (copia para un punto de control)       NFR-203
  B10  a_dto y buscar_exploradas con el mapa completo                R5 (b) y (c)
  B11  armar GrafoMapaConocido y un paso_desde_cero                  R5 (a); referencia para NFR-250

Sin dict, set ni sorted (constitución v1.2.0). Corre sin vista (Principio V). medir() junta B1 a B11; las pruebas
llaman a medir() y a las funciones de preparación con tamaños chicos.
"""
import random

from DTO.Direcciones import E, N, O, S
from DTO.MapaConocidoDTO import (ABIERTA, AVISTADA, CERRADA, DESCONOCIDA, EXPLORADA, SIN_OBSERVAR,
                                 MapaConocidoGuardadoDTO)
from DTO.ResultadoBenchDTO import ResultadoBenchDTO
from Logic.BenchLogica import SEMILLA, _cronometrar, _mejor_y_mediana
from Logic.BenchRutas import _centro, _cuadricula_con_costos, _motor_con_cazadores, _peor
from Logic.BusquedaCostoMinimo import paso_desde_cero
from Logic.Efectos import Antorcha
from Logic.GrafoMapaConocido import GrafoMapaConocido
from Logic.HistorialRetroceso import HistorialRetroceso
from Logic.MapaConocido import MapaConocido
from Logic.Mazmorra import Mazmorra

SUBSISTEMA = "mapa conocido"
LIMITE_CICLO_MS = 20         # NFR-205, SC-206 (el mismo límite que §5.2)
LIMITE_PASO_MS = 5           # NFR-250 del integrante 3: B11 con 1 024 salas solo dice si queda por debajo
LIMITE_UNA_REPETICION_MS = 500   # una alternativa que tarda más que esto se mide con 1 repetición
OPUESTA = [S, N, O, E]


def medir(lados=(10, 32, 100), repeticiones: int = 7, consultas: int = 100000, consultas_lista: int = 1000,
          lado_ciclo: int = 32, cazadores: int = 30, otros: int = 20, ciclos: int = 200,
          ciclos_comprobados: int = 30) -> list[ResultadoBenchDTO]:
    """B1 a B11 con los tamaños por defecto (las pruebas pasan tamaños chicos)."""
    mazmorras = []
    for lado in lados:
        mazmorras.append(armar_cuadricula(lado))
    cortas = 6 * repeticiones + 9           # B4 y B6 cronometran una sola entrada: más repeticiones, misma mediana
    return (medir_consultas(lados, mazmorras, repeticiones, consultas, consultas_lista)
            + medir_entrada(lados, mazmorras, cortas, repeticiones)
            + medir_ciclo_con_antorcha(lado_ciclo, cazadores, otros, ciclos, ciclos_comprobados)
            + medir_copias_y_vista(lados, mazmorras, repeticiones)
            + medir_grafo(lados, mazmorras, repeticiones))


# ====================================================================== cargas sintéticas
class _JugadorBench:
    """Lo único que MapaConocido lee del jugador: la sala en la que está."""

    def __init__(self, sala: int) -> None:
        self.Sala_Actual = sala


def armar_cuadricula(lado: int) -> Mazmorra:
    """Mazmorra con el esqueleto de una cuadrícula de lado × lado salas (ids 1..lado²) con costos por semilla."""
    salas = _cuadricula_con_costos(lado, random.Random(SEMILLA))
    mazmorra = Mazmorra(lado * lado, "itm_llave")
    mazmorra.cargar_esqueleto(salas)
    return mazmorra


def _mapa_con(mazmorra: Mazmorra, estado: list[int], caras: list[int], sala_jugador: int,
              historial: HistorialRetroceso | None):
    """(MapaConocido, jugador) con los arreglos dados, puestos con restaurar (no registra en el historial)."""
    jugador = _JugadorBench(sala_jugador)
    mapa = MapaConocido(mazmorra, jugador, historial)
    mapa.restaurar(MapaConocidoGuardadoDTO(estado, caras))
    return mapa, jugador


def mapa_por_tercios(mazmorra: Mazmorra) -> MapaConocido:
    """
    Mapa para B1 a B3: las salas, barajadas con la semilla, un tercio exploradas, un tercio avistadas y el resto
    desconocidas; cada cara de una salida que existe, sin observar, abierta o cerrada al azar (con la semilla).
    """
    total = len(mazmorra.salas)
    azar = random.Random(SEMILLA + total)
    ids = list(range(1, total))
    azar.shuffle(ids)
    tercio = len(ids) // 3
    estado = [DESCONOCIDA] * total
    for i in range(len(ids)):
        if i < tercio:
            estado[ids[i]] = EXPLORADA
        elif i < 2 * tercio:
            estado[ids[i]] = AVISTADA
    caras = [SIN_OBSERVAR] * (4 * total)
    for sala in range(1, total):
        for d in range(4):
            if mazmorra.salas[sala].salidas[d] is not None:
                caras[sala * 4 + d] = azar.randrange(3)
    return _mapa_con(mazmorra, estado, caras, 1, None)[0]


def mapa_completo(mazmorra: Mazmorra) -> MapaConocido:
    """Mapa para B9 a B11: todas las salas exploradas y todas las caras recordadas como son (abiertas)."""
    total = len(mazmorra.salas)
    estado = [DESCONOCIDA] * total
    caras = [SIN_OBSERVAR] * (4 * total)
    for sala in range(1, total):
        estado[sala] = EXPLORADA
        for d in range(4):
            s = mazmorra.salas[sala].salidas[d]
            if s is not None:
                caras[sala * 4 + d] = CERRADA if s.cerrada else ABIERTA
    return _mapa_con(mazmorra, estado, caras, 1, None)[0]


def mapa_para_antorcha(mazmorra: Mazmorra, lado: int, con_historial: bool = True):
    """
    Mapa para B4 a B7: todo explorado salvo la sala del centro (desconocida) y sus 4 vecinas (avistadas), sin
    observar sus caras. Entrar al centro con la antorcha revela siempre lo mismo (5 salas y 8 caras), sea cual sea el
    tamaño. Devuelve (mapa, historial o None, jugador, centro).
    """
    total = len(mazmorra.salas)
    centro = _centro(lado)
    estado = [DESCONOCIDA] * total
    for sala in range(1, total):
        estado[sala] = EXPLORADA
    estado[centro] = DESCONOCIDA
    vecinas = []
    for d in range(4):
        s = mazmorra.salas[centro].salidas[d]
        if s is not None:
            vecinas.append(s.destino)
            estado[s.destino] = AVISTADA
    caras = [SIN_OBSERVAR] * (4 * total)
    for sala in range(1, total):
        if estado[sala] != EXPLORADA:
            continue
        for d in range(4):
            if mazmorra.salas[sala].salidas[d] is not None:
                caras[sala * 4 + d] = ABIERTA
    historial = HistorialRetroceso() if con_historial else None
    mapa, jugador = _mapa_con(mazmorra, estado, caras, vecinas[0], historial)
    return mapa, historial, jugador, centro


def listas_de_ids(mapa: MapaConocido) -> tuple[list[int], list[int]]:
    """B3: los ids explorados y los avistados, en orden de id (la representación descartada de R1)."""
    exploradas, avistadas = [], []
    for sala in range(len(mapa.estado)):
        if mapa.estado[sala] == EXPLORADA:
            exploradas.append(sala)
        elif mapa.estado[sala] == AVISTADA:
            avistadas.append(sala)
    return exploradas, avistadas


def estado_por_lista(exploradas: list[int], avistadas: list[int], sala: int) -> int:
    """B3, alternativa descartada de R1: el estado de una sala recorriendo las listas de ids. O(X)."""
    for explorada in exploradas:
        if explorada == sala:
            return EXPLORADA
    for avistada in avistadas:
        if avistada == sala:
            return AVISTADA
    return DESCONOCIDA


def entrar_con_antorcha(mapa: MapaConocido, jugador: _JugadorBench, sala: int) -> None:
    """Lo que hace el motor al entrar: mueve al jugador y llama a mapa.entrar con la antorcha encendida."""
    jugador.Sala_Actual = sala
    mapa.entrar(sala, True)


def recalcular_avistadas(mapa: MapaConocido) -> list[int]:
    """
    B5, alternativa descartada de R2: el estado de todas las salas recalculado desde las exploradas, recorriendo todo
    el mapa (avistada = no explorada y destino de una salida de una explorada). O(S + X · g).
    """
    salas = mapa.mazmorra.salas
    nuevo = [DESCONOCIDA] * len(mapa.estado)
    for sala in range(len(mapa.estado)):
        if mapa.estado[sala] == EXPLORADA:
            nuevo[sala] = EXPLORADA
    for sala in range(len(mapa.estado)):
        if nuevo[sala] != EXPLORADA:
            continue
        for d in range(4):
            s = salas[sala].salidas[d]
            if s is not None and nuevo[s.destino] == DESCONOCIDA:
                nuevo[s.destino] = AVISTADA
    return nuevo


def entrar_cerrar_y_deshacer(mapa: MapaConocido, historial: HistorialRetroceso, jugador: _JugadorBench,
                             sala: int) -> None:
    """B6: entrar con la antorcha, cerrar el intervalo y deshacerlo con el pergamino (NFR-203)."""
    entrar_con_antorcha(mapa, jugador, sala)
    historial.cerrar_intervalo()
    historial.deshacer()


def copiar_entrar_y_restaurar(mapa: MapaConocido, jugador: _JugadorBench, sala: int) -> None:
    """B7, alternativa descartada de R3: copiar el mapa entero antes de la acción y restaurarlo después. O(S)."""
    copia = mapa.a_guardado()
    entrar_con_antorcha(mapa, jugador, sala)
    mapa.restaurar(copia)


def paso_b11(mapa: MapaConocido, lado: int) -> tuple[int, int] | None:
    """B11: un GrafoMapaConocido nuevo y un paso_desde_cero desde la esquina 1 hacia la opuesta (lado²)."""
    return paso_desde_cero(GrafoMapaConocido(mapa), lado * lado, 1, None)


# ====================================================================== B1, B2, B3
def medir_consultas(lados, mazmorras, repeticiones: int, consultas: int,
                    consultas_lista: int) -> list[ResultadoBenchDTO]:
    """B1 y B2 (consultas O(1)) y B3 (la lista de ids recorrida), con un tercio de las salas en cada estado."""
    b1, b2, b3 = [], [], []
    por_consulta_b1, por_consulta_b2 = [], []
    anteriores = [None, None, None]
    for i in range(len(lados)):
        mazmorra = mazmorras[i]
        mapa = mapa_por_tercios(mazmorra)
        total = len(mazmorra.salas)
        n = total - 1
        azar = random.Random(SEMILLA + 1 + n)
        ids = [azar.randint(1, n) for _ in range(consultas)]
        direcciones = [azar.randrange(4) for _ in range(consultas)]
        estado_sala, estado_cara = mapa.estado_sala, mapa.estado_cara

        def salas_b1():
            for sala in ids:
                estado_sala(sala)

        def caras_b2():
            for j in range(consultas):
                estado_cara(ids[j], direcciones[j])

        for filas, por_consulta, funcion, k, caso in ((b1, por_consulta_b1, salas_b1, 0, "B1 estado de sala"),
                                                      (b2, por_consulta_b2, caras_b2, 1, "B2 cara recordada")):
            mejor, mediana = _mejor_y_mediana(_cronometrar(funcion, repeticiones))
            micro = 1000 * mediana / consultas
            por_consulta.append(micro)
            nota = f"{consultas} consultas, un tercio de las salas en cada estado; {micro:.4f} µs por consulta"
            nota += _factor(mediana, anteriores[k])
            if len(por_consulta) == len(lados) and len(lados) > 1:
                razon = por_consulta[-1] / por_consulta[0]
                nota += (f"; {n} contra {len(mazmorras[0].salas) - 1} salas: {razon:.2f} veces; SC-203 (< 2): "
                         f"{'cumple' if razon < 2 else 'NO cumple'}")
            anteriores[k] = mediana
            filas.append(ResultadoBenchDTO(SUBSISTEMA, f"{caso}: arreglo por id (elegida)", n, mejor, mediana, nota))

        exploradas, avistadas = listas_de_ids(mapa)
        ids_lista = ids[:consultas_lista]

        def por_lista():
            for sala in ids_lista:
                estado_por_lista(exploradas, avistadas, sala)

        tiempos, una = _medir_alternativa(por_lista, repeticiones)
        mejor, mediana = _mejor_y_mediana(tiempos)
        micro = 1000 * mediana / max(1, len(ids_lista))
        nota = (f"{len(ids_lista)} consultas sobre {len(exploradas)} exploradas y {len(avistadas)} avistadas; "
                f"{micro:.3f} µs por consulta, {micro / max(por_consulta_b1[-1], 1e-9):.0f} veces B1")
        nota += _factor(mediana, anteriores[2]) + una
        anteriores[2] = mediana
        b3.append(ResultadoBenchDTO(SUBSISTEMA, "B3 estado de sala: listas de ids recorridas (descartada, R1)", n,
                                    mejor, mediana, nota))
    return b1 + b2 + b3


# ====================================================================== B4, B5, B6, B7
def medir_entrada(lados, mazmorras, repeticiones_cortas: int, repeticiones: int) -> list[ResultadoBenchDTO]:
    """
    B4 a B7: entrar al centro con la antorcha revela siempre 5 salas y 8 caras, con el resto del mapa explorado. B4 y
    B5 reponen el estado fuera del cronómetro con el pergamino; B6 cronometra entrar, cerrar y deshacer; B7 copia el
    mapa entero y lo restaura (sin historial).
    """
    b4, b5, b6, b7 = [], [], [], []
    medianas = [[], [], [], []]
    for i in range(len(lados)):
        lado, mazmorra = lados[i], mazmorras[i]
        n = len(mazmorra.salas) - 1
        mapa, historial, jugador, centro = mapa_para_antorcha(mazmorra, lado)

        def reponer():
            historial.cerrar_intervalo()
            historial.deshacer()

        antes = (list(mapa.estado), list(mapa.caras))
        tiempos = _cronometrar(lambda _: entrar_con_antorcha(mapa, jugador, centro), repeticiones_cortas, reponer)
        reponer()
        if (mapa.estado, mapa.caras) != antes:
            raise AssertionError("B4: el pergamino no dejó el mapa como antes de la entrada")
        _fila(b4, medianas[0], tiempos, n, "B4 entrada con antorcha (elegida)",
              "revela 5 salas y 8 caras", "SC-204", lados)

        tiempos, una = _medir_alternativa(
            lambda _: (entrar_con_antorcha(mapa, jugador, centro), recalcular_avistadas(mapa)), repeticiones, reponer)
        reponer()
        _fila(b5, medianas[1], tiempos, n, "B5 entrada + recalcular avistadas (descartada, R2)",
              f"recorre las {n} salas después de entrar" + una, None, lados)

        tiempos = _cronometrar(lambda: entrar_cerrar_y_deshacer(mapa, historial, jugador, centro),
                               repeticiones_cortas)
        if (mapa.estado, mapa.caras) != antes:
            raise AssertionError("B6: deshacer no dejó el mapa como antes de la entrada")
        _fila(b6, medianas[2], tiempos, n, "B6 entrar, cerrar y deshacer (elegida)",
              "13 casillas registradas e invertidas", "SC-207", lados)

        sin_historial, _, jugador_b7, _ = mapa_para_antorcha(mazmorra, lado, con_historial=False)
        tiempos, una = _medir_alternativa(lambda: copiar_entrar_y_restaurar(sin_historial, jugador_b7, centro),
                                          repeticiones)
        _fila(b7, medianas[3], tiempos, n, "B7 copiar el mapa y restaurarlo (descartada, R3)",
              f"copia {5 * (n + 1)} casillas dos veces" + una, None, lados)
    return b4 + b5 + b6 + b7


def _fila(filas: list, medianas: list, tiempos: list[float], n: int, caso: str, texto: str, criterio: str | None,
          lados, por_sala: bool = False) -> None:
    """
    Agrega la fila con el factor respecto del tamaño anterior y, en el mayor, el criterio (mayor contra menor). Con
    'por_sala', la nota dice también el costo por sala, para leer si crece en forma lineal con S.
    """
    mejor, mediana = _mejor_y_mediana(tiempos)
    nota = f"{texto}; {1000 * mediana:.2f} µs (mediana)"
    if por_sala:
        nota += f", {1000000 * mediana / n:.1f} ns por sala"
    nota += _factor(mediana, medianas[-1] if medianas else None)
    medianas.append(mediana)
    if criterio is not None and len(medianas) == len(lados) and len(lados) > 1:
        razon = medianas[-1] / medianas[0]
        nota += f"; mayor contra menor: {razon:.2f} veces; {criterio} (< 2): {'cumple' if razon < 2 else 'NO cumple'}"
    filas.append(ResultadoBenchDTO(SUBSISTEMA, caso, n, mejor, mediana, nota))


# ====================================================================== B8
def _antorcha(motor) -> None:
    """Enciende la antorcha del jugador por toda la medición."""
    motor.efectos.aplicar(Antorcha(motor.jugador, 10 ** 9))


def _cambiar_puerta_del_jugador(motor, observadores: list) -> None:
    """
    Abre o cierra las dos caras de la puerta norte de la sala del jugador y avisa como la Mazmorra (con los destinos
    de las caras) a cada observador de la lista. En B8 la lista es [motor.mazmorra.observador_puertas], es decir, el
    RepartidorAvisosPuertas del motor (el camino real), nunca BenchRutas._cambiar_puerta.
    """
    sala = motor.jugador.Sala_Actual
    cara = motor.mazmorra.salida(sala, N)
    if cara is None:
        return
    vuelta = motor.mazmorra.salida(cara.destino, OPUESTA[N])
    cerrada = not cara.cerrada
    cara.cerrada = cerrada
    vuelta.cerrada = cerrada
    for observador in observadores:
        observador.puerta_cambio(cara.destino, vuelta.destino)


def _ciclo(motor, lado: int, con_puertas: bool, observadores: list) -> None:
    """Una decisión del jugador, que se mueve entre el centro y su vecina al este, y el avance del Motor."""
    if con_puertas:
        _cambiar_puerta_del_jugador(motor, observadores)
    motor.mover_jugador(E if motor.jugador.Sala_Actual == _centro(lado) else O)
    motor.avanzar_hasta_jugador()


def comprobar_contra_control(lado: int, cazadores: int, otros: int, ciclos: int,
                             con_puertas: bool) -> tuple[int, int]:
    """
    Sin cronometrar: juega 'ciclos' ciclos en dos motores iguales con la antorcha encendida. En el medido, el aviso de
    cada puerta va por motor.mazmorra.observador_puertas (el repartidor); en el de control, la Mazmorra avisa solo a
    las rutas y el bench llama a las rutas y al mapa por separado. Después de cada ciclo, los dos mapas deben ser
    iguales casilla por casilla y, en la sala del jugador, cada cara recordada igual a la real (FR-207). Si no,
    AssertionError. Devuelve (comparaciones, ciclos en los que el aviso cambió una cara del mapa medido).
    """
    motor = _motor_con_cazadores(lado, cazadores, otros)
    control = _motor_con_cazadores(lado, cazadores, otros)
    control.mazmorra.observador_puertas = control.rutas
    _antorcha(motor)
    _antorcha(control)
    comparaciones, caras_cambiadas = 0, 0
    for _ in range(ciclos):
        caras_antes = list(motor.mapa.caras)
        if con_puertas:
            _cambiar_puerta_del_jugador(motor, [motor.mazmorra.observador_puertas])
            _cambiar_puerta_del_jugador(control, [control.rutas, control.mapa])
            if motor.mapa.caras != caras_antes:
                caras_cambiadas += 1
        _ciclo(motor, lado, False, [])
        _ciclo(control, lado, False, [])
        if motor.mapa.estado != control.mapa.estado or motor.mapa.caras != control.mapa.caras:
            raise AssertionError("B8: el mapa del motor medido no coincide con el del motor de control")
        sala = motor.jugador.Sala_Actual
        for d in range(4):
            s = motor.mazmorra.salida(sala, d)
            if s is not None and motor.mapa.caras[sala * 4 + d] != (CERRADA if s.cerrada else ABIERTA):
                raise AssertionError(f"B8: la cara {d} de la sala del jugador no se recuerda como es")
        comparaciones += 1
    if motor.terminado or control.terminado:
        raise AssertionError("la partida sintética terminó durante la comprobación")
    return comparaciones, caras_cambiadas


def medir_ciclo_con_antorcha(lado: int, cazadores: int, otros: int, ciclos: int,
                             ciclos_comprobados: int) -> list[ResultadoBenchDTO]:
    """
    B8: ciclo de eventos con la antorcha encendida, 'cazadores' cazadores y 'otros' errantes y rastreadores en una
    cuadrícula de lado × lado (1 024 salas, H-6); el jugador se mueve en cada ciclo; variante con una puerta de su sala
    que cambia en cada ciclo, avisada por el repartidor del motor. Peor ciclo frente a LIMITE_CICLO_MS.
    """
    resultados = []
    for con_puertas in (False, True):
        variante = ("el jugador se mueve y una puerta de su sala cambia" if con_puertas
                    else "el jugador se mueve")
        comparaciones, _ = comprobar_contra_control(lado, cazadores, otros, ciclos_comprobados, con_puertas)
        motor = _motor_con_cazadores(lado, cazadores, otros)
        _antorcha(motor)
        observadores = [motor.mazmorra.observador_puertas]
        tiempos = _cronometrar(lambda: _ciclo(motor, lado, con_puertas, observadores), ciclos)
        if motor.terminado:
            raise AssertionError("la partida sintética terminó durante la medición")
        mejor, mediana = _mejor_y_mediana(tiempos)
        peor = _peor(tiempos)
        exploradas = motor.mapa.estado.count(EXPLORADA)
        veredicto = "cumple" if peor < LIMITE_CICLO_MS else "NO cumple"
        nota = (f"{lado * lado} salas, {cazadores} cazadores y {otros} errantes y rastreadores, antorcha encendida; "
                f"{ciclos} ciclos; {exploradas} salas exploradas al final; peor {peor:.3f} ms; límite "
                f"{LIMITE_CICLO_MS} ms: {veredicto}; antes, {comparaciones} ciclos con el mapa igual al de un motor de "
                f"control")
        resultados.append(ResultadoBenchDTO(SUBSISTEMA, f"B8 ciclo con la antorcha: {variante}", cazadores,
                                            mejor, mediana, nota))
    return resultados


# ====================================================================== B9, B10
def medir_copias_y_vista(lados, mazmorras, repeticiones: int) -> list[ResultadoBenchDTO]:
    """B9 (a_guardado + restaurar), B10 (a_dto y buscar_exploradas) con el mapa completo: O(S)."""
    b9, b10a, b10b = [], [], []
    medianas = [[], [], []]
    for i in range(len(lados)):
        lado, mazmorra = lados[i], mazmorras[i]
        n = len(mazmorra.salas) - 1
        mapa = mapa_completo(mazmorra)
        nombre = mazmorra.salas[_centro(lado)].nombre
        _fila(b9, medianas[0], _cronometrar(lambda: mapa.restaurar(mapa.a_guardado()), repeticiones), n,
              "B9 a_guardado + restaurar", f"copia {5 * (n + 1)} casillas dos veces", None, lados, True)
        _fila(b10a, medianas[1], _cronometrar(mapa.a_dto, repeticiones), n, "B10 a_dto",
              f"{n} salas exploradas", None, lados, True)
        _fila(b10b, medianas[2], _cronometrar(lambda: mapa.buscar_exploradas(nombre), repeticiones), n,
              "B10 buscar_exploradas", f"compara {n} nombres", None, lados, True)
    return b9 + b10a + b10b


# ====================================================================== B11
def medir_grafo(lados, mazmorras, repeticiones: int) -> list[ResultadoBenchDTO]:
    """
    B11: con el mapa completo, armar un GrafoMapaConocido (su primera entradas arma el índice inverso en O(S + E)),
    un paso_desde_cero sobre un grafo ya armado desde la esquina 1 hacia la opuesta, y las dos cosas juntas, que es lo
    que cuesta una búsqueda nueva por paso (I3-8). Con 1 024 salas, la nota dice si «armar el grafo + un paso» queda
    por debajo de LIMITE_PASO_MS (referencia para NFR-250 del integrante 3).
    """
    armar, paso, juntos = [], [], []
    medianas = [[], [], []]
    for i in range(len(lados)):
        lado, mazmorra = lados[i], mazmorras[i]
        n = len(mazmorra.salas) - 1
        mapa = mapa_completo(mazmorra)
        destino = lado * lado
        armado = GrafoMapaConocido(mapa)
        armado.entradas(destino)
        resultado = [None]

        def solo_paso():
            resultado[0] = paso_desde_cero(armado, destino, 1, None)

        _fila(armar, medianas[0], _cronometrar(lambda: GrafoMapaConocido(mapa).entradas(destino), repeticiones), n,
              "B11 armar GrafoMapaConocido", "constructor + índice inverso de entradas, O(S + E)", None, lados, True)
        _fila(paso, medianas[1], _cronometrar(solo_paso, repeticiones), n, "B11 un paso_desde_cero",
              f"esquina 1 hacia {destino} con el grafo ya armado", None, lados, True)
        tiempos = _cronometrar(lambda: paso_b11(mapa, lado), repeticiones)
        texto = f"grafo nuevo + un paso (búsqueda nueva por paso); paso {resultado[0]}"
        if n == 1024:
            _, mediana = _mejor_y_mediana(tiempos)
            debajo = "sí queda por debajo" if mediana < LIMITE_PASO_MS else "NO queda por debajo"
            texto += f"; con 1 024 salas, mediana {mediana:.3f} ms: {debajo} de {LIMITE_PASO_MS} ms (NFR-250)"
        _fila(juntos, medianas[2], tiempos, n, "B11 armar el grafo + un paso", texto, None, lados, True)
    return armar + paso + juntos


# ====================================================================== auxiliares
def _factor(mediana: float, anterior: float | None) -> str:
    """El factor respecto del tamaño anterior, para la nota."""
    if anterior is None or anterior <= 0:
        return ""
    return f"; ×{mediana / anterior:.2f} respecto del tamaño anterior"


def _medir_alternativa(funcion, repeticiones: int, preparar=None) -> tuple[list[float], str]:
    """
    Tiempos de una alternativa descartada: si una sola ejecución tarda más de LIMITE_UNA_REPETICION_MS, se queda con
    esa (después de la de calentamiento) y la nota dice «1 repetición»; si no, 'repeticiones'.
    """
    una = _cronometrar(funcion, 1, preparar)
    if una[0] > LIMITE_UNA_REPETICION_MS:
        return una, "; 1 repetición"
    return _cronometrar(funcion, repeticiones, preparar), ""
