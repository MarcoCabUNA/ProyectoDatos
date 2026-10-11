from Logic.ActorBase import ActorBase


class Jugador(ActorBase):
    # COORDINAR (Integrante 2): CriptaDTO con jugador_vida_max, jugador_ataque, jugador_defensa, jugador_velocidad y sala_inicial
    def __init__(self, cripta):
        super().__init__(
            "jugador",
            cripta.jugador_vida_max,
            cripta.jugador_vida_max,
            cripta.jugador_ataque,
            cripta.jugador_defensa,
            cripta.jugador_velocidad,
            cripta.sala_inicial
        )
        self.arma = None
        self.armadura = None
        self.acciones = 0
        # COORDINAR (Integrante 3): definir si el inventario vive aquí o en Servicios

    def tipo(self):
        return "jugador"

    def nombre_visible(self):
        return "Jugador"

    # COORDINAR (Integrante 3): mover el objeto al frente del inventario le corresponde al Inventario
    def equipar(self, objeto):
        if objeto.clase == "arma":
            self.arma = objeto

        elif objeto.clase == "armadura":
            self.armadura = objeto

    def ataque_efectivo(self):
        if self.arma is None:
            return self.Ataque_bas()
        return self.Ataque_bas() + self.arma.ataque_bonus

    def defensa_efectiva(self):
        if self.armadura is None:
            return self.Defensa_bas()
        return self.Defensa_bas() + self.armadura.defensa_bonus

#a