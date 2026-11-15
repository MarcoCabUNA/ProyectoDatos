"""
Ayudantes de prueba de la feature 002 (mapa conocido, memoria de puertas y antorcha). No es un archivo de pruebas.

Se apoyan en tests/ayudas_terreno.py (salida, salida_sin_vuelta, mazmorra_con_costos, motor_con), sin modificarlo.

- Notación de la spec: las salas se nombran con letras, A = 1, B = 2, … (constantes A a M y X de este módulo).
- cripta_mapa(cantidad, salidas): una Mazmorra armada a mano con salidas con y sin vuelta y con costo en las dos
  caras, en una sola o en ninguna (las tuplas de tests/ayudas_terreno.py).
- cara_cerrada_sin_llave(mazmorra, a, b): deja cerrada solo la cara de a de la puerta a–b (escenario H2-6).
- JugadorPrueba(sala): un objeto con Sala_Actual, para usar MapaConocido sin motor.
- mapa_de_prueba(mazmorra, sala_jugador, historial=None): (MapaConocido, JugadorPrueba).
- estados(mapa): (list(mapa.estado), list(mapa.caras)), para comparar casilla por casilla.
- entrar_a(mapa, jugador, sala, antorcha=False): mueve al jugador de prueba y llama a mapa.entrar, como el motor.
- casillas_distintas(antes, despues): cuántas casillas cambiaron entre dos estados(mapa).
- motor_con_inventario(mazmorra, sala_jugador, objetos=()): (motor, mensajes) de motor_con con un Inventario
  enlazado al historial y los objetos dados ya recogidos, sin llamar a iniciar (T031).

Ninguna cripta de ejemplo usa datos de una cripta publicada (Principio VI): todas se arman aquí con letras.
"""
from DTO.Direcciones import E as ESTE, N as NORTE, O as OESTE, S as SUR  # noqa: F401  (se reexportan)
from tests.ayudas_terreno import mazmorra_con_costos, motor_con, salida, salida_sin_vuelta  # noqa: F401  (se reexportan)

# Salas con la notación de la spec: A = 1, B = 2, …, M = 13, y X = 24 (la «sala X» de los escenarios).
# Las direcciones se llaman NORTE, SUR, ESTE y OESTE para no chocar con las salas E y las letras N, O y S.
A, B, C, D, E, F, G, H, I, J, K, L, M = range(1, 14)
X = 24


def cripta_mapa(cantidad: int, salidas: list[tuple]):
    """
    Mazmorra con las salas 1..cantidad (A..) y las salidas dadas, con todo el contenido marcado como cargado.

    Cada salida es una tupla de tests/ayudas_terreno.py: salida(a, d, b, costo) tiene las dos caras con el mismo
    costo; salida_sin_vuelta(a, d, b) solo la cara de a; la tupla larga (a, d, b, costo_a, costo_b, cerrada) deja
    poner el costo en una sola cara o en ninguna.
    """
    return mazmorra_con_costos(cantidad, salidas)


def cara_cerrada_sin_llave(mazmorra, a: int, b: int) -> None:
    """Deja cerrada solo la cara de a de la puerta a–b (la cara de b hacia a no cambia). Para H2-6."""
    for salida_a in mazmorra.sala(a).salidas:
        if salida_a is not None and salida_a.destino == b:
            salida_a.cerrada = True
            salida_a.llave = None
            return
    raise ValueError(f"la sala {a} no tiene una salida hacia la sala {b}")


class JugadorPrueba:
    """Lo único que MapaConocido lee del jugador: la sala en la que está."""

    def __init__(self, sala: int):
        self.Sala_Actual = sala


def mapa_de_prueba(mazmorra, sala_jugador: int, historial=None):
    """(MapaConocido, JugadorPrueba) sobre la mazmorra, con el jugador en sala_jugador. No llama a iniciar."""
    from Logic.MapaConocido import MapaConocido     # hasta T012 no existe: es el fallo esperado de las pruebas
    jugador = JugadorPrueba(sala_jugador)
    return MapaConocido(mazmorra, jugador, historial), jugador


def estados(mapa) -> tuple[list[int], list[int]]:
    """Copia de los dos arreglos del mapa: (estado de cada sala, estado recordado de cada cara)."""
    return list(mapa.estado), list(mapa.caras)


def entrar_a(mapa, jugador, sala: int, antorcha: bool = False) -> None:
    """Lo que hace el motor al mover al jugador: primero cambia Sala_Actual y después llama a mapa.entrar."""
    jugador.Sala_Actual = sala
    mapa.entrar(sala, antorcha)


def casillas_distintas(antes: tuple[list[int], list[int]], despues: tuple[list[int], list[int]]) -> int:
    """Cuántas casillas (de estado y de caras) difieren entre dos resultados de estados(mapa)."""
    distintas = 0
    for i in range(2):
        for j in range(len(antes[i])):
            if antes[i][j] != despues[i][j]:
                distintas += 1
    return distintas


def motor_con_inventario(mazmorra, sala_jugador: int, objetos=()):
    """
    (motor, mensajes) de motor_con, con un Inventario de 5 lugares enlazado al historial del motor y los objetos
    (ObjetoDTO) ya recogidos. No llama a iniciar: lo recogido antes de la primera acción no se puede deshacer.
    """
    from Logic.Inventario import Inventario
    motor, mensajes = motor_con(mazmorra, sala_jugador)
    inventario = Inventario(5)
    inventario.historial = motor.historial
    motor.inventario = inventario
    for objeto in objetos:
        inventario.recoger(objeto)
    return motor, mensajes
