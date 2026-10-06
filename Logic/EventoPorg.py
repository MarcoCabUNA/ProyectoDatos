class EventoProgramado:
    def __init__(self, int_tiempo, str_tipo, obj_dueno):
        self.int_tiempo = int_tiempo
        self.int_secuencia = -1
        self.str_tipo = str_tipo
        self.obj_dueno = obj_dueno
        self.bool_valido = True

    def __lt__(self, otro):
        return (self.int_tiempo, self.int_secuencia) < (otro.int_tiempo, otro.int_secuencia)

    def cancelar(self):
        self.bool_valido = False

    def esta_valido(self):
        return self.bool_valido

    def __repr__(self):
        estado = "valido" if self.bool_valido else "cancelado"
        return f"Evento(t={self.int_tiempo}, seq={self.int_secuencia}, {self.str_tipo}, {estado})"