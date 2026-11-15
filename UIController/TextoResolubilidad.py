"""
TextoResolubilidad (Integrante 2, feature 003): el reporte de resolubilidad como líneas de texto, con el formato de
specs/003-resolubilidad/contracts/contrato-reporte-resolubilidad.md («Texto de consola»; FR-314, FR-315).

    for linea in lineas_reporte(reporte):      # reporte: ReporteResolubilidadDTO
        print(linea)

No calcula nada: solo da formato a lo que trae el DTO, que llega completo y ya ordenado. No importa pygame, así que
sirve para --verificar y la vista puede reutilizarlo para que el texto sea idéntico (FR-315).
"""
from DTO.Direcciones import DIRECCIONES
from DTO.ReporteResolubilidadDTO import (NO_CONCLUYO, RESOLUBLE, CicloLlavesDTO, PuertaLlaveDTO,
                                         ReporteResolubilidadDTO)
from DTO.UbicacionLlaveDTO import UbicacionLlaveDTO

_GUION = "–"          # «puerta 2–6»: guion corto (en dash), como en la spec
_FLECHA = " → "


def lineas_reporte(reporte: ReporteResolubilidadDTO) -> list[str]:
    """Las líneas del reporte, en el orden del contrato. Las secciones vacías no se escriben."""
    if reporte.veredicto == NO_CONCLUYO:          # FR-323: sin veredicto, solo el encabezado y el error con contexto
        return [f"Cripta {reporte.id_cripta}: la verificación NO CONCLUYÓ", reporte.mensaje or ""]
    if reporte.veredicto == RESOLUBLE:
        return [_encabezado(reporte, "RESOLUBLE"),
                "Orden de obtención de llaves: " + ", ".join(reporte.orden_llaves)]
    lineas = [_encabezado(reporte, "NO RESOLUBLE")]
    if reporte.motivo is not None:
        lineas.append(f"Motivo: {reporte.motivo}")
    if len(reporte.llaves_no_obtenibles) > 0:
        lineas.append("Llaves no obtenibles:")
        for llave in reporte.llaves_no_obtenibles:
            lugares = "; ".join(_ubicacion(u) for u in llave.ubicaciones) if len(llave.ubicaciones) > 0 \
                else "sin ubicación"
            lineas.append(f"  - {llave.id}: {lugares}")
    if len(reporte.frontera) > 0:
        lineas.append("Frontera bloqueada:")
        for puerta in reporte.frontera:
            lineas.append(f"  - {_puerta(puerta)} (desde la sala {puerta.sala_origen}, salida "
                          f"{DIRECCIONES[puerta.direccion]}): {_requisito(puerta)}")
    if len(reporte.ciclos) > 0:
        lineas.append("Ciclos:")
        for numero in range(len(reporte.ciclos)):
            lineas.extend(_ciclo(numero + 1, reporte.ciclos[numero]))
    return lineas


# ------------------------------------------------------------ partes
def _encabezado(reporte: ReporteResolubilidadDTO, veredicto: str) -> str:
    version = f" (versión {reporte.version_cripta})" if reporte.version_cripta is not None else ""
    return f"Cripta {reporte.id_cripta}{version}: {veredicto}"


def _ubicacion(u: UbicacionLlaveDTO) -> str:
    """«sala 12» o «sala 12 (enemigo e-1203)»."""
    return f"sala {u.sala}" if u.enemigo is None else f"sala {u.sala} (enemigo {u.enemigo})"


def _puerta(p: PuertaLlaveDTO) -> str:
    return f"puerta {p.sala_origen}{_GUION}{p.sala_destino}"


def _requisito(p: PuertaLlaveDTO) -> str:
    """FR-308: la llave que pide esa cara, o que no tiene llave."""
    return f"requiere {p.llave}" if p.llave is not None else "sin llave: no se puede abrir"


def _ciclo(numero: int, ciclo: CicloLlavesDTO) -> list[str]:
    """FR-310: «N. A está en la sala 6 → la puerta 2–6 requiere B → …» y debajo sus dependientes."""
    partes = []
    for paso in ciclo.pasos:
        partes.append(f"{paso.llave} está en la {_ubicacion(paso.ubicacion)}")
        partes.append(f"la {_puerta(paso.puerta)} {_requisito(paso.puerta)}")
    lineas = [f"  {numero}. " + _FLECHA.join(partes)]
    for dependiente in ciclo.dependientes:
        lineas.append(f"     - {dependiente.llave} ({_ubicacion(dependiente.ubicacion)}, {_puerta(dependiente.puerta)} "
                      f"{_requisito(dependiente.puerta)}) depende de {dependiente.depende_de}")
    return lineas
