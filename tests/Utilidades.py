"""
Utilidades compartidas por las pruebas (no es un archivo de pruebas).

- Lee los datos REALES del API desde paquete/ (el que está en el repositorio).
- ApiFalsa: imita al servidor usando esos datos; responde cualquier lote y lo devuelve
  en orden INVERTIDO a propósito, para comprobar que nuestro código reordena.
- FuenteCuadricula: una cripta inventada de N x N salas, para probar criptas grandes.
"""
import json
import os
from typing import cast

from Data.ClienteHttp import ClienteHttp, PresupuestoAgotadoError
from Data.DescargadorPaquete import DescargadorPaquete
from Data.FuenteRed import FuenteRed
from Data.GestorEsqueleto import GestorEsqueleto
from Data.FuenteDatos import FuenteDatos
from DTO.CriptaDTO import CriptaDTO
from DTO.SalaDTO import ContenidoSalaDTO, SalaDTO, SalidaDTO

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAQUETE = os.path.join(RAIZ, "paquete")
ID_CRIPTA = "cripta-01"


def leer_paquete(*partes):
    with open(os.path.join(PAQUETE, *partes), encoding="utf-8") as f:
        return json.load(f)


def general_real() -> dict:
    return leer_paquete(ID_CRIPTA, "general.json")


def pagina_real() -> dict:
    return leer_paquete(ID_CRIPTA, "salas_p1.json")


def contenido_real() -> list:
    return leer_paquete(ID_CRIPTA, "contenido.json")["contenido"]


def catalogo_real() -> list:
    return leer_paquete("catalogo.json")["entidades"]


def ficha_real(id_ficha: str) -> dict:
    for f in catalogo_real():
        if f["id"] == id_ficha:
            return f
    raise KeyError(id_ficha)


def _parametro(parametros, nombre):
    for clave, valor in parametros:
        if clave == nombre:
            return str(valor)
    raise KeyError(nombre)


class ApiFalsa:
    """
    Imita a ClienteHttp (mismos métodos) sin red. Por defecto sirve la cripta real del
    paquete. Cuenta solicitudes y guarda cada pedido en 'pedidos' para revisarlos.
    'falla_en': número de solicitud (0, 1, ...) en la que lanza PresupuestoAgotadoError.
    """

    def __init__(self, criptas=None, generales=None, paginas=None, contenidos=None,
                 catalogo=None, version_catalogo=None, falla_en=None):
        self.criptas = criptas if criptas is not None else leer_paquete("criptas.json")
        self.generales = generales if generales is not None else {ID_CRIPTA: general_real()}
        self.paginas = paginas if paginas is not None else {ID_CRIPTA: [pagina_real()]}
        self.contenidos = contenidos if contenidos is not None else {ID_CRIPTA: contenido_real()}
        self.catalogo = catalogo if catalogo is not None else catalogo_real()
        self.version_catalogo = (version_catalogo if version_catalogo is not None
                                 else leer_paquete("catalogo_version.json")["version"])
        self.falla_en = falla_en
        self.solicitudes_realizadas = 0
        self.presupuesto = None
        self.pedidos = []

    def fijar_presupuesto(self, presupuesto):
        self.presupuesto = presupuesto

    def get_json(self, ruta, operacion, parametros=()):
        if self.falla_en is not None and self.solicitudes_realizadas == self.falla_en:
            self.solicitudes_realizadas += 1
            raise PresupuestoAgotadoError(operacion, "presupuesto agotado (simulado)")
        self.solicitudes_realizadas += 1
        self.pedidos.append((ruta, tuple(parametros)))
        if ruta == "criptas":
            return self.criptas
        if ruta == "catalogo/version":
            return {"version": self.version_catalogo}
        if ruta == "catalogo":
            ids = _parametro(parametros, "ids").split(",")
            assert 1 <= len(ids) <= 10, "el API acepta de 1 a 10 ids"
            elegidas = [f for f in self.catalogo if f["id"] in ids]
            return {"entidades": elegidas[::-1]}
        partes = ruta.split("/")
        id_cripta = partes[1]
        if len(partes) == 2:
            return self.generales[id_cripta]
        if partes[2] == "version":
            return {"id": id_cripta, "version": self.generales[id_cripta]["version"]}
        if partes[2] == "salas":
            return self.paginas[id_cripta][int(_parametro(parametros, "pagina")) - 1]
        if partes[2] == "contenido":
            ids = [int(x) for x in _parametro(parametros, "salas").split(",")]
            assert 1 <= len(ids) <= 10, "el API acepta de 1 a 10 salas"
            elegidos = [c for c in self.contenidos[id_cripta] if c["sala"] in ids]
            return {"contenido": elegidos[::-1]}
        raise AssertionError(f"ruta inesperada: {ruta}")

    def rutas(self):
        return [r for r, _ in self.pedidos]


