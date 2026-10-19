from dataclasses import dataclass, field

from DTO.EfectoFichaDTO import campos_extra, leer_efectos

_CAMPOS = ["id", "clase", "nombre", "vida_max", "ataque", "defensa", "velocidad", "comportamiento", "suelta"]


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
    # Efectos de §2.10 que declare el catálogo (veneno al golpear, regeneración...): ver DTO/EfectoFichaDTO.py
    efectos: tuple = ()
    # Campos del JSON que no son de esta clase; se vuelven a escribir en a_diccionario para que la caché en disco
    # no pierda nada que el API agregue (y efectos se pueda volver a leer de ellos).
    extras: tuple = field(default=(), hash=False)

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
            leer_efectos(d),
            campos_extra(d, _CAMPOS),
        )

    def a_diccionario(self):
        d = {
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
        for clave, valor in self.extras:
            d[clave] = valor
        return d
