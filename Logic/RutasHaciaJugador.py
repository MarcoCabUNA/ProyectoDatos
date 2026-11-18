"""
RutasHaciaJugador (feature 001, T032): la búsqueda de costo mínimo que comparten todos los cazadores.

Decisiones: research.md R2 (una búsqueda compartida, desde el jugador) y R4 (descartarla solo cuando hace
falta). Modelo: data-model.md. Contrato de la búsqueda: contracts/busqueda-rutas.md.

- La búsqueda sale de la sala del jugador y mide la distancia de cada sala hacia él. Como el costo de una
  salida es el mismo en los dos sentidos (FR-101), sirve para todos los cazadores a la vez: cada uno la
  extiende solo hasta resolver su sala (o hasta pasar su rango) y las demás llamadas la reutilizan.
- Se empieza una búsqueda nueva si el jugador cambió de sala o si la búsqueda se descartó.
- Se descarta (R4) cuando una puerta cambia y toca una sala ya resuelta: una salida u -> v solo se lee al
  resolver v, así que si ninguna de las salas avisadas está resuelta, la búsqueda sigue siendo correcta.
- Pergamino de retroceso: deshacer devuelve puertas y salas a un estado anterior sin avisar. Por eso se
  registra «descartar» en el historial cada vez que la búsqueda se crea o se extiende y cada vez que llega
  un aviso de puerta. Deshacer un intervalo en el que no pasó nada de eso la conserva.

La respuesta es siempre la misma que la de paso_desde_cero (FR-114): reutilizar solo ahorra trabajo.
Los contadores 'reutilizaciones' y 'recalculos' son para el bench; no son estado del juego.
"""
from Logic.BusquedaCostoMinimo import BusquedaCostoMinimo


class RutasHaciaJugador:
    """La búsqueda compartida por los cazadores y cuándo se descarta."""

    def __init__(self, grafo, historial=None) -> None:
        self.busqueda = BusquedaCostoMinimo(grafo)     # se crea una vez; reiniciar reutiliza sus arrays
        self.valida = False
        self.historial = historial
        self.reutilizaciones = 0
        self.recalculos = 0

    def decidir(self, sala_cazador: int, sala_jugador: int, rango: int | None) -> tuple[int, int] | None:
        """
        (destino, costo) del paso del cazador hacia el jugador por una ruta de costo mínimo d <= rango, o None
        para esperar (sin ruta, d > rango o ya está en la sala del jugador). Igual que paso_desde_cero.
        """
        if sala_cazador == sala_jugador:
            return None
        nueva = not self.valida or self.busqueda.origen != sala_jugador
        if nueva:
            self.busqueda.reiniciar(sala_jugador)
            self.valida = True
            self.recalculos += 1
        else:
            self.reutilizaciones += 1
        resueltas = self.busqueda.resueltas
        d = self.busqueda.distancia_hasta(sala_cazador, rango)
        if nueva or self.busqueda.resueltas != resueltas:
            self._registrar_descarte()                  # deshacer este intervalo la vuelve a calcular
        if d is None:
            return None
        return self.busqueda.paso_hacia_origen(sala_cazador, d)

    def puerta_cambio(self, a: int, b: int) -> None:
        """Aviso de la Mazmorra: cambiaron las caras de una puerta cuyos destinos son a y b."""
        if self.valida and (self.busqueda.esta_resuelta(a) or self.busqueda.esta_resuelta(b)):
            self.descartar()
        self._registrar_descarte()                      # deshacer el cambio de la puerta no avisa

    def descartar(self) -> None:
        self.valida = False

    def _registrar_descarte(self) -> None:
        if self.historial is not None:
            self.historial.registrar_cambio(self.descartar)
