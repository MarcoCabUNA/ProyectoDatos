from dataclasses import dataclass


@dataclass(frozen=True)
class Actor:
    str_Id: str # instancia de entidad final
    str_Type: str # jugador o enemigo denominado en logica
    str_Name: str
    int_Health: int
    int_max_H: int
    int_Attack: int
    int_Def: int
    int_Velo: int
    int_Room: int

    @classmethod
    def FromDiccionary(cls, Dicionary):
        return cls(
            Dicionary["id"],
            Dicionary["tipo"],
            Dicionary["nombre"],
            Dicionary["vida"],
            Dicionary["vida_max"],
            Dicionary["ataque"],
            Dicionary["defensa"],
            Dicionary["velocidad"],
            Dicionary["sala_actual"],
        )

    def ToDiccionary(self):
        return {
            "id": self.str_Id,
            "tipo": self.str_Type,
            "nombre": self.str_Name,
            "vida": self.int_Health,
            "vida_max": self.int_max_H,
            "ataque": self.int_Attack,
            "defensa": self.int_Def,
            "velocidad": self.int_Velo,
            "sala_actual": self.int_Room,
        }