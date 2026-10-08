from DTO.EfectoDTO import EfectoDTO


class GestorEfectos:
    def __init__(self, motor):
        self.motor = motor
        self.activos = []

    # ---------- Metodos publicos

    # COORDINAR (Integrante 3): usar objetos -> aplicar(Velocidad(...)) para pociones de velocidad, aplicar(Antorcha(...)) para antorchas
    # COORDINAR (Integrante 3): registrar el cambio en HistorialRetroceso (alta del efecto)
    def aplicar(self, efecto):
        if efecto.UNICO:
            self.cancelar(efecto.actor, efecto.tipo)
        efecto.fin = self.motor.reloj + efecto.duracion
        efecto.al_aplicar(self.motor)
        efecto.evento = self.motor.programar_efecto(efecto.primer_retraso, efecto.tipo, efecto)
        self.activos.append(efecto)

    def tiene(self, actor, tipo):
        return self._buscar(actor, tipo) is not None

    # COORDINAR (Integrante 3): el antídoto llama cancelar(jugador, "veneno")
    def cancelar(self, actor, tipo):
        efecto = self._buscar(actor, tipo)
        if efecto is None:
            return False
        efecto.evento.cancelar()
        self.quitar(efecto)
        return True

    # COORDINAR (Integrante 3): registrar el cambio en HistorialRetroceso (baja del efecto)
    def quitar(self, efecto):
        self.activos.remove(efecto)

    # COORDINAR (Integrante 3): Servicios usa esta lista para EstadoJuegoDTO
    def visibles(self, actor):
        resultado = []
        for efecto in self.activos:
            if efecto.actor is actor:
                restante = efecto.fin - self.motor.reloj
                resultado.append(EfectoDTO(efecto.tipo, restante, efecto.valor))
        return resultado

    # ---------- Metodos privados

    def _buscar(self, actor, tipo):
        for efecto in self.activos:
            if efecto.actor is actor and efecto.tipo == tipo:
                return efecto
        return None
