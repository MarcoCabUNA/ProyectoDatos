"""
Ayudantes de prueba de la feature 001 (terreno con costo por salida y cazador). No es un archivo de pruebas.

- Criptas pequeñas con costos declarados en uno, en los dos o en ningún lado de cada salida (FR-101).
- Una cuadrícula de n x n salas con costos al azar, iguales en los dos lados (para pruebas de equivalencia).
- Fichas de cazador, errante y rastreador, y un motor listo para usar.
- FuenteConFichaInvalida: una fuente de prueba cuya sala trae un cazador con la ficha sin `rango` (FR-122, T054).
- FuenteConObjetoInvalido y FuenteConBotinInvalido: un objeto con `duracion` inválida en el suelo de una sala
  (H2-21) o en la `suelta` de un enemigo de una sala (H2-22) (FR-122).

Una salida se describe con una tupla (sala_a, direccion_a, sala_b, costo_a, costo_b, cerrada[, con_vuelta]):
costo_a es lo que declara el lado de sala_a y costo_b lo que declara el lado de sala_b (None = no lo declara).
Si con_vuelta es False, solo existe la cara de sala_a.
"""
import os
import random
import sys
from dataclasses import replace

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.CriptaDTO import CriptaDTO  # noqa: E402
from DTO.Direcciones import E, N, O, S  # noqa: E402
from DTO.FichaEnemigoDTO import FichaEnemigoDTO  # noqa: E402
from DTO.ObjetoDTO import ObjetoDTO  # noqa: E402
from DTO.SalaDTO import EnemigoEnSalaDTO, SalaDTO, SalidaDTO  # noqa: E402
from Logic.Enemigo import Enemigo  # noqa: E402
from Logic.jugador import Jugador  # noqa: E402
from Logic.Mazmorra import Mazmorra  # noqa: E402
from Logic.motorJuego import Motor  # noqa: E402

from tests.Utilidades import FuenteCuadricula, salas_cuadricula  # noqa: E402

# Dirección opuesta de cada índice N, S, E, O.
OPUESTA = [S, N, O, E]

LLAVE_FINAL = "llave_final"


def salida(sala_a: int, direccion_a: int, sala_b: int, costo: int | None = None,
           cerrada: bool = False) -> tuple:
    """Atajo: una salida con las dos caras y el mismo costo declarado en los dos lados."""
    return (sala_a, direccion_a, sala_b, costo, costo, cerrada, True)


def salida_sin_vuelta(sala_a: int, direccion_a: int, sala_b: int, costo: int | None = None,
                      cerrada: bool = False) -> tuple:
    """Una salida que solo existe del lado de sala_a (la sala_b no tiene la cara de vuelta)."""
    return (sala_a, direccion_a, sala_b, costo, None, cerrada, False)


def salidas_con_costos(cantidad: int, salidas: list[tuple]) -> list[SalaDTO]:
    """
    Arma las salas 1..cantidad con las salidas dadas. Para cada tupla crea la cara de sala_a y, si tiene
    vuelta, la cara de sala_b en la dirección opuesta. Lanza ValueError si una dirección se usa dos veces.
    """
    caras: list[list[SalidaDTO | None]] = []
    for _ in range(cantidad + 1):
        caras.append([None, None, None, None])
    for tupla in salidas:
        sala_a, direccion_a, sala_b, costo_a, costo_b, cerrada = tupla[:6]
        con_vuelta = tupla[6] if len(tupla) > 6 else True
        _poner_cara(caras, sala_a, direccion_a, SalidaDTO(sala_b, cerrada, costo=costo_a))
        if con_vuelta:
            _poner_cara(caras, sala_b, OPUESTA[direccion_a], SalidaDTO(sala_a, cerrada, costo=costo_b))
    salas = []
    for id_sala in range(1, cantidad + 1):
        salas.append(SalaDTO(id_sala, f"Sala {id_sala}", caras[id_sala], "1"))
    return salas


def _poner_cara(caras: list, id_sala: int, direccion: int, cara: SalidaDTO) -> None:
    if caras[id_sala][direccion] is not None:
        raise ValueError(f"La sala {id_sala} ya tiene una salida en la dirección {direccion}")
    caras[id_sala][direccion] = cara


def cuadricula_con_costos(n: int, azar: random.Random) -> list[SalaDTO]:
    """
    Las salas de salas_cuadricula(n) (mismos ids y vecinas), con un costo entre 1 y 300 en cada salida,
    sacado de 'azar' una vez por par de salas y declarado igual en los dos lados.
    """
    salas = salas_cuadricula(n)
    for sala in salas:                        # los ids van de 1 a n*n, en orden: salas[id - 1]
        for direccion in range(4):
            cara = sala.salidas[direccion]
            if cara is None or cara.sala_destino < sala.id:
                continue                      # el par ya se sorteó desde la otra sala
            costo = azar.randint(1, 300)
            sala.salidas[direccion] = replace(cara, costo=costo)
            vecina = salas[cara.sala_destino - 1]
            vuelta = vecina.salidas[OPUESTA[direccion]]
            assert vuelta is not None and vuelta.sala_destino == sala.id
            vecina.salidas[OPUESTA[direccion]] = replace(vuelta, costo=costo)
    return salas


