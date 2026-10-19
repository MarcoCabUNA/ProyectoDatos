"""
Convención de direcciones compartida por los tres integrantes.

Las salidas de una sala se guardan en un array de 4 posiciones:
    índice 0 = N, 1 = S, 2 = E, 3 = O
Una posición sin salida se guarda como None.
AccionDTO (Kristel) usa estos mismos índices en su campo 'direccion'.
"""

N = 0
S = 1
E = 2
O = 3

# Array de letras en el orden de los índices. Solo se lee; no se modifica.
DIRECCIONES = ["N", "S", "E", "O"]


def indice_direccion(letra: str) -> int:
    """'N' -> 0, 'S' -> 1, 'E' -> 2, 'O' -> 3. Lanza ValueError si la letra no existe."""
    for i in range(len(DIRECCIONES)):
        if DIRECCIONES[i] == letra:
            return i
    raise ValueError(f"Dirección desconocida: {letra!r} (se esperaba N, S, E u O)")