class EventoProgramado:
    def __init__(self, tiempo, tipo, dueno):
        self.tiempo = tiempo
        self.secuencia = -1
        self.tipo = tipo
        self.dueno = dueno
        self.valido = True

    def __lt__(self, otro):
        if self.tiempo != otro.tiempo:
            return self.tiempo < otro.tiempo
        return self.secuencia < otro.secuencia

    def cancelar(self):
        self.valido = False

    def esta_valido(self):
        return self.valido

    def __repr__(self):
        estado = "valido" if self.valido else "cancelado"
        return f"Evento(t={self.tiempo}, seq={self.secuencia}, {self.tipo}, {estado})"