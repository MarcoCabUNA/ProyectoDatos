from dataclasses import dataclass, field

from DTO.EfectoFichaDTO import buscar, campos_extra, dano_inmediato_de_trampa, entero, leer_efectos

_CAMPOS = ["id", "clase", "nombre", "daño", "rearme"]


@dataclass(frozen=True)
class FichaTrampaDTO:
    id: str
    nombre: str
    danio: int     # en el JSON del API la clave es "daño"
    rearme: int    # si viene null en el catálogo, se usa 300
    # Efectos de §2.10 que aplica al activarse (veneno, velocidad...): ver DTO/EfectoFichaDTO.py
    efectos: tuple = ()
    # Campos del JSON que no son de esta clase (se reescriben en a_diccionario; ver FichaEnemigoDTO)
    extras: tuple = field(default=(), hash=False)
    # Daño que hace al activarse. Es 'danio', salvo que la ficha diga "efecto": "veneno" sin "valor":
    # entonces 'danio' es el daño por pulso del veneno y no hay daño inmediato. None: igual a 'danio'.
    danio_inmediato: int | None = None

    @classmethod
    def desde_diccionario(cls, d):
        # "daño" es obligatorio en el Swagger; una trampa que solo envenena podría no traerlo.
        danio = entero(buscar(d, "dano", "danio"))
        danio = 0 if danio is None or danio < 0 else danio
        rearme = entero(d.get("rearme"))
        return cls(
            d["id"],
            d["nombre"],
            danio,
            300 if rearme is None or rearme <= 0 else rearme,
            leer_efectos(d, danio),
            campos_extra(d, _CAMPOS),
            dano_inmediato_de_trampa(d, danio),
        )

    def dano_al_activarse(self):
        return self.danio if self.danio_inmediato is None else self.danio_inmediato

    def a_diccionario(self):
        d = {
            "id": self.id,
            "clase": "trampa",
            "nombre": self.nombre,
            "daño": self.danio,
            "rearme": self.rearme,
        }
        for clave, valor in self.extras:
            d[clave] = valor
        return d
