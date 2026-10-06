from dataclasses import dataclass

@dataclass(frozen=True)
class  FichaEnemigoDTO:
    id: str
    nombre: str
    vida_max: int
    ataque: int
    defensa: int
    velocidad: int
    comportamiento: str
    suelta: list

    @classmethod
    def desde_diccionario(cls, d):
        return cls(
            d["id"],
            d["nombre"],
            d["vida_max"],
            d["ataque"],
            d["defensa"],
            d["velocidad"],
            d["comportamiento"],
            list(d.get("suelta") or []),
        )

    def a_diccionario(self):
        return {
            "id": self.id,
            "clase": "enemigo",
            "nombre": self.nombre,
            "vida_max": self.vida_max,
            "ataque": self.ataque,
            "defensa": self.defensa,
            "velocidad": self.velocidad,
            "comportamiento": self.comportamiento,
            "suelta": list(self.suelta),
        }