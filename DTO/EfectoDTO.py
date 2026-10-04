from dataclasses import dataclass


@dataclass(frozen=True)
class EfectoDTO:
    Type: str
    Time: int
    Value: int | None = None