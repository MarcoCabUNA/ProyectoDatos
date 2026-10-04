from dataclasses import dataclass


@dataclass(frozen=True)
class Efect:
    str_Type: str
    int_Time: int
    int_Value: int | None = None