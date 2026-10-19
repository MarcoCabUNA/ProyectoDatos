"""
ServicioInventario (Servicios, Integrante 3): recorrer y ordenar la VISTA del inventario.

Mover el cursor y cambiar la vista no son acciones del jugador: no consumen tiempo, no se registran en la
bitácora de replay y no se pueden deshacer. Las acciones que sí lo son (recoger, soltar, equipar, usar)
las ejecuta ServicioAccionJugador, que identifica el objeto por su id.

Vista ordenada (criterio 'peso', 'valor' o 'nombre'): es una copia; el orden real no cambia. Mientras hay un
criterio activo, siguiente() y anterior() recorren la VISTA ordenada, y el cursor real se coloca sobre el
objeto elegido con Inventario.ubicar(). Si hay objetos con el mismo id, el recorrido salta los repetidos
(el cursor real no puede distinguirlos: ubicar() siempre elige la misma instancia).
Todos los métodos devuelven el InventarioDTO resultante para la Vista.
"""
from DTO.InventarioDTO import InventarioDTO
from Service.ArmadorEstado import ArmadorEstado
from Service.ContextoPartida import ContextoPartida


class ServicioInventario:

    def __init__(self):
        self._armador = ArmadorEstado()

    def inventario(self, contexto: ContextoPartida) -> InventarioDTO:
        return self._armador.armar_inventario(contexto, contexto.criterio_vista)

    def siguiente(self, contexto: ContextoPartida) -> InventarioDTO:
        self._mover(contexto, +1)
        return self.inventario(contexto)

    def anterior(self, contexto: ContextoPartida) -> InventarioDTO:
        self._mover(contexto, -1)
        return self.inventario(contexto)

    def ordenar(self, contexto: ContextoPartida, criterio: str | None) -> InventarioDTO:
        """Cambia la vista: None (orden real), 'peso', 'valor' o 'nombre'. Lanza ValueError si el criterio no existe."""
        foto = self._armador.armar_inventario(contexto, criterio)      # falla aquí, antes de cambiar nada
        contexto.criterio_vista = criterio
        return foto

    # ---- interno ----

    @staticmethod
    def _mover(contexto, paso: int) -> None:
        inventario = contexto.inventario
        if contexto.criterio_vista is None:
            if paso > 0:
                inventario.siguiente()
            else:
                inventario.anterior()
            return
        vista = inventario.vista_ordenada(contexto.criterio_vista)
        actual = inventario.objeto_actual()          # None solo si está vacío, y entonces la vista no tiene nada que recorrer
        posicion = 0
        for i in range(len(vista)):
            if vista[i] is actual:
                posicion = i
                break
        i = posicion + paso
        while 0 <= i < len(vista) and vista[i].id == actual.id:        # saltar los repetidos
            i += paso
        if 0 <= i < len(vista):
            inventario.ubicar(vista[i].id)