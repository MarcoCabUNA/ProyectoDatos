from dataclasses import dataclass

@dataclass(frozen=True)
class Enemy: 
    def __init__(self, id, name, healt, attack, _def, velo, behave, drops ):
        str_Id = id 
        str_Name = name
        int_max_H = healt
        int_Attack = attack
        int_Def = _def
        int_Velo = velo
        str_Behave = behave
        list_Drops = drops 

    @classmethod
    def From_diccionary(cls,Dicionary):
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
            "suelta": list(self.arr_suelta),
        }