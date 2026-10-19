"""
ServicioBench (Servicios; lo arma Integrante 2, acordado con el equipo): el modo --bench (§5.3).

Corre las mediciones de los tres integrantes con cargas sintéticas y devuelve una lista de
ResultadoBenchDTO. No instancia la Vista ni lee el teclado (§6: --bench debe correr sin la interfaz).

Cada integrante tiene SU archivo de mediciones, así nadie edita el de otro:
    Service/BenchDatos.py        Integrante 2: caché, fichas liberadas, precarga, guardado y bitácora
    Logic/BenchLogica.py         Integrante 1: agenda de eventos y ciclo de eventos < 20 ms (§5.2)
                                 (vive en Lógica porque mide Lógica; trae su propio cronómetro con el
                                 mismo método, porque Lógica no importa Servicios)
    Service/BenchInventario.py   Integrante 3: inventario, historial de retroceso y ordenamientos
Todos miden igual: mejor y mediana de N repeticiones (Service/Cronometro.py).

Uso (desde el Controlador / main.py, cuando config.bench es True):
    resultados = ServicioBench().ejecutar()
    print(ServicioBench.tabla_texto(resultados))
O directamente, desde la raíz del proyecto:
    python -m Service.ServicioBench
"""
from DTO.ResultadoBenchDTO import ResultadoBenchDTO
from Logic import BenchLogica
from Service import BenchDatos, BenchInventario

_COLUMNAS = ["subsistema", "caso", "tamaño", "mejor ms", "mediana ms", "nota"]


class ServicioBench:

    def __init__(self, mediciones=None):
        """
        mediciones: funciones sin argumentos que devuelven list[ResultadoBenchDTO].
        Por defecto, las de los tres integrantes, en orden: Datos, Lógica, Inventario.
        """
        self._mediciones = (mediciones if mediciones is not None
                            else [BenchDatos.medir, BenchLogica.medir, BenchInventario.medir])

    def ejecutar(self, al_avanzar=None) -> list[ResultadoBenchDTO]:
        """
        Corre todas las mediciones y devuelve sus resultados en orden.
        al_avanzar(numero, total): opcional, se llama después de cada grupo (para mostrar avance).
        """
        resultados: list[ResultadoBenchDTO] = []
        for i in range(len(self._mediciones)):
            resultados.extend(self._mediciones[i]())
            if al_avanzar is not None:
                al_avanzar(i + 1, len(self._mediciones))
        return resultados

    @staticmethod
    def tabla_texto(resultados: list[ResultadoBenchDTO]) -> str:
        """Los resultados como una tabla de texto alineada (para imprimirla en la consola)."""
        filas = [_COLUMNAS]
        for r in resultados:
            filas.append([r.subsistema, r.caso, str(r.tamano), f"{r.mejor_ms:.3f}", f"{r.mediana_ms:.3f}", r.nota])
        anchos = [0] * len(_COLUMNAS)
        for fila in filas:
            for j in range(len(fila)):
                if len(fila[j]) > anchos[j]:
                    anchos[j] = len(fila[j])
        lineas = []
        for i in range(len(filas)):
            celdas = []
            for j in range(len(filas[i])):
                texto = filas[i][j]
                # los números a la derecha; el texto a la izquierda; la nota sin relleno al final
                if j == len(filas[i]) - 1:
                    celdas.append(texto)
                elif 2 <= j <= 4:
                    celdas.append(texto.rjust(anchos[j]))
                else:
                    celdas.append(texto.ljust(anchos[j]))
            lineas.append(" | ".join(celdas))
            if i == 0:
                lineas.append("-+-".join("-" * anchos[j] for j in range(len(anchos))))
        return "\n".join(lineas)


if __name__ == "__main__":
    print("Midiendo (puede tardar unos segundos)...")
    print(ServicioBench.tabla_texto(ServicioBench().ejecutar()))