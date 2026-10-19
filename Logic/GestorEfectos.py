from DTO.EfectoDTO import EfectoDTO


class GestorEfectos:
    def __init__(self, motor):
        self.motor = motor
        self.activos = []

    # ---------- Metodos publicos

    def aplicar(self, efecto):
        if efecto.UNICO:
            self.cancelar(efecto.actor, efecto.tipo)
        efecto.fin = self.motor.reloj + efecto.duracion
        efecto.al_aplicar(self.motor)
        efecto.evento = self.motor.programar_efecto(efecto.primer_retraso, efecto.tipo, efecto)
        self.motor.historial.registrar_cambio(lambda: self.activos.remove(efecto))
        self.activos.append(efecto)

    def tiene(self, actor, tipo):
        return self._buscar(actor, tipo) is not None

    def cancelar(self, actor, tipo):
        efecto = self._buscar(actor, tipo)
        if efecto is None:
            return False
        efecto.evento.cancelar()
        self.quitar(efecto)
        return True

    # Al morir un actor: sus efectos no vuelven a activarse (§4.1). Recorre solo los efectos activos, no la agenda.
    def cancelar_de(self, actor):
        propios = []
        for efecto in self.activos:
            if efecto.actor is actor:
                propios.append(efecto)
        for efecto in propios:
            efecto.evento.cancelar()
            self.quitar(efecto)

    def quitar(self, efecto):
        indice = self.activos.index(efecto)
        self.motor.historial.registrar_cambio(lambda: self.activos.insert(indice, efecto))
        self.activos.pop(indice)

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
