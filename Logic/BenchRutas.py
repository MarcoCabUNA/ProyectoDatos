"""
BenchRutas (Lógica, integrante 1, feature 001, T043): mediciones de --bench para el terreno y el cazador.

Decisiones que respaldan: specs/001-terreno-cazador/research.md R1 a R4 y R6 (§5.1, §5.2, §5.6, §6.3,
NFR-101 a NFR-103, SC-104, SC-105). Tabla de mediciones planificadas: plan.md.

Todas las cargas son SINTÉTICAS (Principio VI) y deterministas (Principio VIII): cuadrículas de lado × lado
salas con un costo entre 1 y 300 por salida, igual en los dos lados, sacado de random.Random(SEMILLA).
Mismo cronómetro y mismo formato que Logic/BenchLogica.py (de allí se reutilizan _cuadricula y _cronometrar).

  1. medir_cola_prioridad   montículo (BusquedaCostoMinimo) frente a recorrer un array de salas (R1)
  2. medir_compartida       paso_desde_cero por cazador frente a RutasHaciaJugador (R2)
  3. medir_rango            tiempo por decisión con rango 200 / 600 / 5 000 y 100 / 1 000 / 10 000 salas (R3, SC-105)
  4. medir_invalidacion     recalcular siempre / descartar ante cualquier puerta / descarte preciso (R4)
  5. medir_ciclo_cazadores  ciclo de eventos con 10 / 30 / 100 cazadores en 1 024 salas, frente a 20 ms (NFR-101)
  6. medir_agenda_con_costos  la agenda de P1 con la carga nueva y sus dos límites conocidos (R6, §5.6)
  7. medir_historial        registros por intervalo con y sin la búsqueda guardada (R6, §5.6)

Las que corren cazadores comprueban además que sus decisiones son las de un cálculo desde cero (FR-114,
escenario H3-8): la nota lo dice. Corre sin vista (Principio V). medir() junta todo con los tamaños por defecto.
"""
import random
from dataclasses import replace

from DTO.CriptaDTO import CriptaDTO
from DTO.Direcciones import E, N, O, S
from DTO.FichaEnemigoDTO import FichaEnemigoDTO
from DTO.ResultadoBenchDTO import ResultadoBenchDTO
from DTO.SalaDTO import EnemigoEnSalaDTO, SalaDTO
from Logic.BenchLogica import (LIMITE_CICLO_MS, SEMILLA, _AgendaOrdenada, _comparar_al_reves, _cronometrar,
                               _cuadricula, _mejor_y_mediana)
from Logic.BusquedaCostoMinimo import BusquedaCostoMinimo, paso_desde_cero
from Logic.ColaEventos import ColaEventos
from Logic.EventoPorg import EventoProgramado
from Logic.GrafoEsqueleto import GrafoEsqueleto
from Logic.Mazmorra import Mazmorra
from Logic.RutasHaciaJugador import RutasHaciaJugador
from Logic.jugador import Jugador
from Logic.motorJuego import Motor
from Estructuras.Ordenador import Ordenador

OPUESTA = [S, N, O, E]
RANGO_PEQUENO = 200          # NFR-102, SC-105 (decisión del grupo)
VELOCIDADES = [60, 80, 100, 150, 200, 300]


def medir() -> list[ResultadoBenchDTO]:
    """Todas las mediciones de la feature 001, con los tamaños por defecto."""
    return (medir_cola_prioridad() + medir_compartida() + medir_rango() + medir_invalidacion()
            + medir_ciclo_cazadores() + medir_agenda_con_costos() + medir_historial())


# ====================================================================== cargas sintéticas
def _cuadricula_con_costos(lado: int, azar: random.Random) -> list[SalaDTO]:
    """
    Las salas de _cuadricula(lado) con un costo entre 1 y 300 en cada salida. Se sortea una vez por par de
    salas, en orden de id, y se declara igual en las dos caras (FR-101). No modifica _cuadricula.
    """
    base = _cuadricula(lado)
    salidas = []
    for sala in base:
        salidas.append(list(sala.salidas))
    for sala in base:                                     # base[id - 1] es la sala id
        for direccion in range(4):
            cara = salidas[sala.id - 1][direccion]
            if cara is None or cara.sala_destino < sala.id:
                continue                                  # el par ya se sorteó desde la otra sala
            costo = azar.randint(1, 300)
            salidas[sala.id - 1][direccion] = replace(cara, costo=costo)
            vuelta = salidas[cara.sala_destino - 1][OPUESTA[direccion]]
            salidas[cara.sala_destino - 1][OPUESTA[direccion]] = replace(vuelta, costo=costo)
    resultado = []
    for sala in base:
        resultado.append(replace(sala, salidas=salidas[sala.id - 1]))
    return resultado


