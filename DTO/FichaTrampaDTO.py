from dataclasses import dataclass


@dataclass(frozen=True)
class TrapFichaTrampaDTO:
    Id: str
    Name: str
    Damage: int
    Rearm: int

    @classmethod
    def desde_diccionario(cls, Dicionary):
        return cls(
            Dicionary["id"],
            Dicionary["nombre"],
            Dicionary["daño"],
            300 if Dicionary.get("rearme") is None else Dicionary["rearme"]
        )

    def a_diccionario(self):
        return {
            "id": self.Id,
            "clase": "trampa",
            "nombre": self.Name,
            "daño": self.Damage,
            "rearme": self.Rearm
        }