def mazmorra_con_costos(cantidad: int, salidas: list[tuple]) -> Mazmorra:
    """Mazmorra con las salas 1..cantidad, todo el contenido marcado como cargado. La salida es la última sala."""
    mazmorra = Mazmorra(sala_salida=cantidad, llave_salida=LLAVE_FINAL)
    mazmorra.cargar_esqueleto(salidas_con_costos(cantidad, salidas))
    for id_sala in range(1, cantidad + 1):
        mazmorra.sala(id_sala).contenido_cargado = True
    return mazmorra


def _ficha(comportamiento: str, velocidad: int, cambios: dict) -> FichaEnemigoDTO:
    datos = dict(id=comportamiento, nombre=comportamiento.capitalize(), vida_max=10, ataque=3, defensa=1,
                 velocidad=velocidad, comportamiento=comportamiento, suelta=[])
    datos.update(cambios)
    return FichaEnemigoDTO(**datos)


def ficha_cazador(rango: int | None, velocidad: int = 100, **cambios) -> FichaEnemigoDTO:
    """Ficha de un cazador. Necesita FichaEnemigoDTO.rango (T021): antes de esa tarea, llamarla falla."""
    cambios["rango"] = rango
    return _ficha("cazador", velocidad, cambios)


def ficha_errante(velocidad: int = 100, **cambios) -> FichaEnemigoDTO:
    """Ficha de un errante."""
    return _ficha("errante", velocidad, cambios)


def ficha_rastreador(velocidad: int = 100, **cambios) -> FichaEnemigoDTO:
    """Ficha de un rastreador."""
    return _ficha("rastreador", velocidad, cambios)


def motor_con(mazmorra: Mazmorra, sala_jugador: int, semilla: int = 1) -> tuple[Motor, list]:
    """(motor, mensajes) como crear_motor de tests/test_logica.py, con el jugador en sala_jugador."""
    cripta = CriptaDTO(id="c-terreno", version="1", salas_total=len(mazmorra.salas) - 1, paginas=1,
                       salas_por_pagina=50, sala_inicial=sala_jugador, sala_salida=mazmorra.sala_salida,
                       llave_salida=mazmorra.llave_salida, presupuesto_solicitudes=10, inventario_max=5,
                       jugador_vida_max=30, jugador_ataque=5, jugador_defensa=2, jugador_velocidad=100)
    mensajes: list = []
    motor = Motor(semilla, Jugador(cripta), mazmorra, mensajes.append)
    return motor, mensajes


def poner_enemigo(motor: Motor, sala: int, ficha: FichaEnemigoDTO, instancia: str = "e-1",
                  vida: int | None = None, numero: int = 1) -> Enemigo:
    """Coloca un enemigo en 'sala' y lo activa con motor.activar_enemigos (programa su primera acción)."""
    enemigo = Enemigo(ficha, instancia, vida, numero, sala)
    motor.mazmorra.sala(sala).enemigos.append(enemigo)
    motor.activar_enemigos([enemigo])
    return enemigo


ID_CAZADOR_SIN_RANGO = "ent_cazador_sin_rango"


class FuenteConFichaInvalida(FuenteCuadricula):
    """
    FR-122 (T054): la sala 'sala_cazador' trae un cazador cuya ficha llega sin 'rango'.

    La fuente NO lanza el error: devuelve el dato inválido, como lo haría el API, y Data lo rechaza con ErrorDatos
    y recuerda la sala. Si la fuente lanzara el error, Data lo trataría como un fallo de red de todo el lote.
    """

    def __init__(self, n: int, sala_cazador: int):
        super().__init__(n)
        self.sala_cazador = sala_cazador
        self.catalogos: list[list[str]] = []     # cada lote pedido a /catalogo, para contar solicitudes

    def obtener_contenido(self, id_cripta, ids_salas):
        contenidos = super().obtener_contenido(id_cripta, ids_salas)
        for c in contenidos:
            if c.sala == self.sala_cazador:
                c.enemigos.append(EnemigoEnSalaDTO("e-1", ID_CAZADOR_SIN_RANGO, 10))
        return contenidos

    def obtener_catalogo(self, ids):
        self.catalogos.append(list(ids))
        return [ficha_cazador(None, id=ID_CAZADOR_SIN_RANGO) for i in ids if i == ID_CAZADOR_SIN_RANGO]


ID_OBJETO_DURACION_INVALIDA = "obj_pocion_duracion_invalida"


