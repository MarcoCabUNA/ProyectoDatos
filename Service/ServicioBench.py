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
    Logic/BenchResolubilidad.py  Integrante 2 (feature 003): verificación de resolubilidad, B1 a B6 (research R7)
Todos miden igual: mejor y mediana de N repeticiones (Service/Cronometro.py).

Además, justo después de las filas de BenchResolubilidad, la fila de la verificación de la CRIPTA CON MÁS SALAS DEL
PAQUETE LOCAL (NFR-301, SC-306): elegida por cantidad de salas entre las que traen llaves.json, sin nombrar ids
(Principio VI) y leída sin red con FuenteOffline, GestorEsqueleto y GestorLlaves sin almacén; se cronometra solo
VerificadorResolubilidad.verificar. No inicia partidas, no crea partida.log ni pasa por ServicioResolubilidad (FR-301).
Si el paquete no trae criptas con llaves.json, la medición no se agrega y una fila sin tiempos dice por qué.

Uso (desde el Controlador / main.py, cuando config.bench es True):
    resultados = ServicioBench().ejecutar()
    print(ServicioBench.tabla_texto(resultados))
O directamente, desde la raíz del proyecto:
    python -m Service.ServicioBench
"""
from Data.ClienteHttp import ErrorRed
from Data.FuenteOffline import CARPETA_POR_DEFECTO, FuenteOffline
from Data.GestorEsqueleto import GestorEsqueleto
from Data.GestorLlaves import GestorLlaves
from DTO.ResultadoBenchDTO import ResultadoBenchDTO
from Logic import BenchLogica, BenchMapaConocido, BenchResolubilidad, VerificadorResolubilidad
from Service import BenchDatos, BenchInventario
from Service.Cronometro import REPETICIONES_POR_DEFECTO, medir

_COLUMNAS = ["subsistema", "caso", "tamaño", "mejor ms", "mediana ms", "nota"]
_CASO_PAQUETE = "verificación de la cripta con más salas del paquete"


class ServicioBench:

    def __init__(self, mediciones=None, carpeta_paquete: str = CARPETA_POR_DEFECTO):
        """
        mediciones: funciones sin argumentos que devuelven list[ResultadoBenchDTO].
        Por defecto, las de los tres integrantes, en orden: Datos, Lógica, resolubilidad (feature 003, justo después
        de Lógica), mapa conocido (feature 002), Inventario.
        carpeta_paquete: el paquete offline del que sale la fila de la cripta con más salas (se agrega justo después
        de las filas de BenchResolubilidad.medir, si está en la lista). Se lee recién al medir.
        """
        self._mediciones = (mediciones if mediciones is not None
                            else [BenchDatos.medir, BenchLogica.medir, BenchResolubilidad.medir,
                                  BenchMapaConocido.medir, BenchInventario.medir])
        self._carpeta_paquete = carpeta_paquete

    def ejecutar(self, al_avanzar=None) -> list[ResultadoBenchDTO]:
        """
        Corre todas las mediciones y devuelve sus resultados en orden.
        al_avanzar(numero, total): opcional, se llama después de cada grupo (para mostrar avance).
        """
        resultados: list[ResultadoBenchDTO] = []
        for i in range(len(self._mediciones)):
            resultados.extend(self._mediciones[i]())
            if self._mediciones[i] is BenchResolubilidad.medir:
                resultados.extend(self.medir_cripta_del_paquete())
            if al_avanzar is not None:
                al_avanzar(i + 1, len(self._mediciones))
        return resultados

    def medir_cripta_del_paquete(self, repeticiones: int = REPETICIONES_POR_DEFECTO) -> list[ResultadoBenchDTO]:
        """
        NFR-301, SC-306: una fila con la verificación de la cripta del paquete con más salas (salas_total de sus datos
        generales; si empatan, la primera de criptas.json) entre las que traen llaves.json. Todo se lee del paquete,
        sin red y sin almacén de llaves; solo se cronometra VerificadorResolubilidad.verificar. Si no hay ninguna
        (o no hay paquete, o la elegida no se puede leer), una fila sin tiempos cuya nota dice por qué.
        """
        try:
            fuente = FuenteOffline(self._carpeta_paquete)
            resumenes = fuente.listar_criptas()
        except ErrorRed as error:
            return [_sin_medicion(f"no se pudo leer el paquete ({error})")]
        elegida = None
        con_llaves = 0
        for resumen in resumenes:
            try:
                cripta = fuente.obtener_datos_generales(resumen.id)
                fuente.obtener_llaves(resumen.id)             # ¿trae llaves.json?
            except ErrorRed:
                continue
            con_llaves += 1
            if elegida is None or cripta.salas_total > elegida.salas_total:
                elegida = cripta
        if elegida is None:
            return [_sin_medicion(f"ninguna de sus {len(resumenes)} criptas trae llaves.json")]
        try:
            esqueleto = GestorEsqueleto(fuente)
            esqueleto.cargar(elegida)
            ubicaciones = GestorLlaves(fuente, None).obtener(elegida, esqueleto)
        except ErrorRed as error:
            return [_sin_medicion(f"no se pudo leer la cripta con más salas del paquete ({error})")]
        salas = [esqueleto.obtener_sala(i) for i in esqueleto.ids_salas()]

        def verificar():
            return VerificadorResolubilidad.verificar(elegida, salas, ubicaciones)

        veredicto = verificar().veredicto
        mejor, mediana = medir(verificar, repeticiones)
        nota = (f"{elegida.id} versión {elegida.version}: {veredicto}, {len(ubicaciones)} ubicaciones de llaves; "
                f"la de más salas entre {con_llaves} criptas del paquete con llaves.json; leída sin red; "
                f"{repeticiones} repeticiones")
        return [ResultadoBenchDTO(BenchResolubilidad.SUBSISTEMA, _CASO_PAQUETE, len(salas), mejor, mediana, nota)]

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


def _sin_medicion(motivo: str) -> ResultadoBenchDTO:
    """La fila del paquete cuando no se midió: sin tiempos, y la nota dice por qué y qué fila vale en su lugar."""
    return ResultadoBenchDTO(BenchResolubilidad.SUBSISTEMA, f"{_CASO_PAQUETE} (no medida)", 0, 0.0, 0.0,
                             f"no se agregó la medición: no hay una cripta del paquete con llaves.json que medir "
                             f"({motivo}); mientras tanto vale B1 con 1000 salas")


if __name__ == "__main__":
    print("Midiendo (puede tardar unos segundos)...")
    print(ServicioBench.tabla_texto(ServicioBench().ejecutar()))