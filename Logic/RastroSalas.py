class RastroSalas:
    ANTIGUEDAD_MAXIMA = 400

    def __init__(self):
        self.tiempos = []

    def marcar(self, sala, tiempo):
        while len(self.tiempos) <= sala:
            self.tiempos.append(None)
        self.tiempos[sala] = tiempo

    def obtener(self, sala):
        if sala >= len(self.tiempos):
            return None
        return self.tiempos[sala]

    def es_fresco(self, sala, ahora):
        tiempo = self.obtener(sala)
        return tiempo is not None and ahora - tiempo < self.ANTIGUEDAD_MAXIMA
