from dataclasses import dataclass


@dataclass(frozen=True)
class ActorDTO:
    Id: str # instancia de entidad final
    Type: str # jugador o enemigo denominado en logica
    Name: str
    Health: int
    max_H: int
    Attack: int
    Def: int
    Velo: int
    Room: int

    @classmethod
    def desde_diccionario(cls, Dicionary):
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

    def a_diccionario(self):
        return {
            "id": self.Id,
            "tipo": self.Type,
            "nombre": self.Name,
            "vida": self.Health,
            "vida_max": self.max_H,
            "ataque": self.Attack,
            "defensa": self.Def,
            "velocidad": self.Velo,
            "sala_actual": self.Room,
        }