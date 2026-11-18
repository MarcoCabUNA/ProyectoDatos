"""
Ayudantes de las pruebas de la feature 003 (verificación de resolubilidad, integrante 2). No es un archivo de pruebas.

Notación de la spec (Convenciones): «salida 1–2» es una salida abierta, «puerta 4–5 (B)» una salida cerrada que
requiere la llave B, y las ubicaciones son las de la consulta de llaves (id, sala y, opcionalmente, enemigo).

    abierta(a, d, b)        salida abierta, las dos caras (de a hacia d y la vuelta desde b)
    puerta(a, d, b, llave)  puerta cerrada, las dos caras con la misma llave
    cara(a, d, b, ...)      una sola cara (salidas sin vuelta, caras con llaves distintas, H1-10, H2-9 a H2-11)
    ubic(id, sala, enemigo) una ubicación de llave
    cripta(...)             (CriptaDTO, list[SalaDTO], list[UbicacionLlaveDTO]) con las salas 1..cantidad_salas

Ninguna cripta de estas pruebas usa datos de una cripta publicada (Principio VI): todo se arma a mano.
Aquí se permite lo que el código del juego no puede usar (set, dict, copias): son solo pruebas.
"""
import json
import os
import random

from Data.ClienteHttp import ErrorRed, PresupuestoAgotadoError
from Data.FuenteDatos import FuenteDatos
from DTO.CriptaDTO import CriptaDTO, ResumenCriptaDTO
from DTO.Direcciones import DIRECCIONES, E, N, O, S
from DTO.SalaDTO import ContenidoSalaDTO, SalaDTO, SalidaDTO
from DTO.UbicacionLlaveDTO import UbicacionLlaveDTO
from Logic.Mazmorra import Mazmorra

# Dirección opuesta de cada índice (N <-> S, E <-> O): la cara de vuelta de una salida.
_OPUESTA = [S, N, O, E]

Cara = tuple[int, int, SalidaDTO]   # (sala de origen, dirección, salida declarada por esa cara)


def opuesta(direccion: int) -> int:
    """Dirección de la cara de vuelta."""
    return _OPUESTA[direccion]


# ---------------------------------------------------------------- salidas
def abierta(a: int, direccion: int, b: int, costo: int | None = None) -> list[Cara]:
    """Salida abierta a–b: la cara de a hacia 'direccion' y la de b en la dirección opuesta."""
    return [(a, direccion, SalidaDTO(b, costo=costo)), (b, opuesta(direccion), SalidaDTO(a, costo=costo))]


def puerta(a: int, direccion: int, b: int, llave: str, costo: int | None = None,
           cierre_automatico: int | None = None) -> list[Cara]:
    """«Puerta a–b (llave)»: las dos caras cerradas y con la misma llave."""
    return [(a, direccion, SalidaDTO(b, True, llave, cierre_automatico, costo)),
            (b, opuesta(direccion), SalidaDTO(a, True, llave, cierre_automatico, costo))]


def cara(a: int, direccion: int, b: int, cerrada: bool | None = None, llave: str | None = None,
         cierre_automatico: int | None = None, costo: int | None = None) -> list[Cara]:
    """Una sola cara, la de la sala a. 'cerrada' None significa lo mismo que False (FR-302)."""
    return [(a, direccion, SalidaDTO(b, bool(cerrada), llave, cierre_automatico, costo))]


def ubic(id_llave: str, sala: int, enemigo: str | None = None) -> UbicacionLlaveDTO:
    """Una ubicación de llave, como la entrega la consulta de llaves."""
    return UbicacionLlaveDTO(id_llave, sala, enemigo)


