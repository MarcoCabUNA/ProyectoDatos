"""
ReporteDatos (Integrante 2): arma el ReporteDatosDTO del final de la partida (enunciado §6.1).

Los contadores ya existen, cada uno en la clase que hace el trabajo:
    FuenteDatos         solicitudes realizadas (incluye reintentos tras un 429) y presupuesto
    ResolvedorCatalogo  aciertos y fallos de caché, lecturas de disco, fichas y lotes de catálogo
    GestorContenido     lotes de contenido y salas pedidas
Esta función solo los junta en un DTO, para que Servicios lo entregue a la Vista (o a --bench)
sin conocer esas clases. No hace solicitudes ni modifica nada: se puede llamar cuantas veces se quiera.
"""
from Data.FuenteDatos import FuenteDatos
from Data.FuenteOffline import FuenteOffline
from Data.GestorContenido import GestorContenido
from Data.ResolvedorCatalogo import ResolvedorCatalogo
from DTO.CriptaDTO import CriptaDTO
from DTO.ReporteDatosDTO import ReporteDatosDTO


def generar_reporte(fuente: FuenteDatos, resolvedor: ResolvedorCatalogo,
                    gestor: GestorContenido | None = None,
                    cripta: CriptaDTO | None = None) -> ReporteDatosDTO:
    """
    fuente:     la misma FuenteRed o FuenteOffline que usó la partida.
    resolvedor: el ResolvedorCatalogo de la partida (caché en memoria y en disco).
    gestor:     opcional; sin él, los datos de la precarga quedan en 0.
    cripta:     opcional; si la fuente no conoce el presupuesto (por ejemplo en --offline),
                se toma de los datos generales de la cripta.
    """
    presupuesto = fuente.presupuesto_solicitudes()
    if presupuesto is None and cripta is not None:
        presupuesto = cripta.presupuesto_solicitudes
    return ReporteDatosDTO(
        solicitudes_realizadas=fuente.solicitudes_realizadas(),
        presupuesto=presupuesto,
        aciertos_cache=resolvedor.aciertos(),
        fallos_cache=resolvedor.fallos(),
        lecturas_disco=resolvedor.lecturas_disco(),
        fichas_descargadas=resolvedor.fichas_descargadas(),
        solicitudes_catalogo=resolvedor.solicitudes_catalogo(),
        lotes_contenido=gestor.lotes_realizados() if gestor is not None else 0,
        salas_pedidas=gestor.salas_pedidas() if gestor is not None else 0,
        offline=isinstance(fuente, FuenteOffline),
    )