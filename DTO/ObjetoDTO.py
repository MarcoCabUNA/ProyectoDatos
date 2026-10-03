"""
ObjetoDTO (Integrante 2): ficha de catálogo de cualquier OBJETO.

Clases que cubre: arma, armadura, pocion, antidoto, llave, antorcha, pergamino_retroceso.
Las clases 'enemigo' y 'trampa' NO son objetos: usan FichaEnemigoDTO y FichaTrampaDTO
(DTOs de Marco). La trampa ni siquiera tiene peso ni valor.

Los campos que no aplican a la clase quedan en None.
"""
from dataclasses import dataclass

CLASES_OBJETO = ["arma", "armadura", "pocion", "antidoto", "llave", "antorcha", "pergamino_retroceso"]

# Campos opcionales en el orden del Swagger. Solo se recorren; no se modifican.
_CAMPOS_OPCIONALES = ["ataque_bonus", "defensa_bonus", "cura", "modificador_velocidad", "duracion", "abre"]


def es_clase_objeto(clase: str) -> bool:
    for c in CLASES_OBJETO:
        if c == clase:
            return True
    return False


@dataclass(frozen=True)
class ObjetoDTO:
    id: str
    nombre: str
    clase: str
    peso: int
    valor: int
    ataque_bonus: int | None = None           # arma
    defensa_bonus: int | None = None          # armadura
    cura: int | None = None                   # pocion
    modificador_velocidad: int | None = None  # pocion
    duracion: int | None = None               # pocion, antorcha
    abre: str | int | None = None             # llave

    @classmethod
    def desde_diccionario(cls, d: dict) -> "ObjetoDTO":
        """Lee 'clase' y llena solo los campos que vienen; los demás quedan en None."""
        clase = d["clase"]
        if not es_clase_objeto(clase):
            raise ValueError(f"La ficha {d.get('id')!r} es de clase {clase!r}, no es un objeto")
        return cls(
            id=d["id"],
            nombre=d["nombre"],
            clase=clase,
            peso=d["peso"],
            valor=d["valor"],
            ataque_bonus=d.get("ataque_bonus"),
            defensa_bonus=d.get("defensa_bonus"),
            cura=d.get("cura"),
            modificador_velocidad=d.get("modificador_velocidad"),
            duracion=d.get("duracion"),
            abre=d.get("abre"),
        )

    def a_diccionario(self) -> dict:
        """Mismo formato del API: solo incluye los campos opcionales que tienen valor."""
        d = {"id": self.id, "nombre": self.nombre, "clase": self.clase,
             "peso": self.peso, "valor": self.valor}
        for nombre in _CAMPOS_OPCIONALES:
            valor = getattr(self, nombre)
            if valor is not None:
                d[nombre] = valor
        return d