from dataclasses import dataclass

@dataclass(frozen=True)
class Enemy:
    str_Id: str
    str_Name: str
    int_max_H: int
    int_Attack: int
    int_Def: int
    int_Velo: int
    str_Behave: str
    list_Drops: list

    @classmethod
    def From_diccionary(cls, Dicionary):
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

    def To_diccionary(self):
        return {
            "id": self.str_Id,
            "clase": "enemigo",
            "nombre": self.str_Name,
            "vida_max": self.int_max_H,
            "ataque": self.int_Attack,
            "defensa": self.int_Def,
            "velocidad": self.int_Velo,
            "comportamiento": self.str_Behave,
            "suelta": list(self.list_Drops),
        }