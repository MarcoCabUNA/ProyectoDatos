import ActorBase

class Jugador(ActorBase):
    def __init__(self, cripta):
        super().__init__(
            "jugador",
            cripta.jugador_vida_max,
            cripta.jugador_vida_max,
            cripta.jugador_ataque,
            cripta.jugador_defensa,
            cripta.jugador_velocidad,
            cripta.sala_inicial,
        )
        self.arma = None
        self.armadura = None
        self.acciones = 0

    def equipar(self, objeto):
        if objeto.clase == "arma":
            self.arma = objeto

        elif objeto.clase == "armadura":
            self.armadura = objeto

    def ataque_efectivo(self):
        if self.arma is None:
            return self.ataque
        return self.ataque + self.arma.ataque_bonus

    def defensa_efectiva(self):
        if self.armadura is None:
            return self.defensa
        return self.defensa + self.armadura.defensa_bonus
