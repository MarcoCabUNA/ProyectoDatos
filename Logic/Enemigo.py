from Logic.ActorBase import ActorBase
from Logic.Comportamientos import crear_comportamiento


class Enemigo(ActorBase):
    # COORDINAR (Integrante 2): self.ficha queda en uso; la caché no puede desalojarla mientras el enemigo viva (§4.4)
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
        self.estrategia = crear_comportamiento(ficha.comportamiento)

    def tipo(self):
        return self.ficha.id

    def nombre_visible(self):
        return f"{self.ficha.nombre} #{self.numero}"

    def comportamiento(self):
        return self.ficha.comportamiento

    # COORDINAR (Integrante 2): los ids de suelta deben incluirse en los lotes de /catalogo
    def objetos_que_suelta(self):
        return self.ficha.suelta

    def activar(self, motor, evento):
        motor.turno_enemigo(self)
