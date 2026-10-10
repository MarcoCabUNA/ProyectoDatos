class Efecto:
    UNICO = False

    def __init__(self, tipo, actor, duracion, valor=None, primer_retraso=None):
        self.tipo = tipo
        self.actor = actor
        self.duracion = duracion
        self.valor = valor
        self.primer_retraso = duracion if primer_retraso is None else primer_retraso
        self.fin = 0
        self.evento = None

    def al_aplicar(self, motor):
        pass

    def activar(self, motor, evento):
        raise NotImplementedError


class Veneno(Efecto):
    PULSO = 80
    DURACION = 400
    UNICO = True

    def __init__(self, actor, dano):
        super().__init__("veneno", actor, self.DURACION, dano, self.PULSO)

    def activar(self, motor, evento):
        if not self.actor.Vivo():
            motor.efectos.quitar(self)
            return
        self.actor.Recibir_Dannio(self.valor)
        motor.mensaje(f"El veneno hace {self.valor} de daño a {self.actor.nombre_visible()}")
        if not self.actor.Vivo():
            motor.efectos.quitar(self)
            motor.morir(self.actor)
        elif motor.reloj + self.PULSO <= self.fin:
            motor.historial.registrar_atributo(self, "evento", self.evento)
            self.evento = motor.programar_efecto(self.PULSO, self.tipo, self)
        else:
            motor.efectos.quitar(self)


class Velocidad(Efecto):
    def __init__(self, actor, modificador, duracion):
        super().__init__("velocidad", actor, duracion, modificador)
        self.cambio_real = 0

    def al_aplicar(self, motor):
        anterior = self.actor.velocidad
        motor.cambiar_velocidad(self.actor, max(1, anterior + self.valor))
        self.cambio_real = self.actor.velocidad - anterior

    def activar(self, motor, evento):
        motor.cambiar_velocidad(self.actor, self.actor.velocidad - self.cambio_real)
        motor.efectos.quitar(self)


class Antorcha(Efecto):
    def __init__(self, actor, duracion):
        super().__init__("antorcha", actor, duracion)

    def activar(self, motor, evento):
        motor.mensaje("La antorcha se apaga")
        motor.efectos.quitar(self)
