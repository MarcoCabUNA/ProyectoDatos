"""
ValidacionDatos (Integrante 2): datos inválidos de la Parte II (FR-122, T002, T052 y T055).

Aquí están, en un solo lugar, las reglas de FR-122 que le tocan a Datos:
  - costo de una salida: entero >= 1 (un bool NO cuenta como entero);
  - cierre_automatico de una salida, si viene: entero >= 1 (tampoco bool); null o ausente es válido (T055);
  - rango de una ficha con comportamiento "cazador": entero >= 0 (tampoco bool); no puede faltar ni ser null;
  - duracion de la ficha de un objeto, si la trae: entero >= 1 (tampoco bool); null o ausente es válido (T055).
cierre_automatico y duracion programan eventos en la agenda, y la feature 004 supone que nada se programa con
retraso 0. La duracion de un efecto de ficha (EfectoFichaDTO) NO se valida aquí: P1 ya convierte las <= 0 en None.
Las reglas del esqueleto (costo, cierre_automatico y los dos lados de una salida con costos distintos) las
aplica GestorEsqueleto con es_costo_valido() y es_cierre_valido() de este archivo; las de las fichas, error_de_ficha().

ErrorDatos es el "error de datos" que pide el contrato (contracts/contrato-datos.md): el dato llegó,
pero no es válido. Es subclase de ErrorRed para que los 'except ErrorRed' de la Parte 1 (Servicios,
ERRORES_ESPERADOS, main) lo sigan atrapando sin cambiar nada; quien necesite distinguirlo de un fallo
de red pregunta isinstance(error, ErrorDatos).

Datos solo valida (Principio I); no decide reglas del juego. Lógica supone que lo que recibe es válido.
"""
from Data.ClienteHttp import ErrorRed
from DTO.FichaEnemigoDTO import FichaEnemigoDTO
from DTO.ObjetoDTO import ObjetoDTO

COMPORTAMIENTO_CAZADOR = "cazador"


class ErrorDatos(ErrorRed):
    """
    Un dato llegó con un valor inválido (FR-122). No es un fallo de red: volver a pedirlo no lo arregla.
    id_ficha: la ficha rechazada, si el error es de una ficha (None si es del esqueleto).
    """

    def __init__(self, operacion: str, detalle: str, id_ficha: str | None = None):
        super().__init__(operacion, detalle)
        self.id_ficha = id_ficha
        # El texto de ErrorRed empieza con "Falló ...", que suena a la red; este dice qué pasó de verdad.
        self.args = (f"Datos inválidos en '{operacion}': {detalle}",)


def es_entero(valor) -> bool:
    """True solo para int de verdad: True y False son int en Python, pero aquí no cuentan."""
    return isinstance(valor, int) and not isinstance(valor, bool)


def es_costo_valido(costo) -> bool:
    """Costo declarado de una salida (FR-101, FR-122): entero >= 1."""
    return es_entero(costo) and costo >= 1


def es_cierre_valido(cierre) -> bool:
    """cierre_automatico de una salida (FR-122, T055): None (no viene) o un entero >= 1."""
    return cierre is None or (es_entero(cierre) and cierre >= 1)


def error_de_ficha(ficha) -> ErrorDatos | None:
    """
    El ErrorDatos de una ficha inválida, o None si es válida. No lanza: así quien la recibe decide
    qué hacer con la ficha (ResolvedorCatalogo la rechaza y sigue con las demás del lote).
    Reglas (FR-122): el rango de un cazador y la duracion de un objeto (T055). Las demás fichas no se
    revisan aquí: su formato ya lo valida FuenteJson al convertirlas.
    """
    if isinstance(ficha, ObjetoDTO):
        return _error_de_duracion(ficha)
    if not isinstance(ficha, FichaEnemigoDTO) or ficha.comportamiento != COMPORTAMIENTO_CAZADOR:
        return None
    rango = ficha.rango
    if isinstance(rango, int) and not isinstance(rango, bool) and rango >= 0:   # misma regla que es_entero()
        return None
    recibido = "falta o es null" if rango is None else f"se recibió {rango!r}"
    return ErrorDatos(f"ficha {ficha.id}",
                      f"el campo 'rango' de un cazador debe ser un entero >= 0 ({recibido})",
                      id_ficha=ficha.id)


def _error_de_duracion(objeto: ObjetoDTO) -> ErrorDatos | None:
    """T055: la duracion de un objeto, si la trae, es un entero >= 1. Mismo formato de mensaje que el rango."""
    duracion = objeto.duracion
    if duracion is None or (es_entero(duracion) and duracion >= 1):
        return None
    return ErrorDatos(f"ficha {objeto.id}",
                      f"el campo 'duracion' de un objeto debe ser un entero >= 1 (se recibió {duracion!r})",
                      id_ficha=objeto.id)