"""
BenchLineaTiempo (Integrante 3, feature 004): mediciones de la línea de tiempo y de los puntos de control para
--bench (§5.3, §6.1, Documento de Decisiones §5.5 y §5.6; NFR-401, NFR-402 y NFR-403).

Todas usan cargas SINTÉTICAS generadas aquí (sin red y sin datos de una cripta específica, §9, Principio VI): una
cripta en cuadrícula con unos pocos enemigos errantes inofensivos y un jugador que no puede morir, que juega una
secuencia fija de acciones. Mismo cronómetro (Service/Cronometro.py) y mismo formato (ResultadoBenchDTO) que
Service/BenchInventario.py. Cada grupo compara lo elegido contra la ALTERNATIVA DESCARTADA cuando la hay:

  M1 medir_historia          `historia #k` e `historia <t>` con K en {1, 5, 20, 100} contra SIN puntos de control
                             (solo el punto 0), con 5 000 acciones, en el peor caso del bloque: la posición que
                             obliga a re-simular K - 1 acciones. Es el criterio de §6.1 (SC-405: < 50 ms).
  M2 medir_posiciones        el mismo tiempo según la posición consultada: inicio, mitad y final.
  M3 medir_memoria           bytes y cantidad de elementos guardados con 100, 1 000 y 5 000 acciones (bytes del
                             archivo binario de cada punto + acciones, sin medir la memoria del intérprete).
  M4 medir_ubicar_punto      ubicar el punto de control: búsqueda binaria contra recorrido lineal.
  M5 medir_copia             costo de UNA copia (un punto de control) según las salas y los enemigos (riesgo R-1).
  M6 medir_recorte           costo de leer un pergamino (recorte + copia del punto nuevo) según la historia (NFR-403).
  §5.6 medir_costo_por_accion   costo por acción de ServicioLineaTiempo.ejecutar con y sin línea activa.

Memoria (M3): el formato de archivo versión 2 con la línea (T003, de Data) todavía no existe, así que los bytes
son los que escribe GuardadoBinario (versión 1) para CADA punto de control, uno por archivo (cada uno con su
cabecera, que pesa unos 34 bytes), más las acciones (su línea de texto del log y 4 bytes del tiempo). Las cargas
y las fichas se cuentan pero no se pesan: son pocas y no dependen de K.

Las partidas de 5 000 acciones se juegan UNA vez por cada K y se reutilizan entre M1, M2 y M3 (`_Partidas`); como
la partida es determinista, la historia de las primeras n acciones de una partida de 5 000 es la de una partida de n.

Los archivos temporales (caché del catálogo y un punto a la vez) van en `saves/bench_tmp/linea_tiempo` (ya está en
el .gitignore) y se borran al terminar. medir() corre todo con los tamaños por defecto; las pruebas llaman a cada
función con tamaños chicos.
"""
import os
import random

from Data import GuardadoBinario
from Data.FuenteDatos import FuenteDatos
from DTO.AccionDTO import AccionDTO
from DTO.ConfiguracionDTO import CHECKPOINT_POR_DEFECTO, ConfiguracionDTO
from DTO.CriptaDTO import CriptaDTO
from DTO.Direcciones import E, N, O, S
from DTO.FichaEnemigoDTO import FichaEnemigoDTO
from DTO.ResultadoBenchDTO import ResultadoBenchDTO
from DTO.SalaDTO import ContenidoSalaDTO, EnemigoEnSalaDTO, SalaDTO, SalidaDTO
from Logic.Inventario import Inventario
from Logic.LineaTiempo import LineaTiempo, PuntoControl
from Logic.Mazmorra import Mazmorra
from Logic.PartidaGuardada import PartidaGuardada
from Logic.jugador import Jugador
from Logic.motorJuego import Motor
from Service.ContextoPartida import ContextoPartida
from Service.Cronometro import medir as cronometrar
from Service.ReconstructorEstado import ReconstructorEstado
from Service.ServicioLineaTiempo import ServicioLineaTiempo
from Service.ServicioPartida import ServicioPartida

