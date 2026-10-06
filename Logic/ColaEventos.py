class ColaEventos:
    def __init__(self):
        self.arr_eventos = []
        self.int_siguiente_secuencia = 0

    # ---------- Metodos publicos

    def programar(self, evento):
        evento.int_secuencia = self.int_siguiente_secuencia
        self.int_siguiente_secuencia += 1
        self.arr_eventos.append(evento)
        self._subir(len(self.arr_eventos) - 1)
        return evento

    def obtener_siguiente(self):
        self._descartar_invalidos()
        if not self.arr_eventos:
            return None
        return self._extraer_raiz()

    def ver_siguiente(self):
        self._descartar_invalidos()
        return self.arr_eventos[0] if self.arr_eventos else None

    def esta_vacia(self):
        self._descartar_invalidos()
        return not self.arr_eventos

    # --------- metodos privados

    def _descartar_invalidos(self):
        while self.arr_eventos and not self.arr_eventos[0].esta_valido():
            self._extraer_raiz()

    def _extraer_raiz(self):
        arr = self.arr_eventos
        raiz = arr[0]
        ultimo = arr.pop()
        if arr:
            arr[0] = ultimo
            self._bajar(0)
        return raiz

    def _subir(self, i):
        arr = self.arr_eventos
        while i > 0:
            padre = (i - 1) // 2
            if arr[i] < arr[padre]:
                arr[i], arr[padre] = arr[padre], arr[i]
                i = padre
            else:
                break

    def _bajar(self, i):
        arr = self.arr_eventos
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
            arr[i], arr[menor] = arr[menor], arr[i]
            i = menor