# ---------------------------------------------------------------- cripta
def cripta(cantidad_salas: int, salidas: list[list[Cara]], ubicaciones: list[UbicacionLlaveDTO],
           sala_inicial: int = 1, sala_salida: int = 9, llave_salida: str = "S", version: str = "v1",
           id_cripta: str = "prueba") -> tuple[CriptaDTO, list[SalaDTO], list[UbicacionLlaveDTO]]:
    """
    Arma una cripta con las salas 1..cantidad_salas. 'salidas' es una lista de lo que devuelven abierta, puerta
    y cara. Lanza ValueError si dos salidas ocupan la misma cara (un error de la prueba, no de los datos).
    """
    if not (1 <= sala_inicial <= cantidad_salas and 1 <= sala_salida <= cantidad_salas):
        raise ValueError("sala_inicial y sala_salida deben estar entre 1 y cantidad_salas")
    caras: list[list[SalidaDTO | None]] = [[None, None, None, None] for _ in range(cantidad_salas + 1)]
    for grupo in salidas:
        for origen, direccion, salida in grupo:
            if caras[origen][direccion] is not None:
                raise ValueError(f"la sala {origen} ya tiene una salida {DIRECCIONES[direccion]}")
            caras[origen][direccion] = salida
    salas = [SalaDTO(i, f"Sala {i}", caras[i], version) for i in range(1, cantidad_salas + 1)]
    dto = CriptaDTO(id=id_cripta, version=version, salas_total=cantidad_salas, paginas=1,
                    salas_por_pagina=max(cantidad_salas, 1), sala_inicial=sala_inicial, sala_salida=sala_salida,
                    llave_salida=llave_salida, presupuesto_solicitudes=20, inventario_max=10,
                    jugador_vida_max=30, jugador_ataque=6, jugador_defensa=2, jugador_velocidad=100)
    return dto, salas, list(ubicaciones)


def permutar(lista: list, semilla: int) -> list:
    """Copia barajada con random.Random(semilla) (FR-306: la entrada en otro orden)."""
    copia = list(lista)
    random.Random(semilla).shuffle(copia)
    return copia


# ---------------------------------------------------------------- referencia de FR-305 (SC-304)
def _alcanzables(mazmorra: Mazmorra, inicio: int, llaves: set) -> set:
    """Salas alcanzables desde 'inicio' con salidas abiertas y caras cerradas cuya llave está en 'llaves'."""
    vistas = {inicio}
    pendientes = [inicio]
    while pendientes:
        u = pendientes.pop()
        for d in range(4):
            s = mazmorra.salida(u, d)
            if s is None or s.destino >= len(mazmorra.salas) or mazmorra.salas[s.destino] is None:
                continue
            if s.cerrada and (s.llave is None or s.llave not in llaves):
                continue
            if s.destino not in vistas:
                vistas.add(s.destino)
                pendientes.append(s.destino)
    return vistas


def orden_es_valido(dto: CriptaDTO, salas: list[SalaDTO], ubicaciones: list[UbicacionLlaveDTO],
                    orden: list[str]) -> bool:
    """
    Comprueba FR-305 recorriendo el orden llave por llave, con un recorrido aparte armado a mano: cada llave está
    en una sala alcanzable con las llaves anteriores; no hay repetidas; están todas las obtenibles; y con todas se
    entra a sala_salida por una cara cerrada que pide llave_salida (FR-304). Las caras se combinan con Mazmorra.
    """
    mazmorra = Mazmorra(dto.sala_salida, dto.llave_salida)
    mazmorra.cargar_esqueleto(salas)
    tenidas: set = set()
    for llave in orden:
        if llave in tenidas:
            return False
        region = _alcanzables(mazmorra, dto.sala_inicial, tenidas)
        if not any(u.id == llave and u.sala in region for u in ubicaciones):
            return False
        tenidas.add(llave)
    region = _alcanzables(mazmorra, dto.sala_inicial, tenidas)
    if any(u.sala in region and u.id not in tenidas for u in ubicaciones):
        return False                                 # falta una llave obtenible
    if dto.llave_salida not in tenidas:
        return False
    for u in region:
        for d in range(4):
            s = mazmorra.salida(u, d)
            if s is not None and s.destino == dto.sala_salida and s.cerrada and s.llave == dto.llave_salida:
                return True
    return False


