from dataclasses import dataclass

from DTO.EstadoJuegoDTO import EstadoJuegoDTO

LLEGO = "llego"
ENEMIGOS = "enemigos"
DANO = "dano"
SIN_RUTA = "sin_ruta"
DESTINO_INVALIDO = "destino_invalido"
YA_AQUI = "ya_aqui"
AMBIGUO = "ambiguo"
INTERRUMPIDO = "interrumpido"
TERMINADA = "terminada"
PASO_RECHAZADO = "paso_rechazado"


@dataclass(frozen=True)
class ViajeDTO:
    destino: int
    nombre_destino: str
    pasos_dados: int
    acciones_esperadas: int


@dataclass(frozen=True)
class InicioViajeDTO:
    viaje: ViajeDTO | None
    motivos: list[str]


@dataclass(frozen=True)
class PasoViajeDTO:
    viaje: ViajeDTO | None
    motivos: list[str]
    estado: EstadoJuegoDTO
