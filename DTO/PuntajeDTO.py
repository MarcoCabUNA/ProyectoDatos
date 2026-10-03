from dataclasses import dataclass

@dataclass(frozen=True)
class PuntajeDTO:
    """Una fila de la tabla de puntajes local.

        mazmorra: id de la cripta jugada (se mantiene el nombre del documento de DTOs)
        version: versión de la cripta jugada
        """