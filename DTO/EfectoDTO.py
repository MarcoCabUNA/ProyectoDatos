from dataclasses import dataclass


@dataclass(frozen=True)
class EfectoDTO:
    tipo: str
    restante: int
    valor: int | None = None