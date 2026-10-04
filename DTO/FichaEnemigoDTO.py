from dataclasses import dataclass

@dataclass(frozen=True)
class  FichaEnemigoDTO:
    id: str
    Name: str
    max_H: int
    Attack: int
    Def: int
    Velo: int
    Behave: str
    Drops: list

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
            "nombre": self.Name,
            "vida_max": self.max_H,
            "ataque": self.Attack,
            "defensa": self.Def,
            "velocidad": self.Velo,
            "comportamiento": self.Behave,
            "suelta": list(self.Drops),
        }