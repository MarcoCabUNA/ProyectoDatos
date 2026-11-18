"""ViajeDTO (DTO, feature 002): el viaje de «ir a» en curso y lo que devuelven su inicio y cada paso."""
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
    """Un viaje en curso: el destino, cuántos pasos lleva y las acciones del jugador que se esperan."""
    destino: int
    nombre_destino: str
    pasos_dados: int
    acciones_esperadas: int


@dataclass(frozen=True)
class InicioViajeDTO:
    """El resultado de pedir «ir a»: el viaje, o None con los motivos por los que no empieza."""
    viaje: ViajeDTO | None
    motivos: list[str]


@dataclass(frozen=True)
class PasoViajeDTO:
    """El resultado de un paso: el viaje que sigue (None si se detuvo), los motivos y el estado del juego."""
    viaje: ViajeDTO | None
    motivos: list[str]
    estado: EstadoJuegoDTO
