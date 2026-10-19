"""
BenchLogica (Lógica, Integrante 1, Marco): mediciones de Lógica para --bench (§5.2 y §5.3).

Todas usan cargas SINTÉTICAS generadas aquí (sin red y sin datos de una cripta específica, §9):

  1. medir_agenda  la agenda de eventos (ColaEventos, un heap binario): programar un lote de eventos y sacar
                   el siguiente, con cientos y miles de eventos ya en la agenda. Se compara contra la
                   ALTERNATIVA DESCARTADA, un array ordenado (sacar es O(1), pero programar corre O(n) elementos).
  2. medir_ciclo   el ciclo completo de eventos entre dos decisiones del jugador (§5.2): el jugador espera
                   y el Motor procesa todo lo que ocurre hasta que le vuelve a tocar (turnos enemigos,
                   historial, rastro, azar). Debe tardar menos de LIMITE_CICLO_MS; la nota dice si cumple.

Devuelven list[ResultadoBenchDTO], el mismo formato que las demás mediciones de --bench. Lógica no importa
Servicios, por eso el cronómetro está aquí (mismo método que Service/Cronometro.py: perf_counter, una
ejecución de calentamiento, mejor y mediana de N repeticiones, ordenadas con el Ordenador del equipo).

medir() corre todo con los tamaños por defecto. Las pruebas pueden llamar a cada función con tamaños chicos.
"""
import random
import time

from DTO.CriptaDTO import CriptaDTO
from DTO.FichaEnemigoDTO import FichaEnemigoDTO
from DTO.ResultadoBenchDTO import ResultadoBenchDTO
from DTO.SalaDTO import EnemigoEnSalaDTO, SalaDTO, SalidaDTO
from Estructuras.Ordenador import Ordenador
from Logic.ColaEventos import ColaEventos
from Logic.EventoPorg import EventoProgramado
from Logic.Mazmorra import Mazmorra
from Logic.jugador import Jugador
from Logic.motorJuego import Motor

SEMILLA = 2026          # las cargas sintéticas son siempre las mismas: los resultados se pueden comparar
LIMITE_CICLO_MS = 20    # §5.2


def medir() -> list[ResultadoBenchDTO]:
    """Todas las mediciones de Lógica, con los tamaños por defecto."""
    return medir_agenda() + medir_ciclo()


# ====================================================================== 1. agenda de eventos
def medir_agenda(tamanos=(100, 1000, 10000), lote: int = 100,
                 repeticiones: int = 15) -> list[ResultadoBenchDTO]:
    """
    Con n eventos ya en la agenda: cuánto tarda programar 'lote' eventos más y sacar 'lote' veces el siguiente.
    Cada repetición parte de una agenda nueva con los mismos n eventos (armarla no se cronometra).
    """
    resultados = []
    for n in tamanos:
        azar = random.Random(SEMILLA + n)
        tiempos_base = [azar.randrange(10 * n) for _ in range(n)]
        tiempos_lote = [azar.randrange(10 * n) for _ in range(lote)]

        # se arman una vez; cada repetición copia el array (llenar el array ordenado evento por evento es O(n²))
        cola_base = ColaEventos()
        for t in tiempos_base:
            cola_base.programar(EventoProgramado(t, "bench", None))
        eventos_ordenados = Ordenador.ordenar(cola_base.eventos, _comparar_al_reves)

        def heap_lleno():
            cola = ColaEventos()
            cola.eventos = list(cola_base.eventos)
            cola.siguiente_secuencia = n
            return cola

        def array_lleno():
            agenda = _AgendaOrdenada()
            agenda.eventos = list(eventos_ordenados)
            agenda.siguiente_secuencia = n
            return agenda

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
        for operacion, estructura, preparar, funcion, cantidad in casos:
            tiempos = _cronometrar(funcion, repeticiones, preparar)
            mejor, mediana = _mejor_y_mediana(tiempos)
            nota = (f"{operacion} {cantidad} eventos con {n} en la agenda; "
                    f"{1000 * mediana / cantidad:.2f} µs por evento (mediana)")
            resultados.append(ResultadoBenchDTO("agenda de eventos", f"{operacion}: {estructura}",
                                                n, mejor, mediana, nota))
    return resultados


