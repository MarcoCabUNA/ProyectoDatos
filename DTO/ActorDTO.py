from dataclasses import dataclass


@dataclass(frozen=True)
class ActorDTO:
    id: str # instancia de entidad final
    tipo: str # jugador o enemigo denominado en logica
    nombre: str
    vida: int
    vida_max: int
    ataque: int
    defensa: int
    velocidad: int
    sala_actual: int

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
            "id": self.id,
            "tipo": self.tipo,
            "nombre": self.nombre,
            "vida": self.vida,
            "vida_max": self.vida_max,
            "ataque": self.ataque,
            "defensa": self.defensa,
            "velocidad": self.velocidad,
            "sala_actual": self.sala_actual,
        }