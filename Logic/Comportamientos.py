class Comportamiento:
    NOMBRE = ""

    def decidir(self, enemigo, motor):
        raise NotImplementedError

    def decidir_paso(self, enemigo, motor) -> tuple[int, int] | None:
        """
        (destino, costo) del paso que da el enemigo, o None si no se mueve (FR-102, FR-104).
        Usa decidir() y paga la salida abierta más barata hacia ese destino.
        """
        destino = self.decidir(enemigo, motor)
        if destino is None:
            return None
        return destino, motor.mazmorra.costo_paso(enemigo.Sala_Actual, destino)


class Guardian(Comportamiento):
    NOMBRE = "guardián"

    def decidir(self, enemigo, motor):
        return None


class Errante(Comportamiento):
    NOMBRE = "errante"

    def decidir(self, enemigo, motor):
        destinos = motor.mazmorra.salidas_abiertas(enemigo.Sala_Actual)
        if not destinos:
            return None
        return destinos[motor.azar.randint(0, len(destinos) - 1)]

    def decidir_paso(self, enemigo, motor) -> tuple[int, int] | None:
        """
        Mismo sorteo que decidir(), pero sobre las salidas con su costo: cada salida es una opción y el errante
        paga la que le toca (FR-104). Hace la misma llamada a randint que P1 (Principio IV).
        """
        opciones = motor.mazmorra.salidas_abiertas_con_costo(enemigo.Sala_Actual)
        if not opciones:
            return None
        return opciones[motor.azar.randint(0, len(opciones) - 1)]


class Rastreador(Comportamiento):
    NOMBRE = "rastreador"

    def decidir(self, enemigo, motor):
        mejor_sala = None
        mejor_tiempo = None
        for destino in motor.mazmorra.salidas_abiertas(enemigo.Sala_Actual):
            if not motor.rastro.es_fresco(destino, motor.reloj):
                continue
            tiempo = motor.rastro.obtener(destino)
            if (mejor_tiempo is None or tiempo > mejor_tiempo
                    or (tiempo == mejor_tiempo and destino < mejor_sala)):
                mejor_sala = destino
                mejor_tiempo = tiempo
        return mejor_sala


class Cazador(Comportamiento):
    """
    Parte II §3.2: avanza un paso por la ruta más barata hacia el jugador si su costo d no pasa su rango;
    si no hay ruta o d > rango, espera (FR-106 a FR-111). Decide sin azar (FR-115) y sin abrir puertas (FR-113).
    Usa la búsqueda compartida de todos los cazadores (motor.rutas, R2 y R4); decide igual que paso_desde_cero
    (FR-114).
    """
    NOMBRE = "cazador"

    def decidir(self, enemigo, motor):
        paso = self.decidir_paso(enemigo, motor)
        return None if paso is None else paso[0]

    def decidir_paso(self, enemigo, motor) -> tuple[int, int] | None:
        """(destino, costo) del paso hacia el jugador, o None para esperar."""
        return motor.rutas.decidir(enemigo.Sala_Actual, motor.jugador.Sala_Actual, enemigo.ficha.rango)


COMPORTAMIENTOS = [Guardian, Errante, Rastreador, Cazador]


def crear_comportamiento(nombre):
    for clase in COMPORTAMIENTOS:
        if clase.NOMBRE == nombre:
            return clase()
    raise ValueError(f"Comportamiento desconocido: {nombre}")
