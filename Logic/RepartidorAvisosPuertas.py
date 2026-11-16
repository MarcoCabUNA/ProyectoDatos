"""
RepartidorAvisosPuertas (Lógica, integrante 2, feature 002): reparte el aviso de puertas de la Mazmorra (data-model §7).

La Mazmorra tiene un solo observador_puertas (001 FR-114). El motor le asigna este repartidor, que reenvía cada
puerta_cambio(a, b) a sus observadores en orden fijo: [motor.rutas, motor.mapa] (FR-207). Así ni la Mazmorra ni las
rutas del cazador cambian. No conoce a sus observadores: solo les pide puerta_cambio.
"""


class RepartidorAvisosPuertas:
    """Reenvía el aviso puerta_cambio a varios observadores, en el orden de la lista."""

    def __init__(self, observadores: list) -> None:
        self.observadores: list = list(observadores)       # copia: el orden queda fijo

    def puerta_cambio(self, a: int, b: int) -> None:
        """Llama a puerta_cambio(a, b) de cada observador, en orden. O(cantidad de observadores)."""
        for observador in self.observadores:
            observador.puerta_cambio(a, b)