SUBSISTEMA = "línea de tiempo"
SEMILLA = 2026                          # las cargas sintéticas son siempre las mismas: los resultados se pueden comparar
REPETICIONES = 15                       # con 15 el mínimo es estable
ACCIONES_POR_DEFECTO = 5000             # el tamaño de partida de §6.1
KS_POR_DEFECTO = (1, 5, 20, 100)        # plan, M1
SIN_PUNTOS = 10 ** 9                    # un K tan grande que nunca se toma otro punto que el 0: la alternativa descartada
LADO = 4                                # la cripta sintética de las partidas jugadas: LADO x LADO salas
CARPETA = os.path.join("saves", "bench_tmp", "linea_tiempo")
ID_ENEMIGO = "ent_bench_errante"
VIDA_JUGADOR = 10 ** 9                  # el jugador no puede morir durante la medición

_ESPERAR = AccionDTO("esperar")
_CICLO = (_ESPERAR, AccionDTO("mover", direccion=E), _ESPERAR, AccionDTO("mover", direccion=S),
          _ESPERAR, AccionDTO("mover", direccion=O), _ESPERAR, AccionDTO("mover", direccion=N))


def medir() -> list[ResultadoBenchDTO]:
    """Todas las mediciones de la línea de tiempo, con los tamaños por defecto."""
    partidas = _Partidas()
    try:
        return (medir_historia(partidas=partidas) + medir_posiciones(partidas=partidas)
                + medir_memoria(partidas=partidas) + medir_ubicar_punto() + medir_copia()
                + medir_recorte() + medir_costo_por_accion())
    finally:
        partidas.liberar()
        _borrar_carpeta(CARPETA)


# ====================================================================== M1 y M2: tiempo de `historia`
def medir_historia(acciones: int = ACCIONES_POR_DEFECTO, ks=KS_POR_DEFECTO, repeticiones: int = REPETICIONES,
                   partidas=None) -> list[ResultadoBenchDTO]:
    """`historia #k` y `historia <t>` en el peor caso del bloque, para cada K y sin puntos de control (M1, SC-405)."""
    resultados = []
    with _Compartidas(partidas) as compartidas:
        servicio = ServicioLineaTiempo()
        for k in _con_la_alternativa(ks):
            contexto = compartidas.obtener(acciones, k)
            numero = _peor_posicion(acciones, k)
            instante = contexto.linea.accion(numero).tiempo
            etiqueta = _etiqueta(k)
            reaplicadas = _reaplicadas_por_accion(contexto, numero)
            nota = f"re-simula {reaplicadas} acción(es) de las {acciones}; {len(contexto.linea.puntos)} puntos de control"
            for nombre, consulta in (("historia #k", lambda: servicio.consultar_por_accion(contexto, numero)),
                                     ("historia <t>", lambda: servicio.consultar_por_instante(contexto, instante))):
                mejor, mediana = cronometrar(consulta, repeticiones)
                resultados.append(ResultadoBenchDTO(SUBSISTEMA, f"{etiqueta}: {nombre} (peor caso del bloque)",
                                                    acciones, mejor, mediana, nota))
    return resultados