def _comparar_al_reves(a, b):
    """De mayor a menor según el orden de la agenda (tiempo y secuencia)."""
    if b < a:
        return -1
    if a < b:
        return 1
    return 0


class _AgendaOrdenada:
    """
    La alternativa descartada: un array ordenado de mayor a menor (el siguiente evento queda al final).
    Sacar el siguiente es un pop() O(1), pero programar busca el lugar y corre los elementos: O(n).
    Mismo orden que ColaEventos (tiempo y, si empatan, secuencia de programación).
    """

    def __init__(self):
        self.eventos = []
        self.siguiente_secuencia = 0

    def programar(self, evento):
        evento.secuencia = self.siguiente_secuencia
        self.siguiente_secuencia += 1
        arr = self.eventos
        arr.append(evento)
        i = len(arr) - 1
        while i > 0 and arr[i - 1] < evento:        # corre a la derecha los que van después
            arr[i] = arr[i - 1]
            i -= 1
        arr[i] = evento
        return evento

    def obtener_siguiente(self):
        while self.eventos and not self.eventos[-1].esta_valido():
            self.eventos.pop()
        return self.eventos.pop() if self.eventos else None


# ====================================================================== 2. ciclo de eventos (§5.2)
def medir_ciclo(enemigos=(10, 100, 500), ciclos: int = 200) -> list[ResultadoBenchDTO]:
    """
    Una mazmorra en cuadrícula con 'e' enemigos activos (errantes y rastreadores, velocidades distintas).
    Cada ciclo: el jugador espera y el Motor avanza hasta su siguiente decisión. Se cronometran 'ciclos'
    ciclos seguidos (cada uno parte del estado que dejó el anterior, como en una partida real).
    """
    resultados = []
    for e in enemigos:
        motor = _motor_sintetico(e)
        secuencia_inicial = motor.cola.siguiente_secuencia

        def ciclo():
            motor.esperar()
            motor.avanzar_hasta_jugador()

        tiempos = _cronometrar(ciclo, ciclos)
        if motor.terminado:
            raise AssertionError("la partida sintética terminó durante la medición")
        mejor, mediana = _mejor_y_mediana(tiempos)
        peor = tiempos[0]
        for t in tiempos:
            if t > peor:
                peor = t
        programados = (motor.cola.siguiente_secuencia - secuencia_inicial) / (ciclos + 1)
        veredicto = "cumple" if peor < LIMITE_CICLO_MS else "NO cumple"
        nota = (f"{ciclos} ciclos, ~{programados:.0f} eventos por ciclo; peor {peor:.3f} ms; "
                f"límite {LIMITE_CICLO_MS} ms: {veredicto}")
        resultados.append(ResultadoBenchDTO("ciclo de eventos", "esperar + avanzar hasta el jugador",
                                            e, mejor, mediana, nota))
    return resultados


