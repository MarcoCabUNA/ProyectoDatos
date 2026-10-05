"""
DTOs de una cripta (Integrante 2).

ResumenCriptaDTO -> un elemento de GET /criptas (para elegir cripta).
CriptaDTO        -> los datos generales de GET /criptas/{id}.

Regla de los DTOs: solo transportan datos. desde_diccionario() lee el JSON del API
y a_diccionario() produce EL MISMO formato del API, para que la persistencia en
disco reutilice el mismo lector.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ResumenCriptaDTO:
    id: str
    nombre: str
    salas: int
    dificultad: int

    @classmethod
    def desde_diccionario(cls, d: dict) -> "ResumenCriptaDTO":
        return cls(id=d["id"], nombre=d["nombre"], salas=d["salas"], dificultad=d["dificultad"])

    def a_diccionario(self) -> dict:
        return {"id": self.id, "nombre": self.nombre,
                "salas": self.salas, "dificultad": self.dificultad}


@dataclass(frozen=True)
class CriptaDTO:
    id: str
    version: str
    salas_total: int
    paginas: int
    salas_por_pagina: int
    sala_inicial: int
    sala_salida: int
    llave_salida: str
    presupuesto_solicitudes: int
    inventario_max: int
    jugador_vida_max: int
    jugador_ataque: int
    jugador_defensa: int
    jugador_velocidad: int

    @classmethod
    def desde_diccionario(cls, d: dict) -> "CriptaDTO":
        """Aplana el objeto anidado 'jugador' en los cuatro campos jugador_*."""
        j = d["jugador"]
        return cls(
            id=d["id"],
            version=d["version"],
            salas_total=d["salas_total"],
            paginas=d["paginas"],
            salas_por_pagina=d["salas_por_pagina"],
            sala_inicial=d["sala_inicial"],
            sala_salida=d["sala_salida"],
            llave_salida=d["llave_salida"],
            presupuesto_solicitudes=d["presupuesto_solicitudes"],
            inventario_max=d["inventario_max"],
            jugador_vida_max=j["vida_max"],
            jugador_ataque=j["ataque"],
            jugador_defensa=j["defensa"],
            jugador_velocidad=j["velocidad"],
        )

    def a_diccionario(self) -> dict:
        """Vuelve a anidar 'jugador': mismo formato que GET /criptas/{id}."""
        return {
            "id": self.id,
            "version": self.version,
            "salas_total": self.salas_total,
            "paginas": self.paginas,
            "salas_por_pagina": self.salas_por_pagina,
            "sala_inicial": self.sala_inicial,
            "sala_salida": self.sala_salida,
            "llave_salida": self.llave_salida,
            "presupuesto_solicitudes": self.presupuesto_solicitudes,
            "inventario_max": self.inventario_max,
            "jugador": {
                "vida_max": self.jugador_vida_max,
                "ataque": self.jugador_ataque,
                "defensa": self.jugador_defensa,
                "velocidad": self.jugador_velocidad,
            },
        }