def medir_posiciones(acciones: int = ACCIONES_POR_DEFECTO, ks=KS_POR_DEFECTO, repeticiones: int = REPETICIONES,
                     partidas=None) -> list[ResultadoBenchDTO]:
    """`historia #k` al inicio, a la mitad y al final de la partida, para cada K y sin puntos de control (M2)."""
    resultados = []
    posiciones = (("inicio", 1), ("mitad", max(1, acciones // 2)), ("final", acciones))
    with _Compartidas(partidas) as compartidas:
        servicio = ServicioLineaTiempo()
        for k in _con_la_alternativa(ks):
            contexto = compartidas.obtener(acciones, k)
            for nombre, numero in posiciones:
                reaplicadas = _reaplicadas_por_accion(contexto, numero)
                mejor, mediana = cronometrar(lambda: servicio.consultar_por_accion(contexto, numero), repeticiones)
                resultados.append(ResultadoBenchDTO(
                    SUBSISTEMA, f"{_etiqueta(k)}: historia #k, posición {nombre}", acciones, mejor, mediana,
                    f"acción {numero}; re-simula {reaplicadas} acción(es)"))
    return resultados


def _con_la_alternativa(ks) -> list[int]:
    """Los K pedidos y, al final, la alternativa descartada: ningún punto de control más que el 0."""
    return list(ks) + [SIN_PUNTOS]


def _etiqueta(k: int) -> str:
    return "sin puntos de control (descartada)" if k == SIN_PUNTOS else f"K={k}"


def _peor_posicion(acciones: int, k: int) -> int:
    """El número de acción, hacia la mitad de la partida, que obliga a re-simular K - 1 acciones (el peor del bloque).

    La acción n usa el último punto con <= n - 1 acciones; el peor caso es n = (m + 1) * K, justo antes del siguiente
    punto. Sin puntos de control (K >= acciones) el peor caso es la última acción."""
    if k >= acciones:
        return acciones
    mitad = (acciones // 2) // k
    return min(acciones, (mitad + 1) * k)


def _reaplicadas_por_accion(contexto: ContextoPartida, numero: int) -> int:
    """Cuántas acciones re-simula `historia #numero` (FR-416: nunca más de K)."""
    reconstructor = ReconstructorEstado(contexto)
    reconstructor.hasta_accion(numero)
    return reconstructor.acciones_reaplicadas


# ====================================================================== M3: memoria
def medir_memoria(tamanos=(100, 1000, ACCIONES_POR_DEFECTO), ks=KS_POR_DEFECTO, partidas=None,
                  carpeta: str = os.path.join(CARPETA, "puntos")) -> list[ResultadoBenchDTO]:
    """Bytes y elementos guardados con n acciones, para cada K y sin puntos de control (M3, NFR-402).

    Una fila por (K, tamaño). Las columnas de ms van en 0: esto es memoria, no tiempo."""
    resultados = []
    mayor = tamanos[-1]
    with _Compartidas(partidas) as compartidas:
        for k in _con_la_alternativa(ks):
            linea = compartidas.obtener(mayor, k).linea
            ruta = os.path.join(carpeta, "punto.sav")
            bytes_puntos = 0
            siguiente = 0                                        # el primer punto que todavía no se pesó
            for tamano in tamanos:
                # la historia de las primeras n acciones es la de una partida de n acciones (determinista)
                while siguiente < len(linea.puntos) and linea.puntos[siguiente].acciones_completadas <= tamano:
                    bytes_puntos += _bytes_de_un_punto(linea.puntos[siguiente], ruta)
                    siguiente += 1
                bytes_acciones = _bytes_de_las_acciones(linea, tamano)
                cargas = _contar_hasta(linea.cargas, tamano, lambda c: c.ordinal)
                nota = (f"memoria: {bytes_puntos + bytes_acciones} bytes ({bytes_puntos} de {siguiente} puntos, "
                        f"{bytes_acciones} de {tamano} acciones); {tamano} acciones, {siguiente} puntos, "
                        f"{cargas} cargas, {len(linea.fichas)} fichas")
                resultados.append(ResultadoBenchDTO(SUBSISTEMA, f"{_etiqueta(k)}: memoria de la línea",
                                                    tamano, 0.0, 0.0, nota))
        _borrar_carpeta(carpeta)
    return resultados


def _contar_elementos(linea: LineaTiempo) -> tuple[int, int, int, int]:
    """(acciones, puntos de control, registros de carga, fichas) que guarda la línea."""
    return len(linea.acciones), len(linea.puntos), len(linea.cargas), len(linea.fichas)


def _contar_hasta(elementos: list, limite: int, clave) -> int:
    cuenta = 0
    for elemento in elementos:
        if clave(elemento) <= limite:
            cuenta += 1
    return cuenta


def _bytes_de_un_punto(punto: PuntoControl, ruta: str) -> int:
    """Lo que ocupa un punto de control en el archivo binario del equipo (GuardadoBinario, un archivo por punto)."""
    return GuardadoBinario.guardar(ruta, punto.partida, punto.salas)


def _bytes_de_las_acciones(linea: LineaTiempo, cantidad: int) -> int:
    """Las primeras `cantidad` acciones: su línea de texto del log, un salto de línea y 4 bytes del tiempo."""
    total = 0
    for i in range(cantidad):
        total += len(linea.acciones[i].accion.a_linea().encode("utf-8")) + 1 + 4
    return total


def _bytes_de_la_nota(nota: str) -> int:
    """El total de bytes que dice la nota de una fila de memoria («memoria: N bytes ...»)."""
    return int(nota.split("memoria: ")[1].split(" bytes")[0])


# ====================================================================== M4: ubicar el punto de control
def medir_ubicar_punto(cantidades=(100, 1000, 10000), consultas: int = 200,
                       repeticiones: int = REPETICIONES) -> list[ResultadoBenchDTO]:
    """Ubicar el punto de control con búsqueda binaria contra recorrido lineal, con P puntos (M4, R5)."""
    resultados = []
    for cantidad in cantidades:
        linea = _linea_con_puntos(cantidad - 1, 1)               # k = 1: la línea trae exactamente `cantidad` puntos
        azar = random.Random(SEMILLA + cantidad)
        pedidos = [azar.randrange(cantidad) for _ in range(consultas)]
        nota = f"{consultas} consultas por tanda; {cantidad} puntos de control"
        for nombre, funcion in (("búsqueda binaria", lambda: _ubicar_todos_binaria(linea, pedidos)),
                                ("recorrido lineal (descartada)", lambda: _ubicar_todos_lineal(linea, pedidos))):
            mejor, mediana = cronometrar(funcion, repeticiones)
            resultados.append(ResultadoBenchDTO(SUBSISTEMA, f"{nombre}: ubicar el punto de control",
                                                cantidad, mejor, mediana, nota))
    return resultados


def _linea_con_puntos(acciones: int, k: int) -> LineaTiempo:
    """Una línea con `acciones` acciones y un punto de control en 0, k, 2k, ... (sin estado real: solo la forma)."""
    linea = LineaTiempo(k)
    for i in range(acciones):
        linea.agregar_accion(i, _ESPERAR)
    for acciones_completadas in range(0, acciones + 1, k):
        linea.agregar_punto(PuntoControl(acciones_completadas, None, []))
    return linea


def _ubicar_lineal(puntos: list[PuntoControl], acciones: int) -> PuntoControl | None:
    """La alternativa descartada: recorrer los puntos desde el principio hasta pasar el pedido."""
    encontrado = None
    for punto in puntos:
        if punto.acciones_completadas > acciones:
            break
        encontrado = punto
    return encontrado


def _ubicar_todos_binaria(linea: LineaTiempo, pedidos: list[int]) -> None:
    for acciones in pedidos:
        linea.ubicar_punto(acciones)


def _ubicar_todos_lineal(linea: LineaTiempo, pedidos: list[int]) -> None:
    for acciones in pedidos:
        _ubicar_lineal(linea.puntos, acciones)


# ====================================================================== M5: costo de una copia
def medir_copia(salas=(6, 50, 1000, 10000), enemigos=(0, 10, 100),
                repeticiones: int = REPETICIONES) -> list[ResultadoBenchDTO]:
    """Costo de UNA copia completa del estado (PartidaGuardada.guardar), con S salas y E enemigos (M5, riesgo R-1)."""
    resultados = []
    for n in salas:
        for e in enemigos:
            motor = _motor_con(n, e)
            cripta = _cripta(n)
            mejor, mediana = cronometrar(lambda: PartidaGuardada.guardar(motor, cripta, "v", SEMILLA), repeticiones)
            resultados.append(ResultadoBenchDTO(SUBSISTEMA, f"PartidaGuardada.guardar: {e} enemigos", n, mejor, mediana,
                                                f"1 copia de {n} salas con {e} enemigos activos"))
    return resultados


# ====================================================================== M6: recorte del pergamino
def medir_recorte(historias=(100, 500, 1000, 5000), k: int = CHECKPOINT_POR_DEFECTO,
                  repeticiones: int = REPETICIONES) -> list[ResultadoBenchDTO]:
    """Costo de leer un pergamino: quitar la última acción, recortar puntos y copiar el punto nuevo (M6, NFR-403).

    No debe crecer con la historia."""
    resultados = []
    for historia in historias:
        mejor, mediana = cronometrar(lambda par: _leer_pergamino(par[0], par[1]), repeticiones,
                                     preparar=lambda: _linea_y_motor_para_recorte(historia, k))
        resultados.append(ResultadoBenchDTO(SUBSISTEMA, "pergamino: recorte + copia del punto de control", historia,
                                            mejor, mediana,
                                            f"K={k}; PartidaGuardada.guardar + LineaTiempo.retroceder_una "
                                            f"(armar la línea no se cronometra)"))
    return resultados


def _linea_y_motor_para_recorte(historia: int, k: int) -> tuple[LineaTiempo, Motor]:
    """Una línea de `historia` acciones con un punto cada K, y el motor ya revertido a historia - 1 acciones."""
    motor = _motor_con(6, 0)
    motor.jugador.acciones = historia
    partida, salas = PartidaGuardada.guardar(motor, _cripta(6), "v", SEMILLA)
    linea = LineaTiempo(k)
    for i in range(historia):
        linea.agregar_accion(i, _ESPERAR)
    for acciones_completadas in range(0, historia + 1, k):
        linea.agregar_punto(PuntoControl(acciones_completadas, partida, salas))     # la forma basta: se comparte la copia
    motor.jugador.acciones = historia - 1                        # lo que deja el pergamino en el estado vivo
    return linea, motor


def _leer_pergamino(linea: LineaTiempo, motor: Motor) -> None:
    """Lo que hace ServicioLineaTiempo.ejecutar cuando se lee un pergamino: guardar el estado y recortar."""
    estado = PartidaGuardada.guardar(motor, _cripta(6), "v", SEMILLA)
    linea.retroceder_una(estado)


# ====================================================================== §5.6: costo por acción
def medir_costo_por_accion(acciones: int = 200, repeticiones: int = 9) -> list[ResultadoBenchDTO]:
    """Costo de ServicioLineaTiempo.ejecutar con la línea activa (K por defecto) y sin línea (§5.6, NFR-401)."""
    resultados = []
    _borrar_carpeta(CARPETA)
    try:
        servicio = ServicioLineaTiempo()
        con_linea = _partida_con(0, CHECKPOINT_POR_DEFECTO)
        sin_linea = _partida_con(0, CHECKPOINT_POR_DEFECTO)
        sin_linea.linea = None                                   # ServicioLineaTiempo.ejecutar sin línea = solo la acción
        casos = (("ServicioLineaTiempo.ejecutar con línea activa", con_linea, f"K={CHECKPOINT_POR_DEFECTO}"),
                 ("ServicioLineaTiempo.ejecutar sin línea (descartada)", sin_linea, "sin línea"))
        for caso, contexto, detalle in casos:
            mejor, mediana = cronometrar(lambda: _jugar(servicio, contexto, contexto.jugador.acciones + acciones),
                                         repeticiones)
            nota = (f"{acciones} acciones por tanda; {1000 * mediana / acciones:.1f} µs por acción (mediana); "
                    f"{detalle}")
            resultados.append(ResultadoBenchDTO(SUBSISTEMA, caso, acciones, mejor, mediana, nota))
    finally:
        _borrar_carpeta(CARPETA)
    return resultados


# ====================================================================== la partida sintética
class _FuenteSintetica(FuenteDatos):
    """FuenteDatos inventada: LADO x LADO salas conectadas N, S, E, O y unos enemigos errantes inofensivos."""

    def __init__(self, lado: int):
        self._lado = lado

    def listar_criptas(self):
        return []

    def obtener_datos_generales(self, id_cripta: str) -> CriptaDTO:
        return _cripta(self._lado * self._lado, VIDA_JUGADOR)

    def obtener_version_cripta(self, id_cripta: str) -> str:
        return "v"

    def obtener_pagina_salas(self, id_cripta: str, pagina: int, version: str) -> list[SalaDTO]:
        return _salas(self._lado * self._lado, version)

    def obtener_contenido(self, id_cripta: str, ids_salas: list[int]) -> list[ContenidoSalaDTO]:
        """Un errante en la segunda sala y otro en la diagonal: el jugador pasa por ahí (E, S, O, N desde la sala 1)."""
        con_enemigo = (2, self._lado + 2)
        contenidos = []
        for id_sala in ids_salas:
            enemigos = [EnemigoEnSalaDTO(f"e-{id_sala}", ID_ENEMIGO)] if id_sala in con_enemigo else []
            contenidos.append(ContenidoSalaDTO(id_sala, enemigos))
        return contenidos

    def obtener_version_catalogo(self) -> str:
        return "v"

    def obtener_catalogo(self, ids: list[str]) -> list:
        return [_ficha_enemigo(i) for i in ids if i == ID_ENEMIGO]


def _ficha_enemigo(id_ficha: str = ID_ENEMIGO) -> FichaEnemigoDTO:
    """Un errante que no hace daño y no muere: se mueve (eventos en la agenda) pero no cambia el rumbo de la partida."""
    return FichaEnemigoDTO(id_ficha, "Errante de prueba", 10 ** 6, 0, 0, 100, "errante", [])


def _cripta(salas: int, vida_jugador: int = VIDA_JUGADOR) -> CriptaDTO:
    return CriptaDTO(id="bench_linea", version="v", salas_total=salas, paginas=1, salas_por_pagina=salas,
                     sala_inicial=1, sala_salida=salas, llave_salida="itm_llave",
                     presupuesto_solicitudes=10 * salas, inventario_max=10, jugador_vida_max=vida_jugador,
                     jugador_ataque=6, jugador_defensa=2, jugador_velocidad=100)


def _salas(cantidad: int, version: str = "v") -> list[SalaDTO]:
    """`cantidad` salas (ids 1..cantidad) en una cuadrícula de filas casi cuadradas, conectadas N, S, E, O."""
    columnas = 1
    while columnas * columnas < cantidad:
        columnas += 1
    salas = []
    for id_sala in range(1, cantidad + 1):
        fila, columna = divmod(id_sala - 1, columnas)
        salidas: list[SalidaDTO | None] = [None, None, None, None]
        if fila > 0:
            salidas[N] = SalidaDTO(id_sala - columnas)
        if id_sala + columnas <= cantidad:
            salidas[S] = SalidaDTO(id_sala + columnas)
        if columna < columnas - 1 and id_sala + 1 <= cantidad:
            salidas[E] = SalidaDTO(id_sala + 1)
        if columna > 0:
            salidas[O] = SalidaDTO(id_sala - 1)
        salas.append(SalaDTO(id_sala, f"Sala {id_sala}", salidas, version))
    return salas


def _motor_con(salas: int, enemigos: int) -> Motor:
    """Un motor listo para la primera decisión, con `salas` salas y `enemigos` enemigos ya activos (repartidos)."""
    ficha = _ficha_enemigo()
    esqueleto = _salas(salas)
    por_sala = [[] for _ in range(salas + 1)]
    for i in range(enemigos):
        por_sala[2 + i % max(1, salas - 1) if salas > 1 else 1].append(EnemigoEnSalaDTO(f"e-{i}", ficha.id))
    mazmorra = Mazmorra(salas, "itm_llave")
    mazmorra.cargar_esqueleto(esqueleto)
    for sala in esqueleto:
        mazmorra.cargar_contenido(SalaDTO(sala.id, sala.nombre, sala.salidas, sala.version, True,
                                          por_sala[sala.id]), lambda tipo: ficha)
    motor = Motor(SEMILLA, Jugador(_cripta(salas)), mazmorra, None, Inventario(10))
    motor.iniciar()
    todos = []
    for id_sala in range(1, salas + 1):
        todos.extend(mazmorra.enemigos_dormidos(id_sala))
    motor.activar_enemigos(todos)
    motor.avanzar_hasta_jugador()
    return motor


def _partida_con(acciones: int, k: int, lado: int = LADO) -> ContextoPartida:
    """Una partida sintética con la línea de tiempo (punto de control cada `k`), jugada hasta `acciones` acciones."""
    config = ConfiguracionDTO(offline=True, cache_size=25, checkpoint_cada=k)
    servicio = ServicioPartida(config, fuente=_FuenteSintetica(lado), carpeta_cache=os.path.join(CARPETA, "cache"),
                               carpeta_logs=os.path.join(CARPETA, "logs"))
    contexto = servicio.iniciar_partida("bench_linea", "Bench", semilla=SEMILLA, registrar_bitacora=False)
    _jugar(ServicioLineaTiempo(), contexto, acciones)
    return contexto


def _jugar(servicio: ServicioLineaTiempo, contexto: ContextoPartida, hasta: int) -> None:
    """Juega la secuencia fija (esperar y dar la vuelta a una manzana de salas) hasta que el jugador lleve `hasta` acciones.

    Una acción rechazada no cuenta: se espera y se sigue. La secuencia depende solo de las acciones hechas, así que
    es la misma en todas las partidas con la misma semilla (la historia de n acciones es prefijo de la de n + 1)."""
    while contexto.jugador.acciones < hasta:
        if contexto.motor.terminado:
            raise AssertionError("la partida sintética terminó durante la medición")
        hechas = contexto.jugador.acciones
        servicio.ejecutar(contexto, _CICLO[hechas % len(_CICLO)])
        if contexto.jugador.acciones == hechas:                  # rechazada: una espera siempre se acepta
            servicio.ejecutar(contexto, _ESPERAR)


class _Partidas:
    """Las partidas ya jugadas, por (acciones, K): se juegan una vez y las comparten M1, M2 y M3."""

    def __init__(self) -> None:
        self._guardadas: list[tuple[int, int, ContextoPartida]] = []

    def obtener(self, acciones: int, k: int) -> ContextoPartida:
        for cantidad, tope, contexto in self._guardadas:
            if cantidad == acciones and tope == k:
                return contexto
        contexto = _partida_con(acciones, k)
        self._guardadas.append((acciones, k, contexto))
        return contexto

    def liberar(self) -> None:
        self._guardadas.clear()


class _Compartidas:
    """Usa las partidas que le pasan, o crea las suyas y las libera (junto con la carpeta temporal) al terminar."""

    def __init__(self, partidas: "_Partidas | None") -> None:
        self._propias = partidas is None
        self._partidas = _Partidas() if partidas is None else partidas

    def __enter__(self) -> "_Partidas":
        return self._partidas

    def __exit__(self, *_) -> None:
        if self._propias:
            self._partidas.liberar()
            _borrar_carpeta(CARPETA)


# ====================================================================== auxiliares
def _borrar_carpeta(carpeta: str) -> None:
    """Borra la carpeta temporal con todo lo que tenga adentro (solo con os)."""
    if not os.path.isdir(carpeta):
        return
    for raiz, carpetas, archivos in os.walk(carpeta, topdown=False):
        for nombre in archivos:
            os.remove(os.path.join(raiz, nombre))
        for nombre in carpetas:
            os.rmdir(os.path.join(raiz, nombre))
    os.rmdir(carpeta)
