"""
VerificadorResolubilidad (Integrante 2, feature 003): decide si una cripta es resoluble y arma el reporte
(data-model §3; contracts/contrato-reporte-resolubilidad.md).

    verificar(cripta, salas, ubicaciones) -> ReporteResolubilidadDTO

Sin estado entre llamadas. Lógica: no importa Data ni Service y supone datos válidos (Data ya validó FR-321 y FR-323).
Regla del veredicto (FR-304, FR-322):
    hay_puerta_de_salida falso                          -> NO_RESOLUBLE con motivo
    llave_salida obtenida y caras_de_salida no vacía    -> RESOLUBLE con el orden de las oleadas
    cualquier otro caso                                 -> NO_RESOLUBLE sin motivo
No se mira alcanzable[sala_salida]: llegar por una salida abierta o por una cara que pide otra llave no cuenta.

Si no es resoluble, el reporte sale del MISMO recorrido (NFR-303), sin recorridos por llave: la frontera y la fase
hacia afuera de RecorridoLlaves y los ciclos de CiclosLlaves; aquí solo se traducen los índices a DTO, ya ordenados.
"""
from DTO.CriptaDTO import CriptaDTO
from DTO.ReporteResolubilidadDTO import (NO_RESOLUBLE, RESOLUBLE, CicloLlavesDTO, DependienteCicloDTO,
                                         LlaveNoObtenibleDTO, PasoCicloDTO, PuertaLlaveDTO, ReporteResolubilidadDTO)
from DTO.SalaDTO import SalaDTO
from DTO.UbicacionLlaveDTO import UbicacionLlaveDTO
from Logic.CiclosLlaves import CiclosLlaves
from Logic.GrafoLlaves import CERRADA_CON_LLAVE, GrafoLlaves
from Logic.RecorridoLlaves import RecorridoLlaves


def verificar(cripta: CriptaDTO, salas: list[SalaDTO], ubicaciones: list[UbicacionLlaveDTO]) -> ReporteResolubilidadDTO:
    """Veredicto y reporte de la cripta. No modifica lo que recibe ni ningún estado del juego (FR-301)."""
    grafo = GrafoLlaves(cripta, salas, ubicaciones)
    recorrido = RecorridoLlaves(grafo)
    recorrido.recorrer()
    if grafo.hay_puerta_de_salida and recorrido.obtenida(grafo.llave_salida) and len(recorrido.caras_de_salida) > 0:
        return ReporteResolubilidadDTO(cripta.id, RESOLUBLE, cripta.version, cripta.llave_salida,
                                       orden_llaves=[grafo.ids[k] for k in recorrido.orden])
    recorrido.calcular_frontera()
    recorrido.fase_hacia_afuera()
    ciclos = CiclosLlaves(grafo, recorrido)
    motivo = None if grafo.hay_puerta_de_salida else motivo_sin_puerta_de_salida(cripta)
    return ReporteResolubilidadDTO(cripta.id, NO_RESOLUBLE, cripta.version, cripta.llave_salida,
                                   llaves_no_obtenibles=_no_obtenibles(grafo, recorrido),
                                   frontera=[_puerta(grafo, c) for c in recorrido.frontera],
                                   ciclos=_ciclos(grafo, ciclos), motivo=motivo)


def motivo_sin_puerta_de_salida(cripta: CriptaDTO) -> str:
    """Texto del motivo de FR-322, listo para mostrar (lo arma Lógica para que consola y ventana digan lo mismo)."""
    return (f"Ninguna puerta cerrada por la que se entra a la sala de salida {cripta.sala_salida} pide "
            f"{cripta.llave_salida} desde la sala de la que se entra (las puertas que piden {cripta.llave_salida} "
            f"pero no llevan a la sala {cripta.sala_salida} no cuentan): la victoria es imposible (§3.5, P1 §2.12).")


# ------------------------------------------------------------ traducción a DTO
def _puerta(grafo: GrafoLlaves, c: int) -> PuertaLlaveDTO:
    """La cara c vista desde su sala; llave None si es «sin llave»."""
    llave = grafo.ids[grafo.llave_cara[c]] if grafo.tipo_cara[c] == CERRADA_CON_LLAVE else None
    return PuertaLlaveDTO(c // 4, c % 4, grafo.destino[c], llave)


def _no_obtenibles(grafo: GrafoLlaves, recorrido: RecorridoLlaves) -> list[LlaveNoObtenibleDTO]:
    """FR-307 y FR-309: todas las no obtenidas, por id, con sus ubicaciones distintas en orden (vacía ⇒ «sin ubicación»)."""
    resultado: list[LlaveNoObtenibleDTO] = []
    for k in range(grafo.cantidad_llaves):
        if recorrido.obtenida(k):
            continue
        ubicaciones = [grafo.ubicaciones[p] for p in range(grafo.inicio_ubic[k], grafo.fin_ubic[k])]
        resultado.append(LlaveNoObtenibleDTO(grafo.ids[k], ubicaciones))
    return resultado


def _ciclos(grafo: GrafoLlaves, ciclos: CiclosLlaves) -> list[CicloLlavesDTO]:
    """FR-310: cada ciclo con sus pasos y, a continuación, sus dependientes (las de entrada −1 no aparecen aquí)."""
    resultado: list[CicloLlavesDTO] = []
    for numero in range(len(ciclos.ciclos)):
        pasos = [PasoCicloDTO(grafo.ids[k], grafo.ubicaciones[ciclos.ubic_usada[k]], _puerta(grafo, ciclos.puerta_usada[k]))
                 for k in ciclos.ciclos[numero]]
        dependientes = [DependienteCicloDTO(grafo.ids[k], grafo.ubicaciones[ciclos.ubic_usada[k]],
                                            _puerta(grafo, ciclos.puerta_usada[k]), grafo.ids[ciclos.entrada[k]])
                        for k in ciclos.dependientes[numero]]
        resultado.append(CicloLlavesDTO(pasos, dependientes))
    return resultado