class FuenteConObjetoInvalido(FuenteCuadricula):
    """
    FR-122 (T056, escenario H2-21): la sala 'sala_objeto' trae una poción cuya ficha llega con 'duracion' inválida.

    Igual que FuenteConFichaInvalida, la fuente NO lanza el error: devuelve el dato inválido y Data (T055) lo
    rechaza con ErrorDatos y recuerda la sala.
    """

    def __init__(self, n: int, sala_objeto: int, duracion):
        super().__init__(n)
        self.sala_objeto = sala_objeto
        self.duracion = duracion
        self.catalogos: list[list[str]] = []     # cada lote pedido a /catalogo, para contar solicitudes

    def obtener_contenido(self, id_cripta, ids_salas):
        contenidos = super().obtener_contenido(id_cripta, ids_salas)
        for c in contenidos:
            if c.sala == self.sala_objeto:
                c.objetos.append(ID_OBJETO_DURACION_INVALIDA)
        return contenidos

    def obtener_catalogo(self, ids):
        self.catalogos.append(list(ids))
        return [ObjetoDTO(ID_OBJETO_DURACION_INVALIDA, "Poción rara", "pocion", 1, 10,
                          modificador_velocidad=20, duracion=self.duracion)
                for i in ids if i == ID_OBJETO_DURACION_INVALIDA]


ID_ENEMIGO_BOTIN_INVALIDO = "ent_errante_botin_invalido"


class FuenteConBotinInvalido(FuenteCuadricula):
    """
    FR-122 (escenario H2-22, T057): la sala 'sala_enemigo' trae un errante válido cuya ficha suelta la poción de
    FuenteConObjetoInvalido, con 'duracion' inválida. La poción NO está en el suelo de ninguna sala: solo llega
    al catálogo porque ResolvedorCatalogo baja las fichas de 'suelta'. La fuente no lanza el error.
    """

    def __init__(self, n: int, sala_enemigo: int, duracion):
        super().__init__(n)
        self.sala_enemigo = sala_enemigo
        self.duracion = duracion
        self.catalogos: list[list[str]] = []     # cada lote pedido a /catalogo, para contar solicitudes

    def obtener_contenido(self, id_cripta, ids_salas):
        contenidos = super().obtener_contenido(id_cripta, ids_salas)
        for c in contenidos:
            if c.sala == self.sala_enemigo:
                c.enemigos.append(EnemigoEnSalaDTO("e-1", ID_ENEMIGO_BOTIN_INVALIDO, 10))
        return contenidos

    def obtener_catalogo(self, ids):
        self.catalogos.append(list(ids))
        fichas = []
        for id_ficha in ids:
            if id_ficha == ID_ENEMIGO_BOTIN_INVALIDO:
                fichas.append(ficha_errante(id=ID_ENEMIGO_BOTIN_INVALIDO, suelta=[ID_OBJETO_DURACION_INVALIDA]))
            elif id_ficha == ID_OBJETO_DURACION_INVALIDA:
                fichas.append(ObjetoDTO(ID_OBJETO_DURACION_INVALIDA, "Poción rara", "pocion", 1, 10,
                                        modificador_velocidad=20, duracion=self.duracion))
        return fichas


ID_CAZADOR = "ent_cazador"
ID_ERRANTE = "ent_errante"


class FuenteCuadriculaConCazador(FuenteCuadricula):
    """
    FR-118 (T048): una cuadrícula de 4 × 4 con costos entre 1 y 300, iguales en los dos lados
    (cuadricula_con_costos(4, random.Random(semilla))), un cazador en la sala 2 y un errante en la sala 5, con sus
    fichas en el catálogo. Los dos están junto a la sala inicial (la 1), así que se activan pronto.
    """

    def __init__(self, semilla: int, rango: int = 600):
        super().__init__(4)
        self.semilla = semilla
        self.rango = rango

    def obtener_pagina_salas(self, id_cripta, pagina, version):
        return cuadricula_con_costos(4, random.Random(self.semilla))

    def obtener_contenido(self, id_cripta, ids_salas):
        contenidos = super().obtener_contenido(id_cripta, ids_salas)
        for c in contenidos:
            if c.sala == 2:
                c.enemigos.append(EnemigoEnSalaDTO("e-1", ID_CAZADOR))
            elif c.sala == 5:
                c.enemigos.append(EnemigoEnSalaDTO("e-2", ID_ERRANTE))
        return contenidos

    def obtener_catalogo(self, ids):
        fichas = []
        for id_ficha in ids:
            if id_ficha == ID_CAZADOR:
                fichas.append(ficha_cazador(self.rango, id=ID_CAZADOR, nombre="Cazador", vida_max=40))
            elif id_ficha == ID_ERRANTE:
                fichas.append(ficha_errante(id=ID_ERRANTE, nombre="Errante", vida_max=40))
        return fichas
