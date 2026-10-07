import ActorBase
class Enemigo(ActorBase):
    def __init__(self, ficha, instancia, vida, numero, sala):
        vida_inicial = ficha.vida_max if vida is None else vida
        super().__init__(
            instancia,
            vida_inicial,
            ficha.vida_max,
            ficha.ataque,
            ficha.defensa,
            ficha.velocidad,
            sala
        )
        self.ficha = ficha
        self.numero = numero
        self.activo = False

    def nombre_visible(self):
        return f"{self.ficha.nombre} #{self.numero}"

    def comportamiento(self):
        return self.ficha.comportamiento

    def objetos_que_suelta(self):
        return self.ficha.suelta