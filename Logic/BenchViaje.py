"""
BenchViaje (Lógica, integrante 3, feature 002, T120): mediciones de --bench del paso de «ir a» (NFR-250, NFR-251, SC-252,
escenario A32; Principio VIII). Mismo cronómetro y formato que Logic/BenchMapaConocido.py, del que se reutilizan
armar_cuadricula y mapa_completo, y de Logic/BenchLogica.py, SEMILLA, _cronometrar y _mejor_y_mediana, sin modificarlos.

Cargas SINTÉTICAS y deterministas (Principios VI y VIII): cuadrículas de lado 10, 32 y 100 (100, 1 024 y 10 000 salas) y una
cuadrícula de 15 × 20 = 300 salas, el tamaño de la cripta de referencia cripta-06 (SC-252), con costos de
random.Random(SEMILLA) entre 1 y 300 y el mapa conocido completo. El paso va desde la esquina 1 hacia la sala opuesta.

  V1   armar el GrafoMapaConocido, con su primera entradas      una vez por viaje (ServicioIrA lo guarda)
  V2   un paso con el grafo ya armado: decidir_paso             lo que cuesta cada paso después del primero
  V3   un paso completo: grafo nuevo + decidir_paso             el peor caso; es el que se compara con NFR-250 (< 5 ms)

El criterio de NFR-250 se anota en la fila V3 del tamaño de referencia (300 salas). Los demás tamaños son evidencia.
Si cripta-06 está en el paquete, ServicioBench agrega además la medición con esa cripta (medir_paso_en). Sin dict, set ni
sorted. Corre sin vista (Principio V).
"""
import random

from DTO.Direcciones import E, N, O, S
from DTO.ResultadoBenchDTO import ResultadoBenchDTO
from DTO.SalaDTO import SalaDTO, SalidaDTO
from Logic.BenchLogica import SEMILLA, _cronometrar, _mejor_y_mediana
from Logic.BenchMapaConocido import armar_cuadricula, mapa_completo
from Logic.GrafoMapaConocido import GrafoMapaConocido
from Logic.Mazmorra import Mazmorra
from Logic.ViajeAutomatico import decidir_paso

SUBSISTEMA = "viaje automático"
LIMITE_PASO_MS = 5                      # NFR-250, SC-252
CRIPTA_REFERENCIA = "cripta-06"
FILAS_REFERENCIA = 15                   # 15 × 20 = 300 salas, el tamaño de cripta-06
COLUMNAS_REFERENCIA = 20
OPUESTA = [S, N, O, E]


def medir(lados=(10, 32, 100), repeticiones: int = 9, filas: int = FILAS_REFERENCIA,
          columnas: int = COLUMNAS_REFERENCIA) -> list[ResultadoBenchDTO]:
    resultados = []
    for lado in lados:
        mazmorra = armar_cuadricula(lado)
        resultados.extend(medir_en(mazmorra, repeticiones, f"cuadrícula {lado} × {lado}", False))
    mazmorra = mazmorra_de(armar_rectangulo(filas, columnas))
    resultados.extend(medir_en(mazmorra, repeticiones,
                               f"cuadrícula sintética {filas} × {columnas} = {filas * columnas} salas, el tamaño de "
                               f"{CRIPTA_REFERENCIA}", True))
    return resultados


def armar_rectangulo(filas: int, columnas: int) -> list[SalaDTO]:
    azar = random.Random(SEMILLA)
    salidas = []
    for f in range(filas):
        for c in range(columnas):
            salidas.append([None, None, None, None])
    for f in range(filas):
        for c in range(columnas):
            id_sala = f * columnas + c + 1
            for direccion in (S, E):                      # cada par se sortea una vez, desde su sala menor
                if direccion == S and f < filas - 1:
                    otra = id_sala + columnas
                elif direccion == E and c < columnas - 1:
                    otra = id_sala + 1
                else:
                    continue
                costo = azar.randint(1, 300)
                salidas[id_sala - 1][direccion] = SalidaDTO(otra, costo=costo)
                salidas[otra - 1][OPUESTA[direccion]] = SalidaDTO(id_sala, costo=costo)
    salas = []
    for i in range(filas * columnas):
        salas.append(SalaDTO(i + 1, f"Sala {i + 1}", salidas[i], "v"))
    return salas


def mazmorra_de(salas: list[SalaDTO]) -> Mazmorra:
    mazmorra = Mazmorra(len(salas), "itm_llave")
    mazmorra.cargar_esqueleto(salas)
    return mazmorra


def paso_completo(mapa, mazmorra: Mazmorra, origen: int, destino: int):
    return decidir_paso(GrafoMapaConocido(mapa), mapa, mazmorra, origen, destino)


def medir_en(mazmorra: Mazmorra, repeticiones: int, etiqueta: str, es_referencia: bool, origen: int = 1,
             destino: int | None = None) -> list[ResultadoBenchDTO]:
    n = len(mazmorra.salas) - 1
    mapa = mapa_completo(mazmorra)
    destino = n if destino is None else destino
    armado = GrafoMapaConocido(mapa)
    armado.entradas(destino)
    decision = decidir_paso(armado, mapa, mazmorra, origen, destino)
    resultado = [None]

    def solo_paso():
        resultado[0] = decidir_paso(armado, mapa, mazmorra, origen, destino)

    def completo():
        resultado[0] = paso_completo(mapa, mazmorra, origen, destino)

    filas = []
    mejor, mediana = _mejor_y_mediana(_cronometrar(lambda: GrafoMapaConocido(mapa).entradas(destino), repeticiones))
    filas.append(ResultadoBenchDTO(SUBSISTEMA, "V1 armar el grafo (una vez por viaje)", n, mejor, mediana,
                                   f"{etiqueta}; constructor + índice inverso de entradas, O(S + E); "
                                   f"{1000000 * mediana / n:.1f} ns por sala"))
    mejor, mediana = _mejor_y_mediana(_cronometrar(solo_paso, repeticiones))
    filas.append(ResultadoBenchDTO(SUBSISTEMA, "V2 un paso con el grafo armado", n, mejor, mediana,
                                   f"{etiqueta}; decidir_paso desde la sala {origen} hacia la sala {destino}; "
                                   f"decisión {decision}"))
    mejor, mediana = _mejor_y_mediana(_cronometrar(completo, repeticiones))
    nota = f"{etiqueta}; grafo nuevo + decidir_paso (peor caso: ServicioIrA arma el grafo una vez por viaje)"
    if es_referencia:
        cumple = "cumple" if mediana < LIMITE_PASO_MS else "NO cumple"
        nota += f"; mediana {mediana:.3f} ms contra {LIMITE_PASO_MS} ms (NFR-250, SC-252): {cumple}"
    filas.append(ResultadoBenchDTO(SUBSISTEMA, "V3 un paso completo: grafo nuevo + un paso", n, mejor, mediana, nota))
    return filas
