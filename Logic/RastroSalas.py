class RastroSalas:
    ANTIGUEDAD_MAXIMA = 400

    def __init__(self, historial=None):
        self.tiempos = []
        self.historial = historial

    def marcar(self, sala, tiempo):
        while len(self.tiempos) <= sala:
            self.tiempos.append(None)
        if self.historial is not None:
            anterior = self.tiempos[sala]
            self.historial.registrar_cambio(lambda: self._restaurar(sala, anterior))
        self.tiempos[sala] = tiempo

    def obtener(self, sala):
        if sala >= len(self.tiempos):
            return None
        return self.tiempos[sala]

    def es_fresco(self, sala, ahora):
        tiempo = self.obtener(sala)
        return tiempo is not None and ahora - tiempo < self.ANTIGUEDAD_MAXIMA

    def _restaurar(self, sala, tiempo):
        self.tiempos[sala] = tiempo
