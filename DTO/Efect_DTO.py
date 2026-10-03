from dataclasses import dataclass

@dataclass(frozen=True)
class Efect:
    def __init__(self, name, damage, R_Time):
        str_type = name
        int_Damage = damage
        int_Time = R_Time