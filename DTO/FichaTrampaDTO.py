from dataclasses import dataclass


@dataclass(frozen=True)
class FichaTrampaDTO:
    id: str
    nombre: str
    danio: int     # en el JSON del API la clave es "daño"
    rearme: int    # si viene null en el catálogo, se usa 300

    @classmethod
    def desde_diccionario(cls, d):
        return cls(
            d["id"],
            d["nombre"],
            d["daño"],
            300 if d.get("rearme") is None else d["rearme"],
        )

    def a_diccionario(self):
        return {
            "id": self.id,
            "clase": "trampa",
            "nombre": self.nombre,
            "daño": self.danio,
            "rearme": self.rearme,
        }