from DTO.ActorDTO import ActorDTO


class ActorBase:
    def __init__(self, Id, Vida, vida_M, Ataq, Def, Velo, SAct, ObjEvent=None):
        self.id = Id
        self.vida = Vida
        self.vida_Max = vida_M
        self.ataque = Ataq
        self.defensa = Def
        self.velocidad = Velo
        self.Sala_Actual = SAct
        self.Evento_pendiente = ObjEvent

    def Calcu_de_Intervalo(self, Costo):
        return max(1, Costo * 100 // self.velocidad)

    def Recibir_Dannio(self, Cant):
        if Cant <= 0:
            return
        if Cant > self.vida:
            self.vida = 0
        else:
            self.vida -= Cant

    def Vivo(self):
        return self.vida > 0

    def Curacion(self, Cant):
        if self.Vivo():
            if self.vida + Cant > self.vida_Max:
                self.vida = self.vida_Max
            else:
                self.vida += Cant

    def Ataque_bas(self):
        return self.ataque

    def Defensa_bas(self):
        return self.defensa

    def ataque_efectivo(self):
        return self.Ataque_bas()

    def defensa_efectiva(self):
        return self.Defensa_bas()

    def tipo(self):
        raise NotImplementedError

    def nombre_visible(self):
        raise NotImplementedError

    def a_dto(self):
        return ActorDTO(
            self.id,
            self.tipo(),
            self.nombre_visible(),
            self.vida,
            self.vida_Max,
            self.ataque_efectivo(),
            self.defensa_efectiva(),
            self.velocidad,
            self.Sala_Actual
        )
