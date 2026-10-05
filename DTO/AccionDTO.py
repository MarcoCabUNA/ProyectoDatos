"""
AccionDTO (Integrante 3): una acción del jugador.

Es exactamente lo que se escribe en la bitácora de --replay. Lo produce el Controlador
(desde el teclado) o ServicioReplay (desde el log), por eso Lógica no distingue entre
una partida en vivo y una reproducción.

Tipos de acción: mover, atacar, esperar, abrir, recoger, soltar, usar, equipar, retroceder.

Cruces con los DTO del integrante 2:
    direccion -> índice de DTO/Direcciones.py (0=N, 1=S, 2=E, 3=O), el mismo que usa
                 el array SalaDTO.salidas.
    objeto    -> id de catálogo (ObjetoDTO.id). SalaDTO.objetos también identifica los
                 objetos por su id de catálogo.
Cruce con el integrante 1:
    objetivo  -> id de instancia del enemigo (ActorDTO.Id; en SalaDTO es
                 EnemigoEnSalaDTO.instancia).

Regla de los DTOs: solo transportan datos. La validación de reglas del juego
(por ejemplo, si el tipo existe) la hace el Controlador o Servicios, no el DTO.
"""
from dataclasses import dataclass

SEPARADOR = "|"


@dataclass(frozen=True)
class AccionDTO:
    tipo: str
    direccion: int | None = None   # solo para mover y abrir
    objetivo: str | None = None    # solo para atacar
    objeto: str | None = None      # solo para recoger, soltar, usar y equipar

    @classmethod
    def desde_linea(cls, texto: str) -> "AccionDTO":
        """Reconstruye la acción desde una línea del log (inverso de a_linea)."""
        partes = texto.strip().split(SEPARADOR)
        if len(partes) != 4:
            raise ValueError(f"Línea de acción con formato inválido: {texto!r}")
        tipo, direccion, objetivo, objeto = partes
        return cls(
            tipo=tipo,
            direccion=int(direccion) if direccion != "" else None,
            objetivo=objetivo if objetivo != "" else None,
            objeto=objeto if objeto != "" else None,
        )

    def a_linea(self) -> str:
        """Convierte la acción en una línea de texto: tipo|direccion|objetivo|objeto.

        Un campo None se escribe vacío. Ejemplos:
            mover|0||
            atacar||e-201|
            recoger|||itm_daga_oxidada
        """
        direccion = "" if self.direccion is None else str(self.direccion)
        objetivo = "" if self.objetivo is None else self.objetivo
        objeto = "" if self.objeto is None else self.objeto
        return SEPARADOR.join([self.tipo, direccion, objetivo, objeto])