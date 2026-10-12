"""
HistorialRetroceso (Lógica, Integrante 3): deshacer las últimas 5 acciones del jugador (§2.11, §4.6).

Idea central: NO se guardan copias del estado (el enunciado lo prohíbe). Cada vez que algo
cambia, quien lo cambia le entrega al historial una pequeña función que sabe INVERTIR ese cambio.
Deshacer es ejecutar esas funciones, de la última a la primera.

Intervalo = to-do lo que ocurre entre dos decisiones del jugador: su propia acción y lo que pasa
después hasta que vuelve a decidir (acciones enemigas, efectos, reloj, eventos, rastro...).
Un intervalo es lo mínimo que se puede deshacer.

Cómo se usa:
    historial = HistorialRetroceso()

    # durante una acción y los eventos que le siguen: ANTES de cambiar algo, se registra cómo volver
    historial.registrar_atributo(actor, "vida", actor.vida)          # un valor simple
    actor.vida = nueva_vida
    historial.registrar_cambio(lambda: lista.remove(elemento))       # cualquier otro cambio
    lista.append(elemento)

    historial.cerrar_intervalo()          # cuando el control vuelve al jugador

    # el jugador usa un pergamino de retroceso:
    if historial.deshacer():              # False si no hay nada que deshacer
        ...                               # quien llama consume el pergamino DESPUÉS

Reglas:
    - Se registra el valor ANTERIOR, antes de modificarlo.
    - Los cambios de un intervalo se deshacen en orden inverso: así cada uno encuentra el estado
      tal como lo dejó el cambio siguiente.
    - Mientras se deshace, los registros nuevos se ignoran: las operaciones que usan las funciones
      de reversión pueden llamar a los mismos puntos de registro sin ensuciar el historial.
    - Se guarda como máximo MAX_ACCIONES intervalos; al cerrar uno más se descarta el más antiguo.
    - Un intervalo sin cambios cuenta como una acción (esperar también es una acción del jugador).
    - Estado del azar: UNA vez al empezar cada intervalo, por ejemplo
          estado = azar.getstate(); historial.registrar_cambio(lambda: azar.setstate(estado))
      para que, tras deshacer, el generador repita la misma secuencia (determinismo).
    - Quedan FUERA del historial, por el enunciado: la caché y los pergaminos de retroceso (su
      cantidad no se registra ni se restaura). Quien usa el pergamino lo descuenta después de deshacer.
    - Precondición de deshacer(): no hay cambios sin cerrar (se llama en una decisión del jugador,
      justo después de cerrar el intervalo anterior).
    - Los cambios hechos al preparar la partida, antes de la primera decisión, se descartan con
      descartar_intervalo_abierto(); así la primera acción del jugador es lo más antiguo que se deshace.

Estructura: un array de 5 posiciones usado como buffer circular de intervalos cerrados; cada
intervalo es un array de funciones. Descartar el más antiguo no desplaza nada: solo avanza un índice.

Costos:
    registrar_cambio, registrar_atributo, cerrar_intervalo   O(1)
    deshacer                                                 O(c), c = cambios de ESE intervalo
Deshacer no depende del tamaño del estado del juego ni de cuánto lleva la partida.
Memoria: O(cambios de los últimos 5 intervalos).
Regla del equipo: no cambiar los nombres de los métodos sin avisar a los demás.
"""


class HistorialRetroceso:
    MAX_ACCIONES = 5

    def __init__(self):
        self._cerrados = [None] * HistorialRetroceso.MAX_ACCIONES   # buffer circular de intervalos
        self._primero = 0           # posición del intervalo más antiguo
        self._cantidad = 0          # cuántos intervalos cerrados hay
        self._abierto = []          # funciones de reversión del intervalo en curso
        self._deshaciendo = False

    # ---- Registro ----

    def registrar_cambio(self, deshacer) -> None:
        """Guarda una función SIN argumentos que invierte un cambio. Se ignora mientras se deshace."""
        if self._deshaciendo:
            return
        self._abierto.append(deshacer)

    def registrar_atributo(self, objeto, nombre: str, valor_anterior) -> None:
        """Atajo para el caso más común: al deshacer, 'objeto.nombre' vuelve a 'valor_anterior'."""
        if self._deshaciendo:
            return
        self._abierto.append(lambda: setattr(objeto, nombre, valor_anterior))

    def cerrar_intervalo(self) -> None:
        """Termina el intervalo en curso: pasa a ser la acción más reciente que se puede deshacer."""
        maximo = HistorialRetroceso.MAX_ACCIONES
        if self._cantidad == maximo:                 # lleno: el nuevo ocupa el lugar del más antiguo
            self._cerrados[self._primero] = self._abierto
            self._primero = (self._primero + 1) % maximo
        else:
            self._cerrados[(self._primero + self._cantidad) % maximo] = self._abierto
            self._cantidad += 1
        self._abierto = []

    def descartar_intervalo_abierto(self) -> None:
        """Olvida los cambios aún sin cerrar (por ejemplo, los de preparar la partida)."""
        self._abierto = []

    # ---- Deshacer ----

    def deshacer(self) -> bool:
        """Revierte la última acción cerrada. False si no hay ninguna que deshacer."""
        if self._cantidad == 0:
            return False
        maximo = HistorialRetroceso.MAX_ACCIONES
        posicion = (self._primero + self._cantidad - 1) % maximo
        cambios = self._cerrados[posicion]
        self._cerrados[posicion] = None
        self._cantidad -= 1
        self._deshaciendo = True
        try:
            for i in range(len(cambios) - 1, -1, -1):      # del último cambio al primero
                cambios[i]()
        finally:
            self._deshaciendo = False
        return True

    # ---- Consulta ----

    def cantidad(self) -> int:
        """Cuántas acciones se pueden deshacer ahora (como máximo MAX_ACCIONES)."""
        return self._cantidad