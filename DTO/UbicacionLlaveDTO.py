"""
UbicacionLlaveDTO (Integrante 2, feature 003): un elemento de GET /criptas/{id}/llaves (contracts/contrato-llaves.md).

    { "id": "itm_llave_negra", "sala": 12, "enemigo": "e-1203" }

Con 'enemigo', la llave está en el campo 'suelta' de esa instancia y 'sala' es donde el enemigo inicia (FR-303).
Solo transporta datos: no valida, no ordena ni deduplica (el formato lo valida FuenteJson; el orden y las ubicaciones
idénticas los resuelve Lógica, FR-309). Una misma llave puede aparecer varias veces: cada una es una copia (FR-316).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class UbicacionLlaveDTO:
    id: str
    sala: int
    enemigo: str | None = None   # ausente o null en el JSON -> None

    @classmethod
    def desde_diccionario(cls, d: dict) -> "UbicacionLlaveDTO":
        """Lee un elemento de la lista 'llaves' del API."""
        return cls(id=d["id"], sala=d["sala"], enemigo=d.get("enemigo"))

    def a_diccionario(self) -> dict:
        """El mismo formato del API: omite 'enemigo' si es None."""
        d: dict = {"id": self.id, "sala": self.sala}
        if self.enemigo is not None:
            d["enemigo"] = self.enemigo
        return d