def _motor_sintetico(cantidad_enemigos: int) -> Motor:
    """Motor listo para la primera decisión del jugador, con todos los enemigos ya activos."""
    lado = 1
    while lado * lado < max(cantidad_enemigos // 2, 9):     # unos 2 enemigos por sala
        lado += 1
    n = lado * lado
    cripta = CriptaDTO(id="bench", version="v", salas_total=n, paginas=1, salas_por_pagina=n,
                       sala_inicial=1, sala_salida=n, llave_salida="itm_llave",
                       presupuesto_solicitudes=10 * n, inventario_max=10,
                       jugador_vida_max=10 ** 9, jugador_ataque=6, jugador_defensa=2,
                       jugador_velocidad=100)                    # el jugador no puede morir en la medición
    fichas = [FichaEnemigoDTO("ene_rata", "Rata", 10, 1, 0, 150, "errante", []),
              FichaEnemigoDTO("ene_lobo", "Lobo", 15, 1, 0, 100, "rastreador", []),
              FichaEnemigoDTO("ene_zombi", "Zombi", 20, 1, 0, 60, "errante", [])]

    def fn_ficha(tipo):
        for ficha in fichas:
            if ficha.id == tipo:
                return ficha
        raise KeyError(tipo)

    salas = _cuadricula(lado)
    por_sala = [[] for _ in range(n + 1)]
    for i in range(cantidad_enemigos):
        sala = 2 + i % (n - 1)                                   # ninguno empieza junto al jugador
        por_sala[sala].append(EnemigoEnSalaDTO(f"e-{i}", fichas[i % len(fichas)].id))
    mazmorra = Mazmorra(cripta.sala_salida, cripta.llave_salida)
    mazmorra.cargar_esqueleto(salas)
    for sala in salas:
        mazmorra.cargar_contenido(SalaDTO(sala.id, sala.nombre, sala.salidas, sala.version, True,
                                          por_sala[sala.id]), fn_ficha)

    motor = Motor(SEMILLA, Jugador(cripta), mazmorra)
    motor.iniciar()
    todos = []
    for id_sala in range(1, n + 1):
        todos.extend(mazmorra.enemigos_dormidos(id_sala))
    motor.activar_enemigos(todos)
    motor.avanzar_hasta_jugador()                                # primera decisión del jugador
    return motor


def _cuadricula(lado: int) -> list[SalaDTO]:
    """lado x lado salas conectadas N, S, E, O (ids desde 1)."""
    salas = []
    for f in range(lado):
        for c in range(lado):
            salidas: list[SalidaDTO | None] = [None, None, None, None]
            if f > 0:
                salidas[0] = SalidaDTO((f - 1) * lado + c + 1)
            if f < lado - 1:
                salidas[1] = SalidaDTO((f + 1) * lado + c + 1)
            if c < lado - 1:
                salidas[2] = SalidaDTO(f * lado + c + 2)
            if c > 0:
                salidas[3] = SalidaDTO(f * lado + c)
            id_sala = f * lado + c + 1
            salas.append(SalaDTO(id_sala, f"Sala {id_sala}", salidas, "v"))
    return salas


# ====================================================================== cronómetro
def _cronometrar(funcion, repeticiones: int, preparar=None) -> list[float]:
    """Tiempos en ms de 'repeticiones' ejecuciones, después de una de calentamiento. preparar no se cronometra."""
    if not isinstance(repeticiones, int) or isinstance(repeticiones, bool) or repeticiones < 1:
        raise ValueError(f"las repeticiones deben ser un entero >= 1 (llegó {repeticiones!r})")
    _una_vez(funcion, preparar)
    tiempos = []
    for _ in range(repeticiones):
        tiempos.append(_una_vez(funcion, preparar))
    return tiempos


def _una_vez(funcion, preparar) -> float:
    if preparar is None:
        inicio = time.perf_counter()
        funcion()
    else:
        argumento = preparar()
        inicio = time.perf_counter()
        funcion(argumento)
    return (time.perf_counter() - inicio) * 1000


def _mejor_y_mediana(tiempos: list[float]) -> tuple[float, float]:
    ordenados = Ordenador.ordenar(tiempos, Ordenador.comparar)
    n = len(ordenados)
    mitad = n // 2
    mediana = ordenados[mitad] if n % 2 == 1 else (ordenados[mitad - 1] + ordenados[mitad]) / 2
    return ordenados[0], mediana


if __name__ == "__main__":
    for r in medir():
        print(f"{r.subsistema} | {r.caso} | {r.tamano} | {r.mejor_ms:.3f} | {r.mediana_ms:.3f} | {r.nota}")
