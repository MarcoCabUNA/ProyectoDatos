"""
MapaConocidoDTO (integrante 2, feature 002): constantes y DTO del mapa conocido (data-model §1, §4 y §5).

Las constantes viven aquí porque las leen Lógica (MapaConocido), Datos (al validar el binario) y la Vista; ningún
otro módulo define estos valores. Este archivo no importa nada del proyecto.

DTO de la vista (solo lectura, los arma MapaConocido.a_dto):
    MapaConocidoDTO    -> las salas exploradas, en orden creciente de id
    SalaConocidaDTO    -> una sala explorada: id, nombre y sus 4 salidas
    SalidaConocidaDTO  -> una salida vista desde una sala explorada: costo igualado, estado recordado y destino
DTO guardado (lo copian PartidaGuardada y la línea de tiempo; lo escribe GuardadoBinario):
    MapaConocidoGuardadoDTO -> copia de los dos arreglos del mapa

No hay campos de contenido (enemigos, objetos, trampas) ni de estado real. Si en el futuro se agregan campos, van al
final y con valor por defecto. Las colecciones son arrays (list).
"""
from dataclasses import dataclass

# Estado de una sala (FR-201, FR-204, FR-206).
DESCONOCIDA = 0     # la sala no existe para el jugador
AVISTADA = 1        # no explorada y destino de una salida de una explorada
EXPLORADA = 2       # entró, es la inicial o la exploró la antorcha

# Estado recordado de una cara (FR-208, FR-212). Una cara es una salida vista desde una sala: c = sala * 4 + dirección.
SIN_OBSERVAR = 0    # nunca observada; también toda cara de una dirección sin salida
ABIERTA = 1         # abierta en su última observación
CERRADA = 2         # cerrada en su última observación


@dataclass(frozen=True)
class SalidaConocidaDTO:
    """Una salida vista desde una sala explorada."""
    costo: int              # igualado (001 FR-101, FR-205); nunca el declarado por una sola cara
    estado_puerta: int      # ABIERTA, CERRADA o SIN_OBSERVAR: el RECORDADO de la cara de esta sala
    destino: int | None     # id si el destino está explorado; None si está avistado


@dataclass(frozen=True)
class SalaConocidaDTO:
    """Una sala explorada."""
    id: int                                     # id real (solo de exploradas: une salidas con su destino, H5-5)
    nombre: str
    salidas: list[SalidaConocidaDTO | None]     # 4 posiciones (N, S, E, O); None si no hay salida


@dataclass(frozen=True)
class MapaConocidoDTO:
    """Vista de solo lectura del mapa conocido."""
    salas: list[SalaConocidaDTO]                # solo exploradas, en orden creciente de id


@dataclass(frozen=True)
class MapaConocidoGuardadoDTO:
    """Copia de los dos arreglos de MapaConocido, para el guardado y los puntos de control."""
    estado_salas: list[int]     # copia de MapaConocido.estado (largo S)
    caras: list[int]            # copia de MapaConocido.caras (largo 4·S)

    @classmethod
    def desde_diccionario(cls, d: dict) -> "MapaConocidoGuardadoDTO":
        """Inverso de a_diccionario; copia las dos listas."""
        return cls(list(d["estado_salas"]), list(d["caras"]))

    def a_diccionario(self) -> dict:
        """{"estado_salas": [...], "caras": [...]}, con copias de las listas (comparación JSON contra binario)."""
        return {"estado_salas": list(self.estado_salas), "caras": list(self.caras)}
