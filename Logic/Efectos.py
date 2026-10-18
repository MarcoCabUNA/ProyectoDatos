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

    # duracion: la del enunciado (400) salvo que la ficha del catálogo indique otra
    def __init__(self, actor, dano, duracion=None):
        super().__init__("veneno", actor, self.DURACION if duracion is None else duracion, dano, self.PULSO)

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


# Un enemigo que declare regeneración recupera 'valor' cada 200 unidades mientras viva (§2.10).
# No termina por tiempo: 'fin' es el instante del próximo pulso (lo que muestra 'restante').
class Regeneracion(Efecto):
    PULSO = 200
    UNICO = True

    def __init__(self, actor, cantidad):
        super().__init__("regeneracion", actor, self.PULSO, cantidad, self.PULSO)

    def activar(self, motor, evento):
        if not self.actor.Vivo():
            motor.efectos.quitar(self)
            return
        antes = self.actor.vida
        self.actor.Curacion(self.valor)        # Curacion ya topa en vida_max
        if self.actor.vida > antes:
            motor.mensaje(f"{self.actor.nombre_visible()} regenera {self.actor.vida - antes} de vida")
        motor.historial.registrar_atributo(self, "fin", self.fin)
        self.fin = motor.reloj + self.PULSO
        motor.historial.registrar_atributo(self, "evento", self.evento)
        self.evento = motor.programar_efecto(self.PULSO, self.tipo, self)