# ---------------------------------------------------------------- cripta grande inventada
def id_cuadricula(fila: int, columna: int, n: int) -> int:
    return fila * n + columna + 1


def salas_cuadricula(n: int, version: str = "v") -> list[SalaDTO]:
    """n x n salas; cada una conecta con sus vecinas N, S, E, O (como un tablero)."""
    salas = []
    for f in range(n):
        for c in range(n):
            salidas: list[SalidaDTO | None] = [None, None, None, None]
            if f > 0:
                salidas[0] = SalidaDTO(id_cuadricula(f - 1, c, n))
            if f < n - 1:
                salidas[1] = SalidaDTO(id_cuadricula(f + 1, c, n))
            if c < n - 1:
                salidas[2] = SalidaDTO(id_cuadricula(f, c + 1, n))
            if c > 0:
                salidas[3] = SalidaDTO(id_cuadricula(f, c - 1, n))
            salas.append(SalaDTO(id_cuadricula(f, c, n), f"Sala {id_cuadricula(f, c, n)}", salidas, version))
    return salas


def cripta_cuadricula(n: int) -> CriptaDTO:
    return CriptaDTO(id="cuadricula", version="v", salas_total=n * n, paginas=1, salas_por_pagina=50,
                     sala_inicial=1, sala_salida=n * n, llave_salida="itm_llave",
                     presupuesto_solicitudes=99, inventario_max=10, jugador_vida_max=30,
                     jugador_ataque=6, jugador_defensa=2, jugador_velocidad=100)


class FuenteCuadricula(FuenteDatos):
    """FuenteDatos inventada (n x n salas). Guarda cada lote de contenido pedido."""

    def __init__(self, n: int, falla_en=None):
        self.n = n
        self.lotes: list[list[int]] = []
        self.falla_en = falla_en   # índice del lote de contenido que falla

    def listar_criptas(self):
        return []

    def obtener_datos_generales(self, id_cripta):
        return cripta_cuadricula(self.n)

    def obtener_version_cripta(self, id_cripta):
        return "v"

    def obtener_pagina_salas(self, id_cripta, pagina, version):
        return salas_cuadricula(self.n, version)

    def obtener_contenido(self, id_cripta, ids_salas):
        assert 1 <= len(ids_salas) <= 10
        if self.falla_en is not None and len(self.lotes) == self.falla_en:
            self.falla_en = None
            raise PresupuestoAgotadoError("contenido", "presupuesto agotado (simulado)")
        self.lotes.append(list(ids_salas))
        return [ContenidoSalaDTO(i) for i in ids_salas]

    def obtener_version_catalogo(self):
        return "v"

    def obtener_catalogo(self, ids):
        return []


# ---------------------------------------------------------------- ayudas para las pruebas
def fuente_red(api: ApiFalsa) -> FuenteRed:
    """FuenteRed que usa la ApiFalsa en lugar de la red (tiene los mismos métodos que ClienteHttp)."""
    return FuenteRed(cast(ClienteHttp, api))


def descargador(carpeta: str, api: ApiFalsa) -> DescargadorPaquete:
    return DescargadorPaquete(carpeta, cast(ClienteHttp, api))


def sala_de(esqueleto: GestorEsqueleto, id_sala: int) -> SalaDTO:
    """obtener_sala() puede devolver None; en las pruebas la sala siempre debe existir."""
    sala = esqueleto.obtener_sala(id_sala)
    assert sala is not None, f"la sala {id_sala} debería existir"
    return sala


def destino(sala: SalaDTO, direccion: int) -> int:
    salida = sala.salidas[direccion]
    assert salida is not None, f"la sala {sala.id} debería tener salida en la dirección {direccion}"
    return salida.sala_destino