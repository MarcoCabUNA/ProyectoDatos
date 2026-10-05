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
    def desde_diccionario(cls, Dicionary):
        return cls(
            Dicionary["id"],
            Dicionary["nombre"],
            Dicionary["vida_max"],
            Dicionary["ataque"],
            Dicionary["defensa"],
            Dicionary["velocidad"],
            Dicionary["comportamiento"],
            list(Dicionary.get("suelta") or []),
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