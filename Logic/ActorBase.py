class ActorBase:
    def __init__(self,Id,Vida, vida_M, Ataq, Def, Velo, SAct, ObjEvent):
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
        if Cant > self.vida:
            self.vida = 0;
        else: 
            self.vida -= Cant

    def Vivo(self):
        return self.vida > 0
    
    def Curacion(self, Cant):
        if self.Vivo():
            if Cant > self.vida_Max:
                self.vida = self.vida_Max
            else: 
                self.vida += Cant

    def Ataque_bas(self):
        return self.ataque
    
    def Defensa_bas(self):
        return self.defensa