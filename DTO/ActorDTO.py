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
    comportamiento: str | None = None # FR-117: None para el jugador

    @classmethod
    def desde_diccionario(cls, d):
        return cls(
            d["id"],
            d["tipo"],
            d["nombre"],
            d["vida"],
            d["vida_max"],
            d["ataque"],
            d["defensa"],
            d["velocidad"],
            d["sala_actual"],
            d.get("comportamiento"),
        )

    def a_diccionario(self):
        datos = {
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
        if self.comportamiento is not None:
            datos["comportamiento"] = self.comportamiento
        return datos