from dataclasses import dataclass


@dataclass(frozen=True)
class FichaTrampaDTO:
    id: str
    nombre: str
    danio: int
    rearme: int

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
            "nombre": self.nombre,
            "daño": self.danio,
            "rearme": self.rearme
        }