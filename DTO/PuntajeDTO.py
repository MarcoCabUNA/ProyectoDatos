"""
PuntajeDTO (Integrante 3): una fila de la tabla de puntajes local (§2.12).

Cruces con los DTO del integrante 2:
    mazmorra -> CriptaDTO.id (se mantiene el nombre de campo del documento de reparto).
    version  -> CriptaDTO.version.
Los contadores (acciones, enemigos_derrotados, tiempo_final) los expone el integrante 1
y ServicioPartida arma el DTO al terminar la partida.

Regla de los DTOs: solo transportan datos. a_diccionario() / desde_diccionario() sirven
para guardar y cargar la tabla de puntajes en disco.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class PuntajeDTO:
    nombre: str
    mazmorra: str
    version: str
    acciones: int
    enemigos_derrotados: int
    tiempo_final: int

    @classmethod
    def desde_diccionario(cls, d: dict) -> "PuntajeDTO":
        """Para cargar la tabla de puntajes."""
        return cls(
            nombre=d["nombre"],
            mazmorra=d["mazmorra"],
            version=d["version"],
            acciones=d["acciones"],
            enemigos_derrotados=d["enemigos_derrotados"],
            tiempo_final=d["tiempo_final"],
        )

    def a_diccionario(self) -> dict:
        """Para guardar la tabla de puntajes en disco."""
        return {
            "nombre": self.nombre,
            "mazmorra": self.mazmorra,
            "version": self.version,
            "acciones": self.acciones,
            "enemigos_derrotados": self.enemigos_derrotados,
            "tiempo_final": self.tiempo_final,
        }