class Comportamiento:
    NOMBRE = ""

    def decidir(self, enemigo, motor):
        raise NotImplementedError


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


COMPORTAMIENTOS = [Guardian, Errante, Rastreador]


def crear_comportamiento(nombre):
    for clase in COMPORTAMIENTOS:
        if clase.NOMBRE == nombre:
            return clase()
    raise ValueError(f"Comportamiento desconocido: {nombre}")
