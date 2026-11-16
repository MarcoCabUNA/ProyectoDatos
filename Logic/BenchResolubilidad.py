"""
BenchResolubilidad (Integrante 2, feature 003): criptas sintéticas para medir la verificación de resolubilidad
(research R7, NFR-304). Por ahora solo el generador de cuadrícula; las mediciones de --bench llegan en la fase 9.

cripta_en_cuadricula(filas, columnas, semilla, resoluble), determinista por semilla (random.Random):
  - filas × columnas salas; la sala (fila, columna) tiene id fila*columnas + columna + 1; sala_inicial es (0, 0);
  - salidas abiertas entre vecinas de la misma columna;
  - entre la columna c y la c + 1, puertas cerradas que piden la llave c (llaves encadenadas; una llave abre varias);
  - la llave c está en una fila de la columna c elegida por la semilla; el orden de la lista de ubicaciones también
    se mezcla con la semilla (el resultado no debe depender de él, FR-306);
  - sala_salida es (0, última columna); su única entrada es la puerta desde (1, última columna), que pide
    llave_salida, ubicada en la última columna (en una fila ≥ 1). Por eso se exigen filas ≥ 2;
  - llaves: columnas − 1 de las fronteras más llave_salida;
  - variante no resoluble: se mueve SOLO la llave de la columna m = (columnas − 1) // 2 a la columna m + 1, detrás de
    las puertas que la piden: un ciclo de un paso (m → m) y una cadena de unas K/2 dependientes de m.
Sin datos de criptas publicadas (Principio VI). Lógica: no importa Data ni Service.
"""
import random

from DTO.CriptaDTO import CriptaDTO
from DTO.Direcciones import E, N, O, S
from DTO.SalaDTO import SalaDTO, SalidaDTO
from DTO.UbicacionLlaveDTO import UbicacionLlaveDTO

LLAVE_SALIDA = "llave_salida"


def _id_llave(columna: int) -> str:
    """Id de la llave de la frontera columna → columna + 1. Con ceros a la izquierda: el orden de id es el de columna."""
    return f"llave_{columna:05d}"


def cripta_en_cuadricula(filas: int, columnas: int, semilla: int,
                         resoluble: bool) -> tuple[CriptaDTO, list[SalaDTO], list[UbicacionLlaveDTO]]:
    """Cripta sintética en cuadrícula con llaves encadenadas (research R7). Lanza ValueError si filas < 2."""
    if filas < 2:
        raise ValueError(f"la cuadrícula necesita al menos 2 filas (se pidieron {filas})")
    if columnas < 2:
        raise ValueError(f"la cuadrícula necesita al menos 2 columnas (se pidieron {columnas})")
    ultima = columnas - 1

    def id_sala(fila: int, columna: int) -> int:
        return fila * columnas + columna + 1

    salas: list[SalaDTO] = []
    for fila in range(filas):
        for columna in range(columnas):
            salidas: list[SalidaDTO | None] = [None, None, None, None]
            if fila > 0:
                if columna == ultima and fila == 1:      # la entrada a sala_salida: pide llave_salida
                    salidas[N] = SalidaDTO(id_sala(0, columna), True, LLAVE_SALIDA)
                else:
                    salidas[N] = SalidaDTO(id_sala(fila - 1, columna))
            if fila < filas - 1:
                if columna == ultima and fila == 0:      # la vuelta desde sala_salida pide lo mismo
                    salidas[S] = SalidaDTO(id_sala(1, columna), True, LLAVE_SALIDA)
                else:
                    salidas[S] = SalidaDTO(id_sala(fila + 1, columna))
            entra_a_salida = fila == 0 and columna + 1 == ultima
            sale_de_salida = fila == 0 and columna == ultima
            if columna < ultima and not entra_a_salida:
                salidas[E] = SalidaDTO(id_sala(fila, columna + 1), True, _id_llave(columna))
            if columna > 0 and not sale_de_salida:
                salidas[O] = SalidaDTO(id_sala(fila, columna - 1), True, _id_llave(columna - 1))
            salas.append(SalaDTO(id_sala(fila, columna), f"Sala {id_sala(fila, columna)}", salidas, "bench"))

    generador = random.Random(semilla)
    medio = (columnas - 1) // 2
    ubicaciones: list[UbicacionLlaveDTO] = []
    for columna in range(ultima):
        fila = generador.randrange(filas)
        destino = columna + 1 if (not resoluble and columna == medio) else columna
        if destino == ultima and fila == 0:
            fila = 1                                     # sala_salida no guarda llaves
        ubicaciones.append(UbicacionLlaveDTO(_id_llave(columna), id_sala(fila, destino)))
    ubicaciones.append(UbicacionLlaveDTO(LLAVE_SALIDA, id_sala(generador.randrange(1, filas), ultima)))
    generador.shuffle(ubicaciones)

    cripta = CriptaDTO(id="bench", version="bench", salas_total=filas * columnas, paginas=1,
                       salas_por_pagina=filas * columnas, sala_inicial=id_sala(0, 0), sala_salida=id_sala(0, ultima),
                       llave_salida=LLAVE_SALIDA, presupuesto_solicitudes=1, inventario_max=10, jugador_vida_max=30,
                       jugador_ataque=6, jugador_defensa=2, jugador_velocidad=100)
    return cripta, salas, ubicaciones
