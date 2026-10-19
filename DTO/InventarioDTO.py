"""
InventarioDTO (Integrante 3): foto del inventario para la Vista.

Solo se muestra; no tiene métodos. Lo arma ServicioInventario recorriendo los nodos
de la lista doblemente enlazada (Inventario) o usando Ordenador para vistas ordenadas.
Como 'objetos' es una copia en array (list), ordenar la vista no altera el orden real.

Cruces con los DTO del integrante 2:
    objetos           -> array de ObjetoDTO.
    arma_equipada     -> ObjetoDTO.id del arma equipada (o None).
    armadura_equipada -> ObjetoDTO.id de la armadura equipada (o None).
    capacidad_maxima  -> CriptaDTO.inventario_max.
"""
from dataclasses import dataclass

from DTO.ObjetoDTO import ObjetoDTO


@dataclass(frozen=True)
class InventarioDTO:
    objetos: list[ObjetoDTO]          # en el orden real o en una vista ordenada
    cursor: int                       # posición que el jugador está viendo
    capacidad: int                    # cantidad de objetos actuales
    capacidad_maxima: int
    arma_equipada: str | None = None
    armadura_equipada: str | None = None
    criterio: str | None = None       # "peso", "valor", "nombre" o None (orden real)