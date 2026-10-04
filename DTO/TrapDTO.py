from dataclasses import dataclass


@dataclass(frozen=True)
class Trap:
    str_Id: str
    str_Name: str
    int_Damage: int
    int_Rearm: int = 300

    @classmethod
    def From_diccionary(cls, Dicionary):
        return cls(
            Dicionary["id"],
            Dicionary["nombre"],
            Dicionary["daño"],
            Dicionary.get("rearme") or 300,
        )

    def To_diccionary(self):
        return {
            "id": self.str_Id,
            "clase": "trampa",
            "nombre": self.str_Name,
            "daño": self.int_Damage,
            "rearme": self.int_Rearm,
        }