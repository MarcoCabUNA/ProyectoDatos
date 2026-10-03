from dataclasses import dataclass


@dataclass(frozen=True)
class Trap: 
    def __init__(self, id, name, damage, rearme):
        str_Id = id
        str_Name = name
        int_damage = damage
        int_reareme = rearme