from dataclasses import dataclass


@dataclass(frozen=True)
class FichaTrampaDTO:
    id: str
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
            "id": self.id,
            "clase": "trampa",
            "nombre": self.Name,
            "daño": self.Damage,
            "rearme": self.Rearm
        }