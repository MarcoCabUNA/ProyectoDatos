from dataclasses import dataclass

# TODO: quitar el comentario de la linea 4 de esta clase cuando este implementado ObjetoDTO
# from DTO.objeto_dto import ObjetoDTO

@dataclass(frozen=True)
class InventarioDTO:
    """Foto del inventario para la Vista. Solo se muestra; no tiene métodos.

    objetos: list de ObjetoDTO, en el orden real o en una vista ordenada
    cursor: posición que el jugador está viendo
    capacidad: cantidad de objetos actuales
    capacidad_maxima: inventario_max de la cripta
    arma_equipada: id del arma equipada, o None
    armadura_equipada: id de la armadura equipada, o None
    criterio: "peso", "valor", "nombre", o None si es el orden real
    """

    #objetos : list[ObjetoDTO]
    cursor : int
    capacidad : int
    capacidad_max : int
    arma_equipada : str | None = None
    armadura_equipada : str | None = None
    criterio : str | None = None