# ---------------------------------------------------------------- fuente falsa
class FuenteConLlaves(FuenteDatos):
    """
    FuenteDatos falsa (como FuenteCuadricula de tests/Utilidades.py) que entrega la cripta, su esqueleto y la
    ubicación de las llaves, y cuenta las solicitudes por operación. 'falla_llaves' hace fallar obtener_llaves:
    "presupuesto" (PresupuestoAgotadoError), "429" (ErrorRed con código 429) o "red" (ErrorRed sin código).
    'inexistente' hace que obtener_datos_generales responda 404, como el servicio con una cripta que no existe.
    """

    def __init__(self, dto: CriptaDTO, salas: list[SalaDTO], ubicaciones: list[UbicacionLlaveDTO],
                 falla_llaves: str | None = None, inexistente: bool = False):
        self.cripta = dto
        self.salas = list(salas)
        self.ubicaciones = list(ubicaciones)
        self.falla_llaves = falla_llaves
        self.inexistente = inexistente
        self.pedidos_generales = 0
        self.pedidos_esqueleto = 0
        self.pedidos_contenido = 0
        self.pedidos_catalogo = 0
        self.pedidos_llaves = 0

    def listar_criptas(self) -> list[ResumenCriptaDTO]:
        return [ResumenCriptaDTO(self.cripta.id, "Prueba", self.cripta.salas_total, 1)]

    def obtener_datos_generales(self, id_cripta: str) -> CriptaDTO:
        self.pedidos_generales += 1
        if self.inexistente or id_cripta != self.cripta.id:
            raise ErrorRed(f"datos generales de {id_cripta}", "Crypt not found", 404)
        return self.cripta

    def obtener_version_cripta(self, id_cripta: str) -> str:
        return self.cripta.version

    def obtener_pagina_salas(self, id_cripta: str, pagina: int, version: str) -> list[SalaDTO]:
        self.pedidos_esqueleto += 1
        return list(self.salas)

    def obtener_contenido(self, id_cripta: str, ids_salas: list[int]) -> list[ContenidoSalaDTO]:
        self.pedidos_contenido += 1
        return [ContenidoSalaDTO(i) for i in ids_salas]

    def obtener_version_catalogo(self) -> str:
        return "v"

    def obtener_catalogo(self, ids: list[str]) -> list:
        self.pedidos_catalogo += 1
        return []

    def obtener_llaves(self, id_cripta: str) -> list[UbicacionLlaveDTO]:
        self.pedidos_llaves += 1
        op = f"ubicación de llaves de {id_cripta}"
        if self.falla_llaves == "presupuesto":
            raise PresupuestoAgotadoError(op, f"se alcanzó el presupuesto de {self.cripta.presupuesto_solicitudes} "
                                              f"solicitudes")
        if self.falla_llaves == "429":
            raise ErrorRed(op, "límite de frecuencia excedido 6 veces seguidas", 429)
        if self.falla_llaves == "red":
            raise ErrorRed(op, "no se pudo conectar al servidor (simulado)")
        return list(self.ubicaciones)

    def solicitudes_realizadas(self) -> int:
        return (self.pedidos_generales + self.pedidos_esqueleto + self.pedidos_contenido + self.pedidos_catalogo
                + self.pedidos_llaves)

    def presupuesto_solicitudes(self) -> int | None:
        return self.cripta.presupuesto_solicitudes


# ---------------------------------------------------------------- paquete offline
def _escribir_json(ruta: str, datos) -> None:
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def paquete_temporal(carpeta: str, dto: CriptaDTO, salas: list[SalaDTO],
                     ubicaciones: list[UbicacionLlaveDTO] | None) -> str:
    """
    Escribe en 'carpeta' un paquete offline con el formato de Data/DescargadorPaquete.py (las respuestas del API tal
    cual) y devuelve la carpeta. Si 'ubicaciones' es None, el paquete queda SIN llaves.json (H3-7). llaves.json
    tiene el formato de contracts/contrato-llaves.md.
    """
    carpeta_cripta = os.path.join(carpeta, dto.id)
    os.makedirs(carpeta_cripta, exist_ok=True)
    _escribir_json(os.path.join(carpeta, "criptas.json"),
                   {"criptas": [ResumenCriptaDTO(dto.id, "Prueba", dto.salas_total, 1).a_diccionario()]})
    _escribir_json(os.path.join(carpeta, "catalogo_version.json"), {"version": "v"})
    _escribir_json(os.path.join(carpeta, "catalogo.json"), {"entidades": []})
    _escribir_json(os.path.join(carpeta_cripta, "general.json"), dto.a_diccionario())
    _escribir_json(os.path.join(carpeta_cripta, "salas_p1.json"),
                   {"pagina": 1, "total_paginas": 1, "salas": [s.a_diccionario()["esqueleto"] for s in salas]})
    _escribir_json(os.path.join(carpeta_cripta, "contenido.json"),
                   {"contenido": [ContenidoSalaDTO(s.id).a_diccionario() for s in salas]})
    if ubicaciones is not None:
        _escribir_json(os.path.join(carpeta_cripta, "llaves.json"),
                       {"llaves": [u.a_diccionario() for u in ubicaciones]})
    return carpeta
