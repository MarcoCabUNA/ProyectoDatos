class ColaEventos:
    def __init__(self):
        self.eventos = []
        self.siguiente_secuencia = 0

    # ---------- Metodos publicos

    def programar(self, evento):
        evento.secuencia = self.siguiente_secuencia
        self.siguiente_secuencia += 1
        self.eventos.append(evento)
        self._subir(len(self.eventos) - 1)
        return evento

    def obtener_siguiente(self):
        self._descartar_invalidos()
        if not self.eventos:
            return None
        return self._extraer_raiz()

    def ver_siguiente(self):
        self._descartar_invalidos()
        return self.eventos[0] if self.eventos else None

    def esta_vacia(self):
        self._descartar_invalidos()
        return not self.eventos

    # ---------- Metodos privados

    def _descartar_invalidos(self):
        while self.eventos and not self.eventos[0].esta_valido():
            self._extraer_raiz()

    def _extraer_raiz(self):
        arr = self.eventos
        raiz = arr[0]
        ultimo = arr.pop()
        if arr:
            arr[0] = ultimo
            self._bajar(0)
        return raiz

    def _subir(self, i):
        arr = self.eventos
        while i > 0:
            padre = (i - 1) // 2
            if arr[i] < arr[padre]:
                self._intercambiar(i, padre)
                i = padre
            else:
                break

    def _bajar(self, i):
        arr = self.eventos
        n = len(arr)
        while True:
            menor = i
            izq = 2 * i + 1
            der = izq + 1
            if izq < n and arr[izq] < arr[menor]:
                menor = izq
            if der < n and arr[der] < arr[menor]:
                menor = der
            if menor == i:
                return
            self._intercambiar(i, menor)
            i = menor

    def _intercambiar(self, i, j):
        temporal = self.eventos[i]
        self.eventos[i] = self.eventos[j]
        self.eventos[j] = temporal