def _mazmorra(salas: list[SalaDTO]) -> Mazmorra:
    """Mazmorra con el esqueleto cargado (sin contenido: la búsqueda no lo usa, FR-112)."""
    mazmorra = Mazmorra(len(salas), "itm_llave")
    mazmorra.cargar_esqueleto(salas)
    return mazmorra


def _centro(lado: int) -> int:
    return (lado // 2) * lado + lado // 2 + 1


def _salas_al_azar(azar: random.Random, cantidad: int, total: int, excepto: int) -> list[int]:
    """'cantidad' salas sorteadas entre 1 y total (pueden repetirse), ninguna igual a 'excepto'."""
    salas = []
    while len(salas) < cantidad:
        sala = azar.randint(1, total)
        if sala != excepto:
            salas.append(sala)
    return salas


def _peor(tiempos: list[float]) -> float:
    peor = tiempos[0]
    for t in tiempos:
        if t > peor:
            peor = t
    return peor


# ====================================================================== 1. cola de prioridad (R1)
def medir_cola_prioridad(tamanos=(100, 1000, 10000), repeticiones: int = 7,
                         tamano_max_array: int = 1024) -> list[ResultadoBenchDTO]:
    """
    Búsqueda desde la esquina 1 hasta resolver la esquina opuesta, sin límite: montículo con borrado perezoso
    (R1-C, la elegida) frente a buscar el mínimo recorriendo un array de salas (R1-A). Las dos deben dar la
    misma distancia. A es O(S²): no se mide por encima de 'tamano_max_array' salas.
    """
    resultados = []
    for n in tamanos:
        lado = _lado(n)
        grafo = GrafoEsqueleto(_mazmorra(_cuadricula_con_costos(lado, random.Random(SEMILLA))))
        destino = lado * lado
        busqueda = BusquedaCostoMinimo(grafo)
        salida = [0, 0]

        def con_monticulo():
            busqueda.reiniciar(1)
            salida[0] = busqueda.distancia_hasta(destino, None)
            salida[1] = busqueda.resueltas

        tiempos = _cronometrar(con_monticulo, repeticiones)
        distancia = salida[0]
        mejor, mediana = _mejor_y_mediana(tiempos)
        nota = f"esquina a esquina, d = {distancia}; {lado}×{lado} salas"
        if lado * lado > tamano_max_array:
            nota += f"; el array no se mide (O(S²) con S = {lado * lado})"
        resultados.append(ResultadoBenchDTO("rutas del cazador", "cola de prioridad: montículo (elegida)",
                                            lado * lado, mejor, mediana, nota))
        if lado * lado > tamano_max_array:
            continue
        otra = [0]

        def con_array():
            otra[0] = _distancia_con_array(grafo, 1, destino)

        tiempos = _cronometrar(con_array, repeticiones)
        if otra[0] != distancia:
            raise AssertionError(f"el array da {otra[0]} y el montículo {distancia}")
        mejor_a, mediana_a = _mejor_y_mediana(tiempos)
        resultados.append(ResultadoBenchDTO("rutas del cazador", "cola de prioridad: recorrer un array (descartada)",
                                            lado * lado, mejor_a, mediana_a,
                                            f"misma distancia {distancia}; {mediana_a / mediana:.1f} veces "
                                            f"la mediana del montículo"))
    return resultados


def _lado(salas: int) -> int:
    """El menor lado con lado × lado ≥ salas."""
    lado = 1
    while lado * lado < salas:
        lado += 1
    return lado


def _distancia_con_array(grafo, origen: int, destino: int) -> int | None:
    """R1-A: la misma búsqueda, pero el mínimo se busca recorriendo todas las salas (O(S) por extracción)."""
    total = grafo.cantidad_salas()
    distancia: list[int | None] = [None] * total
    resuelta = [False] * total
    distancia[origen] = 0
    while True:
        x = -1
        for sala in range(total):
            if not resuelta[sala] and distancia[sala] is not None and (x == -1 or distancia[sala] < distancia[x]):
                x = sala
        if x == -1:
            return None
        resuelta[x] = True
        if x == destino:
            return distancia[x]
        for u, costo in grafo.entradas(x):
            nueva = distancia[x] + costo
            if not resuelta[u] and (distancia[u] is None or nueva < distancia[u]):
                distancia[u] = nueva


# ====================================================================== 2. una búsqueda por cazador o compartida (R2)
def medir_compartida(cazadores=(1, 10, 30, 100), lado: int = 32, ciclos: int = 20, rango: int = 3000,
                     repeticiones: int = 3) -> list[ResultadoBenchDTO]:
    """
    'ciclos' ciclos en una cuadrícula de lado × lado: el jugador da un paso al azar y después decide cada
    cazador (y da su paso). Misma secuencia para las dos alternativas: paso_desde_cero por cazador (R2-A)
    frente a la búsqueda compartida (R2-C). Las decisiones deben ser idénticas.
    """
    resultados = []
    salas = _cuadricula_con_costos(lado, random.Random(SEMILLA))
    grafo = GrafoEsqueleto(_mazmorra(salas))
    for k in cazadores:
        decisiones_a: list = []
        decisiones_c: list = []
        rutas_c: list = [None]

        def desde_cero():
            decisiones_a.clear()
            _jugar_ciclos(grafo, lado, k, ciclos, rango, lambda c, j, r: paso_desde_cero(grafo, j, c, r),
                          decisiones_a)

        def compartida():
            decisiones_c.clear()
            rutas = RutasHaciaJugador(grafo)
            rutas_c[0] = rutas
            _jugar_ciclos(grafo, lado, k, ciclos, rango, rutas.decidir, decisiones_c)

        tiempos_a = _cronometrar(desde_cero, repeticiones)
        tiempos_c = _cronometrar(compartida, repeticiones)
        if decisiones_a != decisiones_c:
            raise AssertionError(f"{k} cazadores: la búsqueda compartida decidió distinto que paso_desde_cero")
        rutas = rutas_c[0]
        mejor_a, mediana_a = _mejor_y_mediana(tiempos_a)
        mejor_c, mediana_c = _mejor_y_mediana(tiempos_c)
        tamano = len(decisiones_a)
        resultados.append(ResultadoBenchDTO(
            "rutas del cazador", f"{k} cazadores: una búsqueda por cazador (descartada)", k, mejor_a, mediana_a,
            f"{ciclos} ciclos, {tamano} decisiones, {tamano} búsquedas; "
            f"{1000 * mediana_a / max(1, tamano):.1f} µs por decisión"))
        resultados.append(ResultadoBenchDTO(
            "rutas del cazador", f"{k} cazadores: búsqueda compartida (elegida)", k, mejor_c, mediana_c,
            f"{ciclos} ciclos, {tamano} decisiones, {rutas.recalculos} búsquedas, {rutas.reutilizaciones} "
            f"reutilizadas; {1000 * mediana_c / max(1, tamano):.1f} µs por decisión; "
            f"{mediana_a / mediana_c:.1f} veces más rápida; decisiones iguales a paso_desde_cero"))
    return resultados


def _jugar_ciclos(grafo, lado: int, k: int, ciclos: int, rango: int, decidir, decisiones: list) -> None:
    """Secuencia fija de R2: el jugador da un paso al azar y cada cazador decide y avanza. Anota cada decisión."""
    azar = random.Random(SEMILLA + k)
    jugador = _centro(lado)
    posiciones = _salas_al_azar(azar, k, lado * lado, jugador)
    for _ in range(ciclos):
        vecinas = grafo.salidas(jugador)
        jugador = vecinas[azar.randint(0, len(vecinas) - 1)][0]
        for i in range(k):
            if posiciones[i] == jugador:
                decisiones.append(None)
                continue
            paso = decidir(posiciones[i], jugador, rango)
            decisiones.append(paso)
            if paso is not None:
                posiciones[i] = paso[0]


# ====================================================================== 3. rango pequeño frente a grande (R3, SC-105)
def medir_rango(rangos=(RANGO_PEQUENO, 600, 5000), tamanos=(100, 1000, 10000), decisiones: int = 400,
                repeticiones: int = 7) -> list[ResultadoBenchDTO]:
    """
    Tiempo por decisión de un cazador lejano (en la sala 1), con una búsqueda nueva en cada decisión: en cada
    una el jugador está en otra sala, sorteada con la semilla. Es el peor caso para el cazador: la búsqueda se
    extiende hasta pasar su rango. Se promedian muchas posiciones porque la región dentro del rango depende de
    los costos cerca del jugador, y esos cambian de una cuadrícula a otra. Con rango > 600 se hace una décima
    parte de las decisiones (cada una recorre casi toda la cripta). Con rango 200, cada multiplicación por 10
    del tamaño debe tardar como mucho el doble (SC-105).
    """
    resultados = []
    por_decision_pequeno = []
    for r in rangos:
        cantidad = decisiones if r <= 600 else max(1, decisiones // 10)
        for n in tamanos:
            lado = _lado(n)
            grafo = GrafoEsqueleto(_mazmorra(_cuadricula_con_costos(lado, random.Random(SEMILLA))))
            rutas = RutasHaciaJugador(grafo)
            azar = random.Random(SEMILLA + 3)
            jugadores: list[int] = []
            while len(jugadores) < cantidad:                  # nunca la sala 1 ni dos seguidas iguales
                sala = azar.randint(2, lado * lado)
                if not jugadores or sala != jugadores[-1]:
                    jugadores.append(sala)
            conteo = [0, 0]

            def decidir_lote():
                conteo[0] = 0
                conteo[1] = 0
                for i in range(cantidad):
                    antes = rutas.busqueda.resueltas
                    if rutas.decidir(1, jugadores[i], r) is not None:
                        conteo[0] += 1
                    conteo[1] += rutas.busqueda.resueltas - antes

            tiempos = _cronometrar(decidir_lote, repeticiones)
            mejor, mediana = _mejor_y_mediana(tiempos)
            micro = 1000 * mediana / cantidad
            if r == RANGO_PEQUENO:
                por_decision_pequeno.append(micro)
            nota = (f"{cantidad} decisiones con el jugador en salas al azar; {micro:.1f} µs por decisión; "
                    f"{conteo[1] / cantidad:.1f} salas resueltas por búsqueda; {conteo[0]} avanzan")
            if r == RANGO_PEQUENO and len(por_decision_pequeno) > 1:
                razon = por_decision_pequeno[-1] / por_decision_pequeno[-2]
                veredicto = "cumple" if razon <= 2 else "NO cumple"
                nota += f"; {razon:.2f} veces el tamaño anterior; SC-105 (≤ 2): {veredicto}"
            resultados.append(ResultadoBenchDTO("rutas del cazador", f"rango {r}: tiempo por decisión",
                                                lado * lado, mejor, mediana, nota))
    return resultados


# ====================================================================== 4. invalidación (R4)
class _RecalcularSiempre:
    """R4-A: una búsqueda nueva en cada decisión (paso_desde_cero). Los avisos de puertas no hacen nada."""

    def __init__(self, grafo) -> None:
        self.grafo = grafo
        self.recalculos = 0

    def decidir(self, sala_cazador: int, sala_jugador: int, rango: int | None) -> tuple[int, int] | None:
        if sala_cazador != sala_jugador:
            self.recalculos += 1
        return paso_desde_cero(self.grafo, sala_jugador, sala_cazador, rango)

    def puerta_cambio(self, a: int, b: int) -> None:
        pass


class _DescartarAnteCualquierPuerta(RutasHaciaJugador):
    """R4-B: la búsqueda compartida, pero cualquier aviso de puerta la descarta."""

    def puerta_cambio(self, a: int, b: int) -> None:
        self.descartar()


ESCENARIOS_PUERTAS = ["puertas estables", "puertas inestables al azar", "puertas inestables al azar y junto al jugador"]


def medir_invalidacion(cazadores: int = 30, lado: int = 32, ciclos: int = 60,
                       repeticiones: int = 3) -> list[ResultadoBenchDTO]:
    """
    'ciclos' ciclos con 'cazadores' cazadores (rangos 600, 1 500 y 3 000); el jugador da un paso cada 5 ciclos.
    Tres escenarios (ESCENARIOS_PUERTAS): ninguna puerta cambia; en cada ciclo se abre o se cierra una puerta
    al azar de la cripta; y además, en cada ciclo, una puerta de la sala del jugador. Las puertas cambian como
    en abrir_puerta y CierrePuerta (las dos caras y un aviso). Las tres estrategias deben decidir lo mismo;
    se cuentan las búsquedas reales por ciclo.
    """
    resultados = []
    salas = _cuadricula_con_costos(lado, random.Random(SEMILLA))
    estrategias = [("recalcular siempre (A)", _RecalcularSiempre),
                   ("descartar ante cualquier puerta (B)", _DescartarAnteCualquierPuerta),
                   ("descarte preciso (C, elegida)", RutasHaciaJugador)]
    for cambios in range(len(ESCENARIOS_PUERTAS)):
        escenario = ESCENARIOS_PUERTAS[cambios]
        referencia = None
        for nombre, clase in estrategias:
            decisiones: list = []
            ultima: list = [None]

            def preparar():
                grafo = GrafoEsqueleto(_mazmorra(salas))
                return grafo, clase(grafo)

            def jugar(argumento):
                grafo, estrategia = argumento
                decisiones.clear()
                ultima[0] = estrategia
                _jugar_con_puertas(grafo, estrategia, lado, cazadores, ciclos, cambios, decisiones)

            tiempos = _cronometrar(jugar, repeticiones, preparar)
            if referencia is None:
                referencia = list(decisiones)
            elif decisiones != referencia:
                raise AssertionError(f"{escenario}, {nombre}: decidió distinto que recalcular siempre")
            mejor, mediana = _mejor_y_mediana(tiempos)
            busquedas = ultima[0].recalculos
            resultados.append(ResultadoBenchDTO(
                "invalidación de rutas", f"{escenario}: {nombre}", cazadores, mejor, mediana,
                f"{lado * lado} salas, {ciclos} ciclos, {len(decisiones)} decisiones; {busquedas} búsquedas "
                f"({busquedas / ciclos:.2f} por ciclo); {mediana / ciclos:.3f} ms por ciclo; "
                f"decisiones iguales a recalcular siempre"))
    return resultados


def _jugar_con_puertas(grafo, estrategia, lado: int, k: int, ciclos: int, cambios: int,
                       decisiones: list) -> None:
    """
    Secuencia fija de R4. cambios: 0 ninguna puerta, 1 una al azar por ciclo, 2 además una de la sala del
    jugador. Cambia las puertas como abrir_puerta y CierrePuerta, y avisa a la estrategia.
    """
    mazmorra = grafo.mazmorra
    azar = random.Random(SEMILLA + 4)
    total = lado * lado
    jugador = _centro(lado)
    posiciones = _salas_al_azar(azar, k, total, jugador)
    rangos = [600, 1500, 3000]
    for ciclo in range(ciclos):
        lejos = (azar.randint(1, total), azar.randint(0, 3))         # se sortea siempre: misma secuencia
        cerca = azar.randint(0, 3)
        if cambios >= 1:
            _cambiar_puerta(mazmorra, estrategia, lejos[0], lejos[1])
        if cambios >= 2:
            _cambiar_puerta(mazmorra, estrategia, jugador, cerca)
        if ciclo % 5 == 0:
            vecinas = mazmorra.salidas_abiertas(jugador)
            if vecinas:
                jugador = vecinas[azar.randint(0, len(vecinas) - 1)]
        for i in range(k):
            if posiciones[i] == jugador:
                decisiones.append(None)
                continue
            paso = estrategia.decidir(posiciones[i], jugador, rangos[i % 3])
            decisiones.append(paso)
            if paso is not None:
                posiciones[i] = paso[0]


def _cambiar_puerta(mazmorra, estrategia, sala: int, direccion: int) -> None:
    """Abre o cierra las dos caras de una puerta y avisa con los destinos de las caras (como la Mazmorra)."""
    cara = mazmorra.salida(sala, direccion)
    if cara is None:
        return
    vuelta = mazmorra.salida(cara.destino, OPUESTA[direccion])
    cerrada = not cara.cerrada
    cara.cerrada = cerrada
    vuelta.cerrada = cerrada
    estrategia.puerta_cambio(cara.destino, vuelta.destino)


# ====================================================================== 5. ciclo de eventos con cazadores (NFR-101)
class _RutasComprobadas(RutasHaciaJugador):
    """La búsqueda compartida, que además compara cada decisión con paso_desde_cero (FR-114, H3-8)."""

    def __init__(self, grafo, historial=None) -> None:
        super().__init__(grafo, historial)
        self.comprobadas = 0

    def decidir(self, sala_cazador: int, sala_jugador: int, rango: int | None) -> tuple[int, int] | None:
        paso = super().decidir(sala_cazador, sala_jugador, rango)
        esperado = paso_desde_cero(self.busqueda.grafo, sala_jugador, sala_cazador, rango)
        if paso != esperado:
            raise AssertionError(f"el cazador en {sala_cazador} decidió {paso} y desde cero da {esperado}")
        self.comprobadas += 1
        return paso


def medir_ciclo_cazadores(cazadores=(10, 30, 100), lado: int = 32, otros: int = 20, ciclos: int = 200,
                          ciclos_comprobados: int = 30) -> list[ResultadoBenchDTO]:
    """
    Una cuadrícula de lado × lado con costos, 'cazadores' cazadores (rangos 600, 1 500 y 3 000; velocidades
    distintas) y 'otros' errantes y rastreadores, todos activos. Cada ciclo: el jugador espera, o se mueve
    entre dos salas del centro (búsqueda nueva en cada ciclo), y el Motor avanza hasta su siguiente decisión.
    Peor ciclo frente a LIMITE_CICLO_MS. Antes, sin cronometrar, se juegan 'ciclos_comprobados' ciclos del mismo
    escenario comparando cada decisión de cazador con paso_desde_cero (H3-8).
    """
    resultados = []
    for k in cazadores:
        for se_mueve in (False, True):
            variante = "el jugador se mueve" if se_mueve else "el jugador espera"
            comprobado = _motor_con_cazadores(lado, k, otros)
            comprobadas = _RutasComprobadas(comprobado.grafo, comprobado.historial)
            comprobado.rutas = comprobadas
            comprobado.mazmorra.observador_puertas = comprobadas
            for _ in range(ciclos_comprobados):
                _un_ciclo(comprobado, se_mueve, lado)

            motor = _motor_con_cazadores(lado, k, otros)
            secuencia_inicial = motor.cola.siguiente_secuencia
            tiempos = _cronometrar(lambda: _un_ciclo(motor, se_mueve, lado), ciclos)
            if motor.terminado:
                raise AssertionError("la partida sintética terminó durante la medición")
            mejor, mediana = _mejor_y_mediana(tiempos)
            peor = _peor(tiempos)
            programados = (motor.cola.siguiente_secuencia - secuencia_inicial) / (ciclos + 1)
            veredicto = "cumple" if peor < LIMITE_CICLO_MS else "NO cumple"
            nota = (f"{lado * lado} salas, {k} cazadores y {otros} errantes y rastreadores; {ciclos} ciclos, "
                    f"~{programados:.0f} eventos por ciclo; {motor.rutas.recalculos} búsquedas, "
                    f"{motor.rutas.reutilizaciones} reutilizadas; peor {peor:.3f} ms; límite {LIMITE_CICLO_MS} ms: "
                    f"{veredicto}; {comprobadas.comprobadas} decisiones de cazador comprobadas contra "
                    f"paso_desde_cero")
            resultados.append(ResultadoBenchDTO("ciclo de eventos", f"con cazadores: {variante}", k,
                                                mejor, mediana, nota))
    return resultados


def _un_ciclo(motor: Motor, se_mueve: bool, lado: int) -> None:
    """Una decisión del jugador (esperar, o moverse entre el centro y su vecina al este) y el avance del Motor."""
    if se_mueve:
        motor.mover_jugador(E if motor.jugador.Sala_Actual == _centro(lado) else O)
    else:
        motor.esperar()
    motor.avanzar_hasta_jugador()


def _motor_con_cazadores(lado: int, cazadores: int, otros: int) -> Motor:
    """Motor listo para la primera decisión del jugador, en el centro, con todos los enemigos ya activos."""
    n = lado * lado
    centro = _centro(lado)
    cripta = CriptaDTO(id="bench", version="v", salas_total=n, paginas=1, salas_por_pagina=n,
                       sala_inicial=centro, sala_salida=n, llave_salida="itm_llave",
                       presupuesto_solicitudes=10 * n, inventario_max=10,
                       jugador_vida_max=10 ** 9, jugador_ataque=6, jugador_defensa=2,
                       jugador_velocidad=100)                    # el jugador no puede morir en la medición
    fichas = [FichaEnemigoDTO("ene_cazador_a", "Cazador", 30, 1, 0, 100, "cazador", [], rango=600),
              FichaEnemigoDTO("ene_cazador_b", "Acechador", 30, 1, 0, 80, "cazador", [], rango=1500),
              FichaEnemigoDTO("ene_cazador_c", "Sabueso", 30, 1, 0, 150, "cazador", [], rango=3000),
              FichaEnemigoDTO("ene_rata", "Rata", 10, 1, 0, 150, "errante", []),
              FichaEnemigoDTO("ene_lobo", "Lobo", 15, 1, 0, 100, "rastreador", [])]

    def fn_ficha(tipo):
        for ficha in fichas:
            if ficha.id == tipo:
                return ficha
        raise KeyError(tipo)

    azar = random.Random(SEMILLA + cazadores)
    salas = _cuadricula_con_costos(lado, random.Random(SEMILLA))
    por_sala = [[] for _ in range(n + 1)]
    for i in range(cazadores + otros):
        sala = _salas_al_azar(azar, 1, n, centro)[0]           # ninguno empieza en la sala del jugador
        tipo = fichas[i % 3].id if i < cazadores else fichas[3 + i % 2].id
        por_sala[sala].append(EnemigoEnSalaDTO(f"e-{i}", tipo))
    mazmorra = Mazmorra(cripta.sala_salida, cripta.llave_salida)
    mazmorra.cargar_esqueleto(salas)
    for sala in salas:
        mazmorra.cargar_contenido(replace(sala, contenido_cargado=True, enemigos=por_sala[sala.id]), fn_ficha)

    motor = Motor(SEMILLA, Jugador(cripta), mazmorra)
    motor.iniciar()
    todos = []
    for id_sala in range(1, n + 1):
        todos.extend(mazmorra.enemigos_dormidos(id_sala))
    motor.activar_enemigos(todos)
    motor.avanzar_hasta_jugador()                                # primera decisión del jugador
    return motor


# ====================================================================== 6. agenda de eventos con la carga nueva (R6)
def medir_agenda_con_costos(tamanos=(100, 1000, 10000), lote: int = 100,
                            repeticiones: int = 15) -> list[ResultadoBenchDTO]:
    """
    La comparación de BenchLogica.medir_agenda (montículo frente a array ordenado), con cargas de la feature 001:
      - costos variables: una agenda como la del juego, con reloj = 0. Cada uno de los n eventos es la acción
        pendiente de un actor, en un instante al azar de su intervalo (cruzar una salida de costo 1 a 300 a una
        velocidad de VELOCIDADES: max(1, costo · 100 // velocidad), P1 §2.3); el lote es la siguiente acción de
        actores que acaban de actuar, reloj + su intervalo completo, así que casi siempre va después de los demás;
      - mismo tiempo: los n eventos y el lote en un solo tiempo, y repartidos en 10 tiempos (decide la secuencia);
      - cancelaciones: el 50 % y el 90 % de los n eventos cancelados antes de sacar el lote; la nota dice cuántas
        entradas canceladas se descartaron y el tamaño del arreglo antes y después.
    """
    resultados = []
    for n in tamanos:
        azar = random.Random(SEMILLA + n)
        resultados += _comparar_agendas("agenda de eventos (costos variables)", n, lote, repeticiones,
                                        _tiempos_pendientes(azar, n), _tiempos_nuevos(azar, lote))
        for cantidad in (1, 10):
            tiempos_base = [1000 + 100 * azar.randrange(cantidad) for _ in range(n)]
            tiempos_lote = [1000 + 100 * azar.randrange(cantidad) for _ in range(lote)]
            resultados += _comparar_agendas(f"agenda de eventos (mismo tiempo: {cantidad} tiempo"
                                            f"{'' if cantidad == 1 else 's'})", n, lote, repeticiones,
                                            tiempos_base, tiempos_lote)
        for porcentaje in (50, 90):
            resultados += _medir_cancelaciones(azar, n, lote, porcentaje, repeticiones)
    return resultados


def _intervalo_al_azar(azar: random.Random) -> int:
    """El intervalo de cruzar una salida de costo 1 a 300 a una velocidad de VELOCIDADES (P1 §2.3, FR-102)."""
    costo = azar.randint(1, 300)
    velocidad = VELOCIDADES[azar.randrange(len(VELOCIDADES))]
    return max(1, costo * 100 // velocidad)


def _tiempos_pendientes(azar: random.Random, cantidad: int) -> list[int]:
    """Con reloj = 0, la acción pendiente de cada actor: un instante al azar dentro de su intervalo."""
    tiempos = []
    for _ in range(cantidad):
        tiempos.append(azar.randint(1, _intervalo_al_azar(azar)))
    return tiempos


def _tiempos_nuevos(azar: random.Random, cantidad: int) -> list[int]:
    """Con reloj = 0, la siguiente acción de un actor que acaba de actuar: reloj + su intervalo completo."""
    tiempos = []
    for _ in range(cantidad):
        tiempos.append(_intervalo_al_azar(azar))
    return tiempos


def _agendas_llenas(tiempos_base: list[int]):
    """(heap lleno, array ordenado lleno) con los mismos eventos: funciones que devuelven una copia nueva."""
    n = len(tiempos_base)
    cola_base = ColaEventos()
    for t in tiempos_base:
        cola_base.programar(EventoProgramado(t, "bench", None))
    ordenados = Ordenador.ordenar(cola_base.eventos, _comparar_al_reves)

    def heap_lleno():
        cola = ColaEventos()
        cola.eventos = list(cola_base.eventos)
        cola.siguiente_secuencia = n
        return cola

    def array_lleno():
        agenda = _AgendaOrdenada()
        agenda.eventos = list(ordenados)
        agenda.siguiente_secuencia = n
        return agenda

    return cola_base, heap_lleno, array_lleno


def _comparar_agendas(subsistema: str, n: int, lote: int, repeticiones: int, tiempos_base: list[int],
                      tiempos_lote: list[int]) -> list[ResultadoBenchDTO]:
    _, heap_lleno, array_lleno = _agendas_llenas(tiempos_base)

    def programar_lote(agenda):
        for t in tiempos_lote:
            agenda.programar(EventoProgramado(t, "bench", None))

    def sacar_lote(agenda):
        for _ in range(lote):
            agenda.obtener_siguiente()

    sacados = min(lote, n)
    casos = [("programar", "heap (ColaEventos)", heap_lleno, programar_lote, lote),
             ("programar", "array ordenado (descartada)", array_lleno, programar_lote, lote),
             ("sacar el siguiente", "heap (ColaEventos)", heap_lleno, sacar_lote, sacados),
             ("sacar el siguiente", "array ordenado (descartada)", array_lleno, sacar_lote, sacados)]
    resultados = []
    for operacion, estructura, preparar, funcion, cantidad in casos:
        mejor, mediana = _mejor_y_mediana(_cronometrar(funcion, repeticiones, preparar))
        resultados.append(ResultadoBenchDTO(subsistema, f"{operacion}: {estructura}", n, mejor, mediana,
                                            f"{operacion} {cantidad} eventos con {n} en la agenda; "
                                            f"{1000 * mediana / cantidad:.2f} µs por evento (mediana)"))
    return resultados


def _medir_cancelaciones(azar: random.Random, n: int, lote: int, porcentaje: int,
                         repeticiones: int) -> list[ResultadoBenchDTO]:
    cola_base, heap_lleno, array_lleno = _agendas_llenas(_tiempos_pendientes(azar, n))
    for evento in cola_base.eventos:                      # los mismos objetos están en las dos agendas
        if azar.randrange(100) < porcentaje:
            evento.cancelar()
    validos = 0
    for evento in cola_base.eventos:
        if evento.esta_valido():
            validos += 1
    sacados = min(lote, validos)
    tamanos = [0, 0]

    def sacar_lote(agenda):
        tamanos[0] = len(agenda.eventos)
        for _ in range(lote):
            agenda.obtener_siguiente()
        tamanos[1] = len(agenda.eventos)

    resultados = []
    for estructura, preparar in (("heap (ColaEventos)", heap_lleno), ("array ordenado (descartada)", array_lleno)):
        mejor, mediana = _mejor_y_mediana(_cronometrar(sacar_lote, repeticiones, preparar))
        descartadas = tamanos[0] - tamanos[1] - sacados
        resultados.append(ResultadoBenchDTO(
            f"agenda de eventos ({porcentaje} % cancelados)", f"sacar el siguiente: {estructura}", n, mejor, mediana,
            f"{n - validos} de {n} cancelados; sacar {sacados} válidos descartó {descartadas} cancelados; "
            f"arreglo de {tamanos[0]} a {tamanos[1]} entradas; {1000 * mediana / max(1, sacados):.2f} µs por "
            f"evento válido (mediana)"))
    return resultados


# ====================================================================== 7. historial (R6)
def medir_historial(cazadores: int = 30, lado: int = 32, otros: int = 20,
                    ciclos: int = 200) -> list[ResultadoBenchDTO]:
    """
    Registros de HistorialRetroceso por intervalo (una decisión del jugador y lo que pasa hasta la siguiente),
    con la búsqueda guardada registrando su descarte (R4) y sin registrarlo (RutasHaciaJugador sin historial:
    las mismas decisiones, pero un pergamino podría dejarla vieja). Con el jugador quieto y moviéndose.
    """
    resultados = []
    for se_mueve in (False, True):
        variante = "el jugador se mueve" if se_mueve else "el jugador espera"
        registros = []
        for con_busqueda in (True, False):
            motor = _motor_con_cazadores(lado, cazadores, otros)
            if not con_busqueda:
                motor.rutas = RutasHaciaJugador(motor.grafo, None)
                motor.mazmorra.observador_puertas = motor.rutas
            contador = _contar_registros(motor.historial)
            tiempos = _cronometrar(lambda: _un_ciclo(motor, se_mueve, lado), ciclos)
            por_intervalo = contador[0] / (ciclos + 1)
            registros.append(por_intervalo)
            mejor, mediana = _mejor_y_mediana(tiempos)
            caso = "con la búsqueda registrada (elegida)" if con_busqueda else "sin registrar la búsqueda"
            nota = f"{cazadores} cazadores, {ciclos} ciclos; {por_intervalo:.1f} registros por intervalo"
            if not con_busqueda:
                nota += f"; la búsqueda agrega {registros[0] - por_intervalo:.2f} por intervalo"
            resultados.append(ResultadoBenchDTO("historial de retroceso", f"{variante}: {caso}", cazadores,
                                                mejor, mediana, nota))
    return resultados


def _contar_registros(historial) -> list[int]:
    """Cuenta los registros del historial (los dos métodos de registro). Devuelve el contador, que se actualiza."""
    contador = [0]
    registrar_cambio = historial.registrar_cambio
    registrar_atributo = historial.registrar_atributo

    def contar_cambio(deshacer):
        contador[0] += 1
        registrar_cambio(deshacer)

    def contar_atributo(objeto, nombre, valor_anterior):
        contador[0] += 1
        registrar_atributo(objeto, nombre, valor_anterior)

    historial.registrar_cambio = contar_cambio
    historial.registrar_atributo = contar_atributo
    return contador


if __name__ == "__main__":
    for r in medir():
        print(f"{r.subsistema} | {r.caso} | {r.tamano} | {r.mejor_ms:.3f} | {r.mediana_ms:.3f} | {r.nota}")
