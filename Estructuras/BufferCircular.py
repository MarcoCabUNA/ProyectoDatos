"""
BufferCircular (Integrante 3): guarda solo los últimos N elementos con memoria constante (§4.8).

Pensado para la bitácora en pantalla: la interfaz muestra únicamente los últimos 20 mensajes.

    posiciones:   [0] [1] [2] [3] [4]      capacidad = 5, ya se agregaron 7 elementos
    contenido:     f   g   c   d   e       _inicio = 2: el más antiguo está en la posición 2
                       ^               a_array() -> c, d, e, f, g   (del más antiguo al más reciente)

Un array de tamaño fijo y un índice que da la vuelta. Cuando está lleno, un elemento nuevo
sobrescribe al más antiguo y el índice avanza una posición: nunca se desplazan los demás.

Alternativas descartadas (la sección de decisiones debe medirlas):
    - Un array al que se le quita el primer elemento al pasar del límite: cada mensaje nuevo
      desplaza físicamente los otros 19, O(N) por mensaje.
    - collections.deque: el enunciado prohíbe sustituir las estructuras por las de bibliotecas.

Costos:
    agregar            O(1)   siempre, esté lleno o no
    a_array            O(N)   copia en orden cronológico (N = capacidad como máximo)
Memoria: O(capacidad), constante durante toda la partida.
Regla del equipo: no cambiar los nombres de los métodos sin avisar a los demás.
"""


class BufferCircular:

    def __init__(self, capacidad: int):
        if capacidad < 1:
            raise ValueError("la capacidad del buffer debe ser al menos 1")
        self._capacidad = capacidad
        self._datos = [None] * capacidad     # tamaño fijo: no crece nunca
        self._inicio = 0                     # posición del elemento más antiguo
        self._cantidad = 0

    def agregar(self, elemento) -> None:
        """Agrega un elemento; si está lleno, reemplaza al más antiguo."""
        if self._cantidad < self._capacidad:
            self._datos[(self._inicio + self._cantidad) % self._capacidad] = elemento
            self._cantidad += 1
        else:
            self._datos[self._inicio] = elemento                       # sobrescribe el más antiguo
            self._inicio = (self._inicio + 1) % self._capacidad

    def a_array(self) -> list:
        """Copia en un array, del más antiguo al más reciente (orden cronológico)."""
        resultado = []
        for i in range(self._cantidad):
            resultado.append(self._datos[(self._inicio + i) % self._capacidad])
        return resultado